import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import qs from 'qs'
import bcrypt from 'bcryptjs'
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';


const pinia=createPinia()

// 注册持久化插件
pinia.use(piniaPluginPersistedstate)

import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import { Document, Menu as IconMenu, Location, Setting } from '@element-plus/icons-vue'

const app = createApp(App)
app.use(ElementPlus)
app.use(qs)  //全局注册，使用方法为:this.qs

app.use(pinia)

app.use(router)
app.use(bcrypt)

app.use(Antd);

app.mount('#app')
