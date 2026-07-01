# Puff Admin Web

基于 Vue 3、Vite、TypeScript、Element Plus 的后台管理系统前端骨架。

## 启动

```bash
npm install
npm run dev
```

开发服务器默认运行在 `http://localhost:5173`，`/api` 请求会代理到 `http://127.0.0.1:8000`。

## 常用命令

```bash
npm run dev        # 本地开发
npm run type-check # TypeScript 类型检查
npm run build      # 生产构建
npm run preview    # 预览生产构建
```

## 目录结构

```text
src/
├── api/          # 后端接口
├── components/   # 通用组件
├── layouts/      # 页面布局
├── router/       # 路由与守卫
├── stores/       # Pinia 状态
├── styles/       # 全局样式
├── types/        # TypeScript 类型
├── utils/        # Axios 等基础工具
└── views/        # 业务页面
```

登录页当前使用演示模式；FastAPI 登录接口完成后，在 `src/views/login/LoginView.vue` 接入 `src/api/auth.ts`，并启用 `src/router/index.ts` 中已预留的鉴权守卫即可。
