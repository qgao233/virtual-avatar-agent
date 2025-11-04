import logging
import os
import base64
import signal
import sys
import time
import dashscope
from dashscope.audio.qwen_omni import *
from dashscope.audio.qwen_omni.omni_realtime import TranscriptionParams

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import model_config

def setup_logging():
    """配置日志输出"""
    logger = logging.getLogger('dashscope')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def init_api_key():
    """初始化 API Key"""
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
    dashscope.api_key = model_config.dashscope_api_key

class MyCallback(OmniRealtimeCallback):
    """实时识别回调处理"""
    def __init__(self, conversation):
        self.conversation = conversation
        self.handlers = {
            'session.created': self._handle_session_created,
            'conversation.item.input_audio_transcription.completed': self._handle_final_text,
            'conversation.item.input_audio_transcription.text': self._handle_stash_text,
            'input_audio_buffer.speech_started': lambda r: print('======Speech Start======'),
            'input_audio_buffer.speech_stopped': lambda r: print('======Speech Stop======'),
            'response.done': self._handle_response_done
        }

    def on_open(self):
        print('Connection opened')

    def on_close(self, code, msg):
        print(f'Connection closed, code: {code}, msg: {msg}')

    def on_event(self, response):
        try:
            handler = self.handlers.get(response['type'])
            print(f"\nresponse['type']: {response['type']}")
            # 获取handler的名称
            handler_name = handler.__name__
            print(f"\nhandler_name: {handler_name}")
            if handler:
                handler(response)
        except Exception as e:
            print(f'[Error] {e}')

    def _handle_session_created(self, response):
        print(f"Start session: {response['session']['id']}")

    def _handle_final_text(self, response):
        print(f"Final recognized text: {response['transcript']}")

    def _handle_stash_text(self, response):
        print(f"Got stash result: {response['stash']}")

    def _handle_response_done(self, response):
        print('======RESPONSE DONE======')
        print(f"[Metric] response: {self.conversation.get_last_response_id()}, "
              f"first text delay: {self.conversation.get_last_first_text_delay()}, "
              f"first audio delay: {self.conversation.get_last_first_audio_delay()}")


def read_audio_chunks(file_path, chunk_size=3200):
    """按块读取音频文件"""
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk


def send_audio(conversation, file_path, delay=0.1):
    """发送音频数据"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file {file_path} does not exist.")

    print("Processing audio file... Press 'Ctrl+C' to stop.")
    for chunk in read_audio_chunks(file_path):
        audio_b64 = base64.b64encode(chunk).decode('ascii')
        conversation.append_audio(audio_b64)
        time.sleep(delay)
    # enable_turn_detection为False时，应将下行代码注释取消
    # conversation.commit()
    # print("Audio commit sent.")


def main():
    setup_logging()
    init_api_key()

    audio_file_path = "res/test.pcm"
    conversation = OmniRealtimeConversation(
        model=model_config.asr_model,
        # 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime
        url=model_config.asr_url,
        callback=MyCallback(conversation=None)  # 暂时传None，稍后注入
    )

    # 注入自身到回调
    conversation.callback.conversation = conversation

    def handle_exit(sig, frame):
        print('Ctrl+C pressed, exiting...')
        conversation.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)

    conversation.connect()

    transcription_params = TranscriptionParams(
        language='zh',
        sample_rate=16000,
        input_audio_format="pcm"
        # 输入音频的语料，用于辅助识别
        # corpus_text=""
    )

    conversation.update_session(
        output_modalities=[MultiModality.TEXT],
        enable_input_audio_transcription=True,
        transcription_params=transcription_params
    )

    try:
        send_audio(conversation, audio_file_path)
        time.sleep(3)  # 等待响应
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        conversation.close()
        print("Audio processing completed.")


if __name__ == '__main__':
    main()