"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "Salotto Demo API"
    DESCRIPTION: str = "基于 FastAPI 的多模态 AI 应用后端"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite 开发服务器
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # 模型路径配置
    YOLO_MODEL_PATH: str = "cv/yolo/model/yolov8l-face.pt"
    DLIB_FACE_RECOGNITION_MODEL: str = "cv/fr/model/dlib_face_recognition_resnet_model_v1.dat"
    DLIB_SHAPE_PREDICTOR_MODEL: str = "cv/fr/model/shape_predictor_68_face_landmarks.dat"
    FACE_VECTORS_PATH: str = "cv/fr/face_vectors.pkl"
    KNOWN_FACES_DIR: str = "cv/fr/known_faces"
    
    # 知识库配置
    KNOWLEDGE_VECTORS_PATH: str = "llm/multi_agent_fw/kb_data/knowledge_vectors.json"
    KNOWLEDGE_PERMISSION_PATH: str = "llm/multi_agent_fw/kb_data/knowledge_permission.jsonl"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        settings.UPLOAD_DIR,
        os.path.dirname(settings.YOLO_MODEL_PATH),
        os.path.dirname(settings.FACE_VECTORS_PATH),
        settings.KNOWN_FACES_DIR,
        os.path.dirname(settings.KNOWLEDGE_VECTORS_PATH),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# 初始化时创建目录
ensure_directories()

