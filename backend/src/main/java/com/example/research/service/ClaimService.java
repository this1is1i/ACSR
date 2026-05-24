package com.example.research.service;

import com.example.research.dto.ClaimDto;

import java.util.List;

public interface ClaimService {
    void confirmClaim(Long userId, Long paperId);
    void denyClaim(Long userId, Long paperId);
    List<ClaimDto.ClaimItem> getPendingClaims(Long userId);
    List<ClaimDto.ClaimItem> getConfirmedClaims(Long userId);
}
