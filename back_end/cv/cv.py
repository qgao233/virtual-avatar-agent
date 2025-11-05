"""
计算机视觉模块初始化
整合 YOLO 人脸检测和 dlib 人脸识别功能
"""

import os
import sys
import math
from typing import Optional, Tuple

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from yolo.yolo import YOLOFaceDetector
from fr.fr import FaceRecognizer, FaceVectorDB, FaceRecognitionSystem, load_and_register_from_folder


class CVSystem:
    """计算机视觉系统 - 整合人脸检测和识别"""
    
    def __init__(self):
        """初始化 CV 系统"""
        self.detector: Optional[YOLOFaceDetector] = None
        self.recognizer: Optional[FaceRecognizer] = None
        self.vector_db: Optional[FaceVectorDB] = None
        self.recognition_system: Optional[FaceRecognitionSystem] = None
        self.is_initialized = False
        
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "is_initialized": self.is_initialized,
            "yolo_loaded": self.detector is not None,
            "recognizer_loaded": self.recognizer is not None,
            "registered_faces": len(self.vector_db.list_all()) if self.vector_db else 0,
            "registered_names": self.vector_db.list_all() if self.vector_db else []
        }
    
    def recognize_faces_in_image(self, image) -> list:
        """
        识别图片中的所有人脸
        
        Args:
            image: 输入图片 (numpy array, BGR格式)
            
        Returns:
            识别结果列表，每个元素包含:
            [
                {
                    "face_id": 人脸ID (int),
                    "bbox": 人脸坐标 {"x1": int, "y1": int, "x2": int, "y2": int},
                    "name": 识别出的人名 (str) 或 "Unknown",
                    "confidence": 识别置信度 (float),
                    "distance": 特征距离 (float)
                },
                ...
            ]
            
        Raises:
            RuntimeError: 如果系统未初始化
        """
        import cv2
        
        if not self.is_initialized:
            raise RuntimeError("CV 系统未初始化，请先调用 init_cv_system()")
        
        results = []
        
        # 步骤 1: 使用 YOLO 检测人脸
        yolo_results = self.detector.detect_faces(image, persist=False)
        if not self.detector.has_faces(yolo_results):
            return results  # 没有检测到人脸，返回空列表
        # 步骤 2: 提取人脸框
        face_boxes = self.detector.extract_face_boxes(yolo_results)
        
        # 步骤 3: 对每个检测到的人脸进行识别
        for face_idx, (track_id, box) in enumerate(face_boxes):
            # box 格式: [x1, y1, x2, y2, conf, cls, ...]
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
            conf = box[4] if len(box) > 4 else 1.0
            cls = box[5] if len(box) > 5 else 0.0
            # 裁剪人脸区域
            face = self.detector.crop_face(image, box)
            # 转换为 RGB 格式用于识别
            face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            
            # 人脸识别
            name, distance = self.recognition_system.recognize_face(face_rgb)
            
            # 处理 distance: 如果是 inf，转换为 None（JSON 不支持 inf）
            if distance is not None and math.isinf(distance):
                distance_value = None
            else:
                distance_value = float(distance) if distance is not None else None
            
            # 构建结果
            result = {
                "face_id": face_idx + 1,
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                },
                "name": name if name else "Unknown",
                "confidence": float(conf),
                "distance": distance_value
            }
            
            results.append(result)
        
        return results


