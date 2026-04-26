<template>
  <div class="comment-item">
    <div class="comment-header">
      <div class="comment-author">
        <span class="avatar">{{ comment.author?.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
        <div>
          <strong>{{ comment.author?.username || '未知用户' }}</strong>
          <span class="role">{{ comment.author?.roleLabel || '' }}</span>
        </div>
      </div>
      <span class="time">{{ formatTime(comment.createTime) }}</span>
    </div>
    <div class="comment-content">{{ comment.content }}</div>
    <button class="reply-btn" @click="$emit('reply', comment)">回复</button>

    <div v-if="comment.replies?.length" class="reply-list">
      <CommunityCommentTree
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        @reply="$emit('reply', $event)"
      />
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'CommunityCommentTree' })

defineEmits(['reply'])
defineProps({
  comment: {
    type: Object,
    required: true,
  },
})

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.comment-item {
  padding: 12px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  font-weight: 700;
}

.role,
.time {
  color: var(--text-secondary);
  font-size: 12px;
}

.comment-content {
  margin-top: 8px;
  white-space: pre-wrap;
  line-height: 1.6;
}

.reply-btn {
  margin-top: 8px;
  background: transparent;
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: var(--primary);
  border-radius: 8px;
  padding: 4px 10px;
  cursor: pointer;
}

.reply-list {
  margin-left: 24px;
  padding-left: 16px;
  border-left: 2px solid rgba(99, 102, 241, 0.15);
}
</style>
