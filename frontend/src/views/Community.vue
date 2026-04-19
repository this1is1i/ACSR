<template>
  <div class="community-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <h2>💬 科研社区</h2>
          <p>与全球研究者交流前沿观点，分享学术洞见</p>
        </div>
        <div class="user-info"><div class="user-avatar">A</div></div>
      </header>

      <div class="community-grid">
        <div class="main-feed">
          <div class="post-creator card glass animate-fade-up">
            <div class="creator-header">
              <div class="creator-avatar">A</div>
              <textarea v-model="newPost" class="creator-input" rows="3" placeholder="分享你的科研观点、论文推荐或研究心得..."></textarea>
            </div>
            <div class="creator-actions">
              <div class="creator-tools">
                <button class="tool-btn">📎</button>
                <button class="tool-btn">📊</button>
                <button class="tool-btn">🏷️</button>
                <button class="tool-btn">😊</button>
              </div>
              <button class="post-btn btn" @click="createPost">发布动态</button>
            </div>
          </div>

          <div class="feed-section">
            <div class="feed-tabs">
              <button class="feed-tab" :class="{ active: activeTab === 'recommend' }" @click="activeTab='recommend'">推荐</button>
              <button class="feed-tab" :class="{ active: activeTab === 'following' }" @click="activeTab='following'">关注</button>
              <button class="feed-tab" :class="{ active: activeTab === 'hot' }" @click="activeTab='hot'">热门</button>
              <button class="feed-tab" :class="{ active: activeTab === 'latest' }" @click="activeTab='latest'">最新</button>
            </div>

            <div v-for="post in filteredPosts" :key="post.id" class="post-card">
              <div class="post-header">
                <div class="post-author">
                  <div class="author-avatar" :style="{ background: post.avatarBg }">{{ post.authorInitial }}</div>
                  <div class="author-info">
                    <h4>{{ post.author }}</h4>
                    <p>{{ post.affiliation }}</p>
                  </div>
                </div>
                <span class="post-time">{{ post.time }}</span>
              </div>
              <div class="post-content" v-html="post.content"></div>

              <div v-if="post.paper" class="post-paper" @click="openPaper(post.paperId)">
                <div class="paper-title-small">📄 {{ post.paper.title }}</div>
                <div class="paper-meta-small">{{ post.paper.meta }}</div>
              </div>

              <div class="post-actions">
                <span class="post-action" :class="{ active: post.liked }" @click="toggleLike(post)">👍 {{ post.likes }}</span>
                <span class="post-action" @click="openComments(post)">💬 {{ post.comments }}</span>
                <span class="post-action">🔄 分享</span>
                <span class="post-action">⭐ 收藏</span>
              </div>
            </div>
          </div>
        </div>

        <div class="sidebar-right">
          <div class="side-card card animate-fade-up">
            <div class="side-title">🔥 热门话题</div>
            <div v-for="(t, idx) in trending" :key="idx" class="trending-topic">
              <div class="topic-rank" :class="t.rankClass">{{ idx+1 }}</div>
              <div class="topic-info">
                <div class="topic-name">{{ t.name }}</div>
                <div class="topic-count">{{ t.count }} 讨论</div>
              </div>
            </div>
          </div>

          <div class="side-card card animate-fade-up">
            <div class="side-title">👥 推荐关注</div>
            <div v-for="(u, i) in recommendedUsers" :key="i" class="active-user">
              <div class="active-avatar" :style="{ background: u.avatarBg }">{{ u.initial }}</div>
              <div class="active-info">
                <div class="active-name">{{ u.name }}</div>
                <div class="active-role">{{ u.role }}</div>
              </div>
              <button class="follow-btn btn" @click="toggleFollow(u)">{{ u.following ? '已关注' : '关注' }}</button>
            </div>
          </div>

          <div class="side-card">
            <div class="side-title">📊 社区数据</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: center;">
              <div style="padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 5px;">12.5k</div>
                <div style="font-size: 12px; color: var(--text-secondary);">活跃用户</div>
              </div>
              <div style="padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: var(--accent); margin-bottom: 5px;">3.2k</div>
                <div style="font-size: 12px; color: var(--text-secondary);">今日动态</div>
              </div>
              <div style="padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: var(--secondary); margin-bottom: 5px;">8.9k</div>
                <div style="font-size: 12px; color: var(--text-secondary);">论文分享</div>
              </div>
              <div style="padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #10b981; margin-bottom: 5px;">456</div>
                <div style="font-size: 12px; color: var(--text-secondary);">正在讨论</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Sidebar from '@/components/Sidebar.vue'

const newPost = ref('')
const activeTab = ref('recommend')

