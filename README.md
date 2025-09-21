# GreenMorph - AI驱动的旧物再设计平台

## 项目简介

GreenMorph是一个基于多模态大模型的旧物再设计平台，帮助用户将废旧物品改造为具有新用途的环保产品。平台通过AI分析旧物特征，结合用户需求生成改造方案和效果图。

## 核心功能

### 1. 图片特征分析
- 识别旧物的主要结构和特征
- 分析材料类型、颜色、状态
- 评估改造潜力

### 2. 多模态大模型调用
- 支持OpenAI GPT-4V、Anthropic Claude、Replicate等
- 结合图片和文本生成改造方案
- 智能生成改造说明书

### 3. 结构控制图像生成
- 使用ControlNet保持原物结构特征
- 生成环保自然风格的效果图
- 突出每步改造的关键变化

### 4. 改造步骤可视化
- 生成详细的步骤示意图
- 提供材料工具清单
- 包含安全注意事项

## 技术架构

### 后端框架
- **FastAPI**: 高性能异步Web框架
- **Pydantic**: 数据验证和序列化
- **Uvicorn**: ASGI服务器

### AI模型
- **多模态大模型**: OpenAI GPT-4V, Anthropic Claude
- **图像生成**: Stable Diffusion + ControlNet
- **图像处理**: OpenCV, Pillow

### 核心模块
```
├── main.py                 # FastAPI主应用
├── config.py              # 配置管理
├── models.py              # 数据模型
├── redesign_service.py    # 主服务类
├── image_analyzer.py      # 图片分析
├── multimodal_api.py      # 多模态API调用
├── image_generator.py     # 图像生成
└── step_visualizer.py     # 步骤可视化
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `env_example.txt` 为 `.env` 并填入配置：

```bash
cp env_example.txt .env
```

编辑 `.env` 文件，填入你的API密钥：
- OpenAI API Key (用于GPT-4V)
- Anthropic API Key (用于Claude)
- Replicate API Token (可选)

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 4. 查看API文档

访问 `http://localhost:8000/docs` 查看交互式API文档

## API接口

### 图片分析
```http
POST /analyze
Content-Type: application/json

{
  "image_url": "https://example.com/old-item.jpg",
  "user_requirements": "将旧木椅改造成现代简约风格的书桌"
}
```

### 旧物再设计
```http
POST /redesign
Content-Type: application/json

{
  "image_url": "https://example.com/old-item.jpg",
  "user_requirements": "将旧木椅改造成现代简约风格的书桌",
  "target_style": "modern",
  "target_materials": ["wood"],
  "budget_range": "100-300元",
  "skill_level": "intermediate"
}
```

### 文件上传
```http
POST /redesign/upload
Content-Type: multipart/form-data

file: [图片文件]
user_requirements: "改造需求描述"
target_style: "modern"
```

## 支持的风格和材料

### 改造风格
- modern (现代)
- vintage (复古)
- minimalist (极简)
- industrial (工业)
- scandinavian (北欧)
- bohemian (波西米亚)
- rustic (乡村)
- contemporary (当代)

### 材料类型
- wood (木材)
- metal (金属)
- fabric (布料)
- glass (玻璃)
- ceramic (陶瓷)
- plastic (塑料)
- leather (皮革)
- paper (纸张)

## 环保设计理念

- 保持环保、自然的视觉风格
- 优先使用可持续材料
- 减少浪费，最大化利用原有材料
- 确保改造过程环保
- 提供可持续性评分

## 开发说明

### 项目结构
```
GreenMorph/
├── main.py                 # FastAPI应用入口
├── config.py              # 配置管理
├── models.py              # Pydantic数据模型
├── redesign_service.py    # 核心业务逻辑
├── image_analyzer.py      # 图片分析模块
├── multimodal_api.py      # 多模态API调用
├── image_generator.py     # 图像生成模块
├── step_visualizer.py     # 步骤可视化模块
├── requirements.txt       # 依赖包列表
├── env_example.txt        # 环境变量示例
└── README.md             # 项目说明
```

### 核心流程
1. **图片上传** → 验证格式和大小
2. **特征分析** → 使用多模态模型分析旧物
3. **方案生成** → 结合用户需求生成改造计划
4. **图像生成** → 使用ControlNet生成效果图
5. **步骤可视化** → 生成详细的改造步骤图
6. **结果返回** → 返回完整的改造方案

## 部署建议

### 生产环境
- 使用Gunicorn + Uvicorn workers
- 配置Nginx反向代理
- 设置适当的资源限制
- 配置日志和监控

### 性能优化
- 启用GPU加速（如果可用）
- 使用模型缓存
- 实现请求队列
- 定期清理临时文件

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题，请通过GitHub Issues联系。
