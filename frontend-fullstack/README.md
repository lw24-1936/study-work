# 前端完整知识库

整理日期：2026-08-13

本目录为前端完整知识体系的学习笔记，按篇章组织，每个 `.md` 文档对应一个知识主题。
目录结构由 `前端完整知识库总目录.md` 自动生成，当前为骨架状态，文档内容待逐步编写。

## 目录结构

```text
frontend-fullstack/
├── 01-计算机基础与开发环境/    # 计算机组成原理、操作系统、Linux、Git、IDE 与开发环境
├── 02-计算机网络/    # 网络基础、TCP、UDP、DNS、HTTP、HTTP Header 等 8 个主题
├── 03-Web 标准与浏览器基础/    # Web 标准、URL、MIME、字符编码
├── 04-HTML 完整知识体系/    # HTML 基础、语义化标签、文本、链接、列表、表格 等 11 个主题
├── 05-CSS 核心/    # CSS 基础、选择器、Box Model、Display、Position、Flex 等 8 个主题
├── 06-CSS 高级布局/    # 响应式布局、CSS 单位、函数、CSS 变量、CSS Grid 高级、Container Query
├── 07-CSS 视觉与动画/    # 背景、边框、文本、Transform、Transition、Animation 等 7 个主题
├── 08-CSS 工程化/    # CSS Architecture、CSS 预处理、CSS-in-JS、原子化 CSS、CSS 构建
├── 09-JavaScript 基础/    # ECMAScript、数据类型、原始类型、Number、String、Object
├── 10-JavaScript 语法与执行机制/    # 变量、运算符、控制流、函数、闭包
├── 11-JavaScript 高级机制/    # 执行上下文、this、原型、类、Symbol、Iterator 等 7 个主题
├── 12-JavaScript 异步编程/    # Callback、Promise、Async / Await、Event Loop、并发控制
├── 13-JavaScript 模块化/    # CommonJS、ES Modules、Module Resolution、Module Systems
├── 14-JavaScript 内置对象与 API/    # Object、Array、Map / Set、Date / Temporal、RegExp、JSON 等 7 个主题
├── 15-DOM/    # DOM 树、查询、修改、属性、DOM 遍历
├── 16-DOM 事件/    # Event、事件机制、Event Delegation、常见事件
├── 17-BOM 与 Web API/    # Window、Location、History、Storage、Clipboard、Notification 等 7 个主题
├── 18-Fetch-网络请求/    # Fetch、Axios、REST、GraphQL、WebSocket、SSE 等 7 个主题
├── 19-浏览器原理/    # 浏览器架构、渲染流程、JavaScript 执行、V8、Layout、Composite
├── 20-浏览器存储/    # Cookie、Web Storage、IndexedDB、Cache Storage
├── 21-浏览器缓存/    # HTTP Cache、缓存策略、前端缓存
├── 22-Service Worker-PWA/    # Service Worker、PWA、Cache Strategy
├── 23-Web Components/    # Custom Elements、Shadow DOM、Templates、CSS Shadow Parts
├── 24-TypeScript 基础/    # 类型系统、Interface、Type、类型推断
├── 25-TypeScript 高级/    # Generics、Utility Types、Advanced Types、类型工程
├── 26-npm-pnpm-Yarn 与包管理/    # package.json、Lockfile、SemVer、包发布
├── 27-前端工程化/    # 工程规范、代码质量、Git Hooks、环境管理
├── 28-Webpack/    # 核心概念、Loader、Plugin、优化
├── 29-Vite/    # Vite 原理、配置、Plugin、Vite 优化
├── 30-Rollup-esbuild-SWC-Babel/    # Rollup、esbuild、SWC、Babel、编译原理
├── 31-前端资源与构建优化/    # JavaScript、CSS、图片、字体
├── 32-Source Map 与调试/    # Source Map、Debug
├── 33-React 完整知识体系/    # React 基础、Hooks、React 生命周期思想、Fiber、Concurrent Rendering
├── 34-React 高级/    # Context、Suspense、Error Boundary、React Server Components、React Compiler
├── 35-Vue 完整知识体系/    # Vue 基础、Vue 3、Vue 响应式原理、Vue 编译、Vue Router
├── 36-状态管理/    # 状态分类、Redux、Zustand、MobX、Pinia、TanStack Query
├── 37-前端路由/    # SPA Routing、路由守卫、路由优化
├── 38-表单工程/    # 表单基础、表单状态、表单库、高级表单
├── 39-UI 组件库/    # 基础组件、数据展示、反馈、UI 框架
├── 40-Design System/    # Design Token、Theme、Component API、Design System 工程
├── 41-前端数据可视化/    # 图表基础、D3、ECharts、Three.js、WebGL
├── 42-Node.js/    # Node.js 基础、Node API、Stream、Node 性能
├── 43-Node.js Web 服务/    # Express、Koa、Fastify、NestJS
├── 44-BFF/    # BFF 原理、BFF 工程
├── 45-前端性能优化/    # 性能指标、网络性能、资源优化、JavaScript 优化、Rendering Optimization、React 性能 等 7 个主题
├── 46-Web Worker/    # Worker、Worker 应用
├── 47-WebAssembly/    # WASM 基础、语言生态、WASM 工程、WASM 应用
├── 48-前端安全/    # XSS、CSRF、CORS、Clickjacking、DOM Clobbering、Supply Chain
├── 49-Web 安全高级/    # CSP、Trusted Types、安全 Header、身份认证
├── 50-前端认证与权限/    # Authentication、Authorization、OAuth、SSO
├── 51-前端测试/    # 测试类型、Jest / Vitest、Testing Library、Playwright、Cypress、Mock
├── 52-可访问性测试/    # 
├── 53-前端错误处理/    # JavaScript Error、Promise Error、Resource Error、Framework Error、错误上报
├── 54-前端可观测性/    # Logs、Metrics、Tracing、RUM、工具
├── 55-前端监控系统/    # 错误监控、性能监控、业务监控、Source Map
├── 56-SSR-SSG-ISR/    # SSR、SSG、ISR、Hydration
├── 57-Next.js/    # Routing、Rendering、Server、Cache、Next.js 优化
├── 58-Nuxt/    # Nuxt、Nitro、Nuxt 优化
├── 59-微前端/    # 微前端思想、技术方案、微前端核心问题、Module Federation
├── 60-Monorepo/    # Monorepo、工具、Monorepo 工程
├── 61-前端组件库工程/    # 组件库、Storybook、组件发布、组件质量
├── 62-国际化 i18n/    # 国际化、翻译、RTL、国际化工程
├── 63-前端动画/    # CSS Animation、Web Animations API、requestAnimationFrame、动画库
├── 64-音视频/    # Media、播放、实时通信、WebRTC
├── 65-WebRTC 工程/    # 
├── 66-移动端 Web/    # 移动浏览器、移动适配、移动性能
├── 67-跨端开发/    # React Native、Flutter、UniApp、Taro、Electron、Tauri
├── 68-Electron/    # 架构、安全、工程
├── 69-WebView/    # 
├── 70-Serverless-Edge/    # Serverless、Edge Computing、平台
├── 71-前端 AI/    # AI SDK、浏览器 AI、AI UI、RAG 前端
├── 72-WebGPU/    # WebGPU、WGSL、WebGPU 应用
├── 73-前端数据层架构/    # 数据来源、数据状态、数据同步
├── 74-离线优先/    # Offline First、数据同步、CRDT
├── 75-前端实时系统/    # 实时通信、实时状态、实时协作
├── 76-前端架构模式/    # 架构、代码架构、设计模式
├── 77-前端领域驱动设计/    # DDD、前端领域拆分、Feature-Sliced Design
├── 78-前端 API 架构/    # REST API、GraphQL、RPC、API Contract
├── 79-前端工程性能/    # Build Performance、CI Performance、Bundle Analysis
├── 80-CI-CD/    # CI、CD、Deployment Strategy
├── 81-Docker/    # Docker、前端 Docker
├── 82-Kubernetes/    # 基础、前端部署
├── 83-Nginx/    # 静态服务、反向代理、缓存、SPA
├── 84-前端架构设计/    # 大型应用、高并发、高可用、可扩展
├── 85-大型前端应用工程治理/    # 代码治理、依赖治理、组件治理、技术债务
├── 86-前端国际大厂工程实践/    # Engineering Excellence、Development Process、Quality
├── 87-前端架构文档体系/    # 文档、架构图、文档工具
├── 88-前端算法与数据结构/    # 数据结构、算法、前端常用算法
├── 89-前端框架原理/    # Virtual DOM、Compiler、Reactive System、Scheduler
├── 90-React-Vue 源码学习/    # 
├── 91-前端编译原理/    # Lexer、Parser、Transform、Code Generation、前端应用
├── 92-浏览器 DevTools 实战/    # Elements、Console、Network、Performance、Memory、Application
├── 93-前端性能诊断方法论/    # 
├── 94-前端内存管理/    # GC、内存泄漏、内存诊断
├── 95-前端兼容性/    # Browser Compatibility、Compatibility、Polyfill
├── 96-浏览器 API 高级/    # Observer、Scheduling、Performance
├── 97-文件与大文件处理/    # 文件上传、大文件、下载
├── 98-前端加密与安全编程/    # Web Crypto API、算法、安全原则
├── 99-前端项目实战/    # 
├── 100-前端系统设计实战/    # 设计大型 SPA、设计企业级 Design System、设计微前端平台、设计高性能首页、设计实时协作系统、设计前端监控平台
├── 101-前端源码阅读路线/    # 
├── 102-前端论文与研究方向/    # 浏览器、编程语言、UI、AI + Frontend
└── 103-前端职业方向/    # 前端开发工程师、高级前端工程师、前端架构师、全栈工程师、AI Frontend Engineer
```

