<template>
  <div class="viz-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <h2>📊 兴趣演化与行为分析</h2>
          <p>深度洞察您的学术兴趣轨迹与阅读行为模式</p>
        </div>
        <div class="user-info">
          <div class="user-avatar">A</div>
        </div>
      </header>

      <div class="time-filter">
        <button class="time-btn" :class="{ active: activeRange === '7d' }" @click="setRange('7d')">近7天</button>
        <button class="time-btn" :class="{ active: activeRange === '30d' }" @click="setRange('30d')">近30天</button>
        <button class="time-btn" :class="{ active: activeRange === '3m' }" @click="setRange('3m')">近3个月</button>
        <button class="time-btn" :class="{ active: activeRange === '6m' }" @click="setRange('6m')">近6个月</button>
        <button class="time-btn" :class="{ active: activeRange === '1y' }" @click="setRange('1y')">近1年</button>
      </div>

      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">总阅读时长</span>
            <div class="stat-icon-box">⏱️</div>
          </div>
          <div class="stat-value">{{ stats.readTime }}</div>
          <div class="stat-change positive">↑ {{ stats.readTimeChange }} 较上月</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">阅读论文数</span>
            <div class="stat-icon-box">📄</div>
          </div>
          <div class="stat-value">{{ stats.readCount }}</div>
          <div class="stat-change positive">↑ {{ stats.readCountChange }} 新增</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">活跃领域</span>
            <div class="stat-icon-box">🎯</div>
          </div>
          <div class="stat-value">{{ stats.activeFields }}</div>
          <div class="stat-change positive">↑ {{ stats.activeFieldsChange }} 新领域</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">研究深度</span>
            <div class="stat-icon-box">📈</div>
          </div>
          <div class="stat-value">{{ stats.depth }}</div>
          <div class="stat-change positive">↑ {{ stats.depthChange }} 提升</div>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title"><div class="chart-icon">📈</div>兴趣演化趋势</div>
            <div class="chart-actions">
              <button class="chart-btn" @click="setChartView('week')">周视图</button>
              <button class="chart-btn" @click="setChartView('month')">月视图</button>
            </div>
          </div>
          <div class="chart-container large"><canvas ref="interestChartRef"></canvas></div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title"><div class="chart-icon">🥧</div>领域分布</div>
          </div>
          <div class="chart-container"><canvas ref="fieldChartRef"></canvas></div>
        </div>

        <div class="chart-card fullwidth-chart">
          <div class="chart-header">
            <div class="chart-title"><div class="chart-icon">🔥</div>阅读活跃度热力图</div>
            <div class="chart-actions"><button class="chart-btn" @click="exportData">导出数据</button></div>
          </div>
          <div class="chart-container"><canvas ref="heatmapChartRef"></canvas></div>
        </div>

        <div class="chart-card">
          <div class="chart-header"><div class="chart-title"><div class="chart-icon">☁️</div>兴趣标签云</div></div>
          <div class="tag-cloud">
            <span v-for="(t, idx) in tagCloud" :key="idx" :class="['cloud-tag', 'size-'+t.size]">{{ t.text }}</span>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header"><div class="chart-title"><div class="chart-icon">🎯</div>阅读行为分析</div></div>
          <div class="behavior-list">
            <div class="behavior-item" v-for="(b, i) in behaviors" :key="i">
              <div class="behavior-icon">{{ b.icon }}</div>
              <div class="behavior-info"><h5>{{ b.title }}</h5><p>{{ b.desc }}</p></div>
              <div class="behavior-value">{{ b.value }}</div>
            </div>
          </div>
        </div>
        <div class="chart-card fullwidth-chart">
          <div class="chart-header">
            <div class="chart-title"><div class="chart-icon">🧭</div>知识图谱与学习路线</div>
            <div class="chart-actions">
              <button class="chart-btn btn" @click="stepPrev">上一步</button>
              <button class="chart-btn btn" @click="togglePlay">{{ playing ? '暂停' : '播放' }}</button>
              <button class="chart-btn btn" @click="stepNext">下一步</button>
              <label style="margin-left:12px;color:var(--text-secondary)">速度</label>
              <select v-model.number="playbackSpeed" style="margin-left:8px">
                <option :value="1200">慢</option>
                <option :value="800">正常</option>
                <option :value="400">快</option>
              </select>
            </div>
          </div>
          <div class="chart-container" style="height:520px;">
            <div ref="kgContainer" style="width:100%;height:100%"></div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import Chart from 'chart.js/auto'

