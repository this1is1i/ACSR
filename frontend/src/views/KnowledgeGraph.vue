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
        <div class="chart-card fullwidth-chart" :class="{ 'kg-fullscreen': isFullscreen }" ref="kgCardRef">
          <div class="chart-header">
            <div class="chart-title"><div class="chart-icon">🧭</div>知识图谱与学习路线</div>
            <div class="chart-actions kg-controls">
              <div class="mastery-legend">
                <span class="legend-label">掌握度</span>
                <div class="legend-bar"></div>
                <span class="legend-min">未学习</span>
                <span class="legend-max">已掌握</span>
              </div>
              <div class="kg-buttons">
                <button class="chart-btn btn" @click="stepPrev" :disabled="currentStep <= 0">⏮ 上一步</button>
                <button class="chart-btn btn play-btn" @click="togglePlay">{{ playing ? '⏸ 暂停' : '▶ 播放' }}</button>
                <button class="chart-btn btn" @click="stepNext" :disabled="currentStep >= currentRoute.length - 1">下一步 ⏭</button>
                <button class="chart-btn btn reset-btn" @click="resetPath">↺ 重置</button>
                <select v-model.number="playbackSpeed" class="speed-select">
                  <option :value="1500">0.5x 慢速</option>
                  <option :value="1000">1x 正常</option>
                  <option :value="500">2x 快速</option>
                </select>
                <button class="chart-btn btn fullscreen-btn" @click="toggleFullscreen" :title="isFullscreen ? '退出全屏' : '全屏显示'">
                  {{ isFullscreen ? '⛶ 退出全屏' : '⛶ 全屏' }}
                </button>
              </div>
            </div>
          </div>
          <!-- Learning path info bar -->
          <div class="path-info-bar" v-if="pathMeta.topic">
            <div class="path-meta">
              <span class="meta-chip"><span class="meta-icon">🎯</span>{{ pathMeta.topic }}</span>
              <span class="meta-chip"><span class="meta-icon">⏱️</span>预估 {{ pathMeta.estimatedHours }}h</span>
              <span class="meta-chip"><span class="meta-icon">📊</span>覆盖率 {{ (pathMeta.coverage * 100).toFixed(0) }}%</span>
            </div>
            <div class="path-progress">
              <div class="progress-track">
                <div class="progress-fill" :style="{width: progressPercent + '%'}"></div>
              </div>
              <span class="progress-text">{{ currentStep + 1 }} / {{ currentRoute.length }}</span>
            </div>
          </div>
          <div class="kg-layout">
            <div class="kg-canvas-wrap">
              <div ref="kgContainer" class="kg-canvas"></div>
            </div>
            <!-- Node detail panel -->
            <div class="node-detail" v-if="selectedNode">
              <div class="detail-close" @click="selectedNode = null">✕</div>
              <div class="detail-type-badge" :class="selectedNode.type">{{ selectedNode.type === 'paper' ? '📄 论文' : '🔑 关键词' }}</div>
              <h4 class="detail-name">{{ selectedNode.name }}</h4>
              <div class="detail-mastery">
                <span>掌握度</span>
                <div class="mastery-bar-wrap">
                  <div class="mastery-bar-fill" :style="{width: (selectedNode.mastery * 100) + '%', background: masteryColor(selectedNode.mastery)}"></div>
                </div>
                <span class="mastery-pct">{{ (selectedNode.mastery * 100).toFixed(0) }}%</span>
              </div>
              <div class="detail-row" v-if="selectedNode.year"><span class="detail-label">年份</span><span>{{ selectedNode.year }}</span></div>
              <div class="detail-row"><span class="detail-label">深度层</span><span>{{ depthLabel(selectedNode.depth) }}</span></div>
              <div class="detail-row"><span class="detail-label">节点 ID</span><span class="detail-id">{{ selectedNode.id }}</span></div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import Chart from 'chart.js/auto'
import * as THREE from 'three'

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
const kgCardRef = ref(null)
const isFullscreen = ref(false)
let Graph3D = null
let kgData = null
const playing = ref(false)
let playbackTimer = null
const playbackSpeed = ref(1000)
const currentStep = ref(0)
const currentRoute = ref([])
const selectedNode = ref(null)
const pathMeta = reactive({ topic: '', estimatedHours: 0, coverage: 0 })
const progressPercent = ref(0)

