import router from '@/router'
import { message } from 'ant-design-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'

export const request = axios.create({
  baseURL: import.meta.env.BASE_URL, //基础路径
  timeout: 5000, //发请求超时时间为5s
})

//给request实例添加请求拦截器
request.interceptors.request.use(
  (config) => {
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
    if (error.response) {
      console.log('axios:' + error.response.status)
      let message = ''
      switch (error.response.status) {
        case 403:
          // 返回403 清除token信息并跳转到登录页面
          localStorage.removeItem('token')
          router.replace({
            path: '/login',
            query: { redirect: router.currentRoute.fullPath }, // 重新登录后，返回之前的页面
          })
          message = '未登录，返回登陆界面'
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
    }
    // // 存储网络错误信息
    // let message = ''
    // // 根据http状态码判断网络错误
    // const status = error.response.status
    // switch (status) {
    //   case 401:
    //     message = '登录已过期，请重新登录'
    //     break
    //   case 403:
    //     message = '没有权限，请联系管理员'
    //     break
    //   case 404:
    //     message = '请求资源不存在'
    //     break
    //   case 500:
    //     message = '服务器内部错误'
    //     break
    //   default:
    //     // eslint-disable-next-line @typescript-eslint/no-unused-vars
    //     message = '网络错误'
    //     break
    // }
    // // 提示错误信息
    // ElMessage({
    //   type: 'error',
    //   message,
    // })
    // 返回一个失败的promise对象
    return Promise.reject(error)
  },
)
