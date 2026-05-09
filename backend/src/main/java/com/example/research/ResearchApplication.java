package com.example.research;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@MapperScan("com.example.research.repository")
@EnableAsync
public class ResearchApplication {
    public static void main(String[] args) {
        SpringApplication.run(ResearchApplication.class, args);
    }
}
