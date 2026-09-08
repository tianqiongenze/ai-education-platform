package com.mes.cache;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.CacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.RedisTemplate;

import java.util.Collection;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Builds the {@link TwoLevelCache} instances behind Spring's @Cacheable/@CacheEvict.
 *
 * Per-cache Caffeine L1 spec is read from mes.cache.specs (e.g. "productionOrders:maximumSize=500,expireAfterWrite=60s;...")
 * Each cache gets its own bounded L1 and shares the configured RedisTemplate as L2.
 */
@Configuration
public class TwoLevelCacheManagerConfig {

    @Bean
    public CacheManager twoLevelCacheManager(
            RedisTemplate<String, Object> redisTemplate,
            @Value("${mes.cache.redis.key-prefix:mes:cache:}") String keyPrefix,
            @Value("${mes.cache.redis.ttl-seconds:300}") long redisTtl,
            @Value("${mes.cache.specs:}") String specs,
            @Value("${mes.cache.default-spec:maximumSize=1000,expireAfterWrite=120s}") String defaultSpec,
            CacheMetrics metrics) {

        Map<String, Cache<Object, Object>> l1ByCache = new ConcurrentHashMap<>();
        return new CacheManager() {
            private final Map<String, TwoLevelCache> caches = new ConcurrentHashMap<>();

            @Override
            public org.springframework.cache.Cache getCache(String name) {
                return caches.computeIfAbsent(name, n -> {
                    Cache<Object, Object> l1 = l1ByCache.computeIfAbsent(n,
                            k -> Caffeine.from(resolveSpec(n)).build());
                    return new TwoLevelCache(n, l1, redisTemplate, redisTtl, keyPrefix, metrics);
                });
            }

            @Override
            public Collection<String> getCacheNames() {
                return Collections.unmodifiableSet(caches.keySet());
            }

            private String resolveSpec(String name) {
                if (specs == null || specs.isBlank()) return defaultSpec;
                for (String entry : specs.split(";")) {
                    int idx = entry.indexOf(':');
                    if (idx > 0 && entry.substring(0, idx).trim().equals(name)) {
                        return entry.substring(idx + 1).trim();
                    }
                }
                return defaultSpec;
            }
        };
    }
}
