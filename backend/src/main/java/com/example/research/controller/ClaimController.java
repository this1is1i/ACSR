package com.example.research.controller;

import com.example.research.dto.ClaimDto;
import com.example.research.service.ClaimService;
import com.example.research.util.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ClaimController {

    private final ClaimService claimService;

    @PostMapping("/paper/{paperId}/claim-confirm")
    public Result<ClaimDto.ClaimResponse> confirmClaim(
            @PathVariable Long paperId,
            Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        claimService.confirmClaim(userId, paperId);
        ClaimDto.ClaimResponse resp = new ClaimDto.ClaimResponse();
        resp.setMessage("已确认该论文为您的研究成果");
        return Result.success(resp);
    }

    @PostMapping("/paper/{paperId}/claim-deny")
    public Result<ClaimDto.ClaimResponse> denyClaim(
            @PathVariable Long paperId,
            Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        claimService.denyClaim(userId, paperId);
        ClaimDto.ClaimResponse resp = new ClaimDto.ClaimResponse();
        resp.setMessage("已否认该论文");
        return Result.success(resp);
    }

    @GetMapping("/user/claimed-papers")
    public Result<List<ClaimDto.ClaimItem>> getClaimedPapers(
            @RequestParam(defaultValue = "0") int status,
            Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        if (status == 1) {
            return Result.success(claimService.getConfirmedClaims(userId));
        }
        return Result.success(claimService.getPendingClaims(userId));
    }
}
