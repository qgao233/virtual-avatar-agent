"""
计算机视觉相关 API 路由
包括人脸检测、人脸识别等功能
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import cv2
import numpy as np
from io import BytesIO
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cv.cv import get_cv_system
from config import settings

router = APIRouter()


@router.get("/")
async def cv_root():
    """计算机视觉模块根路径"""
    return {
        "module": "计算机视觉",
        "features": ["人脸识别"],
        "endpoints": {
            "face_recognition": "/recognize-faces",
            "recognition_gap": "/recognition-gap"
        }
    }

@router.post("/recognize-faces")
async def recognize_faces(file: UploadFile = File(...)):
    """
    人脸识别接口
    
    上传图片,返回检测到的所有人脸及其身份信息
    
    参数:
        file: 上传的图片文件
    
    返回:
        {
            "status": "success",
            "filename": "test.jpg",
            "face_count": 2,
            "faces": [
                {
                    "face_id": 1,
                    "bbox": {"x1": 100, "y1": 150, "x2": 300, "y2": 350},
                    "name": "张三",
                    "confidence": 0.95,
                    "distance": 0.25
                },
                ...
            ]
        }
    """
    try:
        # 读取上传的图片
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="无效的图片文件")
        
        # 获取 CV 系统
        cv_system = get_cv_system()
        if cv_system is None or not cv_system.is_initialized:
            raise HTTPException(
                status_code=503, 
                detail="CV 系统未初始化或初始化失败,请稍后重试"
            )
        
        # 识别人脸
        results = cv_system.recognize_faces_in_image(image)
        return {
            "status": "success",
            "filename": file.filename,
            "image_size": {
                "width": image.shape[1],
                "height": image.shape[0]
            },
            "face_count": len(results),
            "faces": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

# 告诉前端settings.RECOGNITION_GAP的值(毫秒)
@router.get("/recognition-gap")
async def get_recognition_gap():
    """
    获取人脸识别间隔时间
    
    返回:
        {
            "recognition_gap": 1000  # 毫秒
        }
    """
    return {
        "recognition_gap": int(settings.RECOGNITION_GAP) 
    }

@router.get("/models/status")
async def get_models_status():
    """获取 CV 模型加载状态"""
    cv_system = get_cv_system()
    if cv_system is None:
        return {
            "status": "待初始化"
        }
    return cv_system.get_status()