const tagCloud = ref([
  { text: '深度学习', size: 5 },{ text: '神经网络', size: 4 },{ text: '计算机视觉', size: 4 },{ text: 'Transformer', size: 3 },{ text: '强化学习', size: 3 },{ text: 'GAN', size: 3 },{ text: '目标检测', size: 2 },{ text: '语义分割', size: 2 },{ text: '迁移学习', size: 2 },{ text: '联邦学习', size: 1 },{ text: '自监督', size: 1 },{ text: '对比学习', size: 1 },{ text: '多模态', size: 1 },{ text: '知识蒸馏', size: 1 }
])

const behaviors = ref([
  { icon: '📖', title: '平均阅读时长', desc: '每篇论文停留时间', value: '12.5 min' },
  { icon: '🔖', title: '收藏转化率', desc: '阅读后收藏比例', value: '34.2%' },
  { icon: '🔄', title: '重复阅读率', desc: '多次查看的论文占比', value: '18.7%' },
  { icon: '⚡', title: '峰值活跃时段', desc: '最高频阅读时间', value: '20:00-22:00' },
])

function setRange(r) { activeRange.value = r }
function setChartView(v) { console.log('set view', v) }
function exportData() {
  const data = { stats: stats.value, tags: tagCloud.value, behaviors: behaviors.value }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'viz-data.json'; a.click(); URL.revokeObjectURL(url)
}

// ── mastery → color helpers ──────────────────────────────────────
function masteryColor(m) {
  // 0.0 → #3B82F6 (blue), 0.5 → #F59E0B (orange), 1.0 → #10B981 (green)
  const clamp = Math.max(0, Math.min(1, m))
  let r, g, b
  if (clamp <= 0.5) {
    const t = clamp / 0.5
    r = Math.round(0x3B + (0xF5 - 0x3B) * t)
    g = Math.round(0x82 + (0x9E - 0x82) * t)
    b = Math.round(0xF6 + (0x0B - 0xF6) * t)
  } else {
    const t = (clamp - 0.5) / 0.5
    r = Math.round(0xF5 + (0x10 - 0xF5) * t)
    g = Math.round(0x9E + (0xB9 - 0x9E) * t)
    b = Math.round(0x0B + (0x81 - 0x0B) * t)
  }
  return `rgb(${r},${g},${b})`
}

function masteryHex(m) {
  const clamp = Math.max(0, Math.min(1, m))
  let r, g, b
  if (clamp <= 0.5) {
    const t = clamp / 0.5
    r = 0x3B + (0xF5 - 0x3B) * t
    g = 0x82 + (0x9E - 0x82) * t
    b = 0xF6 + (0x0B - 0xF6) * t
  } else {
    const t = (clamp - 0.5) / 0.5
    r = 0xF5 + (0x10 - 0xF5) * t
    g = 0x9E + (0xB9 - 0x9E) * t
    b = 0x0B + (0x81 - 0x0B) * t
  }
  return (Math.round(r) << 16) | (Math.round(g) << 8) | Math.round(b)
}

function depthLabel(d) {
  return ['基础 (已掌握)', '中级 (进行中)', '目标方向', '论文阅读'][d] || `层级 ${d}`
}

// ── Three.js text sprite helper ──────────────────────────────────
function createTextSprite(text, fontSize = 48, color = '#e2e8f0') {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = `${fontSize}px "Microsoft YaHei", sans-serif`
  const metric = ctx.measureText(text.length > 18 ? text.slice(0, 18) + '…' : text)
  const displayText = text.length > 18 ? text.slice(0, 18) + '…' : text
  const w = metric.width + 24
  const h = fontSize + 16
  canvas.width = w
  canvas.height = h
  ctx.font = `${fontSize}px "Microsoft YaHei", sans-serif`
  ctx.fillStyle = color
  ctx.textBaseline = 'middle'
  ctx.fillText(displayText, 12, h / 2)
  const texture = new THREE.CanvasTexture(canvas)
  texture.needsUpdate = true
  const mat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false })
  const sprite = new THREE.Sprite(mat)
  sprite.scale.set(w / 8, h / 8, 1)
  return sprite
}

