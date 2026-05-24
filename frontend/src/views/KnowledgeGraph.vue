<template>
  <div class="viz-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <div class="viz-surface-layout">
        <PathInsightRail
          :loading="surfaceLoading"
          :summary="pathSummary"
          :recommendations="recommendations"
          :active-node="insightNode"
        />

        <div class="viz-surface-layout__main">
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
                  <div class="mastery-bar-fill" :style="{width: (selectedNode.mastery * 100) + '%', background: selectedNode.color || '#3B82F6'}"></div>
                </div>
                <span class="mastery-pct">{{ (selectedNode.mastery * 100).toFixed(0) }}%</span>
              </div>
              <div class="detail-row" v-if="selectedNode.year"><span class="detail-label">年份</span><span>{{ selectedNode.year }}</span></div>
              <div class="detail-row"><span class="detail-label">深度层</span><span>{{ depthLabel(selectedNode.depth) }}</span></div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import PathInsightRail from '@/components/path/PathInsightRail.vue'
import * as THREE from 'three'
import { getPathSurfaceData } from '@/api/visualization'
import { buildLearningPathSummary } from '@/utils/path'

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
const visualizationData = ref({})
const recommendations = ref([])
const surfaceLoading = ref(false)

const pathSummary = computed(() => buildLearningPathSummary(visualizationData.value))
const insightNode = computed(() => {
  if (selectedNode.value) return selectedNode.value
  const activeId = currentRoute.value[currentStep.value]
  return pathSummary.value.steps.find((step) => String(step.id) === String(activeId)) || null
})

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

  // Prefer pathNodes/pathEdges (~20 nodes) for clean learning path view, fall back to full graph
  const pathN = data.pathNodes
  const hasPathNodes = Array.isArray(pathN) && pathN.length > 0
  const nodes = (hasPathNodes ? pathN : (data.nodes || [])).map(n => ({ ...n, _visited: false, _active: false }))
  const rawLinks = (hasPathNodes && data.pathEdges && data.pathEdges.length) ? data.pathEdges : (data.links || data.edges || [])
  const normLinks = rawLinks.map(l => ({
    ...l,
    source: (l.source && l.source.id) ? l.source.id : (l.source || l.src),
    target: (l.target && l.target.id) ? l.target.id : (l.target || l.dst),
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
      const hex = parseInt((node.color || '#3B82F6').slice(1), 16)
      const emissiveIntensity = 0.2 + (node.glowIntensity || 0) * 0.5

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
      selectedNode.value = { ...node }
      if (node.x !== undefined && node.y !== undefined && node.z !== undefined) {
        try {
          Graph3D.cameraPosition(
            { x: node.x, y: node.y + 40, z: node.z + 120 },
            { x: node.x, y: node.y, z: node.z },
            1000
          )
        } catch { /* camera move best-effort */ }
      }
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
  surfaceLoading.value = true
  try {
    const surface = await getPathSurfaceData()
    const data = surface.visualization || {}
    visualizationData.value = data
    recommendations.value = surface.recommendations || []

    // 3D knowledge graph & learning path
    if (data.knowledge) {
      await initKnowledgeGraph(data.knowledge)
    }
  } catch (e) {
    // console.error('Failed to load visualization data', e)
  } finally {
    surfaceLoading.value = false
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  stopRoute()
  if (Graph3D) { Graph3D._destructor && Graph3D._destructor() }
})
</script>

<style scoped>
.viz-root {
  min-height: 100vh;
  background: var(--bg-dark, #0f172a);
  color: var(--text-primary, #f8fafc);
}
.bg-animation {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
}

/* ── Layout ─────────────────────────────────────────────────── */
.viz-surface-layout { display: grid; gap: 24px; margin-bottom: 30px }
.viz-surface-layout__main { display: grid; gap: 24px; align-content: start }
.chart-card {
  background: var(--bg-card); backdrop-filter: blur(20px);
  border-radius: 24px; border: 1px solid var(--design-border);
  border-left: 3px solid transparent; padding: 30px; overflow: hidden;
}
.chart-card[data-area="knowledge"] { border-left-color: var(--color-area-knowledge) }
.chart-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 25px; flex-wrap: wrap; gap: 12px;
}
.chart-title { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 10px }
.chart-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.chart-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap }
.chart-btn {
  padding: 8px 16px; border-radius: 8px;
  border: 1px solid var(--design-border);
  background: var(--bg-hover); color: var(--color-text-secondary);
  cursor: pointer; transition: all 0.2s; font-size: 13px;
}
.chart-btn:hover:not(:disabled) { background: var(--primary); color: white }
.chart-btn:disabled { opacity: 0.4; cursor: not-allowed }
.fullwidth-chart { grid-column: 1 / -1 }

/* ── Fullscreen mode ────────────────────────────────────────── */
.fullscreen-btn {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(6, 182, 212, 0.3)) !important;
  border-color: rgba(99, 102, 241, 0.4) !important; color: #e2e8f0 !important;
  font-size: 13px; min-width: 90px;
}
.fullscreen-btn:hover {
  background: linear-gradient(135deg, #6366f1, #06b6d4) !important; color: white !important;
}
.kg-fullscreen {
  position: fixed !important; top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9999; margin: 0; border-radius: 0 !important;
  background: #0f172a !important; padding: 20px 24px;
  display: flex; flex-direction: column;
}
.kg-fullscreen .chart-header { flex-shrink: 0 }
.kg-fullscreen .path-info-bar { flex-shrink: 0 }
.kg-fullscreen .kg-layout { flex: 1; min-height: 0 }
.kg-fullscreen .kg-canvas-wrap { flex: 1; min-height: 0 }
.kg-fullscreen .kg-canvas { height: 100% !important }

/* ── KG controls ────────────────────────────────────────────── */
.kg-controls { display: flex; flex-direction: column; gap: 10px; align-items: flex-end }
.kg-buttons { display: flex; gap: 8px; align-items: center; flex-wrap: wrap }
.play-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  color: white !important; border-color: transparent !important; min-width: 80px;
}
.reset-btn:hover { background: #ef4444 !important; border-color: #ef4444 !important; color: white !important }
.speed-select {
  padding: 6px 12px; border-radius: 8px;
  border: 1px solid var(--design-border);
  background: var(--bg-card); color: var(--color-text-primary);
  font-size: 13px; cursor: pointer; outline: none;
}
.speed-select option { background: var(--color-bg-elevated); color: var(--color-text-primary) }

/* Mastery legend */
.mastery-legend { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--color-text-muted) }
.legend-bar { width: 120px; height: 8px; border-radius: 4px; background: linear-gradient(to right, #3B82F6, #F59E0B, #10B981) }
.legend-min { color: #3B82F6; font-size: 11px }
.legend-max { color: #10B981; font-size: 11px }

/* Path info bar */
.path-info-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px; margin-bottom: 16px;
  background: var(--bg-hover); border-radius: 14px;
  border: 1px solid var(--color-border-strong);
}
.path-meta { display: flex; gap: 16px; flex-wrap: wrap }
.meta-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  background: var(--bg-card); font-size: 13px; font-weight: 500;
  color: var(--color-text-primary);
}
.meta-icon { font-size: 15px }
.path-progress { display: flex; align-items: center; gap: 10px }
.progress-track { width: 140px; height: 6px; border-radius: 3px; background: var(--bg-hover); overflow: hidden }
.progress-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #6366f1, #06b6d4); transition: width 0.4s ease }
.progress-text { font-size: 12px; color: var(--color-text-muted); white-space: nowrap }

/* KG layout */
.kg-layout { display: flex; gap: 16px; position: relative }
.kg-canvas-wrap { flex: 1; min-width: 0 }
.kg-canvas {
  width: 100%; height: 560px; border-radius: 16px; overflow: hidden;
  background: radial-gradient(ellipse at center, rgba(15, 23, 42, 0.95), #0f172a);
  border: 1px solid rgba(99, 102, 241, 0.1);
}

/* Node detail panel */
.node-detail {
  position: relative;
  width: 260px; flex-shrink: 0; padding: 20px; border-radius: 16px;
  background: var(--bg-card); backdrop-filter: blur(16px);
  border: 1px solid var(--design-border);
  animation: slideIn 0.3s ease;
}
@keyframes slideIn { from { opacity: 0; transform: translateX(20px) } to { opacity: 1; transform: translateX(0) } }
.detail-close {
  position: absolute; top: 12px; right: 12px;
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 14px; color: var(--color-text-muted);
  background: var(--bg-hover); transition: all 0.2s;
}
.detail-close:hover { background: rgba(239, 68, 68, 0.3); color: white }
.detail-type-badge { display: inline-flex; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-bottom: 12px }
.detail-type-badge.paper { background: rgba(245, 158, 11, 0.15); color: #d97706 }
.detail-type-badge.keyword { background: rgba(99, 102, 241, 0.15); color: #6366f1 }
.detail-name { font-size: 16px; font-weight: 600; margin-bottom: 16px; line-height: 1.4 }
.detail-mastery { display: flex; align-items: center; gap: 8px; margin-bottom: 14px }
.detail-mastery span:first-child { font-size: 12px; color: var(--color-text-muted); white-space: nowrap }
.mastery-bar-wrap { flex: 1; height: 8px; border-radius: 4px; background: var(--bg-hover); overflow: hidden }
.mastery-bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease }
.mastery-pct { font-size: 13px; font-weight: 600; min-width: 36px; text-align: right }
.detail-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--color-border-subtle); font-size: 13px;
}
.detail-label { color: var(--color-text-muted) }

@media (max-width: 1200px) {
  .kg-layout { flex-direction: column }
  .node-detail { width: 100% }
  .kg-controls { align-items: flex-start }
}
@media (max-width: 768px) {
  .path-info-bar { flex-direction: column; gap: 12px }
}
</style>
