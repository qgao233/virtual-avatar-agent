"""
人脸识别模块
功能: 识别目标人物身份
采用特征提取模型 + 向量库的方案 (无需训练)
"""

import cv2
import dlib
import numpy as np
from typing import Optional, Dict, Tuple, List
import os
import pickle


class FaceRecognizer:
    """人脸识别器 - 基于dlib特征提取"""
    
    def __init__(self, 
                 predictor_path: str = "model/shape_predictor_68_face_landmarks.dat",
                 face_rec_model_path: str = "model/dlib_face_recognition_resnet_model_v1.dat"):
        """
        初始化人脸识别器
        
        Args:
            predictor_path: 人脸关键点检测器路径
            face_rec_model_path: 人脸识别模型路径
        """
        # 人脸检测器
        self.detector = dlib.get_frontal_face_detector()
        # 关键点检测器
        self.shape_predictor = dlib.shape_predictor(predictor_path)
        # 特征编码器
        self.face_encoder = dlib.face_recognition_model_v1(face_rec_model_path)
        
    def extract_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        从人脸图像中提取128维特征向量
        
        Args:
            image: RGB格式的人脸图像
            
        Returns:
            128维特征向量,如果检测失败返回None
        """
        # 人脸检测
        faces = self.detector(image, 1)
        
        # 只处理单张人脸
        if len(faces) == 1:
            # 关键点检测
            shape = self.shape_predictor(image, faces[0])
            # 特征提取
            face_descriptor = self.face_encoder.compute_face_descriptor(image, shape)
            # 转换为numpy数组
            feature_vector = np.array(face_descriptor)
            return feature_vector
        else:
            return None
    
    def compute_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        计算两个特征向量的相似度(欧氏距离)
        
        Args:
            vector1: 特征向量1
            vector2: 特征向量2
            
        Returns:
            欧氏距离(越小越相似)
        """
        return np.linalg.norm(vector1 - vector2)


class FaceVectorDB:
    """
    人脸向量数据库
    用于存储和检索人脸特征向量
    
    TODO: 后续可替换为专业向量数据库(如Milvus、Faiss等)
    """
    
    def __init__(self, db_path: str = "face_vectors.pkl", threshold: float = 0.6):
        """
        初始化向量数据库
        
        Args:
            db_path: 数据库文件路径
            threshold: 相似度阈值,小于此值认为是同一人
        """
        self.db_path = db_path
        self.threshold = threshold
        self.face_db: Dict[str, np.ndarray] = {}  # {name: feature_vector}
        
        # 加载已有数据库
        self.load_db()
    
    def add_face(self, name: str, feature_vector: np.ndarray) -> None:
        """
        向数据库添加人脸特征
        
        Args:
            name: 人名
            feature_vector: 128维特征向量
        """
        self.face_db[name] = feature_vector
        self.save_db()
    
    def search(self, query_vector: np.ndarray) -> Tuple[Optional[str], float]:
        """
        在向量库中检索最相似的人脸
        
        Args:
            query_vector: 待查询的特征向量
            
        Returns:
            (匹配到的人名, 相似度距离) 或 (None, inf) 如果未匹配
        """
        if not self.face_db:
            return None, float('inf')
        
        min_distance = float('inf')
        best_match = None
        
        for name, stored_vector in self.face_db.items():
            distance = np.linalg.norm(query_vector - stored_vector)
            if distance < min_distance:
                min_distance = distance
                best_match = name
        
        # 判断是否超过阈值
        if min_distance < self.threshold:
            return best_match, min_distance
        else:
            return None, min_distance
    
    def remove_face(self, name: str) -> bool:
        """
        从数据库删除人脸
        
        Args:
            name: 人名
            
        Returns:
            是否删除成功
        """
        if name in self.face_db:
            del self.face_db[name]
            self.save_db()
            return True
        return False
    
    def save_db(self) -> None:
        """保存数据库到文件"""
        with open(self.db_path, 'wb') as f:
            pickle.dump(self.face_db, f)
    
    def load_db(self) -> None:
        """从文件加载数据库"""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                self.face_db = pickle.load(f)
        else:
            self.face_db = {}
    
    def list_all(self) -> List[str]:
        """列出所有已注册的人名"""
        return list(self.face_db.keys())


class FaceRecognitionSystem:
    """
    完整的人脸识别系统
    整合特征提取和向量检索
    """
    
    def __init__(self, 
                 recognizer: FaceRecognizer,
                 vector_db: FaceVectorDB):
        """
        初始化识别系统
        
        Args:
            recognizer: 人脸识别器
            vector_db: 向量数据库
        """
        self.recognizer = recognizer
        self.vector_db = vector_db
    
    def register_face(self, name: str, image: np.ndarray) -> bool:
        """
        注册新人脸
        
        Args:
            name: 人名
            image: RGB格式人脸图像
            
        Returns:
            是否注册成功
        """
        # 提取特征
        features = self.recognizer.extract_features(image)
        
        if features is not None:
            # 存入向量库
            self.vector_db.add_face(name, features)
            return True
        else:
            return False
    
    def recognize_face(self, image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        识别人脸身份
        
        Args:
            image: RGB格式人脸图像
            
        Returns:
            (识别到的人名, 相似度) 或 (None, inf) 如果未识别
        """
        # 提取特征
        features = self.recognizer.extract_features(image)
        
        if features is not None:
            # 在向量库中检索
            name, distance = self.vector_db.search(features)
            return name, distance
        else:
            return None, float('inf')


# ============ 工具函数 ============

def load_and_register_from_folder(folder_path: str, 
                                   recognition_system: FaceRecognitionSystem) -> int:
    """
    从文件夹批量注册人脸
    文件命名格式: 姓名.jpg 或 姓名.png
    
    Args:
        folder_path: 人脸图片文件夹路径
        recognition_system: 识别系统实例
        
    Returns:
        成功注册的人脸数量
    """
    success_count = 0
    
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            # 从文件名提取姓名
            name = os.path.splitext(filename)[0]
            
            # 读取图片
            image_path = os.path.join(folder_path, filename)
            image = cv2.imread(image_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 注册
            if recognition_system.register_face(name, image_rgb):
                print(f"✓ 成功注册: {name}")
                success_count += 1
            else:
                print(f"✗ 注册失败: {name} (未检测到人脸特征)")
    
    return success_count


if __name__ == "__main__":
    # 示例: 初始化识别系统
    recognizer = FaceRecognizer()
    vector_db = FaceVectorDB(threshold=0.6)
    system = FaceRecognitionSystem(recognizer, vector_db)
    
    # 示例: 从文件夹批量注册
    success = load_and_register_from_folder("known_faces", system)
    print(f"\n共注册 {success} 个人脸")
    
    # 示例: 识别单张图片
    # test_image = cv2.imread("test.jpg")
    # test_image_rgb = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
    # name, distance = system.recognize_face(test_image_rgb)
    # if name:
    #     print(f"识别结果: {name}, 距离: {distance:.4f}")
    # else:
    #     print("未识别到已注册的人脸")
    
    print("人脸识别系统初始化完成")
    print(f"当前数据库中有 {len(vector_db.list_all())} 个已注册人脸")

