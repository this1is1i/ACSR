<template>
  <div ref="containerRef" class="graph-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
})

const containerRef = ref()
let scene, camera, renderer, animationId

function getMasteryColor(mastery) {
  if (mastery >= 0.7) return 0x4fc3f7  // 高掌握度 - 亮蓝
  if (mastery >= 0.4) return 0x26c6da  // 中掌握度 - 青色
  return 0x546e7a                       // 低掌握度 - 灰色
}

function initScene() {
  const container = containerRef.value
  if (!container) return

  // Scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0d1117)

  // Camera
  camera = new THREE.PerspectiveCamera(
    60,
    container.clientWidth / container.clientHeight,
    0.1,
    1000
  )
  camera.position.z = 15

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  container.appendChild(renderer.domElement)

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)
  const pointLight = new THREE.PointLight(0xffffff, 0.8)
  pointLight.position.set(10, 10, 10)
  scene.add(pointLight)

  renderGraph()
  animate()
}

function renderGraph() {
  if (!props.nodes.length) return

  // 节点位置映射
  const positions = {}
  const radius = 8
  props.nodes.forEach((node, i) => {
    const angle = (i / props.nodes.length) * Math.PI * 2
    positions[node.id] = {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
      z: (Math.random() - 0.5) * 3,
    }
  })

  // 渲染边
  props.edges.forEach(edge => {
    const start = positions[edge.source]
    const end = positions[edge.target]
    if (!start || !end) return

    const points = [
      new THREE.Vector3(start.x, start.y, start.z),
      new THREE.Vector3(end.x, end.y, end.z),
    ]
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({ color: 0x30363d })
    const line = new THREE.Line(geometry, material)
    scene.add(line)
  })

  // 渲染节点
  props.nodes.forEach(node => {
    const pos = positions[node.id]
    const color = getMasteryColor(node.mastery)
    const geometry = new THREE.SphereGeometry(0.5, 32, 32)
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: node.mastery * 0.3,
    })
    const sphere = new THREE.Mesh(geometry, material)
    sphere.position.set(pos.x, pos.y, pos.z)
    scene.add(sphere)

    // 文字标签（简化版，使用 Sprite）
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = 256
    canvas.height = 64
    ctx.fillStyle = '#e6edf3'
    ctx.font = '24px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(node.name, 128, 40)

    const texture = new THREE.CanvasTexture(canvas)
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture })
    const sprite = new THREE.Sprite(spriteMaterial)
    sprite.position.set(pos.x, pos.y + 1, pos.z)
    sprite.scale.set(2, 0.5, 1)
    scene.add(sprite)
  })
}

function animate() {
  animationId = requestAnimationFrame(animate)
  scene.rotation.y += 0.002
  renderer.render(scene, camera)
}

function handleResize() {
  if (!containerRef.value || !camera || !renderer) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

watch(() => [props.nodes, props.edges], () => {
  if (scene) {
    // 清空场景重新渲染
    while (scene.children.length > 0) {
      scene.remove(scene.children[0])
    }
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)
    const pointLight = new THREE.PointLight(0xffffff, 0.8)
    pointLight.position.set(10, 10, 10)
    scene.add(pointLight)
    renderGraph()
  }
}, { deep: true })

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) renderer.dispose()
})
</script>

<style scoped>
.graph-container { width: 100%; height: 100%; }
</style>
