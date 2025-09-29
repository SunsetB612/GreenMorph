# GreenMorph 项目结构

## 📁 目录结构

```
GreenMorph/
├── app/                          # 主应用目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── database.py               # 数据库连接
│   └── core/                     # 核心功能模块
│       ├── auth/                 # 认证授权模块
│       │   ├── __init__.py
│       │   └── router.py
│       ├── user/                 # 用户管理模块
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── models.py
│       ├── redesign/             # 改造项目模块
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── models.py
│       ├── community/            # 社区模块
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── models.py
│       └── gamification/         # 激励系统模块
│           ├── __init__.py
│           ├── router.py
│           └── models.py
├── shared/                       # 共享模块
│   ├── __init__.py
│   ├── database/                 # 数据库相关
│   ├── utils/                    # 工具函数
│   └── exceptions/               # 异常处理
├── ai_modules/                   # AI功能模块 (现有)
│   ├── image_analyzer.py
│   ├── multimodal_api.py
│   ├── image_generator.py
│   └── step_visualizer.py
├── app/static/                   # 静态文件
│   ├── input/                    # 用户上传文件
│   │   ├── avatars/              # 用户头像
│   │   ├── redesign_projects/    # 改造项目原始图片
│   │   └── posts/                # 帖子图片
│   └── output/                   # AI生成文件
│       ├── redesign_projects/    # 改造效果图
│       └── steps/                # 改造步骤图
├── tests/                        # 测试文件
├── frontend/                     # 前端项目 (待创建)
├── requirements.txt              # 依赖包
├── database_design.md            # 数据库设计
└── PROJECT_STRUCTURE.md          # 项目结构说明
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并填入配置：
```bash
cp .env.example .env
```

### 3. 启动服务
```bash
python -m app.main
```

### 4. 访问API文档
打开浏览器访问：http://localhost:8000/docs

## 📊 模块说明

### 核心模块
- **auth** - 用户认证、JWT令牌管理
- **user** - 用户资料管理、头像上传
- **redesign** - 改造项目CRUD、AI分析
- **community** - 帖子、评论、点赞功能
- **gamification** - 成就系统、积分管理

### 共享模块
- **database** - 数据库连接、会话管理
- **utils** - 通用工具函数
- **exceptions** - 异常处理

### AI模块
- **image_analyzer** - 图片分析
- **multimodal_api** - 多模态API调用
- **image_generator** - 图像生成
- **step_visualizer** - 步骤可视化

## 🔧 开发说明

### 数据库模型
所有数据模型都定义在各自模块的 `models.py` 文件中，使用SQLAlchemy ORM。

### API路由
每个模块都有独立的 `router.py` 文件，包含该模块的所有API端点。

### 配置管理
所有配置都在 `app/config.py` 中统一管理，支持环境变量覆盖。

### 文件存储
- `input/` - 存储用户上传的原始文件
- `output/` - 存储AI生成的文件
- 按功能模块分类存储，便于管理

## 🎯 下一步开发

1. **实现数据库模型** - 完善各模块的SQLAlchemy模型
2. **实现API逻辑** - 完善各路由的具体实现
3. **添加认证中间件** - 实现JWT认证
4. **创建前端项目** - 使用Vue.js 3 + TypeScript
5. **集成AI功能** - 连接现有的AI模块
