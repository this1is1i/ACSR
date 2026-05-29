package com.example.research.config;

import com.example.research.enums.UserRole;
import com.example.research.util.JwtUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

/**
 * Spring Security 配置
 * 采用无状态 JWT 认证（无 Session）
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtFilter jwtFilter;

    /** 白名单：无需认证的接口 */
    private static final String[] WHITE_LIST = {
            "/api/user/register",
            "/api/user/login",
            "/api/paper/list",
            "/api/paper/*",
            "/api/paper/*/download/txt",
            "/api/paper/aminer/*",
            "/api/paper/search",
            "/api/knowledge/keywords",  // 注册页关键词选择器
            "/actuator/health",
            "/ws-messages/**",  // WebSocket 端点
            "/uploads/**",      // 头像等静态资源
    };

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // 禁用 CSRF（前后端分离）
            .csrf(AbstractHttpConfigurer::disable)
            // 禁用 Session（无状态）
            .sessionManagement(session ->
                    session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            // 请求授权配置
            .authorizeHttpRequests(auth -> auth
                    .requestMatchers(WHITE_LIST).permitAll()
                    .requestMatchers("/api/admin/**").hasRole("ADMIN")
                    .anyRequest().authenticated()
            )
            // 自定义异常处理
            .exceptionHandling(ex -> ex
                    .authenticationEntryPoint((request, response, authException) -> {
                        response.setContentType("application/json;charset=UTF-8");
                        response.setStatus(HttpStatus.UNAUTHORIZED.value());
                        response.getWriter().write(
                            "{\"code\":401,\"message\":\"未登录或 Token 已过期\",\"data\":null}"
                        );
                    })
                    .accessDeniedHandler((request, response, accessDeniedException) -> {
                        response.setContentType("application/json;charset=UTF-8");
                        response.setStatus(HttpStatus.FORBIDDEN.value());
                        response.getWriter().write(
                            "{\"code\":403,\"message\":\"权限不足\",\"data\":null}"
                        );
                    })
            )
            // 在用户名密码认证过滤器之前插入 JWT 过滤器
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}


/**
 * JWT 认证过滤器
 * 每次请求时从 Authorization 头中解析并校验 JWT Token
 *
 * 使用 Setter 注入 @Value 字段，避免 @RequiredArgsConstructor 只处理 final 字段的问题
 */
@Slf4j
@Component
class JwtFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;

    /** 从 Authorization 请求头中读取 token，可通过 yml 配置 */
    private String headerName = "Authorization";

    public JwtFilter(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    @org.springframework.beans.factory.annotation.Value("${jwt.header:Authorization}")
    public void setHeaderName(String headerName) {
        this.headerName = headerName;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String authHeader = request.getHeader(headerName);
        String token = jwtUtil.extractTokenFromHeader(authHeader);

        if (token != null && jwtUtil.validateToken(token)) {
            try {
                Long userId   = jwtUtil.getUserIdFromToken(token);
                String username = jwtUtil.getUsernameFromToken(token);
                String role   = UserRole.from(jwtUtil.getRoleFromToken(token)).name();

                // 将认证信息放入 SecurityContext
                var authorities = List.of(new SimpleGrantedAuthority("ROLE_" + role));
                var authentication = new UsernamePasswordAuthenticationToken(
                        userId, null, authorities
                );
                authentication.setDetails(username);
                SecurityContextHolder.getContext().setAuthentication(authentication);

                log.debug("JWT 认证成功: userId={}, username={}", userId, username);
            } catch (Exception e) {
                log.warn("JWT 解析异常: {}", e.getMessage());
                SecurityContextHolder.clearContext();
            }
        }

        filterChain.doFilter(request, response);
    }
}
