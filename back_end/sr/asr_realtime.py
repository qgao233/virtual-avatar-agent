"""
实时语音识别模块
基于阿里云 Dashscope Qwen-Omni 模型
"""
import logging
import os
import base64
import sys
import time
from typing import Optional, Callable, Dict, Any
import dashscope
from dashscope.audio.qwen_omni import *
from dashscope.audio.qwen_omni.omni_realtime import TranscriptionParams

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import model_config


def setup_logging(level=logging.INFO):
    """配置日志输出"""
    logger = logging.getLogger('dashscope')
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.propagate = False
    return logger


def init_api_key():
    """初始化 API Key"""
    if not dashscope.api_key:
        dashscope.api_key = model_config.dashscope_api_key

class ASRCallback(OmniRealtimeCallback):
    """
    实时语音识别回调处理器
    
    支持自定义回调函数来处理识别结果
    """
    def __init__(
        self, 
        conversation=None,
        on_final_text: Optional[Callable[[str], None]] = None,
        on_partial_text: Optional[Callable[[str], None]] = None,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_stop: Optional[Callable[[], None]] = None,
        on_session_created: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        verbose: bool = False
    ):
        """
        初始化回调处理器
        
        Args:
            conversation: OmniRealtimeConversation 实例
            on_final_text: 最终识别文本的回调函数
            on_partial_text: 部分识别文本的回调函数
            on_speech_start: 语音开始的回调函数
            on_speech_stop: 语音停止的回调函数
            on_session_created: 会话创建的回调函数
            on_error: 错误处理的回调函数
            verbose: 是否打印详细日志
        """
        self.conversation = conversation
        self.on_final_text = on_final_text
        self.on_partial_text = on_partial_text
        self.on_speech_start = on_speech_start
        self.on_speech_stop = on_speech_stop
        self.on_session_created = on_session_created
        self.on_error = on_error
        self.verbose = verbose
        
        self.handlers = {
            'session.created': self._handle_session_created,
            'conversation.item.input_audio_transcription.completed': self._handle_final_text,
            'conversation.item.input_audio_transcription.text': self._handle_stash_text,
            'input_audio_buffer.speech_started': self._handle_speech_start,
            'input_audio_buffer.speech_stopped': self._handle_speech_stop,
            'response.done': self._handle_response_done
        }

    def on_open(self):
        if self.verbose:
            print('✓ ASR 连接已建立')

    def on_close(self, code, msg):
        if self.verbose:
            print(f'✗ ASR 连接已关闭, code: {code}, msg: {msg}')

    def on_event(self, response):
        try:
            event_type = response.get('type')
            handler = self.handlers.get(event_type)
            
            if self.verbose:
                print(f"📨 收到事件: {event_type}")
            
            if handler:
                handler(response)
        except Exception as e:
            if self.verbose:
                print(f'❌ 事件处理错误: {e}')
            if self.on_error:
                self.on_error(e)

    def _handle_session_created(self, response):
        session_id = response.get('session', {}).get('id', 'unknown')
        if self.verbose:
            print(f"✓ 会话已创建: {session_id}")
        if self.on_session_created:
            self.on_session_created(session_id)

    def _handle_final_text(self, response):
        text = response.get('transcript', '')
        if self.verbose:
            print(f"📝 最终识别: {text}")
        if self.on_final_text:
            self.on_final_text(text)

    def _handle_stash_text(self, response):
        text = response.get('stash', '')
        if self.verbose:
            print(f"📝 部分识别: {text}")
        if self.on_partial_text:
            self.on_partial_text(text)

    def _handle_speech_start(self, response):
        if self.verbose:
            print('🎤 语音开始')
        if self.on_speech_start:
            self.on_speech_start()

    def _handle_speech_stop(self, response):
        if self.verbose:
            print('⏹️  语音停止')
        if self.on_speech_stop:
            self.on_speech_stop()

    def _handle_response_done(self, response):
        if self.verbose and self.conversation:
            print('✓ 响应完成')
            print(f"[性能指标] response: {self.conversation.get_last_response_id()}, "
                  f"首个文本延迟: {self.conversation.get_last_first_text_delay()}, "
                  f"首个音频延迟: {self.conversation.get_last_first_audio_delay()}")