def init_cv_system(
    yolo_model_path: Optional[str] = None,
    predictor_path: Optional[str] = None,
    face_rec_model_path: Optional[str] = None,
    db_path: Optional[str] = None,
    known_faces_dir: Optional[str] = None,
    conf_threshold: float = 0.3,
    recognition_threshold: float = 0.5
) -> Tuple[CVSystem, dict]:
    """
    初始化计算机视觉系统
    
    这个函数整合了 face_test.py 中的前3步:
    1. 加载 YOLO 人脸检测模型
    2. 加载人脸识别模型
    3. 从 known_faces 目录批量注册人脸
    
    Args:
        yolo_model_path: YOLO 模型路径
        predictor_path: dlib 关键点检测器路径
        face_rec_model_path: dlib 人脸识别模型路径
        db_path: 人脸向量数据库路径
        known_faces_dir: 已知人脸目录路径
        conf_threshold: YOLO 检测置信度阈值
        recognition_threshold: 人脸识别相似度阈值
        
    Returns:
        (cv_system, init_log): CV系统实例和初始化日志
    """
    
    # 初始化日志
    init_log = {
        "steps": [],
        "success": False,
        "error": None
    }
    
    # 创建 CV 系统实例
    cv_system = CVSystem()
    
    # 设置默认路径
    if yolo_model_path is None:
        yolo_model_path = os.path.join(current_dir, 'yolo', 'model', 'yolov8l-face.pt')
    if predictor_path is None:
        predictor_path = os.path.join(current_dir, 'fr', 'model', 'shape_predictor_68_face_landmarks.dat')
    if face_rec_model_path is None:
        face_rec_model_path = os.path.join(current_dir, 'fr', 'model', 'dlib_face_recognition_resnet_model_v1.dat')
    if db_path is None:
        db_path = os.path.join(current_dir, 'fr', 'face_vectors.pkl')
    if known_faces_dir is None:
        known_faces_dir = os.path.join(current_dir, 'fr', 'known_faces')
    
    try:
        # ========== 步骤 1: 加载 YOLO 人脸检测模型 ==========
        init_log["steps"].append({
            "step": 1,
            "name": "加载 YOLO 人脸检测模型",
            "status": "processing"
        })
        
        try:
            cv_system.detector = YOLOFaceDetector(
                model_path=yolo_model_path,
                conf_threshold=conf_threshold
            )
            init_log["steps"][-1]["status"] = "success"
            init_log["steps"][-1]["message"] = "✓ YOLO 模型加载成功"
            print(f"✓ YOLO 模型加载成功: {yolo_model_path}")
        except Exception as e:
            init_log["steps"][-1]["status"] = "error"
            init_log["steps"][-1]["error"] = str(e)
            init_log["steps"][-1]["message"] = f"✗ YOLO 模型加载失败: {e}"
            print(f"✗ YOLO 模型加载失败: {e}")
            print(f"  请确保模型文件存在于: {yolo_model_path}")
            raise
        
        # ========== 步骤 2: 加载人脸识别模型 ==========
        init_log["steps"].append({
            "step": 2,
            "name": "加载人脸识别模型",
            "status": "processing"
        })
        
        try:
            cv_system.recognizer = FaceRecognizer(
                predictor_path=predictor_path,
                face_rec_model_path=face_rec_model_path
            )
            cv_system.vector_db = FaceVectorDB(
                db_path=db_path,
                threshold=recognition_threshold
            )
            cv_system.recognition_system = FaceRecognitionSystem(
                cv_system.recognizer, 
                cv_system.vector_db
            )
            
            registered_count = len(cv_system.vector_db.list_all())
            registered_names = cv_system.vector_db.list_all()
            
            init_log["steps"][-1]["status"] = "success"
            init_log["steps"][-1]["message"] = f"✓ 人脸识别模型加载成功"
            init_log["steps"][-1]["registered_count"] = registered_count
            init_log["steps"][-1]["registered_names"] = registered_names
            
            print(f"✓ 人脸识别模型加载成功")
            print(f"✓ 当前向量库中有 {registered_count} 个已注册人脸")
            if registered_names:
                print(f"  已注册人员: {', '.join(registered_names)}")
                
        except Exception as e:
            init_log["steps"][-1]["status"] = "error"
            init_log["steps"][-1]["error"] = str(e)
            init_log["steps"][-1]["message"] = f"✗ 人脸识别模型加载失败: {e}"
            print(f"✗ 人脸识别模型加载失败: {e}")
            print(f"  请确保以下模型文件存在:")
            print(f"    - {predictor_path}")
            print(f"    - {face_rec_model_path}")
            raise
        
        # ========== 步骤 3: 批量注册人脸 ==========
        init_log["steps"].append({
            "step": 3,
            "name": "批量注册人脸",
            "status": "processing"
        })
        
        if os.path.exists(known_faces_dir) and os.listdir(known_faces_dir):
            try:
                print(f"✓ 找到人脸注册目录: {known_faces_dir}")
                print(f"  开始批量注册...")
                
                success_count = load_and_register_from_folder(
                    known_faces_dir, 
                    cv_system.recognition_system
                )
                
                total_registered = len(cv_system.vector_db.list_all())
                registered_names = cv_system.vector_db.list_all()
                
                init_log["steps"][-1]["status"] = "success"
                init_log["steps"][-1]["message"] = f"✓ 成功注册 {success_count} 个人脸"
                init_log["steps"][-1]["success_count"] = success_count
                init_log["steps"][-1]["total_registered"] = total_registered
                init_log["steps"][-1]["registered_names"] = registered_names
                
                print(f"✓ 成功注册 {success_count} 个人脸")
                print(f"✓ 当前向量库中共有 {total_registered} 个已注册人脸")
                if registered_names:
                    print(f"  已注册人员: {', '.join(registered_names)}")
                    
            except Exception as e:
                init_log["steps"][-1]["status"] = "warning"
                init_log["steps"][-1]["error"] = str(e)
                init_log["steps"][-1]["message"] = f"⚠ 批量注册失败: {e}"
                print(f"⚠ 批量注册失败: {e}")
        else:
            init_log["steps"][-1]["status"] = "skipped"
            init_log["steps"][-1]["message"] = "ℹ 未找到 known_faces 目录或目录为空，跳过注册"
            
            print(f"ℹ 未找到 known_faces 目录或目录为空，跳过注册")
            if not os.path.exists(known_faces_dir):
                os.makedirs(known_faces_dir)
                print(f"✓ 已创建目录: {known_faces_dir}")
            print(f"  提示: 如需注册人脸，请将照片放入该目录(文件名格式: 姓名.jpg)")
        
        # 初始化成功
        cv_system.is_initialized = True
        init_log["success"] = True
        init_log["message"] = "✓ CV 系统初始化成功"
        print("\n" + "=" * 60)
        print("✓ CV 系统初始化成功")
        print("=" * 60)
        
    except Exception as e:
        init_log["success"] = False
        init_log["error"] = str(e)
        init_log["message"] = f"✗ CV 系统初始化失败: {e}"
        print("\n" + "=" * 60)
        print(f"✗ CV 系统初始化失败: {e}")
        print("=" * 60)
    
    return cv_system, init_log


