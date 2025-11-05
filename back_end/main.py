"""
FastAPI 主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from routers import cv_router, llm_router, sr_router
from cv.cv import get_cv_system, ensure_cv_system_initialized


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 应用启动中...")
    print(f"📝 环境: {settings.ENVIRONMENT}")
    print(f"🔗 API 文档: http://{settings.HOST}:{settings.PORT}/docs")
    
    # 初始化 CV 系统
    print("\n" + "=" * 60)
    print("初始化 CV 系统...")
    print("=" * 60)
    try:
        cv_system = ensure_cv_system_initialized()
        print("✓ CV 系统初始化成功")
        status = cv_system.get_status()
        print(f"✓ 已注册人脸: {status['registered_faces']} 个")
        if status['registered_names']:
            print(f"✓ 已注册人员: {', '.join(status['registered_names'])}")
    except Exception as e:
        print(f"✗ CV 系统初始化失败: {e}")
        print("⚠️  CV 相关功能将不可用")
    print("=" * 60 + "\n")
    
    yield
    
    # 关闭时执行
    print("👋 应用关闭中...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(cv_router.router, prefix="/api/cv", tags=["计算机视觉"])
app.include_router(llm_router.router, prefix="/api/llm", tags=["大语言模型"])
app.include_router(sr_router.router, prefix="/api/sr", tags=["语音识别"])


@app.get("/", tags=["根路由"])
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 Salotto Demo API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

