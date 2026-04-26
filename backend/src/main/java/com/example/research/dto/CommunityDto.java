package com.example.research.dto;

import com.example.research.enums.PostStatus;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

public class CommunityDto {

    @Data
    public static class PostCreateRequest {
        @Size(max = 200)
        private String title;
        @NotBlank
        @Size(max = 5000)
        private String content;
        private Long paperId;
    }

    @Data
    public static class CommentCreateRequest {
        private Long parentId;
        @NotBlank
        @Size(max = 2000)
        private String content;
    }

    @Data
    public static class AuthorInfo {
        private Long id;
        private String username;
        private String role;
        private String roleLabel;
        private String avatar;
        private String bio;
    }

    @Data
    public static class PaperInfo {
        private Long id;
        private String aminerId;
        private String title;
        private String venue;
        private Integer year;
        private Integer citationCount;
    }

    @Data
    public static class PostItem {
        private Long id;
        private Long paperId;
        private String title;
        private String content;
        private Integer likeCount;
        private Integer replyCount;
        private Integer status;
        private String statusName;
        private String statusLabel;
        private String reviewComment;
        private LocalDateTime createTime;
        private boolean own;
        private AuthorInfo author;
        private PaperInfo paper;

        public void applyStatus(PostStatus postStatus) {
            this.status = postStatus.getCode();
            this.statusName = postStatus.name();
            this.statusLabel = postStatus.getLabel();
        }
    }

    @Data
    public static class CommentItem {
        private Long id;
        private Long postId;
        private Long parentId;
        private Long rootId;
        private String content;
        private Integer likeCount;
        private LocalDateTime createTime;
        private AuthorInfo author;
        private List<CommentItem> replies = new ArrayList<>();
    }

    @Data
    public static class PostStatusUpdateRequest {
        @NotBlank
        private String status;
        @Size(max = 500)
        private String reviewComment;
    }

    @Data
    public static class PaperImportItem {
        private String aminerId;
        @NotBlank
        @Size(max = 500)
        private String title;
        @JsonProperty("abstract")
        private String abstractText;
        private List<String> authors = new ArrayList<>();
        private List<String> keywords = new ArrayList<>();
        private String venue;
        private Integer year;
        private Integer citationCount;
    }

    @Data
    public static class PaperImportRequest {
        @Valid
        @NotEmpty
        private List<PaperImportItem> papers;
    }

    @Data
    public static class PaperImportResult {
        private Integer importedCount;
        private List<String> aminerIds;
    }
}