// ── Knowledge Graph 3D initialization ────────────────────────────
async function initKnowledgeGraph(data) {
  const ForceGraph3D = (await import('3d-force-graph')).default

  const nodes = (data.nodes || []).map(n => ({ ...n, _visited: false, _active: false }))
  const rawLinks = data.links || data.edges || []
  const normLinks = rawLinks.map(l => ({
    ...l,
    source: (l.source && l.source.id) ? l.source.id : l.source,
    target: (l.target && l.target.id) ? l.target.id : l.target,
    _highlight: false,
    _pathEdge: false,
  }))

  // Learning path metadata
  const lp = data.learningPath || {}
  if (lp.topic) {
    pathMeta.topic = lp.topic
    pathMeta.estimatedHours = lp.estimatedHours || 0
    pathMeta.coverage = lp.coverage || 0
  }
  const routeIds = lp.route || []
  currentRoute.value = routeIds

  // Mark edges that belong to the learning path
  const routeSet = new Set(routeIds)
  normLinks.forEach(l => {
    const sId = typeof l.source === 'object' ? l.source.id : l.source
    const tId = typeof l.target === 'object' ? l.target.id : l.target
    if (routeSet.has(sId) && routeSet.has(tId)) l._pathEdge = true
  })

  kgData = { nodes, links: normLinks }

  const container = kgContainer.value
  if (!container) return

  Graph3D = ForceGraph3D()(container)
    .graphData({ nodes: kgData.nodes, links: kgData.links })
    .backgroundColor('#00000000')
    .showNavInfo(false)
    // Hierarchical layout by depth (top-down)
    .dagMode('td')
    .dagLevelDistance(50)
    // Custom 3D node objects
    .nodeThreeObject(node => {
      const group = new THREE.Group()
      const hex = masteryHex(node.mastery || 0)
      const emissiveIntensity = 0.2 + (node.mastery || 0) * 0.5

      // Keyword → sphere, paper → rounded box
      let geometry, size
      if (node.type === 'paper') {
        size = 4
        geometry = new THREE.BoxGeometry(size, size, size)
      } else {
        size = node.depth === 0 ? 5 : (node.depth === 1 ? 4.5 : 4)
        geometry = new THREE.SphereGeometry(size, 24, 24)
      }

      const material = new THREE.MeshPhongMaterial({
        color: hex,
        emissive: hex,
        emissiveIntensity,
        shininess: 80,
        transparent: true,
        opacity: node._active ? 1.0 : (node._visited ? 0.95 : 0.65),
      })
      const mesh = new THREE.Mesh(geometry, material)

      // Glow ring for active node
      if (node._active) {
        const ringGeo = new THREE.RingGeometry(size + 1, size + 2.5, 32)
        const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, opacity: 0.6 })
        const ring = new THREE.Mesh(ringGeo, ringMat)
        group.add(ring)
      }

      // Visited check ring
      if (node._visited && !node._active) {
        const ringGeo = new THREE.RingGeometry(size + 0.5, size + 1.5, 32)
        const ringMat = new THREE.MeshBasicMaterial({ color: hex, side: THREE.DoubleSide, transparent: true, opacity: 0.4 })
        const ring = new THREE.Mesh(ringGeo, ringMat)
        group.add(ring)
      }

      group.add(mesh)

      // Label sprite above node
      const label = createTextSprite(node.name, 36)
      label.position.set(0, size + 4, 0)
      group.add(label)

      return group
    })
    .nodeThreeObjectExtend(false)
    // Custom link rendering
    .linkWidth(link => link._highlight ? 3 : (link._pathEdge ? 1.5 : 0.5))
    .linkColor(link => {
      if (link._highlight) return '#ffffff'
      if (link._pathEdge) return 'rgba(99, 102, 241, 0.6)'
      return 'rgba(148, 163, 184, 0.2)'
    })
    .linkOpacity(0.8)
    .linkDirectionalParticles(link => link._highlight ? 4 : (link._pathEdge ? 1 : 0))
    .linkDirectionalParticleWidth(link => link._highlight ? 3 : 1.5)
    .linkDirectionalParticleSpeed(0.006)
    .linkDirectionalParticleColor(link => link._highlight ? '#ffffff' : '#6366f1')
    // Interaction
    .onNodeClick(node => {
      selectedNode.value = node
      // Camera zoom to node
      const dist = 120
      const pos = node
      Graph3D.cameraPosition(
        { x: pos.x, y: pos.y + 40, z: pos.z + dist },
        { x: pos.x, y: pos.y, z: pos.z },
        1000
      )
    })
    .onBackgroundClick(() => { selectedNode.value = null })
    .width(container.clientWidth)
    .height(560)

  // Add ambient + directional light to the scene
  const scene = Graph3D.scene()
  scene.add(new THREE.AmbientLight(0x404060, 1.5))
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(50, 100, 50)
  scene.add(dirLight)

  // Initial camera position
  setTimeout(() => {
    Graph3D.cameraPosition({ x: 0, y: 120, z: 300 }, { x: 0, y: 0, z: 0 }, 2000)
  }, 500)

  highlightRouteStep(0)
}