class RealtimeASR:
    """
    实时语音识别封装类
    
    提供简单易用的 API 来进行实时语音识别
    """
    def __init__(
        self,
        model: Optional[str] = None,
        url: Optional[str] = None,
        language: str = 'zh',
        sample_rate: int = 16000,
        input_audio_format: str = "pcm",
        verbose: bool = False
    ):
        """
        初始化实时语音识别
        
        Args:
            model: 模型名称，默认使用配置文件中的模型
            url: WebSocket URL，默认使用配置文件中的 URL
            language: 语言，默认为中文 'zh'
            sample_rate: 采样率，默认 16000
            input_audio_format: 音频格式，默认 "pcm"
            verbose: 是否打印详细日志
        """
        init_api_key()
        
        self.model = model or model_config.asr_model
        self.url = url or model_config.asr_url
        self.language = language
        self.sample_rate = sample_rate
        self.input_audio_format = input_audio_format
        self.verbose = verbose
        
        self.conversation: Optional[OmniRealtimeConversation] = None
        self.callback: Optional[ASRCallback] = None
        self.is_connected = False
        
        # 存储识别结果
        self.final_texts = []
        self.partial_texts = []
    
    def connect(
        self,
        on_final_text: Optional[Callable[[str], None]] = None,
        on_partial_text: Optional[Callable[[str], None]] = None,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_stop: Optional[Callable[[], None]] = None,
        on_session_created: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        建立连接
        
        Args:
            on_final_text: 最终识别文本的回调函数
            on_partial_text: 部分识别文本的回调函数
            on_speech_start: 语音开始的回调函数
            on_speech_stop: 语音停止的回调函数
            on_session_created: 会话创建的回调函数
            on_error: 错误处理的回调函数
        """
        if self.is_connected:
            raise RuntimeError("已经连接，请先断开连接")
        
        # 创建回调处理器
        self.callback = ASRCallback(
            conversation=None,  # 稍后注入
            on_final_text=on_final_text or self._default_on_final_text,
            on_partial_text=on_partial_text or self._default_on_partial_text,
            on_speech_start=on_speech_start,
            on_speech_stop=on_speech_stop,
            on_session_created=on_session_created,
            on_error=on_error,
            verbose=self.verbose
        )
        
        # 创建会话
        self.conversation = OmniRealtimeConversation(
            model=self.model,
            url=self.url,
            callback=self.callback
        )
        
        # 注入 conversation 到 callback
        self.callback.conversation = self.conversation
        
        # 建立连接
        self.conversation.connect()
        
        # 配置会话参数
        transcription_params = TranscriptionParams(
            language=self.language,
            sample_rate=self.sample_rate,
            input_audio_format=self.input_audio_format
        )
        
        self.conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_input_audio_transcription=True,
            transcription_params=transcription_params
        )
        
        self.is_connected = True
        
        if self.verbose:
            print(f"✓ ASR 已连接: {self.model}")
    
    def send_audio_chunk(self, audio_data: bytes):
        """
        发送音频数据块
        
        Args:
            audio_data: 音频数据（bytes）
        """
        if not self.is_connected or not self.conversation:
            raise RuntimeError("未连接，请先调用 connect()")
        
        audio_b64 = base64.b64encode(audio_data).decode('ascii')
        self.conversation.append_audio(audio_b64)
    
    def send_audio_file(self, file_path: str, chunk_size: int = 3200, delay: float = 0.1):
        """
        发送音频文件
        
        Args:
            file_path: 音频文件路径
            chunk_size: 每次读取的字节数
            delay: 每次发送的延迟（秒）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        if self.verbose:
            print(f"📤 开始发送音频文件: {file_path}")
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                self.send_audio_chunk(chunk)
                time.sleep(delay)
        
        if self.verbose:
            print("✓ 音频文件发送完成")
    
    def close(self):
        """关闭连接"""
        if self.conversation:
            self.conversation.close()
            self.is_connected = False
            if self.verbose:
                print("✓ ASR 连接已关闭")
    
    def get_final_texts(self) -> list:
        """获取所有最终识别文本"""
        return self.final_texts.copy()
    
    def get_partial_texts(self) -> list:
        """获取所有部分识别文本"""
        return self.partial_texts.copy()
    
    def clear_results(self):
        """清空识别结果"""
        self.final_texts.clear()
        self.partial_texts.clear()
    
    def _default_on_final_text(self, text: str):
        """默认的最终文本处理"""
        self.final_texts.append(text)
    
    def _default_on_partial_text(self, text: str):
        """默认的部分文本处理"""
        self.partial_texts.append(text)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def read_audio_chunks(file_path: str, chunk_size: int = 3200):
    """
    按块读取音频文件
    
    Args:
        file_path: 音频文件路径
        chunk_size: 每次读取的字节数
        
    Yields:
        音频数据块
    """
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk


def main():
    """
    命令行测试入口
    """
    import signal
    
    setup_logging(logging.DEBUG)
    
    audio_file_path = os.path.join(os.path.dirname(__file__), "res/test.pcm")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ 测试音频文件不存在: {audio_file_path}")
        return
    
    print("=" * 60)
    print("实时语音识别测试")
    print("=" * 60)
    
    # 使用上下文管理器自动管理连接
    with RealtimeASR(verbose=True) as asr:
        # 设置退出处理
        def handle_exit(sig, frame):
            print('\n⚠️  Ctrl+C 按下，正在退出...')
            asr.close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_exit)
        
        # 建立连接
        asr.connect()
        
        # 发送音频文件
        try:
            asr.send_audio_file(audio_file_path)
            time.sleep(3)  # 等待响应
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        # 获取识别结果
        final_texts = asr.get_final_texts()
        print("\n" + "=" * 60)
        print("识别结果汇总:")
        print("=" * 60)
        for i, text in enumerate(final_texts, 1):
            print(f"{i}. {text}")
        print("=" * 60)


if __name__ == '__main__':
    main()