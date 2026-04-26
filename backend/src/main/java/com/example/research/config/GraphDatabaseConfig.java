package com.example.research.config;

import org.neo4j.driver.AuthTokens;
import org.neo4j.driver.Config;
import org.neo4j.driver.Driver;
import org.neo4j.driver.GraphDatabase;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

@Configuration
public class GraphDatabaseConfig {

    @Bean(destroyMethod = "close")
    @ConditionalOnProperty(name = "graph.neo4j.enabled", havingValue = "true")
    public Driver neo4jDriver(
            @Value("${graph.neo4j.uri}") String uri,
            @Value("${graph.neo4j.username}") String username,
            @Value("${graph.neo4j.password}") String password) {

        Config driverConfig = Config.builder()
                .withConnectionTimeout(5, TimeUnit.SECONDS)
                .withMaxConnectionPoolSize(20)
                .build();

        return GraphDatabase.driver(uri, AuthTokens.basic(username, password), driverConfig);
    }
}
