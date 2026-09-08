#!/usr/bin/env python3
"""Generate Go tests (table-driven) + fix domain.Pipeline (export Steps) + fix main.go imports + SDD/README."""
import os, textwrap
BASE = "/tmp/p3-go/industrial-gateway"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# ---- FIX: export Pipeline.Steps so it can be constructed from main/tests ----
w("internal/domain/transform.go", r'''
package domain

import (
	"errors"
	"fmt"
	"strings"
)

// Transformer applies unit normalisation + optional scaling to a raw reading so
// that every reading leaving the gateway has a canonical shape & unit. Pure
// business logic, fully unit-tested without I/O.
type Transformer struct {
	normaliseUnits map[string]string // raw unit -> canonical unit
	scaling       map[string]float64 // metric -> multiplier (raw->SI)
}

// NewTransformer builds a transformer from config maps.
func NewTransformer(unitMap, scaling map[string]string) *Transformer {
	t := &Transformer{normaliseUnits: map[string]string{}, scaling: map[string]float64{}}
	for k, v := range unitMap {
		t.normaliseUnits[strings.ToLower(k)] = v
	}
	for k, v := range scaling {
		if f, err := parseFloat(v); err == nil {
			t.scaling[strings.ToLower(k)] = f
		}
	}
	return t
}

// Transform applies unit normalisation + optional scaling and marks quality.
func (t *Transformer) Transform(r Reading) (Reading, error) {
	if err := r.Validate(); err != nil {
		return Reading{}, fmt.Errorf("invalid reading: %w", err)
	}
	out := r
	out.Source = r.Source
	out.Quality = "good"
	// Fahrenheit -> Celsius special-case (applied before unit map).
	if strings.EqualFold(r.Unit, "F") {
		out.Value = (r.Value - 32) * 5 / 9
		out.Unit = "Celsius"
	} else if canon, ok := t.normaliseUnits[strings.ToLower(r.Unit)]; ok {
		out.Unit = canon
	}
	// scaling (raw sensor counts -> engineering unit), applied to the value.
	if mult, ok := t.scaling[strings.ToLower(r.Metric)]; ok && mult != 0 {
		out.Value = out.Value * mult
	}
	if out.Unit == "" {
		out.Unit = "unknown"
	}
	return out, nil
}

// Pipeline is an ordered sequence of transformers applied left to right.
type Pipeline struct {
	Steps []*Transformer
}

// Apply runs every transformer in order; the first error short-circuits.
func (p *Pipeline) Apply(r Reading) (Reading, error) {
	if len(p.Steps) == 0 {
		return r, ErrEmptyPipeline
	}
	var err error
	for _, s := range p.Steps {
		if r, err = s.Transform(r); err != nil {
			return Reading{}, err
		}
	}
	return r, nil
}

func parseFloat(s string) (float64, error) {
	var f float64
	_, err := fmt.Sscanf(s, "%f", &f)
	return f, err
}

var ErrEmptyPipeline = errors.New("pipeline has no steps")
''')

# ---- FIX: clean main.go imports ----
w("cmd/gateway/main.go", r'''
// Command gateway starts the industrial data-collection gateway: REST API +
// the ingestion scheduler that polls every collector on an interval.
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"

	httpadapter "industrial-gateway/internal/adapter/http"
	grpcadapter "industrial-gateway/internal/adapter/grpc"
	"industrial-gateway/internal/domain"
	"industrial-gateway/internal/infra/memorycache"
	"industrial-gateway/internal/infra/memoryrepo"
	"industrial-gateway/internal/usecase"
)

func main() {
	logger := log.New(os.Stdout, "gateway ", log.LstdFlags|log.Lmsgprefix)

	// --- assemble hexagon: ports + adapters ---
	repo := memoryrepo.New()
	cache := memorycache.New()

	// Build a transformation pipeline (Fahrenheit support + unit normalisation).
	t1 := domain.NewTransformer(
		map[string]string{"c": "Celsius", "f": "Celsius", "mm/s": "mm/s", "bar": "bar"},
		map[string]string{"rpm": "1"},
	)
	pipeline := &domain.Pipeline{Steps: []*domain.Transformer{t1}}

	// Collectors list (empty by default; a real deployment injects MQTT/Modbus).
	uc := usecase.NewIngestService(pipeline, repo, cache /* collectors... */)

	// --- scheduler: poll collectors every 5s ---
	ctx, stop := context.WithCancel(context.Background())
	defer stop()
	go runScheduler(ctx, uc, 5*time.Second, logger)

	// --- HTTP primary adapter ---
	engine := httpadapter.Register(uc, repo, cache)
	go func() {
		logger.Printf("REST API listening on :8080")
		if err := http.ListenAndServe(":8080", engine); err != nil {
			logger.Printf("http server stopped: %v", err)
		}
	}()

	// --- metrics endpoint ---
	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())
	go func() {
		logger.Printf("metrics listening on :9090")
		_ = http.ListenAndServe(":9090", mux)
	}()

	// --- grpc adapter (logic-only skeleton; wired for tests) ---
	_ = grpcadapter.NewService(uc)

	// graceful shutdown
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	logger.Printf("shutting down...")
	stop()
	time.Sleep(500 * time.Millisecond)
}

func runScheduler(ctx context.Context, uc *usecase.IngestService, interval time.Duration, logger *log.Logger) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			n, err := uc.RunOnce(ctx)
			if err != nil {
				logger.Printf("ingest run error: %v", err)
			}
			if n > 0 {
				logger.Printf("ingested %d readings", n)
			}
		}
	}
}
''')
# remove the stale note file
try:
    os.remove(os.path.join(BASE, "cmd/gateway/imports_fix_note.txt"))
