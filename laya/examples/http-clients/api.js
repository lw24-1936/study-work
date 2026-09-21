// Vue 2（CLI5 + router3 + Vuex3）项目里的调用方式：axios 封装成一个 api 模块。
// 本文件依赖 axios，没有在本机跑过（本机没有对应的 Vue 工程），仅作为接入示例；
// 同目录的 client.js 是用 Node 内置 fetch 写的可运行版本，本机实测通过。

import axios from 'axios'

const http = axios.create({
  baseURL: process.env.VUE_APP_LAYA_URL || 'http://192.168.1.167:8077',
  timeout: 60000, // 服务端首次请求可能慢一个数量级，别用默认的 0（不超时）或 5 秒
  headers: { 'Content-Type': 'application/json' },
})

// key 放在 .env.local（VUE_APP_* 前缀才会被 CLI 注入），不要写进代码提交
http.interceptors.request.use((config) => {
  const key = process.env.VUE_APP_LAYA_KEY
  if (key) config.headers['X-API-Key'] = key
  return config
})

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const status = err.response && err.response.status
    if (status === 401) {
      return Promise.reject(new Error('Laya 服务鉴权失败：X-API-Key 不对'))
    }
    if (status === 503) {
      return Promise.reject(new Error('Laya 服务还在加载模型，稍后重试'))
    }
    return Promise.reject(err)
  }
)

/** 单条分诊：state 直接给文本，服务端用默认问题集 */
export function decide(text, model) {
  const payload = { state: { message: text } }
  if (model) payload.model = model
  return http.post('/decide', payload)
}

/** 自定义问题集：schema 由调用方决定（type 只能是 choice / score / noul） */
export function decideWith(text, questions, model) {
  const payload = { state: { message: text }, questions }
  if (model) payload.model = model
  return http.post('/decide', payload)
}

export function health() {
  return http.get('/health')
}
