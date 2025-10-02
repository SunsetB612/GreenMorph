# GreenMorph - 旧物回收设计智能助手

基于AI的旧物改造设计平台，为旧物提供智能化的改造方案。

## 🚀 快速启动

### 1. 数据库准备
```bash
# 确保MySQL服务正在运行
# 安装依赖
pip install -r requirements.txt

# 初始化MySQL数据库
python init_mysql_db.py
```

### 2. 后端启动
```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥和MySQL配置

# 启动后端服务
python run.py
```
后端服务: http://localhost:8000

### 3. 前端启动
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
│   ├── users/               # 用户相关文件
│   │   └── {userid}/
│   │       ├── input/       # 改造项目输入图片
│   │       └── output/      # 改造项目输出图片
│   │           ├── result/  # 最终效果图
│   │           └── steps/   # 步骤图片
│   └── community/           # 社区公共文件
│       ├── posts/           # 帖子图片
│       │   └── {post_id}/   # 按帖子ID分组
│       └── comments/        # 评论图片
│           └── {comment_id}/ # 按评论ID分组
├── requirements.txt         # Python依赖
└── run.py                   # 后端启动脚本
```

## 🛠️ 开发指南

### 前端开发
- **技术栈**: React 18 + TypeScript + Ant Design + Vite
- **开发目录**: `frontend/src/`
- **主要页面**: 
  - `pages/Home.tsx` - 首页
  - `pages/Profile.tsx` - 个人中心
  - `pages/About.tsx` - 关于页面
  - `pages/Community.tsx` - 社区
  - `pages/AIAssistant.tsx` - AI助手
- **开发命令**: `npm run dev`

### 后端开发
- **技术栈**: FastAPI + SQLAlchemy + Pydantic
- **开发目录**: `app/`
- **主要模块**:
  - `core/` - 核心业务模块
    - `auth/` - 用户认证
    - `user/` - 用户管理
    - `community/` - 社区功能
    - `gamification/` - 激励系统
    - `redesign/` - 旧物改造
  - `shared/` - 共享工具和模型
  - `static/` - 静态文件存储
- **开发命令**: `python run.py`

### 数据库
- **类型**: MySQL 8.0+
- **设计文档**: `database_design.md`
- **主要表**: users, redesign_projects, posts, comments, community_images, likes, achievements
- **初始化**: 运行 `python init_mysql_db.py` 创建数据库和表
- **迁移**: 如果已有数据库，运行 `python migrate_database_structure.py` 更新结构

### API文档
- 开发环境: http://localhost:8000/docs
- 管理界面: http://localhost:8000/redoc
