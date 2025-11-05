"""
Pydantic 数据模型定义
用于请求和响应的数据验证
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 通用模型 ============

class BaseResponse(BaseModel):
    """基础响应模型"""
    status: str = Field(default="success", description="响应状态")
    message: Optional[str] = Field(default=None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    status: str = Field(default="error", description="错误状态")
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(default=None, description="错误详情")


# ============ CV 模型 ============

class FaceDetectionResult(BaseModel):
    """人脸检测结果"""
    face_count: int = Field(..., description="检测到的人脸数量")
    faces: List[Dict[str, Any]] = Field(default=[], description="人脸位置信息")
    confidence: List[float] = Field(default=[], description="置信度列表")


class FaceRecognitionResult(BaseModel):
    """人脸识别结果"""
    recognized: bool = Field(..., description="是否识别成功")
    identity: Optional[str] = Field(default=None, description="识别出的身份")
    confidence: Optional[float] = Field(default=None, description="识别置信度")
    faces: List[Dict[str, Any]] = Field(default=[], description="识别详情")


# ============ LLM 模型 ============

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, description="用户消息")
    conversation_id: Optional[str] = Field(default=None, description="会话ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    history: Optional[List[ChatMessage]] = Field(default=[], description="历史消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好,请介绍一下自己",
                "user_id": "user123"
            }
        }


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str = Field(..., description="AI 回复")
    conversation_id: str = Field(..., description="会话ID")
    timestamp: str = Field(..., description="时间戳")
    model: Optional[str] = Field(default=None, description="使用的模型")


class MultiAgentRequest(BaseModel):
    """多智能体请求"""
    query: str = Field(..., min_length=1, description="查询内容")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    agents: Optional[List[str]] = Field(default=None, description="指定使用的智能体")


class MultiAgentResponse(BaseModel):
    """多智能体响应"""
    query: str = Field(..., description="原始查询")
    result: str = Field(..., description="查询结果")
    agents_used: List[str] = Field(default=[], description="使用的智能体列表")
    execution_time: Optional[float] = Field(default=None, description="执行时间(秒)")


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")


class KnowledgeSearchResult(BaseModel):
    """知识库搜索结果"""
    content: str = Field(..., description="知识内容")
    score: float = Field(..., description="相似度分数")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应"""
    query: str = Field(..., description="搜索查询")
    results: List[KnowledgeSearchResult] = Field(default=[], description="搜索结果")
    total: int = Field(..., description="结果总数")


# ============ SR 模型 ============

class ASRRequest(BaseModel):
    """语音识别请求"""
    audio_format: str = Field(default="pcm", description="音频格式")
    sample_rate: int = Field(default=16000, description="采样率")
    language: str = Field(default="zh", description="语言代码")


class ASRResult(BaseModel):
    """语音识别结果"""
    text: str = Field(..., description="识别文本")
    confidence: Optional[float] = Field(default=None, description="置信度")
    duration: Optional[float] = Field(default=None, description="音频时长(秒)")
    is_final: bool = Field(default=True, description="是否为最终结果")


class ASRResponse(BaseModel):
    """语音识别响应"""
    status: str = Field(default="success", description="状态")
    result: ASRResult = Field(..., description="识别结果")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


# ============ 文件上传模型 ============

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小(字节)")
    content_type: Optional[str] = Field(default=None, description="文件类型")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")