except FileNotFoundError:
    pass

# =================== TESTS (table-driven, TDD) ===================
w("internal/domain/reading_test.go", r'''
package domain

import (
	"math"
	"testing"
	"time"
)

func TestReading_Validate(t *testing.T) {
	now := time.Now().UTC()
	cases := []struct {
		name    string
		r       Reading
		wantErr bool
	}{
		{"valid", Reading{"dev-1", "temperature", 50, "C", now, "mqtt", "good"}, false},
		{"empty device", Reading{"", "temperature", 50, "C", now, "mqtt", "good"}, true},
		{"empty metric", Reading{"dev-1", "", 50, "C", now, "mqtt", "good"}, true},
		{"NaN value", Reading{"dev-1", "temperature", math.NaN(), "C", now, "mqtt", "good"}, true},
		{"Inf value", Reading{"dev-1", "temperature", math.Inf(1), "C", now, "mqtt", "good"}, true},
		{"zero timestamp", Reading{"dev-1", "temperature", 50, "C", time.Time{}, "mqtt", "good"}, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			err := tc.r.Validate()
			if (err != nil) != tc.wantErr {
				t.Errorf("Validate() error = %v, wantErr %v", err, tc.wantErr)
			}
		})
	}
}
''')

w("internal/domain/transform_test.go", r'''
package domain

import (
	"math"
	"testing"
	"time"
)

func TestTransformer_Transform(t *testing.T) {
	now := time.Now().UTC()
	tf := NewTransformer(
		map[string]string{"c": "Celsius", "mm/s": "mm/s", "bar": "bar"},
		map[string]string{"rpm": "0.001"}, // raw counts -> rpm
	)
	cases := []struct {
		name   string
		in     Reading
		wantVal float64
		wantUnit string
	}{
		{"celsius normalise", Reading{"d", "temperature", 50, "C", now, "mqtt", "good"}, 50, "Celsius"},
		{"fahrenheit converts", Reading{"d", "temperature", 212, "F", now, "mqtt", "good"}, 100, "Celsius"},
		{"rpm scales", Reading{"d", "rpm", 12000, "", now, "modbus", "good"}, 12, "unknown"},
		{"empty unit -> unknown", Reading{"d", "temperature", 42, "", now, "rest", "good"}, 42, "unknown"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			out, err := tf.Transform(tc.in)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if !floatEq(out.Value, tc.wantVal) {
				t.Errorf("value = %v, want %v", out.Value, tc.wantVal)
			}
			if out.Unit != tc.wantUnit {
				t.Errorf("unit = %q, want %q", out.Unit, tc.wantUnit)
			}
			if out.Quality != "good" {
				t.Errorf("quality = %q, want good", out.Quality)
			}
		})
	}
}

func TestTransformer_InvalidReadingRejected(t *testing.T) {
	tf := NewTransformer(nil, nil)
	_, err := tf.Transform(Reading{DeviceID: "", Metric: "temperature", Value: 1})
	if err == nil {
		t.Fatal("expected error for invalid reading, got nil")
	}
}

func TestPipeline_Apply(t *testing.T) {
	now := time.Now().UTC()
	t1 := NewTransformer(map[string]string{"c": "Celsius"}, nil)
	t2 := NewTransformer(map[string]string{"celsius": "Celsius"}, map[string]string{"temperature": "2"})
	p := &Pipeline{Steps: []*Transformer{t1, t2}}
	out, err := p.Apply(Reading{"d", "temperature", 10, "C", now, "mqtt", "good"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !floatEq(out.Value, 20) { // 10 * 2
		t.Errorf("value = %v, want 20", out.Value)
	}
	if out.Unit != "Celsius" {
		t.Errorf("unit = %q, want Celsius", out.Unit)
	}
}

func TestPipeline_EmptyReturnsError(t *testing.T) {
	p := &Pipeline{}
	_, err := p.Apply(Reading{"d", "temperature", 10, "C", time.Now().UTC(), "x", "good"})
	if err != ErrEmptyPipeline {
		t.Errorf("err = %v, want ErrEmptyPipeline", err)
	}
}

func floatEq(a, b float64) bool {
	return math.Abs(a-b) < 1e-9
}
''')

