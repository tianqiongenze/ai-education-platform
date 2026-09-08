package com.mes.cache;

import org.springframework.cache.Cache;
import org.springframework.cache.support.AbstractValueAdaptingCache;
import org.springframework.data.redis.core.RedisTemplate;

import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

/**
 * A read-through two-level cache.
 *
 * L1 = Caffeine in-process (low latency, per-instance, bounded size + TTL).
 * L2 = Redis (shared across all instances, survives restarts).
 *
 * Read flow:  L1 -> (miss) -> L2 -> (miss) -> valueLoader, then backfill L1 + L2.
 * Write/evict: {@link #evict} removes the key from BOTH levels (write-through invalidation).
 */
public class TwoLevelCache extends AbstractValueAdaptingCache {

    private final String name;
    private final com.github.benmanes.caffeine.cache.Cache<Object, Object> l1;
    private final RedisTemplate<String, Object> redisTemplate;
    private final long redisTtlSeconds;
    private final String redisKeyPrefix;
    private final CacheMetrics metrics;

    public TwoLevelCache(String name,
                         com.github.benmanes.caffeine.cache.Cache<Object, Object> l1,
                         RedisTemplate<String, Object> redisTemplate,
                         long redisTtlSeconds,
                         String redisKeyPrefix,
                         CacheMetrics metrics) {
        super(true);
        this.name = name;
        this.l1 = l1;
        this.redisTemplate = redisTemplate;
        this.redisTtlSeconds = redisTtlSeconds;
        this.redisKeyPrefix = redisKeyPrefix;
        this.metrics = metrics == null ? new CacheMetrics() : metrics;
    }

    @Override
    public String getName() { return name; }

    @Override
    public Object getNativeCache() { return this; }

    @Override
    public ValueWrapper get(Object key) {
        Object v = lookup(key);
        return v == null ? null : () -> v;
    }

    @Override
    public <T> T get(Object key, Callable<T> valueLoader) {
        Object v = lookup(key);
        if (v != null) {
            @SuppressWarnings("unchecked") T cast = (T) fromStore(v);
            return cast;
        }
        // miss on both levels: load then backfill
        try {
            T value = valueLoader.call();
            put(key, value);
            return value;
        } catch (Exception e) {
            if (e instanceof RuntimeException) throw (RuntimeException) e;
            throw new IllegalStateException("value loader failed for key " + key, e);
        }
    }

    @Override
    public void put(Object key, Object value) {
        if (value == null) {
            evict(key);
            return;
        }
        l1.put(cacheKey(key), toStore(value));
        redisTemplate.opsForValue().set(redisKey(key), toStore(value),
                redisTtlSeconds, TimeUnit.SECONDS);
    }

    @Override
    public ValueWrapper putIfAbsent(Object key, Object value) {
        Object existing = lookup(key);
        if (existing == null) {
            put(key, value);
        }
        return existing == null ? null : () -> existing;
    }

    @Override
    public void evict(Object key) {
        l1.invalidate(cacheKey(key));
        redisTemplate.delete(redisKey(key));
        metrics.recordEviction(name);
    }

    @Override
    public boolean evictIfPresent(Object key) {
        boolean present = l1.getIfPresent(cacheKey(key)) != null
                || Boolean.TRUE.equals(redisTemplate.hasKey(redisKey(key)));
        evict(key);
        return present;
    }

    @Override
    public void clear() {
        l1.asMap().keySet().forEach(k -> {
            if (k instanceof String s && s.startsWith(redisKeyPrefix)) l1.invalidate(k);
        });
        // best-effort: clear keys for this cache namespace
        java.util.Set<String> keys = redisTemplate.keys(redisKeyPrefix + "*");
        if (keys != null && !keys.isEmpty()) redisTemplate.delete(keys);
    }

    /** Remove a key from both L1 and L2 (alias used by @CacheEvict allEntries=false). */
    public void evict(String key) { evict((Object) key); }

    /** Read-through: L1 (Caffeine) -> L2 (Redis) -> caller loads. Backfills L1 on L2 hit. */
    @Override
    protected Object lookup(Object key) {
        Object ck = cacheKey(key);
        Object l1val = l1.getIfPresent(ck);
        if (l1val != null) {
            metrics.recordL1Hit(name);
            return l1val;
        }
        Object l2val = redisTemplate.opsForValue().get(redisKey(key));
        if (l2val != null) {
            // backfill L1 (read-through)
            l1.put(ck, l2val);
            metrics.recordL2Hit(name);
        } else {
            metrics.recordMiss(name);
        }
        return l2val;
    }

    private Object cacheKey(Object key) { return name + "::" + key; }
    private String redisKey(Object key) { return redisKeyPrefix + name + "::" + key; }

    private Object toStore(Object value) {
        if (value == null) return null;
        return value;
    }

    private Object fromStore(Object stored) { return stored; }

    /** Async evict used by the manager to write-through invalidation without blocking callers. */
    public CompletableFuture<Void> evictAsync(Object key) {
        return CompletableFuture.runAsync(() -> evict(key));
    }
}
