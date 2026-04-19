package com.example.research;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.example.research.repository")
public class ResearchApplication {
    public static void main(String[] args) {
        SpringApplication.run(ResearchApplication.class, args);
    }
}