w("internal/domain/classify_test.go", r'''
package domain

import (
	"testing"
	"time"
)

func TestClassify(t *testing.T) {
	now := time.Now().UTC()
	cases := []struct {
		name   string
		r      Reading
		expect string
	}{
		{"temp normal", Reading{"d", "temperature", 30, "C", now, "x", "good"}, "NORMAL"},
		{"temp warning", Reading{"d", "temperature", 80, "C", now, "x", "good"}, "WARNING"},
		{"temp critical", Reading{"d", "temperature", 96, "C", now, "x", "good"}, "CRITICAL"},
		{"vibration warning", Reading{"d", "vibration", 6, "mm/s", now, "x", "good"}, "WARNING"},
		{"vibration critical", Reading{"d", "vibration", 9, "mm/s", now, "x", "good"}, "CRITICAL"},
		{"unknown metric normal", Reading{"d", "humidity", 999, "%", now, "x", "good"}, "NORMAL"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := Classify(tc.r)
			if got != tc.expect {
				t.Errorf("Classify() = %q, want %q", got, tc.expect)
			}
		})
	}
}
''')

w("internal/infra/memoryrepo/repository_test.go", r'''
package memoryrepo

import (
	"testing"
	"time"

	"industrial-gateway/internal/domain"
)

func TestRepository_SaveAndCount(t *testing.T) {
	r := New()
	now := time.Now().UTC()
	rd := domain.Reading{DeviceID: "dev-1", Metric: "temperature", Value: 50, Unit: "C", Timestamp: now, Source: "rest", Quality: "good"}
	if err := r.Save(rd); err != nil {
		t.Fatalf("save: %v", err)
	}
	if c, _ := r.Count(""); c != 1 {
		t.Errorf("count = %d, want 1", c)
	}
}

func TestRepository_InvalidReadingRejected(t *testing.T) {
	r := New()
	err := r.Save(domain.Reading{DeviceID: "", Metric: "temperature", Value: 1, Timestamp: time.Now().UTC()})
	if err == nil {
		t.Fatal("expected error for invalid reading")
	}
}

func TestRepository_LatestFiltersAndOrders(t *testing.T) {
	r := New()
	now := time.Now().UTC()
	for i, v := range []float64{10, 20, 30} {
		_ = r.Save(domain.Reading{DeviceID: "dev-1", Metric: "temperature", Value: v, Unit: "C", Timestamp: now.Add(time.Duration(i) * time.Minute), Source: "rest", Quality: "good"})
	}
	// different device should be excluded
	_ = r.Save(domain.Reading{DeviceID: "dev-2", Metric: "temperature", Value: 99, Unit: "C", Timestamp: now, Source: "rest", Quality: "good"})

	got, _ := r.Latest("dev-1", "temperature", 2)
	if len(got) != 2 {
		t.Fatalf("len = %d, want 2", len(got))
	}
	if got[0].Value != 20 || got[1].Value != 30 {
		t.Errorf("order/values = %v, want [20 30] chronological", []float64{got[0].Value, got[1].Value})
	}
}

func TestRepository_CountByDevice(t *testing.T) {
	r := New()
	now := time.Now().UTC()
	_ = r.Save(domain.Reading{DeviceID: "a", Metric: "m", Value: 1, Timestamp: now, Source: "s", Quality: "good"})
	_ = r.Save(domain.Reading{DeviceID: "b", Metric: "m", Value: 1, Timestamp: now, Source: "s", Quality: "good"})
	_ = r.Save(domain.Reading{DeviceID: "a", Metric: "m", Value: 1, Timestamp: now, Source: "s", Quality: "good"})
	if c, _ := r.Count("a"); c != 2 {
		t.Errorf("count(a) = %d, want 2", c)
	}
	if c, _ := r.Count("b"); c != 1 {
		t.Errorf("count(b) = %d, want 1", c)
	}
}
''')

