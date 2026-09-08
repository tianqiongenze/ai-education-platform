package com.mes.cache;

import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * Lightweight hit/miss counters for cache analysis. Hooked into the cache
 * lifecycle via {@link CacheMetricsAdvice} (or read from actuator when present).
 * Counters are exposed at GET /api/v1/.../metrics/cache via controllers.
 */
@Component
public class CacheMetrics {

    private final Map<String, AtomicLong> l1Hits = new ConcurrentHashMap<>();
    private final Map<String, AtomicLong> l2Hits = new ConcurrentHashMap<>();
    private final Map<String, AtomicLong> misses = new ConcurrentHashMap<>();
    private final Map<String, AtomicLong> evictions = new ConcurrentHashMap<>();

    public void recordL1Hit(String cache) { l1Hits.computeIfAbsent(cache, k -> new AtomicLong()).incrementAndGet(); }
    public void recordL2Hit(String cache) { l2Hits.computeIfAbsent(cache, k -> new AtomicLong()).incrementAndGet(); }
    public void recordMiss(String cache) { misses.computeIfAbsent(cache, k -> new AtomicLong()).incrementAndGet(); }
    public void recordEviction(String cache) { evictions.computeIfAbsent(cache, k -> new AtomicLong()).incrementAndGet(); }

    public Map<String, Object> snapshot() {
        long total = sum(l1Hits) + sum(l2Hits) + sum(misses);
        double hitRate = total == 0 ? 0.0 : (double)(sum(l1Hits) + sum(l2Hits)) / total * 100.0;
        return Map.of(
                "l1Hits", copy(l1Hits),
                "l2Hits", copy(l2Hits),
                "misses", copy(misses),
                "evictions", copy(evictions),
                "hitRatePercent", Math.round(hitRate * 100.0) / 100.0,
                "totalRequests", total);
    }

    private long sum(Map<String, AtomicLong> m) {
        return m.values().stream().mapToLong(AtomicLong::get).sum();
    }
    private Map<String, Long> copy(Map<String, AtomicLong> m) {
        return m.entrySet().stream().collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().get()));
    }
}