## 进度追踪表

| 篇章 | 状态 | 完成日期 |
|------|------|---------|
| 01-计算机基础与开发环境 | 待编写 | - |
| 02-计算机网络 | 待编写 | - |
| 03-Web 标准与浏览器基础 | 待编写 | - |
| 04-HTML 完整知识体系 | 待编写 | - |
| 05-CSS 核心 | 待编写 | - |
| 06-CSS 高级布局 | 待编写 | - |
| 07-CSS 视觉与动画 | 待编写 | - |
| 08-CSS 工程化 | 待编写 | - |
| 09-JavaScript 基础 | 待编写 | - |
| 10-JavaScript 语法与执行机制 | 待编写 | - |
| 11-JavaScript 高级机制 | 待编写 | - |
| 12-JavaScript 异步编程 | 待编写 | - |
| 13-JavaScript 模块化 | 待编写 | - |
| 14-JavaScript 内置对象与 API | 待编写 | - |
| 15-DOM | 待编写 | - |
| 16-DOM 事件 | 待编写 | - |
| 17-BOM 与 Web API | 待编写 | - |
| 18-Fetch-网络请求 | 待编写 | - |
| 19-浏览器原理 | 待编写 | - |
| 20-浏览器存储 | 待编写 | - |
| 21-浏览器缓存 | 待编写 | - |
| 22-Service Worker-PWA | 待编写 | - |
| 23-Web Components | 待编写 | - |
| 24-TypeScript 基础 | 待编写 | - |
| 25-TypeScript 高级 | 待编写 | - |
| 26-npm-pnpm-Yarn 与包管理 | 待编写 | - |
| 27-前端工程化 | 待编写 | - |
| 28-Webpack | 待编写 | - |
| 29-Vite | 待编写 | - |
| 30-Rollup-esbuild-SWC-Babel | 待编写 | - |
| 31-前端资源与构建优化 | 待编写 | - |
| 32-Source Map 与调试 | 待编写 | - |
| 33-React 完整知识体系 | 待编写 | - |
| 34-React 高级 | 待编写 | - |
| 35-Vue 完整知识体系 | 待编写 | - |
| 36-状态管理 | 待编写 | - |
| 37-前端路由 | 待编写 | - |
| 38-表单工程 | 待编写 | - |
| 39-UI 组件库 | 待编写 | - |
| 40-Design System | 待编写 | - |
| 41-前端数据可视化 | 待编写 | - |
| 42-Node.js | 待编写 | - |
| 43-Node.js Web 服务 | 待编写 | - |
| 44-BFF | 待编写 | - |
| 45-前端性能优化 | 待编写 | - |
| 46-Web Worker | 待编写 | - |
| 47-WebAssembly | 待编写 | - |
| 48-前端安全 | 待编写 | - |
| 49-Web 安全高级 | 待编写 | - |
| 50-前端认证与权限 | 待编写 | - |
| 51-前端测试 | 待编写 | - |
| 52-可访问性测试 | 待编写 | - |
| 53-前端错误处理 | 待编写 | - |
| 54-前端可观测性 | 待编写 | - |
| 55-前端监控系统 | 待编写 | - |
| 56-SSR-SSG-ISR | 待编写 | - |
| 57-Next.js | 待编写 | - |
| 58-Nuxt | 待编写 | - |
| 59-微前端 | 待编写 | - |
| 60-Monorepo | 待编写 | - |
| 61-前端组件库工程 | 待编写 | - |
| 62-国际化 i18n | 待编写 | - |
| 63-前端动画 | 待编写 | - |
| 64-音视频 | 待编写 | - |
| 65-WebRTC 工程 | 待编写 | - |
| 66-移动端 Web | 待编写 | - |
| 67-跨端开发 | 待编写 | - |
| 68-Electron | 待编写 | - |
| 69-WebView | 待编写 | - |
| 70-Serverless-Edge | 待编写 | - |
| 71-前端 AI | 待编写 | - |
| 72-WebGPU | 待编写 | - |
| 73-前端数据层架构 | 待编写 | - |
| 74-离线优先 | 待编写 | - |
| 75-前端实时系统 | 待编写 | - |
| 76-前端架构模式 | 待编写 | - |
| 77-前端领域驱动设计 | 待编写 | - |
| 78-前端 API 架构 | 待编写 | - |
| 79-前端工程性能 | 待编写 | - |
| 80-CI-CD | 待编写 | - |
| 81-Docker | 待编写 | - |
| 82-Kubernetes | 待编写 | - |
| 83-Nginx | 待编写 | - |
| 84-前端架构设计 | 待编写 | - |
| 85-大型前端应用工程治理 | 待编写 | - |
| 86-前端国际大厂工程实践 | 待编写 | - |
| 87-前端架构文档体系 | 待编写 | - |
| 88-前端算法与数据结构 | 待编写 | - |
| 89-前端框架原理 | 待编写 | - |
| 90-React-Vue 源码学习 | 待编写 | - |
| 91-前端编译原理 | 待编写 | - |
| 92-浏览器 DevTools 实战 | 待编写 | - |
| 93-前端性能诊断方法论 | 待编写 | - |
| 94-前端内存管理 | 待编写 | - |
| 95-前端兼容性 | 待编写 | - |
| 96-浏览器 API 高级 | 待编写 | - |
| 97-文件与大文件处理 | 待编写 | - |
| 98-前端加密与安全编程 | 待编写 | - |
| 99-前端项目实战 | 待编写 | - |
| 100-前端系统设计实战 | 待编写 | - |
| 101-前端源码阅读路线 | 待编写 | - |
| 102-前端论文与研究方向 | 待编写 | - |
| 103-前端职业方向 | 待编写 | - |