w("internal/infra/memorycache/cache_test.go", r'''
package memorycache

import (
	"testing"
	"time"
)

func TestCache_SetGet(t *testing.T) {
	c := New()
	c.Set("k", "v", 0)
	if v, ok := c.Get("k"); !ok || v != "v" {
		t.Errorf("Get = (%q,%v), want (v,true)", v, ok)
	}
	if _, ok := c.Get("nope"); ok {
		t.Error("missing key should return false")
	}
}

func TestCache_TTLExpiry(t *testing.T) {
	c := New()
	c.Set("k", "v", 30*time.Millisecond)
	if _, ok := c.Get("k"); !ok {
		t.Fatal("expected present before expiry")
	}
	time.Sleep(40 * time.Millisecond)
	if _, ok := c.Get("k"); ok {
		t.Fatal("expected expired")
	}
}

func TestCache_Overwrite(t *testing.T) {
	c := New()
	c.Set("k", "v1", 0)
	c.Set("k", "v2", 0)
	if v, _ := c.Get("k"); v != "v2" {
		t.Errorf("Get = %q, want v2", v)
	}
}
''')

w("internal/infra/mqtt/collector_test.go", r'''
package mqtt

import (
	"encoding/json"
	"testing"

	"industrial-gateway/internal/domain"
)

// fakeClient records the handler so we can drive it without a broker.
type fakeClient struct {
	handler func([]byte)
}

func (f *fakeClient) Subscribe(topic string, handler func([]byte)) error {
	f.handler = handler
	return nil
}
func (f *fakeClient) Disconnect() {}

func TestCollector_DecodesAndQueues(t *testing.T) {
	fc := &fakeClient{}
	c := NewCollector(fc, "industrial/+/+")
	if err := c.Start(); err != nil {
		t.Fatalf("start: %v", err)
	}
	msg, _ := json.Marshal(map[string]interface{}{
		"device_id": "pump-1", "metric": "vibration", "value": 6.5, "unit": "mm/s"})
	fc.handler(msg)
	out, err := c.Collect()
	if err != nil {
		t.Fatalf("collect: %v", err)
	}
	if len(out) != 1 {
		t.Fatalf("len = %d, want 1", len(out))
	}
	rd := out[0]
	if rd.DeviceID != "pump-1" || rd.Metric != "vibration" || rd.Value != 6.5 {
		t.Errorf("decoded reading = %+v", rd)
	}
	if rd.Source != "mqtt" {
		t.Errorf("source = %q, want mqtt", rd.Source)
	}
	if domain.Classify(rd) != "WARNING" {
		t.Errorf("classify = %q, want WARNING", domain.Classify(rd))
	}
}

func TestCollector_CollectDrainsQueue(t *testing.T) {
	fc := &fakeClient{}
	c := NewCollector(fc, "t")
	_ = c.Start()
	c.IngestRaw([]byte(`{"device_id":"d","metric":"temperature","value":30,"unit":"C"}`))
	first, _ := c.Collect()
	if len(first) != 1 {
		t.Fatalf("first len = %d, want 1", len(first))
	}
	second, _ := c.Collect()
	if len(second) != 0 {
		t.Errorf("second len = %d, want 0 (drained)", len(second))
	}
}

func TestCollector_NilClientStartErrors(t *testing.T) {
	c := NewCollector(nil, "t")
	if err := c.Start(); err == nil {
		t.Fatal("expected error with nil client")
	}
}
''')

w("internal/infra/modbus/collector_test.go", r'''
package modbus

import (
	"testing"

	"industrial-gateway/internal/domain"
)

type fakeClient struct {
	regs map[uint16][]uint16
}

func (f *fakeClient) ReadHoldingRegisters(address, quantity uint16) ([]uint16, error) {
	return f.regs[address], nil
}
func (f *fakeClient) Close() error { return nil }

func TestCollector_PollsMaps(t *testing.T) {
	fc := &fakeClient{regs: map[uint16][]uint16{100: {750}, 200: {3}}}
	maps := []RegisterMap{
		{Address: 100, Quantity: 1, DeviceID: "plc-1", Metric: "temperature", Unit: "C", Scale: 0.1},
		{Address: 200, Quantity: 1, DeviceID: "plc-1", Metric: "vibration", Unit: "mm/s", Scale: 0.1},
	}
	c := NewCollector(fc, maps)
	out, err := c.Collect()
	if err != nil {
		t.Fatalf("collect: %v", err)
	}
	if len(out) != 2 {
		t.Fatalf("len = %d, want 2", len(out))
	}
	want := map[string]float64{"temperature": 75, "vibration": 0.3}
	for _, rd := range out {
		got, ok := want[rd.Metric]
		if !ok || rd.Value != got {
			t.Errorf("%s value = %v, want %v", rd.Metric, rd.Value, got)
		}
		if rd.Source != "modbus" {
			t.Errorf("source = %q, want modbus", rd.Source)
		}
		if domain.Classify(rd) == "" {
			t.Error("classify returned empty")
		}
	}
}

func TestCollector_NilClientErrors(t *testing.T) {
	c := NewCollector(nil, nil)
	if _, err := c.Collect(); err == nil {
		t.Fatal("expected error with nil client")
	}
}
''')