# 全局 CV 系统实例
_global_cv_system: Optional[CVSystem] = None


def get_cv_system() -> Optional[CVSystem]:
    """获取全局 CV 系统实例"""
    return _global_cv_system


def set_cv_system(cv_system: CVSystem):
    """设置全局 CV 系统实例"""
    global _global_cv_system
    _global_cv_system = cv_system


def ensure_cv_system_initialized() -> CVSystem:
    """
    确保 CV 系统已初始化，如果未初始化则自动初始化
    
    Returns:
        CV 系统实例
        
    Raises:
        RuntimeError: 如果初始化失败
    """
    global _global_cv_system
    
    if _global_cv_system is None or not _global_cv_system.is_initialized:
        print("CV 系统未初始化，正在自动初始化...")
        _global_cv_system, init_log = init_cv_system()
        
        if not init_log["success"]:
            raise RuntimeError(f"CV 系统初始化失败: {init_log.get('error', '未知错误')}")
    
    return _global_cv_system


if __name__ == "__main__":
    """测试初始化和识别功能"""
    import cv2
    
    print("=" * 60)
    print("测试 CV 系统初始化和识别")
    print("=" * 60)
    
    # 初始化系统
    cv_system, init_log = init_cv_system()
    
    # 打印初始化日志
    print("\n初始化日志:")
    print(f"成功: {init_log['success']}")
    for step in init_log["steps"]:
        print(f"  步骤 {step['step']}: {step['name']} - {step['status']}")
        if "message" in step:
            print(f"    {step['message']}")
    
    # 打印系统状态
    print("\n系统状态:")
    status = cv_system.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # 测试识别功能
    if init_log["success"]:
        print("\n" + "=" * 60)
        print("测试人脸识别功能")
        print("=" * 60)
        
        # 查找测试图片
        test_faces_dir = os.path.join(current_dir, "test", "test_faces")
        if os.path.exists(test_faces_dir):
            test_images = [f for f in os.listdir(test_faces_dir) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            
            if test_images:
                # 测试第一张图片
                test_image_path = os.path.join(test_faces_dir, test_images[0])
                print(f"\n测试图片: {test_images[0]}")
                
                # 读取图片
                image = cv2.imread(test_image_path)
                if image is not None:
                    print(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")
                    
                    # 调用识别函数
                    results = cv_system.recognize_faces_in_image(image)
                    
                    # 打印结果
                    print(f"\n检测到 {len(results)} 张人脸:")
                    for result in results:
                        print(f"\n  人脸 #{result['face_id']}:")
                        print(f"    位置: ({result['bbox']['x1']}, {result['bbox']['y1']}) -> ({result['bbox']['x2']}, {result['bbox']['y2']})")
                        print(f"    识别结果: {result['name']}")
                        print(f"    检测置信度: {result['confidence']:.2f}")
                        if result['distance'] is not None:
                            print(f"    特征距离: {result['distance']:.4f}")
                else:
                    print("  ✗ 无法读取图片")
            else:
                print(f"\n  ℹ 测试目录中没有图片: {test_faces_dir}")
        else:
            print(f"\n  ℹ 测试目录不存在: {test_faces_dir}")
    
    print("\n" + "=" * 60)

