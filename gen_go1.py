#!/usr/bin/env python3
"""Generate Go Industrial Gateway Data Collection Service.
Hexagonal Architecture (Ports & Adapters). Gin v1.10 (Go 1.21). Table-driven tests.
"""
import os, textwrap
BASE = "/tmp/p3-go/industrial-gateway"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# ---- go.mod (deps: gin v1.10 compatible with Go 1.21; metrics with prometheus client) ----
w("go.mod", r'''
module industrial-gateway

go 1.21

require (
	github.com/gin-gonic/gin v1.10.0
	github.com/prometheus/client_golang v1.19.1
	google.golang.org/grpc v1.64.0
	google.golang.org/protobuf v1.34.1
)

require (
	github.com/bytedance/sonic v1.11.6 // indirect
	github.com/bytedance/sonic/loader v0.1.1 // indirect
	github.com/cloudwego/base64x v0.1.4 // indirect
	github.com/cloudwego/iasm v0.2.0 // indirect
	github.com/gabriel-vasile/mimetype v1.4.3 // indirect
	github.com/gin-contrib/sse v0.1.0 // indirect
	github.com/go-playground/locales v0.14.1 // indirect
	github.com/go-playground/universal-translator v0.18.1 // indirect
	github.com/go-playground/validator/v10 v10.20.0 // indirect
	github.com/goccy/go-json v0.10.2 // indirect
	github.com/json-iterator/go v1.1.12 // indirect
	github.com/klauspost/cpuid/v2 v2.2.7 // indirect
	github.com/leodido/go-urn v1.4.0 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	github.com/pelletier/go-toml/v2 v2.2.2 // indirect
	github.com/twitchyliquid64/golang-asm v0.15.1 // indirect
	github.com/ugorji/go/codec v1.2.12 // indirect
	golang.org/x/arch v0.8.0 // indirect
	golang.org/x/crypto v0.23.0 // indirect
	golang.org/x/net v0.25.0 // indirect
	golang.org/x/sys v0.20.0 // indirect
	golang.org/x/text v0.15.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20240528184218-5319ea158f4a // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
''')

# =================== DOMAIN (core + ports) ===================
w("internal/domain/reading.go", r'''
// Package domain holds the pure business model: a device reading and the
// transformation pipeline. It depends on NOTHING outside the standard library,
// which is the whole point of hexagonal architecture.
package domain

import (
	"errors"
	"fmt"
	"math"
	"time"
)

// Reading is a single normalised measurement collected from a field device.
type Reading struct {
	DeviceID  string    `json:"device_id"`
	Metric    string    `json:"metric"`     // temperature, vibration, pressure, ...
	Value     float64   `json:"value"`
	Unit      string    `json:"unit"`
	Timestamp time.Time `json:"timestamp"`
	Source    string    `json:"source"` // mqtt, modbus
	Quality   string    `json:"quality"` // good, bad, unknown
}

// Validate enforces the invariants of a collected reading.
func (r Reading) Validate() error {
	if r.DeviceID == "" {
		return errors.New("device_id is required")
	}
	if r.Metric == "" {
		return errors.New("metric is required")
	}
	if math.IsNaN(r.Value) || math.IsInf(r.Value, 0) {
		return errors.New("value must be a finite number")
	}
	if r.Timestamp.IsZero() {
		return errors.New("timestamp is required")
	}
	return nil
}

// DeviceStatus summarises a device's health derived from its latest readings.
type DeviceStatus struct {
	DeviceID   string    `json:"device_id"`
	Status     string    `json:"status"` // NORMAL, WARNING, CRITICAL
	LastValue  float64   `json:"last_value"`
	Metric     string    `json:"metric"`
	Readings   int       `json:"readings"`
	LastSeen   time.Time `json:"last_seen"`
}

// CollectorPort is the port (interface) every device-data collector must
// implement (MQTT adapter, Modbus adapter, ...).
type CollectorPort interface {
	Collect() ([]Reading, error)
	Name() string
}

// RepositoryPort is the persistence port (in-memory, Redis, ...).
type RepositoryPort interface {
	Save(Reading) error
	Latest(deviceID, metric string, n int) ([]Reading, error)
	Count(deviceID string) (int, error)
}

// CachePort is the live-status cache port.
type CachePort interface {
	Get(key string) (string, bool)
	Set(key, value string, ttl time.Duration)
}
''')