const activeRange = ref('30d')
const stats = ref({ readTime: '42.5h', readTimeChange: '18%', readCount: 128, readCountChange: '24', activeFields: 6, activeFieldsChange: 2, depth: 85.3, depthChange: '5.2' })

import { getVisualizationData } from '@/api/visualization'

const interestChartRef = ref(null)
const fieldChartRef = ref(null)
const heatmapChartRef = ref(null)
let interestChart = null
let fieldChart = null
let heatmapChart = null

// knowledge graph refs
const kgContainer = ref(null)
let Graph3D = null
let kgData = null
const playing = ref(false)
let playbackTimer = null
const playbackSpeed = ref(800)
const currentStep = ref(0)
let currentRoute = []

const tagCloud = ref([
  { text: '深度学习', size: 5 },{ text: '神经网络', size: 4 },{ text: '计算机视觉', size: 4 },{ text: 'Transformer', size: 3 },{ text: '强化学习', size: 3 },{ text: 'GAN', size: 3 },{ text: '目标检测', size: 2 },{ text: '语义分割', size: 2 },{ text: '迁移学习', size: 2 },{ text: '联邦学习', size: 1 },{ text: '自监督', size: 1 },{ text: '对比学习', size: 1 },{ text: '多模态', size: 1 },{ text: '知识蒸馏', size: 1 }
])

const behaviors = ref([
  { icon: '📖', title: '平均阅读时长', desc: '每篇论文停留时间', value: '12.5 min' },
  { icon: '🔖', title: '收藏转化率', desc: '阅读后收藏比例', value: '34.2%' },
  { icon: '🔄', title: '重复阅读率', desc: '多次查看的论文占比', value: '18.7%' },
  { icon: '⚡', title: '峰值活跃时段', desc: '最高频阅读时间', value: '20:00-22:00' },
])

function setRange(r) {
  activeRange.value = r
}

function setChartView(v) {
  // placeholder: switch dataset or granularity
  console.log('set view', v)
}

function exportData() {
  // placeholder: export current charts data
  const data = { stats: stats.value, tags: tagCloud.value, behaviors: behaviors.value }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'viz-data.json'; a.click(); URL.revokeObjectURL(url)
}

// ---------------- Knowledge Graph (playback helpers) ----------------
async function initKnowledgeGraph(data) {
  // support backend that returns `edges` instead of `links`
  const ForceGraph3D = (await import('3d-force-graph')).default
  const nodes = data.nodes || []
  const rawLinks = data.links || data.edges || []
  // normalize links so source/target are ids (not node objects)
  const normLinks = rawLinks.map(l => ({ ...l, source: (l.source && l.source.id) ? l.source.id : l.source, target: (l.target && l.target.id) ? l.target.id : l.target }))

  kgData = { nodes, links: normLinks, routes: data.routes || [] }
  if (kgData.routes && kgData.routes.length) currentRoute = kgData.routes[0]

  Graph3D = ForceGraph3D()(kgContainer.value)
    .graphData({ nodes: kgData.nodes, links: kgData.links })
    .nodeAutoColorBy(node => node.group || node.cluster || 'group')
    .nodeRelSize(4)
    .linkWidth(link => (link._highlight ? 4 : 1))
    .linkDirectionalParticles(link => (link._highlight ? 2 : 0))
    .linkDirectionalParticleWidth(1)
    .nodeLabel(node => node.name)
    .onNodeClick(node => {
      Graph3D.centerAt(node.x, node.y, node.z, 1000)
      Graph3D.zoom(2, 1000)
    })

  highlightRouteStep(0)
}

function highlightRouteStep(step) {
  currentStep.value = step
  if (!kgData) return
  kgData.links.forEach(l => { l._highlight = false })
  kgData.nodes.forEach(n => { n._visited = false })

  for (let i = 0; i <= step && i < currentRoute.length; i++) {
    const nid = currentRoute[i]
    const node = kgData.nodes.find(n => n.id == nid)
    if (node) node._visited = true
    if (i > 0) {
      const prev = currentRoute[i-1]
      const link = kgData.links.find(l => {
        const s = (l.source && l.source.id) ? l.source.id : l.source
        const t = (l.target && l.target.id) ? l.target.id : l.target
        return (s == prev && t == nid) || (s == nid && t == prev)
      })
      if (link) link._highlight = true
    }
  }

  if (Graph3D) {
    Graph3D.graphData({ nodes: kgData.nodes, links: kgData.links })
  }
}