const posts = ref([
  { id: 'p1', author: '张三 教授', authorInitial: '张', affiliation: '清华大学 · 机器学习实验室', time: '2小时前', content: '刚刚读完这篇关于<a href="#">Graph Neural Networks for Recommendation</a>的综述，作者对GNN在推荐系统中的应用做了非常系统的梳理。', likes: 128, comments: 23, liked: false, paper: { title: 'Graph Neural Networks for Recommendation: A Comprehensive Survey', meta: 'Nature Machine Intelligence · 2024 · 被引 2,341' }, avatarBg: 'linear-gradient(135deg, #8b5cf6, #a78bfa)' },
  { id: 'p2', author: '李四 博士', authorInitial: '李', affiliation: '中科院自动化所 · CV组', time: '5小时前', content: '我们在CVPR 2024上的工作终于放出了代码！这是一个关于<a href="#">自监督学习在医学影像分割</a>的研究，欢迎大家试用。', likes: 256, comments: 45, liked: false },
  { id: 'p3', author: '王五 研究员', authorInitial: '王', affiliation: '北大 · 自然语言处理实验室', time: '昨天', content: '最近大语言模型的推理能力引起了广泛关注。我想发起一个讨论：<b>如何评估LLM的真实推理能力而非模式匹配？</b>', likes: 89, comments: 67, liked: true },
  { id: 'p4', author: '赵六 副教授', authorInitial: '赵', affiliation: '浙江大学 · 数据挖掘组', time: '2天前', content: '分享一个有趣的发现：在联邦学习场景下，<a href="#">梯度压缩</a>和<a href="#">差分隐私</a>的结合使用可以在保护隐私的同时，将通信开销降低80%。', likes: 167, comments: 34, liked: false }
])

const filteredPosts = computed(() => {
  // simple filters based on activeTab (demo)
  if (activeTab.value === 'recommend') return posts.value
  if (activeTab.value === 'following') return posts.value.filter(p => p.liked)
  if (activeTab.value === 'hot') return posts.value.slice().sort((a,b) => b.likes - a.likes)
  return posts.value.slice().reverse()
})

const trending = ref([
  { name: '大语言模型对齐', count: '1.2k', rankClass: 'hot' },
  { name: '多模态融合', count: '856', rankClass: 'hot' },
  { name: 'AI for Science', count: '723', rankClass: 'warm' },
  { name: '神经架构搜索', count: '534', rankClass: 'normal' },
  { name: '可解释AI', count: '412', rankClass: 'normal' }
])

const recommendedUsers = ref([
  { name: '陈七 教授', initial: '陈', role: '复旦 · 强化学习专家', avatarBg: 'linear-gradient(135deg, #f59e0b, #fbbf24)', following: false },
  { name: '刘八 博士', initial: '刘', role: 'MSRA · 计算机视觉', avatarBg: 'linear-gradient(135deg, #6366f1, #8b5cf6)', following: false },
  { name: '周九 研究员', initial: '周', role: '阿里 · NLP组', avatarBg: 'linear-gradient(135deg, #ec4899, #f472b6)', following: false }
])

function createPost() {
  if (!newPost.value.trim()) return
  posts.value.unshift({ id: 'p'+(Date.now()), author: '我', authorInitial: '我', affiliation: '我的机构', time: '刚刚', content: newPost.value, likes: 0, comments: 0, liked: false })
  newPost.value = ''
}

function toggleLike(p) {
  p.liked = !p.liked
  p.likes += p.liked ? 1 : -1
}

function openComments(p) { console.log('open comments for', p.id) }
function openPaper(id) { console.log('open paper', id) }
function toggleFollow(u) { u.following = !u.following }
</script>

<style scoped>
@import '@/style.css';

/* Ensure main content leaves space for the fixed sidebar */
.main-content { margin-left: 260px; min-height: 100vh; padding: 30px 40px }

.community-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 28px;
  align-items: start;
}

.main-feed {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.post-creator .creator-header { display:flex; gap:12px; align-items:flex-start }
.creator-avatar { width:48px; height:48px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-weight:700 }
.creator-input { flex:1; min-height:76px; resize:vertical; border-radius:10px }
.creator-actions { display:flex; justify-content:space-between; align-items:center; margin-top:10px }
.creator-tools .tool-btn { background:transparent; border:none; font-size:18px; opacity:0.85 }

.feed-section { display:flex; flex-direction:column; gap:12px }
.feed-tabs { display:flex; gap:10px; margin-bottom:12px }
.feed-tab { padding:8px 12px; border-radius:8px; background:transparent; border:1px solid var(--design-border); color:var(--text-secondary) }
.feed-tab.active { background:linear-gradient(90deg,var(--primary),var(--secondary)); color:white; box-shadow:0 10px 30px rgba(99,102,241,0.12) }

.post-card { padding:18px; border-radius:12px; background:var(--bg-card); border:1px solid var(--design-border); box-shadow:0 8px 30px rgba(2,6,23,0.25) }
.post-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px }
.post-author { display:flex; gap:12px; align-items:center }
.author-avatar { width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-weight:700 }
.post-content { margin-top:10px; color:var(--text-primary) }
.post-actions { display:flex; gap:16px; margin-top:12px; color:var(--text-secondary) }
.post-action { cursor:pointer }

.sidebar-right { display:flex; flex-direction:column; gap:18px }
.side-card { padding:14px }
.trending-topic { display:flex; gap:12px; align-items:center; padding:8px 0; border-bottom:1px dashed rgba(255,255,255,0.03) }
.topic-rank { width:28px; height:28px; border-radius:6px; display:flex; align-items:center; justify-content:center; color:white; font-weight:700 }
.topic-rank.hot { background:linear-gradient(90deg,var(--primary),var(--secondary)) }
.topic-info .topic-name { font-weight:600 }

@media (max-width: 980px) {
  .community-grid { grid-template-columns: 1fr; padding: 16px }
  .main-content { margin-left: 0; padding: 18px }
  .sidebar { transform:none }
}
</style>