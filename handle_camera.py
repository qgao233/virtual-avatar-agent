"""
整合示例 - 人脸检测 + 人脸识别
将YOLO检测和dlib识别功能整合在一起
"""

import cv2
import sys
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolo'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'fr'))

from yolo.yolo import YOLOFaceDetector
from fr.fr import FaceRecognizer, FaceVectorDB, FaceRecognitionSystem


class IntegratedFaceSystem:
    """整合的人脸检测+识别系统"""
    
    def __init__(self):
        # 初始化YOLO检测器
        print("加载YOLO人脸检测模型...")
        self.detector = YOLOFaceDetector(
            model_path='model/yolov8l-face.pt',
            conf_threshold=0.3
        )
        
        # 初始化人脸识别系统
        print("加载人脸识别模型...")
        recognizer = FaceRecognizer(
            predictor_path="model/shape_predictor_68_face_landmarks.dat",
            face_rec_model_path="model/dlib_face_recognition_resnet_model_v1.dat"
        )
        vector_db = FaceVectorDB(
            db_path="face_vectors.pkl",
            threshold=0.6
        )
        self.recognition_system = FaceRecognitionSystem(recognizer, vector_db)
        
        # 缓存: 追踪ID -> 识别结果
        self.track_id_cache: dict = {}
        
        print("系统初始化完成!")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理单帧图像
        
        Args:
            frame: BGR格式的输入帧
            
        Returns:
            标注后的图像
        """
        # 1. YOLO检测人脸
        results = self.detector.detect_faces(frame)
        
        if not self.detector.has_faces(results):
            return frame
        
        # 2. 提取人脸框
        face_boxes = self.detector.extract_face_boxes(results)
        
        frame_copy = frame.copy()
        
        # 3. 对每个检测到的人脸进行识别
        for track_id, box in face_boxes:
            # 裁剪人脸区域
            face = self.detector.crop_face(frame_copy, box)
            
            # 检查缓存
            if track_id not in self.track_id_cache:
                # 转换为RGB用于识别
                face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                
                # TODO: 调用向量库进行人脸识别
                # 目前暂留白,使用占位符
                # name, distance = self.recognition_system.recognize_face(face_rgb)
                
                # 暂时使用"未知"作为占位
                name = "未知"
                is_recognized = False
                
                # 缓存结果
                self.track_id_cache[track_id] = {
                    'name': name,
                    'recognized': is_recognized
                }
            
            # 获取识别结果
            person_info = self.track_id_cache[track_id]
            name = person_info['name']
            is_recognized = person_info['recognized']
            
            # 绘制边界框
            color = (0, 255, 0) if is_recognized else (0, 0, 255)  # 绿色/红色
            label = name if is_recognized else "无法识别"
            
            frame = self.draw_chinese_label(frame, box, label, color)
        
        return frame
    
    def draw_chinese_label(self, 
                          image: np.ndarray,
                          box: list,
                          label: str,
                          color: tuple,
                          font_path: str = "SimHei.ttf") -> np.ndarray:
        """
        绘制支持中文的标签
        
        Args:
            image: 输入图像
            box: 边界框
            label: 标签文本
            color: 颜色
            font_path: 字体路径
            
        Returns:
            绘制后的图像
        """
        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        
        # 绘制矩形框
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness=2, lineType=cv2.LINE_AA)
        
        # 计算标签背景宽度
        text_size = 20
        if len(label) == 2:
            w = 40
        elif len(label) == 3:
            w = 60
        elif len(label) == 4:
            w = 80
        else:
            w = len(label) * 20
        
        h = 25
        
        # 确保不超出图像范围
        outside = y1 - h >= 3
        p3_y = y1 - h - 3 if outside else y1 + h + 3
        
        # 绘制标签背景
        cv2.rectangle(image, (x1, y1 if not outside else p3_y), 
                     (x1 + w, y1 if not outside else y1), color, -1, cv2.LINE_AA)
        
        # 使用PIL绘制中文
        img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        try:
            font = ImageFont.truetype(font_path, text_size, encoding="utf-8")
        except:
            font = ImageFont.load_default()
        
        text_y = p3_y - 2 if outside else y1 + 2
        draw.text((x1, text_y), label, (255, 255, 255), font=font)
        
        # 转回OpenCV格式
        return cv2.cvtColor(np.asarray(img_pil), cv2.COLOR_RGB2BGR)


def main():
    """主函数"""
    # 初始化系统
    system = IntegratedFaceSystem()
    
    # 选择输入源
    # 选项1: 摄像头
    cap = cv2.VideoCapture(0)
    
    # 选项2: 视频文件
    # cap = cv2.VideoCapture("media/00009.MTS")
    
    # 获取视频参数
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 可选: 保存输出视频
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # out = cv2.VideoWriter('result/output.mp4', fourcc, fps, (width, height))
    
    print("开始处理视频流...")
    print("按 'q' 键退出")
    
    frame_count = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        
        if not success:
            break
        
        # 处理帧
        processed_frame = system.process_frame(frame)
        
        # 显示帧数
        frame_count += 1
        cv2.putText(processed_frame, f'Frame: {frame_count}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        # 显示已识别人数
        recognized_count = sum(1 for info in system.track_id_cache.values() 
                              if info['recognized'])
        cv2.putText(processed_frame, f'Recognized: {recognized_count}', 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 显示结果
        cv2.imshow("Face Detection & Recognition", processed_frame)
        
        # 保存视频
        # out.write(processed_frame)
        
        # 按键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 释放资源
    cap.release()
    # out.release()
    cv2.destroyAllWindows()
    
    print(f"处理完成! 共处理 {frame_count} 帧")


if __name__ == "__main__":
    main()