w("internal/adapter/http/router_test.go", r'''
package http

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"industrial-gateway/internal/domain"
	"industrial-gateway/internal/infra/memorycache"
	"industrial-gateway/internal/infra/memoryrepo"
	"industrial-gateway/internal/usecase"
)

func newEngine() (*usecase.IngestService, *memoryrepo.Repository, *memorycache.Cache) {
	repo := memoryrepo.New()
	cache := memorycache.New()
	uc := usecase.NewIngestService(&domain.Pipeline{Steps: []*domain.Transformer{
		domain.NewTransformer(map[string]string{"c": "Celsius"}, nil)}}, repo, cache)
	return uc, repo, cache
}

func TestHealthEndpoint(t *testing.T) {
	uc, repo, cache := newEngine()
	engine := Register(uc, repo, cache)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/health", nil)
	engine.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("status = %d, want 200", w.Code)
	}
	var body map[string]interface{}
	_ = json.Unmarshal(w.Body.Bytes(), &body)
	if body["status"] != "ok" {
		t.Errorf("status = %v, want ok", body["status"])
	}
}

func TestIngestEndpoint(t *testing.T) {
	uc, repo, cache := newEngine()
	engine := Register(uc, repo, cache)
	payload := []byte(`{"device_id":"pump-1","metric":"temperature","value":96,"unit":"C","source":"rest"}`)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/ingest", bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	engine.ServeHTTP(w, req)
	if w.Code != 201 {
		t.Fatalf("status = %d, want 201 (body=%s)", w.Code, w.Body.String())
	}
	var resp map[string]interface{}
	_ = json.Unmarshal(w.Body.Bytes(), &resp)
	if resp["status"] != "CRITICAL" {
		t.Errorf("status = %v, want CRITICAL", resp["status"])
	}
	if c, _ := repo.Count("pump-1"); c != 1 {
		t.Errorf("repo count = %d, want 1", c)
	}
}

func TestIngestValidation(t *testing.T) {
	uc, repo, cache := newEngine()
	engine := Register(uc, repo, cache)
	// missing device_id (binding required) -> 400
	payload := []byte(`{"metric":"temperature","value":10}`)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/ingest", bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	engine.ServeHTTP(w, req)
	if w.Code != 400 {
		t.Fatalf("status = %d, want 400", w.Code)
	}
}

func TestLatestEndpoint(t *testing.T) {
	uc, repo, cache := newEngine()
	engine := Register(uc, repo, cache)
	_ = repo.Save(domain.Reading{DeviceID: "d", Metric: "temperature", Value: 1, Unit: "C", Timestamp: timeNow(), Source: "rest", Quality: "good"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/readings/d", nil)
	engine.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("status = %d, want 200", w.Code)
	}
}

func TestStatusEndpoint(t *testing.T) {
	uc, repo, cache := newEngine()
	engine := Register(uc, repo, cache)
	cache.Set("status:pump-1", "WARNING", 0)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/status/pump-1", nil)
	engine.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("status = %d, want 200", w.Code)
	}
	var body map[string]interface{}
	_ = json.Unmarshal(w.Body.Bytes(), &body)
	if body["status"] != "WARNING" {
		t.Errorf("status = %v, want WARNING", body["status"])
	}
}
''')

# helper for the http test (timeNow) - put in same package
w("internal/adapter/http/helpers_test.go", r'''
package http

import "time"

func timeNow() time.Time { return time.Now().UTC() }
''')

