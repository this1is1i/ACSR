<template>
  <div class="app-shell" :class="{ 'app-shell--admin': admin }">
    <aside v-if="$slots.sidebar" class="app-shell__sidebar">
      <slot name="sidebar" />
    </aside>
    <main class="app-shell__main">
      <slot />
    </main>
  </div>
</template>

<script setup>
defineProps({
  admin: {
    type: Boolean,
    default: false,
  },
})
</script>
