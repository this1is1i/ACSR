package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.research.dto.ClaimDto;
import com.example.research.entity.PaperAuthorClaim;
import com.example.research.repository.PaperAuthorClaimMapper;
import com.example.research.service.ClaimService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ClaimServiceImpl implements ClaimService {

    private final PaperAuthorClaimMapper claimMapper;

    @Override
    public void confirmClaim(Long userId, Long paperId) {
        PaperAuthorClaim claim = findPendingClaim(userId, paperId);
        claim.setStatus(1);
        claim.setRespondedAt(LocalDateTime.now());
        claimMapper.updateById(claim);
    }

    @Override
    public void denyClaim(Long userId, Long paperId) {
        PaperAuthorClaim claim = findPendingClaim(userId, paperId);
        claim.setStatus(2);
        claim.setRespondedAt(LocalDateTime.now());
        claimMapper.updateById(claim);
    }

    @Override
    public List<ClaimDto.ClaimItem> getPendingClaims(Long userId) {
        return mapToItems(claimMapper.findByUserAndStatus(userId, 0));
    }

    @Override
    public List<ClaimDto.ClaimItem> getConfirmedClaims(Long userId) {
        return mapToItems(claimMapper.findByUserAndStatus(userId, 1));
    }

    private PaperAuthorClaim findPendingClaim(Long userId, Long paperId) {
        LambdaQueryWrapper<PaperAuthorClaim> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(PaperAuthorClaim::getUserId, userId)
               .eq(PaperAuthorClaim::getPaperId, paperId)
               .eq(PaperAuthorClaim::getStatus, 0);
        PaperAuthorClaim claim = claimMapper.selectOne(wrapper);
        if (claim == null) {
            throw new IllegalArgumentException("认领记录不存在或已处理");
        }
        return claim;
    }

    private List<ClaimDto.ClaimItem> mapToItems(List<Map<String, Object>> rows) {
        List<ClaimDto.ClaimItem> items = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            ClaimDto.ClaimItem item = new ClaimDto.ClaimItem();
            item.setClaimId((Long) row.get("claim_id"));
            item.setPaperId((Long) row.get("paper_id"));
            item.setAminerId((String) row.get("aminer_id"));
            item.setTitle((String) row.get("title"));
            item.setAuthors((String) row.get("authors"));
            item.setVenue((String) row.get("venue"));
            item.setYear(row.get("year") != null ? ((Number) row.get("year")).intValue() : null);
            item.setAuthorName((String) row.get("author_name"));
            item.setMatchMethod((String) row.get("match_method"));
            item.setConfidence(row.get("confidence") != null ? ((Number) row.get("confidence")).doubleValue() : null);
            Integer status = row.get("status") != null ? ((Number) row.get("status")).intValue() : 0;
            item.applyStatus(status);
            item.setRespondedAt((java.time.LocalDateTime) row.get("responded_at"));
            item.setCreateTime((java.time.LocalDateTime) row.get("claim_time"));
            items.add(item);
        }
        return items;
    }
}