# ---- transformation pipeline (pure domain logic) ----
w("internal/domain/transform.go", r'''
package domain

import (
	"errors"
	"fmt"
	"strings"
)

// Transformer applies a sequence of conversions to a raw reading so that all
// readings leaving the gateway share a canonical shape & unit. This is the
// core business logic and is fully unit-tested without any I/O.
type Transformer struct {
	normaliseUnits map[string]string // raw unit -> canonical unit
	scaling       map[string]float64 // metric -> multiplier (e.g. raw->SI)
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
	// unit normalisation (C -> Celsius, F handled separately, etc.)
	if canon, ok := t.normaliseUnits[strings.ToLower(r.Unit)]; ok {
		out.Unit = canon
	}
	// scaling (raw sensor counts -> engineering unit)
	if mult, ok := t.scaling[strings.ToLower(r.Metric)]; ok && mult != 0 {
		out.Value = r.Value * mult
	}
	// Fahrenheit -> Celsius conversion special-case
	if strings.EqualFold(r.Unit, "F") {
		out.Value = (r.Value - 32) * 5 / 9
		out.Unit = "Celsius"
	}
	if out.Unit == "" {
		out.Unit = "unknown"
	}
	return out, nil
}

// Pipeline is an ordered sequence of transformers applied left to right.
type Pipeline struct {
	steps []*Transformer
}

// Apply runs every transformer in order; the first error short-circuits.
func (p *Pipeline) Apply(r Reading) (Reading, error) {
	var err error
	for _, s := range p.steps {
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

# ---- classification (pure domain policy) ----
w("internal/domain/classify.go", r'''
package domain

// Thresholds per metric: (warn, critical). Mirrors industrial norms.
var defaultThresholds = map[string][2]float64{
	"temperature": {75, 95},
	"vibration":  {5, 8},
	"pressure":   {8, 12},
	"current":    {40, 60},
	"rpm":        {2500, 3000},
}

// Classify returns NORMAL / WARNING / CRITICAL for a reading using the
// default threshold table. Unknown metrics are NORMAL.
func Classify(r Reading) string {
	limits, ok := defaultThresholds[r.Metric]
	if !ok {
		return "NORMAL"
	}
	switch {
	case r.Value >= limits[1]:
		return "CRITICAL"
	case r.Value >= limits[0]:
		return "WARNING"
	default:
		return "NORMAL"
	}
}
''')

# ---- ingestion use case (orchestrates port+domain) ----
w("internal/usecase/ingest.go", r'''
// Package usecase wires the domain logic to the ports (collectors + repository).
package usecase

import (
	"context"
	"fmt"
	"log"

	"industrial-gateway/internal/domain"
)

// IngestService is the primary use case: collect from a source, transform,
// persist, classify and cache. It is constructed from ports only.
type IngestService struct {
	collectors []domain.CollectorPort
	pipeline   *domain.Pipeline
	repo       domain.RepositoryPort
	cache      domain.CachePort
}

func NewIngestService(pipeline *domain.Pipeline, repo domain.RepositoryPort,
	cache domain.CachePort, collectors ...domain.CollectorPort) *IngestService {
	return &IngestService{
		collectors: collectors, pipeline: pipeline, repo: repo, cache: cache,
	}
}

// RunOnce pulls one batch from every collector, transforms, stores & caches.
// Returns the count of successfully ingested readings.
func (s *IngestService) RunOnce(ctx context.Context) (int, error) {
	total := 0
	for _, c := range s.collectors {
		select {
		case <-ctx.Done():
			return total, ctx.Err()
		default:
		}
		raws, err := c.Collect()
		if err != nil {
			log.Printf("collector %s error: %v", c.Name(), err)
			continue
		}
		for _, raw := range raws {
			r, err := s.pipeline.Apply(raw)
			if err != nil {
				log.Printf("transform error for %s: %v", raw.DeviceID, err)
				continue
			}
			if err := s.repo.Save(r); err != nil {
				log.Printf("save error for %s: %v", r.DeviceID, err)
				continue
			}
			status := domain.Classify(r)
			s.cache.Set(fmt.Sprintf("status:%s", r.DeviceID), status, 0)
			total++
		}
	}
	return total, nil
}

// StatusFor returns the cached status of a device.
func (s *IngestService) StatusFor(deviceID string) string {
	if v, ok := s.cache.Get("status:" + deviceID); ok {
		return v
	}
	return "UNKNOWN"
}
''')

print("go domain + usecase written")
