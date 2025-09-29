# GreenMorph 前端项目

GreenMorph 是一个基于AI技术的旧物回收设计智能助手平台的前端应用。

## 技术栈

- **React 19** - 现代化的用户界面库
- **TypeScript** - 类型安全的JavaScript超集
- **Vite** - 快速的构建工具
- **Ant Design** - 企业级UI设计语言
- **React Router** - 声明式路由管理

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 可复用组件
│   │   └── Layout.tsx     # 主布局组件
│   ├── pages/             # 页面组件
│   │   ├── Home.tsx       # 首页
│   │   ├── AIAssistant.tsx # AI助手页面
│   │   ├── Community.tsx  # 社区页面
│   │   ├── Profile.tsx    # 个人中心
│   │   └── About.tsx      # 关于我们
│   ├── styles/            # 样式文件
│   │   └── global.css     # 全局样式
│   ├── App.tsx            # 主应用组件
│   ├── main.tsx          # 应用入口
│   └── index.css          # 基础样式
├── package.json           # 项目配置
└── README.md             # 项目说明
```

## 功能特性

### 🏠 首页
- 平台概览和快速入口
- 功能特色介绍
- 响应式设计

### 🤖 AI助手
- 智能对话界面
- 图片上传功能
- 快速开始按钮
- 实时消息展示

### 👥 社区
- 帖子展示和搜索
- 用户互动（点赞、评论、分享）
- 热门话题标签
- 推荐用户

### 👤 个人中心
- 用户信息展示
- 统计数据可视化
- 成就系统
- 作品管理

### ℹ️ 关于我们
- 平台介绍
- 团队信息
- 发展历程
- 联系方式

## 开发指南

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173 查看应用

### 构建生产版本

```bash
npm run build
```

### 代码检查

```bash
npm run lint
```

## 设计特色

### 🎨 现代化UI设计
- 基于Ant Design设计系统
- 响应式布局适配
- 优雅的动画效果
- 深色模式支持

### 📱 移动端优化
- 移动端优先设计
- 触摸友好的交互
- 自适应布局
- 性能优化

### ♿ 无障碍访问
- 语义化HTML结构
- 键盘导航支持
- 屏幕阅读器友好
- 高对比度支持

## 浏览器支持

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目链接: [https://github.com/your-username/GreenMorph](https://github.com/your-username/GreenMorph)
- 问题反馈: [Issues](https://github.com/your-username/GreenMorph/issues)
- 邮箱: contact@greenmorph.com