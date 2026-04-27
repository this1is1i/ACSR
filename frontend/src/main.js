import './style.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

const initialTheme = localStorage.getItem('theme') || 'dark'
document.documentElement.setAttribute('data-theme', initialTheme)
document.documentElement.classList.toggle('dark', initialTheme !== 'light')

app.mount('#app')
