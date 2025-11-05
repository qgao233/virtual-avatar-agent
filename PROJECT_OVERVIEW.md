# Salotto Demo 项目总览

这是一个完整的全栈多模态 AI 应用,集成了计算机视觉、大语言模型和语音识别功能。

## 🎯 项目简介

Salotto Demo 是一个展示现代 AI 技术集成的演示项目,包含:

- 🎨 **前端**: Vue3 + TypeScript + Vite
- ⚡ **后端**: Python + FastAPI
- 👁️ **计算机视觉**: YOLOv8 人脸检测 + dlib 人脸识别
- 🤖 **大语言模型**: 阿里云通义千问
- 🎤 **语音识别**: 实时语音转文字

## 📁 项目结构

```
demo/
├── front_end/              # 前端项目 (Vue3 + TypeScript + Vite)
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── App.vue        # 根组件
│   │   └── main.ts        # 入口文件
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── back_end/               # 后端项目 (Python + FastAPI)
│   ├── main.py            # FastAPI 应用入口
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   ├── utils.py           # 工具函数
│   │
│   ├── routers/           # API 路由
│   │   ├── cv_router.py   # 计算机视觉 API
│   │   ├── llm_router.py  # 大语言模型 API
│   │   └── sr_router.py   # 语音识别 API
│   │
│   ├── cv/                # 计算机视觉模块
│   │   ├── yolo/         # YOLO 人脸检测
│   │   └── fr/           # 人脸识别
│   │
│   ├── llm/               # 大语言模型模块
│   │   ├── assistant.py
│   │   └── multi_agent_fw/
│   │
│   ├── sr/                # 语音识别模块
│   │   └── asr_realtime.py
│   │
│   ├── requirements.txt
│   └── README.md
│
└── PROJECT_OVERVIEW.md     # 本文件
```

## 🚀 快速开始

### 前端启动

```bash
# 进入前端目录
cd front_end

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问: http://localhost:5173
```

### 后端启动

```bash
# 进入后端目录
cd back_end

# 安装依赖
pip install -r requirements.txt

# 启动服务器
python start.py --reload

# 访问 API 文档: http://localhost:8000/docs
```

## 📚 详细文档

### 前端文档
- [前端 README](front_end/README.md) - 前端项目说明

### 后端文档
- [后端 README](back_end/README.md) - 后端项目详细说明
- [快速开始指南](back_end/QUICKSTART.md) - 快速上手教程
- [架构文档](back_end/ARCHITECTURE.md) - 系统架构设计

## 🎨 技术栈

### 前端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5+ | 渐进式 JavaScript 框架 |
| TypeScript | 5.9+ | JavaScript 超集 |
| Vite | 7.1+ | 下一代前端构建工具 |

### 后端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.8+ | 编程语言 |
| FastAPI | 0.104+ | 现代高性能 Web 框架 |
| Uvicorn | 0.24+ | ASGI 服务器 |
| OpenCV | 4.8+ | 计算机视觉库 |
| YOLOv8 | 8.0+ | 目标检测模型 |
| dlib | 19.24+ | 人脸识别库 |
| Qwen | - | 阿里云通义千问 |

## 🌟 核心功能

### 1. 计算机视觉 (CV)

#### 人脸检测
- 基于 YOLOv8 的高精度人脸检测
- 支持多人脸同时检测
- 实时处理能力

#### 人脸识别
- 基于 dlib 的人脸特征提取
- 人脸特征向量比对
- 支持人脸库管理

**API 端点:**
- `POST /api/cv/detect-faces` - 人脸检测
- `POST /api/cv/recognize-faces` - 人脸识别
- `GET /api/cv/models/status` - 模型状态

### 2. 大语言模型 (LLM)

#### 对话助手
- 基于通义千问的智能对话
- 上下文理解
- 多轮对话支持

#### 多智能体系统
- 多个 AI 智能体协作
- 任务分解与执行
- 知识库集成

