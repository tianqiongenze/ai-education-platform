package com.mes.cache;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

/**
 * Auto-applied when a service depends on cache-common. Enables Spring's
 * declarative cache abstraction and registers the two-level cache beans.
 */
@Configuration
@AutoConfiguration
@ComponentScan("com.mes.cache")
@ConditionalOnClass(name = "org.springframework.cache.annotation.EnableCaching")
@EnableCaching
public class CacheAutoConfiguration {
}