function playRoute() {
  if (!currentRoute || !currentRoute.length) return
  if (playing.value) return
  playing.value = true
  playbackTimer = setInterval(() => {
    if (currentStep.value < currentRoute.length - 1) {
      highlightRouteStep(currentStep.value + 1)
    } else {
      stopRoute()
    }
  }, playbackSpeed.value)
}

function stopRoute() {
  playing.value = false
  if (playbackTimer) { clearInterval(playbackTimer); playbackTimer = null }
}

function togglePlay() { if (playing.value) stopRoute(); else playRoute() }
function stepNext() { if (currentStep.value < currentRoute.length - 1) highlightRouteStep(currentStep.value + 1) }
function stepPrev() { if (currentStep.value > 0) highlightRouteStep(currentStep.value - 1) }

onMounted(async () => {
  // fetch data from backend
  try {
    const res = await getVisualizationData()
    const data = res.data || res || {}

    // stats
    if (data.stats) stats.value = data.stats

    // interest chart
    if (interestChartRef.value && data.interest) {
      const ctx = interestChartRef.value.getContext('2d')
      const gradient1 = ctx.createLinearGradient(0,0,0,400)
      gradient1.addColorStop(0,'rgba(99,102,241,0.3)')
      gradient1.addColorStop(1,'rgba(99,102,241,0)')
      const gradient2 = ctx.createLinearGradient(0,0,0,400)
      gradient2.addColorStop(0,'rgba(6,182,212,0.3)')
      gradient2.addColorStop(1,'rgba(6,182,212,0)')
      interestChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.interest.labels,
          datasets: data.interest.datasets.map((s, idx) => ({
            label: s.label,
            data: s.data,
            borderColor: idx === 0 ? '#6366f1' : '#06b6d4',
            backgroundColor: idx === 0 ? gradient1 : gradient2,
            fill: true,
            tension: 0.4
          }))
        },
        options: { responsive:true, maintainAspectRatio:false, interaction:{ mode:'index', intersect:false }, plugins:{ legend:{ position:'top' } }, scales:{ y:{ beginAtZero:true, grid:{ color:'rgba(148,163,184,0.1)' } }, x:{ grid:{ display:false } } } }
      })
    }

    // field donut
    if (fieldChartRef.value && data.field) {
      const ctx = fieldChartRef.value.getContext('2d')
      fieldChart = new Chart(ctx, {
        type: 'doughnut',
        data: { labels: data.field.labels, datasets:[{ data: data.field.data, backgroundColor:['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#6b7280'], borderWidth:0, hoverOffset:10 }] },
        options: { responsive:true, maintainAspectRatio:false, cutout:'65%', plugins:{ legend:{ position:'bottom' } } }
      })
    }

    // heatmap bar
    if (heatmapChartRef.value && data.heatmap) {
      const ctx = heatmapChartRef.value.getContext('2d')
      heatmapChart = new Chart(ctx, {
        type: 'bar',
        data: { labels: data.heatmap.labels, datasets:[{ label:'阅读论文数', data: data.heatmap.data, backgroundColor: data.heatmap.data.map(v => 'rgba(99,102,241,0.6)'), borderRadius:8, borderSkipped:false }] },
        options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } }, scales:{ y:{ beginAtZero:true, grid:{ color:'rgba(148,163,184,0.1)' } }, x:{ grid:{ display:false } } } }
      })
    }

    // tag cloud
    if (data.tags) tagCloud.value = data.tags

    // behaviors
    if (data.behaviors) behaviors.value = data.behaviors

    // knowledge graph (init)
    if (data.knowledge) {
      await initKnowledgeGraph(data.knowledge)
    }
  } catch (e) {
    console.error('Failed to load visualization data', e)
  }
})

onBeforeUnmount(()=>{
  if (interestChart) interestChart.destroy()
  if (fieldChart) fieldChart.destroy()
  if (heatmapChart) heatmapChart.destroy()
})
</script>