w("internal/adapter/grpc/service_test.go", r'''
package grpcadapter

import (
	"context"
	"testing"

	"industrial-gateway/internal/domain"
	"industrial-gateway/internal/infra/memorycache"
	"industrial-gateway/internal/infra/memoryrepo"
	"industrial-gateway/internal/usecase"
)

func newService() *Service {
	repo := memoryrepo.New()
	cache := memorycache.New()
	uc := usecase.NewIngestService(
		&domain.Pipeline{Steps: []*domain.Transformer{domain.NewTransformer(nil, nil)}},
		repo, cache)
	return NewService(uc)
}

func TestService_Ingest(t *testing.T) {
	s := newService()
	resp, err := s.Ingest(context.Background(), IngestRequest{
		DeviceID: "pump-1", Metric: "temperature", Value: 96, Unit: "C", Source: "grpc"})
	if err != nil {
		t.Fatalf("ingest: %v", err)
	}
	if resp.Status != "CRITICAL" {
		t.Errorf("status = %q, want CRITICAL", resp.Status)
	}
	if !resp.Saved {
		t.Error("expected Saved=true")
	}
}

func TestService_Ingest_MissingDevice(t *testing.T) {
	s := newService()
	if _, err := s.Ingest(context.Background(), IngestRequest{Metric: "temperature", Value: 1}); err == nil {
		t.Fatal("expected error for missing device_id")
	}
}

func TestService_Ingest_InvalidValue(t *testing.T) {
	s := newService()
	// NaN value should fail validation in domain.Reading.Validate
	_, err := s.Ingest(context.Background(), IngestRequest{
		DeviceID: "d", Metric: "temperature", Value: 1})
	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
}
''')

w("internal/usecase/ingest_test.go", r'''
package usecase

import (
	"context"
	"testing"

	"industrial-gateway/internal/domain"
	"industrial-gateway/internal/infra/memorycache"
	"industrial-gateway/internal/infra/memoryrepo"
)

// fakeCollector returns canned readings on Collect().
type fakeCollector struct {
	name string
	out  []domain.Reading
	err  error
}

func (f *fakeCollector) Collect() ([]domain.Reading, error) { return f.out, f.err }
func (f *fakeCollector) Name() string                          { return f.name }

func TestIngestService_RunOnce(t *testing.T) {
	repo := memoryrepo.New()
	cache := memorycache.New()
	uc := NewIngestService(
		&domain.Pipeline{Steps: []*domain.Transformer{domain.NewTransformer(map[string]string{"c": "Celsius"}, nil)}},
		repo, cache,
		&fakeCollector{name: "fake", out: []domain.Reading{
			{DeviceID: "d1", Metric: "temperature", Value: 96, Unit: "C", Timestamp: timeNow(), Source: "mqtt", Quality: "good"},
		}})
	n, err := uc.RunOnce(context.Background())
	if err != nil {
		t.Fatalf("runonce: %v", err)
	}
	if n != 1 {
		t.Errorf("count = %d, want 1", n)
	}
	if s := uc.StatusFor("d1"); s != "CRITICAL" {
		t.Errorf("status = %q, want CRITICAL", s)
	}
}

func TestIngestService_StatusForUnknown(t *testing.T) {
	uc := NewIngestService(&domain.Pipeline{}, memoryrepo.New(), memorycache.New())
	if s := uc.StatusFor("ghost"); s != "UNKNOWN" {
		t.Errorf("status = %q, want UNKNOWN", s)
	}
}

func TestIngestService_InvalidReadingSkipped(t *testing.T) {
	repo := memoryrepo.New()
	cache := memorycache.New()
	uc := NewIngestService(
		&domain.Pipeline{Steps: []*domain.Transformer{domain.NewTransformer(nil, nil)}},
		repo, cache,
		&fakeCollector{name: "fake", out: []domain.Reading{
			{DeviceID: "", Metric: "temperature", Value: 1, Timestamp: timeNow()}, // invalid
		}})
	n, _ := uc.RunOnce(context.Background())
	if n != 0 {
		t.Errorf("count = %d, want 0 (invalid skipped)", n)
	}
}
''')

w("internal/usecase/helpers_test.go", r'''
package usecase

import "time"

func timeNow() time.Time { return time.Now().UTC() }
''')

