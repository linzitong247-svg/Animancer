/**
 * 应用入口文件
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import './style.css'

// Only import ElMessage styles (not the full Element Plus theme)
import 'element-plus/es/components/message/style/css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
