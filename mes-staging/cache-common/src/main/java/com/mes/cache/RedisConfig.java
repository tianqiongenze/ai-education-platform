package com.mes.cache;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.impl.LaissezFaireSubTypeValidator;
import com.fasterxml.jackson.datatype.jdk8.Jdk8Module;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * Redis connection + serialization. Connection is driven by spring.data.redis.*
 * properties (host/port/password) so each service points at the shared Redis.
 *
 * The value serializer is a GenericJackson2JsonRedisSerializer backed by an
 * ObjectMapper that registers JavaTimeModule so java.time.* (LocalDateTime etc.)
 * values cached in DTOs serialize/deserialize correctly.
 */
@Configuration
@ConditionalOnClass(name = "org.springframework.data.redis.core.RedisTemplate")
public class RedisConfig {

    @Bean
    @ConditionalOnMissingBean(RedisConnectionFactory.class)
    public RedisConnectionFactory redisConnectionFactory(
            RedisStandaloneConfiguration config) {
        return new LettuceConnectionFactory(config);
    }

    @Bean
    @ConditionalOnMissingBean
    public RedisStandaloneConfiguration redisStandaloneConfiguration(
            org.springframework.core.env.Environment env) {
        String host = env.getProperty("spring.data.redis.host", "localhost");
        int port = env.getProperty("spring.data.redis.port", Integer.class, 6379);
        String password = env.getProperty("spring.data.redis.password", "");
        int db = env.getProperty("spring.data.redis.database", Integer.class, 0);
        RedisStandaloneConfiguration c = new RedisStandaloneConfiguration(host, port);
        if (password != null && !password.isBlank()) c.setPassword(password);
        c.setDatabase(db);
        return c;
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory cf) {
        RedisTemplate<String, Object> t = new RedisTemplate<>();
        t.setConnectionFactory(cf);
        t.setKeySerializer(new StringRedisSerializer());
        t.setHashKeySerializer(new StringRedisSerializer());
        t.setValueSerializer(jsonSerializer());
        t.setHashValueSerializer(jsonSerializer());
        t.afterPropertiesSet();
        return t;
    }

    private GenericJackson2JsonRedisSerializer jsonSerializer() {
        ObjectMapper om = new ObjectMapper();
        om.registerModule(new JavaTimeModule());
        om.registerModule(new Jdk8Module());
        om.disable(com.fasterxml.jackson.databind.SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        om.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        // activate default typing so polymorphic types (records, entities) round-trip
        om.activateDefaultTyping(LaissezFaireSubTypeValidator.instance,
                ObjectMapper.DefaultTyping.NON_FINAL,
                com.fasterxml.jackson.annotation.JsonTypeInfo.As.PROPERTY);
        return new GenericJackson2JsonRedisSerializer(om);
    }
}