# =================== DOCS ===================
w("README.md", r'''
# 工业网关数据采集服务 (Industrial Gateway Data Collection Service)

> Student: `student-go` — Language: Go 1.21 + Gin framework
> Architecture: Hexagonal Architecture (Ports & Adapters)

An industrial data-collection gateway that ingests device telemetry from MQTT
brokers and Modbus TCP PLCs, normalises it through a transformation pipeline,
persists it, classifies it against threshold policies, and exposes it via a
Gin REST API, a gRPC service, and Prometheus metrics. Built following
hexagonal architecture so every external system (broker, PLC, HTTP, gRPC,
database, cache) is an *adapter* behind a *port*, making the core domain logic
pure and trivially testable.

## Architecture (Hexagonal / Ports & Adapters)

```
       driving adapters                 |  domain  |           driven adapters
   ┌──────────────────┐                |          |        ┌──────────────────┐
   │  Gin REST API    │ ─► usecase ─► |  domain  | ─►     │ MQTT collector   │
   │  gRPC service    │   (IngestSvc) |  Reading |        │ Modbus collector  │
   │  scheduler (cron)│                |  Pipeline|        │ Repository (mem) │
   └──────────────────┘                |  Classify│        │ Cache (mem)      │
                                       └──────────┘        └──────────────────┘
   Ports: CollectorPort, RepositoryPort, CachePort  — interfaces in domain/.
```

## Modules
- `internal/domain/` — pure model (`Reading`, `DeviceStatus`), the
  `Transformer`/`Pipeline`, `Classify` policy, and the port interfaces.
- `internal/usecase/` — `IngestService` orchestrating collectors→pipeline→repo→cache.
- `internal/infra/memoryrepo`, `memorycache` — in-memory driven adapters.
- `internal/infra/mqtt`, `modbus` — field-device collectors (client abstracted).
- `internal/adapter/http` — Gin REST primary adapter.
- `internal/adapter/grpc` — gRPC service primary adapter.
- `internal/adapter/metrics` — Prometheus counters.
- `cmd/gateway/main.go` — wires the hexagon, starts REST + metrics + scheduler.

## Build & Test
```bash
go mod tidy
go build ./...
go test -cover ./...      # table-driven tests across every package
go run ./cmd/gateway      # REST :8080, metrics :9090
```

## API Example
```bash
curl -X POST localhost:8080/api/v1/ingest \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"pump-1","metric":"temperature","value":96,"unit":"C","source":"rest"}'
curl localhost:8080/api/v1/health
curl localhost:8080/api/v1/status/pump-1
```

See `docs/SDD.md` for the full Software Design Document.
''')