<style scoped>
/* styles ported from design */
:root { --primary: #6366f1; --primary-dark:#4f46e5; --secondary:#8b5cf6; --accent:#06b6d4; --bg-dark:#0f172a; --bg-card:rgba(30,41,59,0.7); --bg-hover:rgba(51,65,85,0.8); --text-primary:#f8fafc; --text-secondary:#94a3b8; --border:rgba(148,163,184,0.1); --shadow:0 25px 50px -12px rgba(0,0,0,0.5) }
.viz-root { min-height:100vh; background:var(--bg-dark); color:var(--text-primary); overflow-x:hidden }
.bg-animation { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background: radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.1) 0%, transparent 50%) }
.main-content { margin-left:260px; min-height:100vh; padding:30px 40px }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding:20px 30px; background:var(--bg-card); backdrop-filter: blur(20px); border-radius:20px; border:1px solid var(--border) }
.page-title h2 { font-size:28px; font-weight:700; margin-bottom:8px }
.page-title p { color:var(--text-secondary); font-size:15px }
.user-avatar { width:45px; height:45px; border-radius:50%; background:linear-gradient(135deg,var(--primary),var(--accent)); display:flex; align-items:center; justify-content:center; font-weight:600 }
.time-filter { display:flex; gap:10px; margin-bottom:30px }
.time-btn { padding:12px 24px; border-radius:12px; border:1px solid var(--border); background: rgba(255,255,255,0.05); color:var(--text-secondary); font-size:14px; cursor:pointer }
.time-btn.active, .time-btn:hover { background:var(--primary); color:white; border-color:var(--primary); transform: translateY(-2px) }
.charts-grid { display:grid; grid-template-columns:2fr 1fr; gap:30px; margin-bottom:30px }
.chart-card { background:var(--bg-card); backdrop-filter: blur(20px); border-radius:24px; border:1px solid var(--border); padding:30px }
.chart-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:25px }
.chart-title { font-size:18px; font-weight:600; display:flex; align-items:center; gap:10px }
.chart-icon { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,var(--primary),var(--secondary)); display:flex; align-items:center; justify-content:center; font-size:18px }
.chart-actions { display:flex; gap:10px }
.chart-btn { padding:8px 16px; border-radius:8px; border:1px solid var(--border); background: rgba(255,255,255,0.05); color:var(--text-secondary); cursor:pointer }
.chart-btn:hover { background:var(--primary); color:white }
.chart-container { position:relative; height:300px }
.chart-container.large { height:400px }
.tag-cloud { display:flex; flex-wrap:wrap; gap:12px; padding:20px 0 }
.cloud-tag { padding:10px 20px; border-radius:25px; font-weight:500; cursor:pointer; position:relative; overflow:hidden }
.cloud-tag.size-1 { font-size:12px; background: rgba(99,102,241,0.2); color:#818cf8 }
.cloud-tag.size-2 { font-size:14px; background: rgba(99,102,241,0.3); color:#a5b4fc }
.cloud-tag.size-3 { font-size:16px; background: rgba(99,102,241,0.4); color:#c7d2fe }
.cloud-tag.size-4 { font-size:18px; background: rgba(99,102,241,0.5); color:#e0e7ff }
.cloud-tag.size-5 { font-size:20px; background: linear-gradient(135deg,var(--primary),var(--secondary)); color:white }
.cloud-tag:hover { transform:scale(1.1) rotate(2deg); box-shadow:0 10px 30px rgba(99,102,241,0.3) }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:25px; margin-bottom:30px }
.stat-card { background:var(--bg-card); border-radius:20px; padding:25px; border:1px solid var(--border) }
.stat-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:15px }
.stat-label { font-size:14px; color:var(--text-secondary) }
.stat-icon-box { width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px }
.stat-value { font-size:28px; font-weight:700; margin-bottom:8px }
.stat-change { font-size:13px; display:flex; align-items:center; gap:5px }
.stat-change.positive { color:#10b981 }
.behavior-list { display:flex; flex-direction:column; gap:15px }
.behavior-item { display:flex; align-items:center; gap:15px; padding:15px; background: rgba(255,255,255,0.03); border-radius:14px; border:1px solid var(--border) }
.behavior-icon { width:45px; height:45px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px }
.behavior-info h5 { font-size:14px; font-weight:600; margin-bottom:4px }
.behavior-info p { font-size:12px; color:var(--text-secondary) }
.behavior-value { font-size:16px; font-weight:600; color:var(--primary) }
.fullwidth-chart { grid-column:1 / -1 }
@media (max-width:1200px) { .charts-grid { grid-template-columns:1fr } .stats-row { grid-template-columns:repeat(2,1fr) } .main-content { margin-left:0; padding:20px } .sidebar { transform: translateX(-100%) } }
@media (max-width:768px) { .stats-row { grid-template-columns:1fr } }
</style>