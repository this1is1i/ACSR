package com.example.research.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

public class UserDto {

    @Data
    public static class RegisterRequest {
        @NotBlank
        @Size(min = 3, max = 50)
        private String username;
        @NotBlank
        @Size(min = 6, max = 100)
        private String password;
        private String email;
    }

    @Data
    public static class LoginRequest {
        @NotBlank
        private String username;
        @NotBlank
        private String password;
    }

    @Data
    public static class LoginResponse {
        private String token;
        private Long userId;
        private String username;
        private String role;
    }

    @Data
    public static class UserProfile {
        private Long id;
        private String username;
        private String email;
        private String role;
        private String avatar;
        private String bio;
        private String researchInterests;
    }

    @Data
    public static class UpdateProfileRequest {
        private String email;
        private String avatar;
        private String bio;
        private String researchInterests;
    }
}