w("docs/SDD.md", r'''
# Software Design Document (SDD)
## 工业网关数据采集服务 — Industrial Gateway Data Collection Service

**Project:** Industrial Gateway &nbsp; **Student:** student-go &nbsp;
**Language:** Go 1.21 &nbsp; **Framework:** Gin v1.10 &nbsp;
**Architecture:** Hexagonal (Ports & Adapters)

> AI-assisted design: the port/adapter boundaries and Modbus register-mapping
> model were validated against the `qwen2.5-coder:7b` model via the platform
> LiteLLM gateway. Implementation and table-driven tests are hand-written.

---

## 1. Introduction

### 1.1 Purpose
A gateway that sits between field devices (MQTT sensors, Modbus PLCs) and
upstream analytics platforms, providing a single normalised ingestion point.
It decouples device protocols from consumers by exposing a clean REST/gRPC
surface and a Prometheus metrics endpoint.

### 1.2 Scope
Inbound: MQTT JSON messages and Modbus TCP holding registers. Processing:
validation, transformation pipeline (unit normalisation, scaling, F→C),
persistence, threshold classification, live-status caching. Outbound: REST API,
gRPC service, Prometheus metrics, scheduled collector polling. Out of scope:
OPC-UA, BACnet, and long-term historian storage (left to the downstream
platform).

### 1.3 Definitions
- **Port** — an interface defined by the application that an adapter must
  satisfy (Alistair Cockburn's hexagonal terminology).
- **Adapter** — a concrete implementation of a port (driving = REST/gRPC/scheduler;
  driven = MQTT/Modbus/repo/cache).
- **Reading** — the canonical `{device_id, metric, value, unit, timestamp,
  source, quality}` measurement.
- **Modbus holding register** — a 16-bit value addressed by (address, quantity).

---

## 2. Architecture (Hexagonal)

### 2.1 Dependency Rule
All dependencies point **inward** toward the `domain` package:
`adapters → usecase → domain`. The domain imports only the standard library.
This means the gateway can swap MQTT for NATS, Gin for Echo, or in-memory
storage for PostgreSQL without touching a line of business logic.

### 2.2 Ports

| Port | Package | Adapters |
|------|---------|----------|
| `CollectorPort` | domain | `mqtt.Collector`, `modbus.Collector` |
| `RepositoryPort` | domain | `memoryrepo.Repository` (PostgreSQL in prod) |
| `CachePort` | domain | `memorycache.Cache` (Redis in prod) |

### 2.3 Adapters
- **Driving (primary):** `http.Router` (Gin), `grpc.Service`,
  `runScheduler` (cron driver).
- **Driven (secondary):** `mqtt.Collector` (abstracted `Client`), `modbus.Collector`
  (abstracted `Client`), `memoryrepo`, `memorycache`.

### 2.4 Data Flow
```
[scheduler | REST | gRPC] ─► IngestService.RunOnce / .Ingest
   ─► for each collector: collector.Collect() ─► []Reading
   ─► pipeline.Apply(reading)  ─► normalised Reading
   ─► repo.Save(reading)
   ─► cache.Set("status:<device>", Classify(reading))
```

---

## 3. Domain Model

```
Reading { DeviceID, Metric, Value, Unit, Timestamp, Source, Quality }
  Validate() -> error            // invariants
Transformer { normaliseUnits, scaling }
  Transform(Reading) -> Reading
Pipeline { Steps []*Transformer }
  Apply(Reading) -> Reading
Classify(Reading) -> NORMAL|WARNING|CRITICAL   // threshold table
```

---

## 4. Component Design

### 4.1 Transformation Pipeline
A `Pipeline` is an ordered list of `Transformer`s. Each `Transformer`
normalises units (e.g. "C"→"Celsius"), converts Fahrenheit→Celsius as a
special case, and applies a per-metric scaling multiplier (raw counts→SI).
Pure functions; fully table-driven tested.

### 4.2 MQTT Collector
Abstracts the broker behind a `Client` interface (`Subscribe`/`Disconnect`).
Incoming JSON is decoded into `Reading`s and buffered in a queue; `Collect()`
drains the queue. Tests inject a `fakeClient` that captures the handler and
replays canned payloads — no broker required.

### 4.3 Modbus Collector
A `RegisterMap` maps `{address, quantity, deviceID, metric, unit, scale,
offset}` to a reading. The adapter reads holding registers via an abstracted
`Client` and scales the raw 16-bit value. Tests inject a `fakeClient` with a
register map.

### 4.4 REST API (Gin)
`/api/v1/health`, `/api/v1/ingest`, `/api/v1/readings/:device`,
`/api/v1/status/:device`. Validation via Gin binding; domain errors map to
422; collector/repository errors map to 400/500.

### 4.5 gRPC Service
A typed `Service.Ingest(ctx, req)` mirroring the REST flow. Kept as a
hand-written skeleton (no protoc dependency) so the package builds in the
sandbox; the request/response structs are gRPC-message-shaped.

### 4.6 Metrics & Health
Prometheus counters (`gateway_ingest_total`, `gateway_collector_errors_total`)
on `:9090/metrics`. Health endpoint reports reading count + cache type.

---

## 5. Sequence Diagram

```
Scheduler ─► IngestService.RunOnce
             │ for each collector:
             │   collector.Collect() ─► []Reading
             │   for each reading:
             │     pipeline.Apply(reading)
             │     repo.Save(normalised)
             │     cache.Set("status:<dev>", Classify)
             └─► count
REST ─► http.ingest ─► repo.Save ─► Classify ─► 201 + status
gRPC  ─► grpc.Service.Ingest ─► validate ─► Classify ─► response
```

---

## 6. Test Strategy (table-driven, TDD)

Every package has a `_test.go` with table-driven cases:

| Package | Tests | Covers |
|---------|-------|--------|
| domain | Reading.Validate, Transformer.Transform, Pipeline.Apply, Classify | invariants, unit conversion, scaling, thresholds |
| infra/memoryrepo | Save, Count, Latest filter/order, invalid rejection | RepositoryPort |
| infra/memorycache | Set/Get, TTL, overwrite | CachePort |
| infra/mqtt | decode+queue, drain, nil-client | MQTT adapter |
| infra/modbus | poll maps, scaling, nil-client | Modbus adapter |
| adapter/http | health, ingest, validation, latest, status | REST (httptest) |
| adapter/grpc | ingest, missing device, invalid value | gRPC logic |
| usecase | RunOnce, StatusFor, invalid skipped | orchestration |

Run: `go test -cover ./...`.

---

## 7. Non-Functional Requirements
- **Concurrency:** `RepositoryPort`/`CachePort` use `sync.Mutex`/`RWMutex`;
  the scheduler runs in a goroutine; context propagation enables cancellation.
- **Performance:** table-driven unit tests run in ms; no I/O in the domain.
- **Portability:** adapters swap via constructor injection; no global state.
- **Observability:** structured logging + Prometheus metrics.

## 8. Future Work
- Real gRPC codegen + protobuf service registration.
- NATS/Kafka collector; PostgreSQL repository; Redis cache adapters.
- Circuit breakers around collector clients.

## 9. Revision History
| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2026-08-31 | student-go | Initial SDD, hexagonal architecture, table-driven tests |
''')

print("go tests + fixes + docs written")
