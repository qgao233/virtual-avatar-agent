"""
语音识别相关 API 路由
包括实时语音识别等功能
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict
import sys
import os
import asyncio
import json
import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sr.asr_realtime import RealtimeASR

router = APIRouter()

# 存储活跃的 WebSocket 连接
active_connections: Dict[str, WebSocket] = {}


class ASRRequest(BaseModel):
    """语音识别请求模型"""
    audio_format: str = "pcm"
    sample_rate: int = 16000


@router.get("/")
async def sr_root():
    """语音识别模块根路径"""
    return {
        "module": "语音识别",
        "features": ["实时语音识别", "音频文件识别"],
        "endpoints": {
            "realtime": "/realtime (WebSocket)",
            "file_recognition": "/recognize"
        }
    }


@router.post("/recognize")
async def recognize_audio(file: UploadFile = File(...)):
    """
    音频文件识别接口
    
    参数:
        file: 上传的音频文件
    
    返回:
        识别出的文字内容
    """
    try:
        # 读取音频文件
        contents = await file.read()
        
        # TODO: 集成语音识别功能
        # 这里需要导入并使用 sr/asr_realtime.py 中的功能
        
        return {
            "status": "success",
            "filename": file.filename,
            "text": "语音识别功能待集成",
            "duration": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


def asr_worker_thread(
    audio_queue: queue.Queue,
    asr: RealtimeASR,
    websocket: WebSocket,
    session_id: str,
    loop: asyncio.AbstractEventLoop,
    stop_event: threading.Event,
    chunk_size: int = 3200
):
    """
    ASR 工作线程：从队列中取音频数据并发送到 RealtimeASR
    
    Args:
        audio_queue: 音频数据队列
        asr: 共享的 RealtimeASR 实例
        websocket: WebSocket 连接
        session_id: 会话 ID
        loop: 主事件循环
        stop_event: 停止事件
        chunk_size: 累积音频块大小（字节）
    """
    
    def send_message_sync(message: dict):
        """在线程中发送 WebSocket 消息到主事件循环"""
        try:
            future = asyncio.run_coroutine_threadsafe(
                websocket.send_json(message),
                loop
            )
            future.result(timeout=1.0)
        except Exception as e:
            print(f"⚠️  发送消息失败: {e}")
    
    # 语音停止标志
    speech_stopped = threading.Event()
    
    # 定义回调函数
    def on_partial_text(text: str):
        print(f"📝 部分结果: {text}")
        send_message_sync({
            "type": "partial",
            "text": text,
            "session_id": session_id
        })
    
    def on_final_text(text: str):
        print(f"✓ 最终结果: {text}")
        send_message_sync({
            "type": "final",
            "text": text,
            "session_id": session_id
        })
    
    def on_speech_start():
        print(f"🎙️  检测到语音开始")
        speech_stopped.clear()
        send_message_sync({
            "type": "speech_start",
            "session_id": session_id
        })
    
    def on_speech_stop():
        print(f"⏸️  检测到语音停止")
        speech_stopped.set()  # 设置语音停止标志
        send_message_sync({
            "type": "speech_stop",
            "session_id": session_id
        })
    
    def on_session_created(sid: str):
        print(f"✓ ASR 会话已创建: {sid}")
        send_message_sync({
            "type": "connected",
            "session_id": session_id,
            "asr_session_id": sid
        })
    
    def on_error(error: Exception):
        print(f"❌ ASR 错误: {error}")
        send_message_sync({
            "type": "error",
            "message": str(error),
            "session_id": session_id
        })
    
    try:
        print(f"🚀 ASR 工作线程启动: {session_id}")
        
        # 连接 ASR（带回调）
        asr.connect(
            on_partial_text=on_partial_text,
            on_final_text=on_final_text,
            on_speech_start=on_speech_start,
            on_speech_stop=on_speech_stop,
            on_session_created=on_session_created,
            on_error=on_error
        )
        
        print(f"✓ ASR 已连接: {session_id}")
        
        # 持续从队列中取音频数据，累积到指定大小后发送
        audio_buffer = []
        
        while not stop_event.is_set():
            try:
                # 从队列中获取音频数据（超时 0.1 秒）
                audio_chunk = audio_queue.get(timeout=0.1)
                
                if audio_chunk is None:  # 结束信号
                    print(f"📭 收到结束信号")
                    break
                
                # 累积音频数据
                audio_buffer.append(audio_chunk)
                
                # 计算累积的总大小
                buffer_size = sum(len(chunk) for chunk in audio_buffer)
                
                # 累积到指定大小后发送
                if buffer_size >= chunk_size:
                    combined_audio = b''.join(audio_buffer)
                    
                    print(f"📤 发送音频块: {buffer_size} 字节")
                    
                    # 发送音频到 ASR
                    asr.send_audio_chunk(combined_audio)
                    
                    # 清空缓冲区
                    audio_buffer.clear()
                    
            except queue.Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                print(f"❌ 处理音频数据错误: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # 发送剩余的音频（如果有）
        if audio_buffer:
            combined_audio = b''.join(audio_buffer)
            buffer_size = len(combined_audio)
            
            print(f"📤 发送剩余音频: {buffer_size} 字节")
            asr.send_audio_chunk(combined_audio)
            audio_buffer.clear()
        
        print(f"✓ ASR 工作线程结束: {session_id}")
        
    except Exception as e:
        print(f"❌ ASR 工作线程错误: {e}")
        import traceback
        traceback.print_exc()
        send_message_sync({
            "type": "error",
            "message": f"ASR 工作线程错误: {str(e)}",
            "session_id": session_id
        })
    finally:
        # 线程结束时不关闭 ASR，因为它是共享的
        print(f"🏁 ASR 工作线程退出: {session_id}")


@router.websocket("/realtime")
async def realtime_asr(websocket: WebSocket):
    """
    实时语音识别 WebSocket 接口
    
    优化方案：
    1. 创建局部线程池（单线程）
    2. 创建共享的 RealtimeASR 实例
    3. 创建音频队列用于接收前端音频流
    4. 工作线程从队列中取音频直接发送到 ASR
    5. ASR 通过回调实时返回识别结果
    
    优势：
    - ✅ 真正的流式识别，实时反馈
    - ✅ 单线程处理，资源占用少
    - ✅ 共享 ASR 实例，避免重复连接
    - ✅ 队列缓冲，不阻塞主循环
    - ✅ 可以优雅关闭（支持 Ctrl+C）
    """
    await websocket.accept()
    
    session_id = f"session_{int(time.time() * 1000)}"
    
    # 创建局部资源
    audio_queue = queue.Queue(maxsize=100)  # 音频队列，最多缓冲 100 个块
    stop_event = threading.Event()
    executor = ThreadPoolExecutor(max_workers=1)  # 单线程池
    asr = None
    worker_future = None
    
    try:
        # 创建共享的 RealtimeASR 实例
        asr = RealtimeASR(verbose=False)
        
        # 获取当前事件循环
        loop = asyncio.get_event_loop()
        
        # 提交工作线程到线程池
        worker_future = executor.submit(
            asr_worker_thread,
            audio_queue,
            asr,
            websocket,
            session_id,
            loop,
            stop_event,
            chunk_size=3200  # 每次发送 3200 字节
        )
        
        # 等待 ASR 连接（最多 3 秒）
        await asyncio.sleep(1)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket 已连接，流式识别模式"
        })
        
        print(f"✓ WebSocket 连接已建立: {session_id}")
        active_connections[session_id] = websocket
        
        # 接收音频数据并放入队列
        audio_count = 0
        while True:
            try:
                # 尝试接收文本消息（控制命令）
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    action = data.get("action")
                    if action == "stop":
                        print(f"收到停止命令: {session_id}")
                        break
                except json.JSONDecodeError:
                    pass
                    
            except Exception:
                # 接收二进制数据（音频）
                try:
                    audio_data = await websocket.receive_bytes()
                    
                    # 放入队列（非阻塞）
                    try:
                        audio_queue.put_nowait(audio_data)
                        audio_count += 1
                        
                        # 每收到 50 个音频块，打印一次进度
                        if audio_count % 50 == 0:
                            print(f"📊 {session_id}: 已接收 {audio_count} 个音频块，队列大小: {audio_queue.qsize()}")
                            
                    except queue.Full:
                        print(f"⚠️  音频队列已满，丢弃数据")
                        
                except WebSocketDisconnect:
                    print(f"WebSocket 断开: {session_id}")
                    break
                except Exception as e:
                    print(f"接收音频数据错误: {e}")
                    import traceback
                    traceback.print_exc()
                    break
            
    except WebSocketDisconnect:
        print(f"WebSocket 断开: {session_id}")
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "session_id": session_id
            })
        except:
            pass
    finally:
        # 停止工作线程
        print(f"🛑 正在停止 ASR 工作线程: {session_id}")
        stop_event.set()
        
        # 发送结束信号到队列
        try:
            audio_queue.put_nowait(None)
        except:
            pass
        
        # 等待工作线程结束（最多 5 秒）
        if worker_future:
            try:
                worker_future.result(timeout=5)
                print(f"✓ ASR 工作线程已结束: {session_id}")
            except Exception as e:
                print(f"⚠️  等待工作线程结束超时: {e}")
        
        # 关闭 ASR 实例
        if asr:
            try:
                asr.close()
                print(f"✓ ASR 实例已关闭: {session_id}")
            except Exception as e:
                print(f"⚠️  关闭 ASR 实例失败: {e}")
        
        # 关闭线程池
        executor.shutdown(wait=True, cancel_futures=True)
        print(f"✓ 线程池已关闭: {session_id}")
        
        # 清理连接记录
        if session_id in active_connections:
            del active_connections[session_id]
        
        # 关闭 WebSocket
        try:
            await websocket.close()
        except:
            pass
        
        print(f"✓ WebSocket 连接已关闭: {session_id}, 共接收 {audio_count} 个音频块")


