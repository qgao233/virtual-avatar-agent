"""
YOLO人脸检测模块
功能: 检测视频/图像中是否存在人脸
"""

import cv2
from ultralytics import YOLO
import numpy as np
from typing import List, Tuple, Optional


class YOLOFaceDetector:
    """YOLO人脸检测器"""
    
    def __init__(self, model_path: str = 'model/yolov8l-face.pt', conf_threshold: float = 0.3):
        """
        初始化YOLO人脸检测器
        
        Args:
            model_path: YOLO模型路径
            conf_threshold: 置信度阈值
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        
    def detect_faces(self, frame: np.ndarray, persist: bool = True) -> Optional[List]:
        """
        检测图像中的人脸
        
        Args:
            frame: 输入图像帧
            persist: 是否持久化追踪
            
        Returns:
            检测结果列表,包含边界框和追踪ID
        """
        results = self.model.track(frame, conf=self.conf_threshold, persist=persist)
        return results
    
    def extract_face_boxes(self, results) -> List[Tuple[int, List[float]]]:
        """
        从检测结果中提取人脸框和追踪ID
        
        Args:
            results: YOLO检测结果
            
        Returns:
            [(track_id, [x1, y1, x2, y2, conf, cls]), ...]
        """
        face_boxes = []
        
        if results[0].boxes.id is not None and len(results) > 0:
            track_ids = results[0].boxes.id.int().cpu().tolist()
            boxes = results[0].boxes.data.cpu().tolist()
            
            for track_id, box in zip(track_ids, boxes):
                face_boxes.append((track_id, box))
                
        return face_boxes
    
    def crop_face(self, frame: np.ndarray, box: List[float]) -> np.ndarray:
        """
        根据边界框裁剪人脸区域
        
        Args:
            frame: 原始图像
            box: 边界框 [x1, y1, x2, y2, ...]
            
        Returns:
            裁剪后的人脸图像
        """
        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        face = frame[y1:y2, x1:x2]
        return face
    
    def has_faces(self, results) -> bool:
        """
        判断检测结果中是否存在人脸
        
        Args:
            results: YOLO检测结果
            
        Returns:
            是否检测到人脸
        """
        return results[0].boxes.id is not None and len(results) > 0


def draw_face_box(image: np.ndarray, 
                  box: List[float], 
                  label: str = '',
                  color: Tuple[int, int, int] = (0, 255, 0),
                  thickness: int = 2) -> np.ndarray:
    """
    在图像上绘制人脸边界框
    
    Args:
        image: 输入图像
        box: 边界框 [x1, y1, x2, y2, ...]
        label: 标签文本
        color: 边界框颜色 (B, G, R)
        thickness: 线条粗细
        
    Returns:
        绘制后的图像
    """
    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    
    # 绘制矩形框
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness, lineType=cv2.LINE_AA)
    
    # 如果有标签,绘制标签背景和文本
    if label:
        # 计算文本大小
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        )
        
        # 绘制标签背景
        cv2.rectangle(
            image, 
            (x1, y1 - text_height - 10),
            (x1 + text_width, y1),
            color, 
            -1
        )
        
        # 绘制文本
        cv2.putText(
            image,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )
    
    return image


if __name__ == "__main__":
    # 测试代码
    detector = YOLOFaceDetector()
    
    # 打开摄像头或视频文件
    cap = cv2.VideoCapture(0)  # 0表示默认摄像头
    
    while cap.isOpened():
        success, frame = cap.read()
        
        if success:
            # 检测人脸
            results = detector.detect_faces(frame)
            
            # 提取人脸框
            face_boxes = detector.extract_face_boxes(results)
            
            # 绘制结果
            for track_id, box in face_boxes:
                frame = draw_face_box(frame, box, f"Face {track_id}")
            
            # 显示结果
            cv2.imshow("YOLO Face Detection", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    
    cap.release()
    cv2.destroyAllWindows()

