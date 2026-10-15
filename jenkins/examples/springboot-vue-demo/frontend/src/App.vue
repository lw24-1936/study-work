<script setup>
import { onMounted, ref } from 'vue'
import { backendHealth, createTodo, deleteTodo, listTodos, toggleTodo } from './api'

const todos = ref([])
const title = ref('')
const health = ref(null)
const error = ref('')

async function refresh() {
  try {
    todos.value = await listTodos()
    health.value = await backendHealth()
    error.value = ''
  } catch (e) {
    error.value = `后端不可用：${e.message}`
  }
}

async function add() {
  if (!title.value.trim()) return
  await createTodo(title.value.trim())
  title.value = ''
  await refresh()
}

async function toggle(id) {
  await toggleTodo(id)
  await refresh()
}

async function remove(id) {
  await deleteTodo(id)
  await refresh()
}

onMounted(refresh)
</script>

<template>
  <main class="card">
    <h1>Jenkins CI/CD 实战</h1>
    <p class="sub">Vue 3 前端 + Spring Boot 后端，由 Jenkins 流水线构建并部署</p>

    <p v-if="health" class="health">
      后端状态：{{ health.status }}，当前待办 {{ health.size }} 条
    </p>
    <p v-if="error" class="error">{{ error }}</p>

    <form class="row" @submit.prevent="add">
      <input v-model="title" placeholder="新增一条待办" />
      <button type="submit">添加</button>
    </form>

    <ul>
      <li v-for="t in todos" :key="t.id">
        <label :class="{ done: t.done }">
          <input type="checkbox" :checked="t.done" @change="toggle(t.id)" />
          {{ t.title }}
        </label>
        <button class="ghost" @click="remove(t.id)">删除</button>
      </li>
    </ul>

    <p v-if="!todos.length" class="empty">还没有数据，添加一条试试</p>
  </main>
</template>

<style>
:root {
  color-scheme: light;
  --brand: #2f6f5e;
  --ink: #1f2933;
  --line: #d8dee6;
}
body {
  margin: 0;
  font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f7f8;
  color: var(--ink);
}
.card {
  max-width: 640px;
  margin: 48px auto;
  padding: 28px 32px 36px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
}
h1 { font-size: 22px; margin: 0 0 6px; }
.sub { color: #5b6b7c; font-size: 13px; margin: 0 0 20px; }
.health { font-size: 13px; color: var(--brand); }
.error { font-size: 13px; color: #b3261e; }
.row { display: flex; gap: 8px; margin: 16px 0 8px; }
input { flex: 1; padding: 8px 10px; border: 1px solid var(--line); border-radius: 6px; font-size: 14px; }
button {
  padding: 8px 14px; border: 0; border-radius: 6px;
  background: var(--brand); color: #fff; font-size: 14px; cursor: pointer;
}
button.ghost { background: transparent; color: #5b6b7c; border: 1px solid var(--line); }
ul { list-style: none; padding: 0; margin: 12px 0 0; }
li { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eef1f4; }
.done { text-decoration: line-through; color: #98a2b3; }
.empty { color: #98a2b3; font-size: 13px; margin-top: 16px; }
</style>