#### 知识库问答
- 向量化知识存储
- 语义搜索
- 相关性排序

**API 端点:**
- `POST /api/llm/chat` - 对话接口
- `POST /api/llm/multi-agent` - 多智能体查询
- `GET /api/llm/kb/search` - 知识库搜索
- `GET /api/llm/models/info` - 模型信息

### 3. 语音识别 (SR)

#### 文件识别
- 支持多种音频格式
- 批量处理能力
- 高准确率识别

#### 实时识别
- WebSocket 实时通信
- 流式音频处理
- 低延迟响应

**API 端点:**
- `POST /api/sr/recognize` - 音频文件识别
- `WebSocket /api/sr/realtime` - 实时语音识别
- `GET /api/sr/models/info` - 模型信息

## 🔄 系统架构

```
┌─────────────────────────────────────────────┐
│          前端 (Vue3 + TypeScript)            │
│            http://localhost:5173            │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WebSocket
                   ↓
┌─────────────────────────────────────────────┐
│         后端 (FastAPI + Python)              │
│            http://localhost:8000            │
├─────────────────────────────────────────────┤
│  CV 模块  │  LLM 模块  │  SR 模块           │
│  人脸检测 │  对话助手  │  语音识别          │
│  人脸识别 │  多智能体  │  实时识别          │
└─────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│              外部 AI 服务                    │
│  YOLOv8  │  通义千问  │  dlib              │
└─────────────────────────────────────────────┘
```

## 📋 开发指南

### 前端开发

1. **组件开发**: 在 `front_end/src/components/` 创建新组件
2. **路由配置**: 配置页面路由
3. **API 调用**: 使用 axios 或 fetch 调用后端 API
4. **状态管理**: 使用 Pinia 或 Vuex (可选)

### 后端开发

1. **添加 API**: 在 `routers/` 目录创建新路由
2. **数据模型**: 在 `models.py` 定义数据结构
3. **业务逻辑**: 在对应模块实现功能
4. **配置管理**: 在 `config.py` 添加配置项

## 🧪 测试

### 后端测试

```bash
# 运行 API 测试
cd back_end
python test_api.py
```

### 前端测试

```bash
# 运行单元测试 (需要配置)
cd front_end
npm run test
```

## 📦 部署

### 开发环境

- 前端: `npm run dev`
- 后端: `python start.py --reload`

### 生产环境

```bash
# 前端构建
cd front_end
npm run build

# 后端生产模式
cd back_end
python start.py --workers 4 --reload=False
```

## 🔐 环境配置

### 后端环境变量

创建 `back_end/.env` 文件:

```bash
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
DASHSCOPE_API_KEY=your_api_key_here
```

## 📊 API 文档

启动后端服务后访问:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ 开发工具推荐

- **IDE**: VS Code / PyCharm
- **API 测试**: Postman / Insomnia
- **版本控制**: Git
- **包管理**: npm / pip

## 📝 待办事项

### 前端
- [ ] 实现人脸检测界面
- [ ] 实现对话界面
- [ ] 实现语音识别界面
- [ ] 添加状态管理
- [ ] 优化 UI/UX

### 后端
- [ ] 完善 CV 模块集成
- [ ] 完善 LLM 功能
- [ ] 完善 SR 实时识别
- [ ] 添加用户认证
- [ ] 添加数据库支持
- [ ] 实现缓存机制
- [ ] 添加日志系统

### DevOps
- [ ] Docker 容器化
- [ ] CI/CD 配置
- [ ] 监控告警
- [ ] 性能优化

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目仅供学习和演示使用。

## 📧 联系方式

如有问题或建议,欢迎联系项目维护者。

## 🎉 开始使用

现在你可以开始探索这个项目了!

1. 先启动后端服务
2. 再启动前端服务
3. 访问 http://localhost:5173 开始使用
4. 查看 http://localhost:8000/docs 了解 API

祝你开发愉快! 🚀