// ── Route playback ───────────────────────────────────────────────
function highlightRouteStep(step) {
  currentStep.value = step
  progressPercent.value = currentRoute.value.length > 1
    ? (step / (currentRoute.value.length - 1)) * 100 : 0
  if (!kgData) return

  // Reset all
  kgData.links.forEach(l => { l._highlight = false })
  kgData.nodes.forEach(n => { n._visited = false; n._active = false })

  // Mark visited & active
  for (let i = 0; i <= step && i < currentRoute.value.length; i++) {
    const nid = currentRoute.value[i]
    const node = kgData.nodes.find(n => n.id === nid)
    if (node) {
      node._visited = true
      if (i === step) node._active = true
    }
    if (i > 0) {
      const prev = currentRoute.value[i - 1]
      const link = kgData.links.find(l => {
        const s = (l.source && l.source.id) ? l.source.id : l.source
        const t = (l.target && l.target.id) ? l.target.id : l.target
        return (s === prev && t === nid) || (s === nid && t === prev)
      })
      if (link) link._highlight = true
    }
  }

  if (Graph3D) {
    Graph3D.nodeThreeObject(Graph3D.nodeThreeObject()) // force re-render
    Graph3D.graphData({ nodes: kgData.nodes, links: kgData.links })

    // Auto-center on active node
    const activeId = currentRoute.value[step]
    const activeNode = kgData.nodes.find(n => n.id === activeId)
    if (activeNode && activeNode.x !== undefined) {
      Graph3D.cameraPosition(
        { x: activeNode.x, y: activeNode.y + 50, z: activeNode.z + 150 },
        { x: activeNode.x, y: activeNode.y, z: activeNode.z },
        800
      )
      selectedNode.value = activeNode
    }
  }
}

function playRoute() {
  if (!currentRoute.value.length) return
  if (playing.value) return
  playing.value = true
  playbackTimer = setInterval(() => {
    if (currentStep.value < currentRoute.value.length - 1) {
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

function stepNext() {
  if (currentStep.value < currentRoute.value.length - 1) highlightRouteStep(currentStep.value + 1)
}

function stepPrev() {
  if (currentStep.value > 0) highlightRouteStep(currentStep.value - 1)
}

function resetPath() {
  stopRoute()
  highlightRouteStep(0)
}

function toggleFullscreen() {
  const el = kgCardRef.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen().catch(() => {
      // Fallback: CSS-only fullscreen if API denied
      isFullscreen.value = !isFullscreen.value
      resizeGraph()
    })
  } else {
    document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
  resizeGraph()
}

function resizeGraph() {
  if (!Graph3D || !kgContainer.value) return
  setTimeout(() => {
    const container = kgContainer.value
    Graph3D.width(container.clientWidth)
    Graph3D.height(container.clientHeight)
  }, 100)
}

// Re-start playback when speed changes
watch(playbackSpeed, () => {
  if (playing.value) {
    stopRoute()
    playRoute()
  }
})

onMounted(async () => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  try {
    const res = await getVisualizationData()
    const data = res.data || res || {}

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
        data: { labels: data.heatmap.labels, datasets:[{ label:'阅读论文数', data: data.heatmap.data, backgroundColor: data.heatmap.data.map(() => 'rgba(99,102,241,0.6)'), borderRadius:8, borderSkipped:false }] },
        options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } }, scales:{ y:{ beginAtZero:true, grid:{ color:'rgba(148,163,184,0.1)' } }, x:{ grid:{ display:false } } } }
      })
    }

    if (data.tags) tagCloud.value = data.tags
    if (data.behaviors) behaviors.value = data.behaviors

    // 3D knowledge graph & learning path
    if (data.knowledge) {
      await initKnowledgeGraph(data.knowledge)
    }
  } catch (e) {
    console.error('Failed to load visualization data', e)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  stopRoute()
  if (interestChart) interestChart.destroy()
  if (fieldChart) fieldChart.destroy()
  if (heatmapChart) heatmapChart.destroy()
  if (Graph3D) { Graph3D._destructor && Graph3D._destructor() }
})
</script>

