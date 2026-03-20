import router from '@/router'
import { message } from 'ant-design-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'

export const request = axios.create({
  baseURL: import.meta.env.BASE_URL, //基础路径
  timeout: 10000, //发请求超时时间为5s
})

//给request实例添加请求拦截器
request.interceptors.request.use(
  (config) => {
    config.headers['Access-Control-Allow-Origin'] = '*'
    // 如果需要携带 token，在这里添加
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

//配置响应拦截器
request.interceptors.response.use(
  //成功响应：返回服务端的数据
  (response) => {
    console.log(response.data)
    return response.data
  },
  //失败响应：会返回错误对象，用来处理http网络错误
  (error) => {
    if (error.code === 'ECONNABORTED') {
      const timeoutError = new Error('请求超时，请稍后重试')
      ElMessage({
        showClose: true,
        type: 'error',
        message: timeoutError.message,
      })
      return Promise.reject(timeoutError)
    }

    if (error.response) {
      console.log('axios:' + error.response.status)
      const detail = error.response.data?.message || error.response.data?.detail || '未知错误'
      const customError = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      customError.status = error.response.status
      let message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      switch (error.response.status) {
        case 401:
          // Token 过期，跳转登录
          localStorage.removeItem('token')
          router.replace({
            path: '/login',
            query: { redirect: router.currentRoute.fullPath }, // 重新登录后，返回之前的页面
          })
          break
        case 403:
          // 返回403 清除token信息并跳转到登录页面
          localStorage.removeItem('token')
          router.replace({
            path: '/login',
            query: { redirect: router.currentRoute.fullPath }, // 重新登录后，返回之前的页面
          })
          break
        case 404:
          message = '请求资源不存在'
          break
      }
      // 提示错误信息
      ElMessage({
        showClose: true,
        type: 'error',
        message,
      })
      return Promise.reject(customError)
    } else {
      return Promise.reject(new Error('网络错误或请求未发送'))
    }
  },
)
