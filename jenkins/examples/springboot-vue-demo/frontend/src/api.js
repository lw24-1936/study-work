import axios from 'axios'

// 生产环境由 nginx 把 /api 反代到后端，所以这里用相对路径就够了；
// 需要指向别的域名时用 VITE_API_BASE 覆盖。
const baseURL = import.meta.env.VITE_API_BASE || '/api'

const http = axios.create({ baseURL, timeout: 5000 })

export async function listTodos() {
  const { data } = await http.get('/todos')
  return data
}

export async function createTodo(title) {
  const { data } = await http.post('/todos', { title })
  return data
}

export async function toggleTodo(id) {
  const { data } = await http.put(`/todos/${id}`)
  return data
}

export async function deleteTodo(id) {
  await http.delete(`/todos/${id}`)
}

export async function backendHealth() {
  const { data } = await http.get('/todos/health')
  return data
}
