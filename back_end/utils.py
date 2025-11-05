"""
工具函数模块
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
import aiofiles


async def save_upload_file(file: UploadFile, upload_dir: str = "uploads") -> dict:
    """
    保存上传的文件
    
    参数:
        file: 上传的文件对象
        upload_dir: 保存目录
    
    返回:
        包含文件信息的字典
    """
    # 确保上传目录存在
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 异步保存文件
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    return {
        "original_filename": file.filename,
        "saved_filename": unique_filename,
        "file_path": file_path,
        "file_size": len(content),
        "content_type": file.content_type,
        "upload_time": datetime.now().isoformat()
    }


def generate_conversation_id() -> str:
    """
    生成会话 ID
    
    返回:
        唯一的会话 ID
    """
    return f"conv_{uuid.uuid4().hex[:16]}"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    格式化时间戳
    
    参数:
        dt: datetime 对象,默认为当前时间
    
    返回:
        格式化的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
    """
    验证文件大小
    
    参数:
        file_size: 文件大小(字节)
        max_size: 最大允许大小(字节),默认 10MB
    
    返回:
        是否符合大小限制
    """
    return file_size <= max_size


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    验证文件扩展名
    
    参数:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表
    
    返回:
        是否为允许的文件类型
    """
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_extensions


class FileValidator:
    """文件验证器"""
    
    # 图片文件扩展名
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
    
    # 音频文件扩展名
    AUDIO_EXTENSIONS = ['.wav', '.mp3', '.pcm', '.flac', '.m4a']
    
    # 视频文件扩展名
    VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
    
    @staticmethod
    def is_image(filename: str) -> bool:
        """判断是否为图片文件"""
        return validate_file_extension(filename, FileValidator.IMAGE_EXTENSIONS)
    
    @staticmethod
    def is_audio(filename: str) -> bool:
        """判断是否为音频文件"""
        return validate_file_extension(filename, FileValidator.AUDIO_EXTENSIONS)
    
    @staticmethod
    def is_video(filename: str) -> bool:
        """判断是否为视频文件"""
        return validate_file_extension(filename, FileValidator.VIDEO_EXTENSIONS)


def clean_old_files(directory: str, max_age_days: int = 7):
    """
    清理旧文件
    
    参数:
        directory: 目录路径
        max_age_days: 文件最大保留天数
    """
    if not os.path.exists(directory):
        return
    
    current_time = datetime.now()
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if os.path.isfile(file_path):
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_days = (current_time - file_modified_time).days
            
            if age_days > max_age_days:
                try:
                    os.remove(file_path)
                    print(f"已删除旧文件: {file_path}")
                except Exception as e:
                    print(f"删除文件失败: {file_path}, 错误: {e}")


def get_file_info(file_path: str) -> dict:
    """
    获取文件信息
    
    参数:
        file_path: 文件路径
    
    返回:
        文件信息字典
    """
    if not os.path.exists(file_path):
        return None
    
    stat = os.stat(file_path)
    
    return {
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "file_size": stat.st_size,
        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_file": os.path.isfile(file_path),
        "is_dir": os.path.isdir(file_path)
    }