<style scoped>
:root { --primary: #6366f1; --primary-dark:#4f46e5; --secondary:#8b5cf6; --accent:#06b6d4; --bg-dark:#0f172a; --bg-card:rgba(30,41,59,0.7); --bg-hover:rgba(51,65,85,0.8); --text-primary:#f8fafc; --text-secondary:#94a3b8; --border:rgba(148,163,184,0.1); --shadow:0 25px 50px -12px rgba(0,0,0,0.5) }
.viz-root { min-height:100vh; background:var(--bg-dark); color:var(--text-primary); overflow-x:hidden }
.bg-animation { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background: radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.1) 0%, transparent 50%) }
.main-content { margin-left:260px; min-height:100vh; padding:30px 40px }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding:20px 30px; background:var(--bg-card); backdrop-filter: blur(20px); border-radius:20px; border:1px solid var(--border) }
.page-title h2 { font-size:28px; font-weight:700; margin-bottom:8px }
.page-title p { color:var(--text-secondary); font-size:15px }
.user-avatar { width:45px; height:45px; border-radius:50%; background:linear-gradient(135deg,var(--primary),var(--accent)); display:flex; align-items:center; justify-content:center; font-weight:600 }
.time-filter { display:flex; gap:10px; margin-bottom:30px }
.time-btn { padding:12px 24px; border-radius:12px; border:1px solid var(--border); background: rgba(255,255,255,0.05); color:var(--text-secondary); font-size:14px; cursor:pointer; transition: all 0.2s }
.time-btn.active, .time-btn:hover { background:var(--primary); color:white; border-color:var(--primary); transform: translateY(-2px) }
.charts-grid { display:grid; grid-template-columns:2fr 1fr; gap:30px; margin-bottom:30px }
.chart-card { background:var(--bg-card); backdrop-filter: blur(20px); border-radius:24px; border:1px solid var(--border); padding:30px }
.chart-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:25px; flex-wrap:wrap; gap:12px }
.chart-title { font-size:18px; font-weight:600; display:flex; align-items:center; gap:10px }
.chart-icon { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,var(--primary),var(--secondary)); display:flex; align-items:center; justify-content:center; font-size:18px }
.chart-actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap }
.chart-btn { padding:8px 16px; border-radius:8px; border:1px solid var(--border); background: rgba(255,255,255,0.05); color:var(--text-secondary); cursor:pointer; transition: all 0.2s; font-size:13px }
.chart-btn:hover:not(:disabled) { background:var(--primary); color:white }
.chart-btn:disabled { opacity:0.4; cursor:not-allowed }
.chart-container { position:relative; height:300px }
.chart-container.large { height:400px }
.tag-cloud { display:flex; flex-wrap:wrap; gap:12px; padding:20px 0 }
.cloud-tag { padding:10px 20px; border-radius:25px; font-weight:500; cursor:pointer; position:relative; overflow:hidden; transition: all 0.2s }
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

/* ── Fullscreen mode ──────────────────────────────────────────── */
.fullscreen-btn {
  background:linear-gradient(135deg, rgba(99,102,241,0.3), rgba(6,182,212,0.3)) !important;
  border-color:rgba(99,102,241,0.4) !important; color:#e2e8f0 !important;
  font-size:13px; min-width:90px;
}
.fullscreen-btn:hover { background:linear-gradient(135deg, var(--primary), var(--accent)) !important; color:white !important }

.kg-fullscreen {
  position:fixed !important; top:0; left:0; right:0; bottom:0;
  z-index:9999; margin:0; border-radius:0 !important;
  background:#0f172a !important; padding:20px 24px;
  display:flex; flex-direction:column;
}
.kg-fullscreen .chart-header { flex-shrink:0 }
.kg-fullscreen .path-info-bar { flex-shrink:0 }
.kg-fullscreen .kg-layout { flex:1; min-height:0 }
.kg-fullscreen .kg-canvas-wrap { flex:1; min-height:0 }
.kg-fullscreen .kg-canvas { height:100% !important }

