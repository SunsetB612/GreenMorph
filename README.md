# GreenMorph - 旧物回收设计智能助手

基于AI的旧物改造设计平台，为旧物提供智能化的改造方案。

## 🚀 快速启动

### 1. 后端启动
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env_example.txt .env
# 编辑 .env 文件，填入API密钥

# 启动后端服务
python run.py
```
后端服务: http://localhost:8000

### 2. 前端启动
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```
前端应用: http://localhost:5173

## 📁 项目结构

```
GreenMorph/
├── frontend/                 # 前端项目 (React + TypeScript)
│   ├── src/
│   │   ├── components/       # 通用组件
│   │   ├── pages/           # 页面组件 (Home, Community, AIAssistant等)
│   │   ├── styles/          # 样式文件
│   │   └── assets/          # 静态资源
│   ├── public/              # 公共静态资源
│   └── package.json         # 前端依赖
├── app/                     # 后端应用 (FastAPI)
│   ├── core/                # 核心业务模块
│   │   ├── auth/            # 用户认证
│   │   ├── redesign/        # 旧物改造
│   │   ├── community/       # 社区功能
│   │   ├── user/            # 用户管理
│   │   └── gamification/    # 游戏化系统
│   ├── shared/              # 共享模块
│   ├── static/              # 静态文件存储
│   └── main.py              # 应用入口
├── ai_modules/              # AI功能模块
├── static/                  # 静态文件存储
│   ├── input/               # 用户上传文件
│   │   ├── avatars/         # 用户头像
│   │   ├── posts/           # 社区帖子图片
│   │   └── redesign_projects/ # 用户上传的旧物图片
│   └── output/              # 生成的文件
│       ├── redesign_projects/ # 生成的改造效果图
│       └── steps/           # 改造步骤图
├── requirements.txt         # Python依赖
└── run.py                   # 后端启动脚本
```

## 🛠️ 开发指南

### 前端开发
- **技术栈**: React 18 + TypeScript + Ant Design + Vite
- **开发目录**: `frontend/src/`
- **主要页面**: 
  - `pages/Home.tsx` - 首页
  - `pages/Redesign.tsx` - 旧物改造
  - `pages/Community.tsx` - 社区
  - `pages/AIAssistant.tsx` - AI助手
- **开发命令**: `npm run dev`

### 后端开发
- **技术栈**: FastAPI + SQLAlchemy + Pydantic
- **开发目录**: `app/`
- **主要模块**:
  - `api/` - API路由定义
  - `models/` - 数据模型
  - `services/` - 业务逻辑
- **开发命令**: `python run.py`

### 数据库
- **文件**: `greenmorph.db` (SQLite)
- **设计文档**: `database_design.md`
- **主要表**: users, projects, posts, comments

### API文档
- 开发环境: http://localhost:8000/docs
- 管理界面: http://localhost:8000/redoc

## 📡 API接口

### 🔐 认证模块 (`/api/auth`)
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `POST /api/auth/refresh` - 刷新令牌

### 👤 用户管理 (`/api/users`)
- `GET /api/users/profile` - 获取用户资料
- `PUT /api/users/profile` - 更新用户资料
- `POST /api/users/avatar` - 上传头像
- `GET /api/users/{user_id}` - 获取其他用户信息

### 🔧 改造项目 (`/api/redesign`)
- `GET /api/redesign/projects` - 获取用户项目列表
- `POST /api/redesign/projects` - 创建改造项目
- `GET /api/redesign/projects/{project_id}` - 获取单个项目详情
- `PUT /api/redesign/projects/{project_id}` - 更新项目信息
- `DELETE /api/redesign/projects/{project_id}` - 删除项目
- `POST /api/redesign/projects/{project_id}/analyze` - AI分析旧物
- `POST /api/redesign/projects/{project_id}/generate` - 生成改造方案
- `POST /api/redesign/upload` - 上传项目图片

### 👥 社区功能 (`/api/community`)
- `GET /api/community/posts` - 获取帖子列表（支持分页、搜索、筛选）
- `POST /api/community/posts` - 创建帖子
- `GET /api/community/posts/{post_id}` - 获取单个帖子详情
- `PUT /api/community/posts/{post_id}` - 更新帖子
- `DELETE /api/community/posts/{post_id}` - 删除帖子
- `GET /api/community/posts/{post_id}/comments` - 获取帖子评论
- `POST /api/community/posts/{post_id}/comments` - 发表评论
- `DELETE /api/community/comments/{comment_id}` - 删除评论
- `POST /api/community/posts/{post_id}/like` - 点赞帖子
- `DELETE /api/community/posts/{post_id}/like` - 取消点赞
- `POST /api/community/comments/{comment_id}/like` - 点赞评论
- `DELETE /api/community/comments/{comment_id}/like` - 取消点赞评论

### 🏆 激励系统 (`/api/gamification`)
- `GET /api/gamification/achievements` - 获取所有成就列表
- `GET /api/gamification/achievements/user/{user_id}` - 获取用户成就
- `POST /api/gamification/achievements/check` - 检查并发放成就
- `GET /api/gamification/leaderboard` - 获取积分排行榜
- `GET /api/gamification/points/{user_id}` - 获取用户积分详情

### 📁 文件管理
- `POST /api/upload/avatar` - 上传用户头像
- `POST /api/upload/post` - 上传帖子图片
- `POST /api/upload/project` - 上传项目图片
- `GET /api/files/{filename}` - 获取文件（带访问控制）

