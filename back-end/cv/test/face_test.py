"""
人脸识别测试脚本
从 test_faces/ 目录读取图片，使用YOLO检测和dlib识别人脸，并打印识别结果
"""

import sys
import os
import cv2

# 添加父目录到路径以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from yolo.yolo import YOLOFaceDetector
from fr.fr import FaceRecognizer, FaceVectorDB, FaceRecognitionSystem, load_and_register_from_folder


def test_face_recognition():
    """测试人脸识别功能"""
    
    print("=" * 60)
    print("人脸识别测试程序")
    print("=" * 60)
    
    # 1. 初始化YOLO检测器
    print("\n[1/4] 加载YOLO人脸检测模型...")
    try:
        # 使用相对于项目根目录的路径
        yolo_model_path = os.path.join(parent_dir,'yolo', 'model', 'yolov8l-face.pt')
        detector = YOLOFaceDetector(
            model_path=yolo_model_path,
            conf_threshold=0.3
        )
        print("✓ YOLO模型加载成功")
    except Exception as e:
        print(f"✗ YOLO模型加载失败: {e}")
        print(f"  请确保模型文件存在于: {os.path.join(parent_dir, 'yolo', 'model', 'yolov8l-face.pt')}")
        return
    
    # 2. 初始化人脸识别系统
    print("\n[2/4] 加载人脸识别模型...")
    try:
        # 使用相对于项目根目录的路径
        predictor_path = os.path.join(parent_dir, 'fr', 'model', 'shape_predictor_68_face_landmarks.dat')
        face_rec_path = os.path.join(parent_dir, 'fr', 'model', 'dlib_face_recognition_resnet_model_v1.dat')
        db_path = os.path.join(parent_dir, 'fr', 'face_vectors.pkl')
        
        recognizer = FaceRecognizer(
            predictor_path=predictor_path,
            face_rec_model_path=face_rec_path
        )
        vector_db = FaceVectorDB(
            db_path=db_path,
            threshold=0.3
        )
        recognition_system = FaceRecognitionSystem(recognizer, vector_db)
        print("✓ 人脸识别模型加载成功")
        print(f"✓ 当前向量库中有 {len(vector_db.list_all())} 个已注册人脸")
        if vector_db.list_all():
            print(f"  已注册人员: {', '.join(vector_db.list_all())}")
    except Exception as e:
        print(f"✗ 人脸识别模型加载失败: {e}")
        print(f"  请确保以下模型文件存在:")
        print(f"    - {predictor_path}")
        print(f"    - {face_rec_path}")
        return
    
    # 3. 注册人脸(从 known_faces 目录批量注册)
    known_faces_dir = os.path.join(parent_dir, "fr", "known_faces")
    print(f"\n[3/5] 检查人脸注册目录: {known_faces_dir}")
    
    if os.path.exists(known_faces_dir) and os.listdir(known_faces_dir):
        print(f"✓ 找到人脸注册目录，开始批量注册...")
        try:
            success_count = load_and_register_from_folder(known_faces_dir, recognition_system)
            print(f"✓ 成功注册 {success_count} 个人脸")
            print(f"✓ 当前向量库中共有 {len(vector_db.list_all())} 个已注册人脸")
            if vector_db.list_all():
                print(f"  已注册人员: {', '.join(vector_db.list_all())}")
        except Exception as e:
            print(f"✗ 批量注册失败: {e}")
    else:
        print(f"ℹ 未找到 known_faces 目录或目录为空，跳过注册")
        if not os.path.exists(known_faces_dir):
            os.makedirs(known_faces_dir)
            print(f"✓ 已创建目录: {known_faces_dir}")
        print(f"  提示: 如需注册人脸，请将照片放入该目录(文件名格式: 姓名.jpg)")
    
    # 4. 读取测试图片
    test_faces_dir = os.path.join(current_dir, "test_faces")
    print(f"\n[4/5] 读取测试图片目录: {test_faces_dir}")
    
    if not os.path.exists(test_faces_dir):
        print(f"✗ 测试图片目录不存在，正在创建...")
        os.makedirs(test_faces_dir)
        print(f"✓ 已创建目录，请将测试图片放入: {test_faces_dir}")
        return
    
    # 获取所有图片文件
    image_files = []
    for filename in os.listdir(test_faces_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            image_files.append(filename)
    
    if not image_files:
        print(f"✗ 目录中没有找到图片文件 (支持格式: jpg, jpeg, png, bmp)")
        print(f"  请将测试图片放入: {test_faces_dir}")
        return
    
    print(f"✓ 找到 {len(image_files)} 张测试图片")
    
    # 5. 处理每张图片
    print(f"\n[5/5] 开始识别人脸...")
    print("=" * 60)
    
    total_faces = 0
    recognized_faces = 0
    
    for idx, filename in enumerate(image_files, 1):
        image_path = os.path.join(test_faces_dir, filename)
        print(f"\n[{idx}/{len(image_files)}] 处理图片: {filename}")
        
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ✗ 无法读取图片")
            continue
        
        print(f"  图片尺寸: {image.shape[1]}x{image.shape[0]}")
        
        # YOLO检测人脸
        results = detector.detect_faces(image, persist=False)
        
        if not detector.has_faces(results):
            print(f"  ✗ 未检测到人脸")
            continue
        
        # 提取人脸框
        face_boxes = detector.extract_face_boxes(results)
        print(f"  ✓ 检测到 {len(face_boxes)} 张人脸")
        
        # 对每个检测到的人脸进行识别
        for face_idx, (track_id, box) in enumerate(face_boxes, 1):
            total_faces += 1
            
            # 裁剪人脸区域
            face = detector.crop_face(image, box)
            
            # 转换为RGB格式用于识别
            face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            
            # 人脸识别
            name, distance = recognition_system.recognize_face(face_rgb)
            
            # 打印识别结果
            if name:
                recognized_faces += 1
                print(f"  ✓ 人脸 #{face_idx}: 【{name}】 (相似度距离: {distance:.4f})")
            else:
                print(f"  ✗ 人脸 #{face_idx}: 【未识别】 (距离: {distance:.4f}, 阈值: {vector_db.threshold})")
    
    # 6. 统计结果
    print("\n" + "=" * 60)
    print("识别结果统计")
    print("=" * 60)
    print(f"处理图片数: {len(image_files)}")
    print(f"检测到的人脸总数: {total_faces}")
    print(f"成功识别的人脸数: {recognized_faces}")
    if total_faces > 0:
        print(f"识别成功率: {recognized_faces/total_faces*100:.1f}%")
    print("=" * 60)


def main():
    """主函数"""
    try:
        test_face_recognition()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n✗ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