/* ── Knowledge Graph 3D Section ──────────────────────────────── */
.kg-controls { display:flex; flex-direction:column; gap:10px; align-items:flex-end }
.kg-buttons { display:flex; gap:8px; align-items:center; flex-wrap:wrap }
.play-btn { background:linear-gradient(135deg, var(--primary), var(--secondary)) !important; color:white !important; border-color:transparent !important; min-width:80px }
.reset-btn:hover { background:#ef4444 !important; border-color:#ef4444 !important; color:white !important }
.speed-select {
  padding:6px 12px; border-radius:8px; border:1px solid var(--border);
  background:rgba(255,255,255,0.05); color:var(--text-secondary);
  font-size:13px; cursor:pointer; outline:none;
}
.speed-select option { background:#1e293b; color:#e2e8f0 }

/* Mastery legend */
.mastery-legend { display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text-secondary) }
.legend-bar {
  width:120px; height:8px; border-radius:4px;
  background: linear-gradient(to right, #3B82F6, #F59E0B, #10B981);
}
.legend-min { color:#3B82F6; font-size:11px }
.legend-max { color:#10B981; font-size:11px }

/* Path info bar */
.path-info-bar {
  display:flex; justify-content:space-between; align-items:center;
  padding:14px 20px; margin-bottom:16px;
  background:rgba(99,102,241,0.08); border-radius:14px;
  border:1px solid rgba(99,102,241,0.15);
}
.path-meta { display:flex; gap:16px; flex-wrap:wrap }
.meta-chip {
  display:flex; align-items:center; gap:6px;
  padding:6px 14px; border-radius:20px;
  background:rgba(255,255,255,0.06); font-size:13px; font-weight:500;
  color:var(--text-primary);
}
.meta-icon { font-size:15px }
.path-progress { display:flex; align-items:center; gap:10px }
.progress-track {
  width:140px; height:6px; border-radius:3px;
  background:rgba(255,255,255,0.1); overflow:hidden;
}
.progress-fill {
  height:100%; border-radius:3px;
  background:linear-gradient(90deg, var(--primary), var(--accent));
  transition: width 0.4s ease;
}
.progress-text { font-size:12px; color:var(--text-secondary); white-space:nowrap }

/* KG layout with side panel */
.kg-layout { display:flex; gap:16px; position:relative }
.kg-canvas-wrap { flex:1; min-width:0 }
.kg-canvas {
  width:100%; height:560px;
  border-radius:16px; overflow:hidden;
  background:radial-gradient(ellipse at center, rgba(15,23,42,0.95), #0f172a);
  border:1px solid rgba(99,102,241,0.1);
}

/* Node detail panel */
.node-detail {
  width:260px; flex-shrink:0;
  padding:20px; border-radius:16px;
  background:rgba(30,41,59,0.9); backdrop-filter:blur(16px);
  border:1px solid var(--border);
  animation: slideIn 0.3s ease;
}
@keyframes slideIn { from { opacity:0; transform:translateX(20px) } to { opacity:1; transform:translateX(0) } }
.detail-close {
  position:absolute; top:12px; right:12px;
  width:28px; height:28px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  cursor:pointer; font-size:14px; color:var(--text-secondary);
  background:rgba(255,255,255,0.05); transition:all 0.2s;
}
.detail-close:hover { background:rgba(239,68,68,0.3); color:white }
.detail-type-badge {
  display:inline-flex; padding:4px 12px; border-radius:12px;
  font-size:12px; font-weight:600; margin-bottom:12px;
}
.detail-type-badge.paper { background:rgba(245,158,11,0.15); color:#fbbf24 }
.detail-type-badge.keyword { background:rgba(99,102,241,0.15); color:#a5b4fc }
.detail-name { font-size:16px; font-weight:600; margin-bottom:16px; line-height:1.4 }
.detail-mastery { display:flex; align-items:center; gap:8px; margin-bottom:14px }
.detail-mastery span:first-child { font-size:12px; color:var(--text-secondary); white-space:nowrap }
.mastery-bar-wrap {
  flex:1; height:8px; border-radius:4px;
  background:rgba(255,255,255,0.08); overflow:hidden;
}
.mastery-bar-fill { height:100%; border-radius:4px; transition:width 0.5s ease }
.mastery-pct { font-size:13px; font-weight:600; min-width:36px; text-align:right }
.detail-row {
  display:flex; justify-content:space-between; align-items:center;
  padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04);
  font-size:13px;
}
.detail-label { color:var(--text-secondary) }
.detail-id { font-family:monospace; font-size:11px; color:var(--text-secondary); word-break:break-all }

@media (max-width:1200px) {
  .charts-grid { grid-template-columns:1fr }
  .stats-row { grid-template-columns:repeat(2,1fr) }
  .main-content { margin-left:0; padding:20px }
  .sidebar { transform: translateX(-100%) }
  .kg-layout { flex-direction:column }
  .node-detail { width:100% }
  .kg-controls { align-items:flex-start }
}
@media (max-width:768px) {
  .stats-row { grid-template-columns:1fr }
  .path-info-bar { flex-direction:column; gap:12px }
}
</style>