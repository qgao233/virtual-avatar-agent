"""
大语言模型相关 API 路由
包括对话、多智能体等功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

router = APIRouter()
# 设置之后的导入模块目录为上上两层的绝对目录下开始搜索
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llm.multi_agent_fw.agents import summary_agent, get_agent_response
from llm.assistant import get_multi_agent_response

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    conversation_id: str
    timestamp: str


@router.get("/")
async def llm_root():
    """大语言模型模块根路径"""
    return {
        "module": "大语言模型",
        "features": ["对话助手", "多智能体系统", "知识库问答"],
        "endpoints": {
            "chat": "/chat",
            "multi_agent": "/multi-agent",
            "knowledge_base": "/kb"
        }
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口
    
    参数:
        request: 包含用户消息的请求体
    
    返回:
        AI 助手的回复
    """
    try:
        from datetime import datetime
        
        # 使用 summary_agent 进行简单对话
        response = get_agent_response(summary_agent, request.message)
        
        return ChatResponse(
            response=response,
            conversation_id=request.conversation_id or f"chat_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


class MultiAgentRequest(BaseModel):
    """多智能体查询请求模型"""
    query: str
    user_id: Optional[str] = None


@router.post("/multi-agent")
async def multi_agent_query(request: MultiAgentRequest):
    """
    多智能体查询接口
    
    参数:
        request: 包含用户查询和用户ID的请求体
    
    返回:
        多智能体协作的查询结果
    """
    try:
        # 调用多智能体系统获取回复
        result = get_multi_agent_response(request.query)
        
        return {
            "status": "success",
            "query": request.query,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/kb/search")
async def knowledge_base_search(query: str, top_k: int = 5):
    """
    知识库搜索接口
    
    参数:
        query: 搜索查询
        top_k: 返回结果数量
    
    返回:
        相关知识库内容
    """
    try:
        # TODO: 集成知识库搜索
        # 这里需要使用向量数据库进行相似度搜索
        
        return {
            "status": "success",
            "query": query,
            "results": [],
            "message": "知识库搜索功能待集成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

