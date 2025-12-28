#!/usr/bin/env python3
"""
可视化测试：对比整图 vs 裁剪区域的关键点检测结果
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_model import load_yolo_model, preprocess_image
from core.keypoint_detector import KeypointDetector
from config import config

def run_comparison(image_dir: str, output_dir: str, num_images: int = 10):
    """
    对比整图和裁剪区域的关键点检测结果
    
    Args:
        image_dir: 图片目录
        output_dir: 输出目录
        num_images: 测试图片数量
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载模型
    print("🤖 加载YOLO模型...")
    yolo_model = load_yolo_model()
    
    print("👁️  加载关键点模型...")
    kp_detector = KeypointDetector()
    kp_detector.load_model()
    
    # 查找JPG文件
    jpg_files = list(Path(image_dir).glob("*.jpg")) + list(Path(image_dir).glob("*.JPG"))
    jpg_files = sorted(jpg_files)[:num_images]
    
    print(f"📁 找到 {len(jpg_files)} 个测试文件\n")
    
    results_summary = []
    
    for i, jpg_path in enumerate(jpg_files, 1):
        print(f"[{i}/{len(jpg_files)}] {jpg_path.name}")
        
        # 读取原图
        img = cv2.imread(str(jpg_path))
        if img is None:
            continue
        
        h_orig, w_orig = img.shape[:2]
        
        # YOLO检测
        img_resized = preprocess_image(str(jpg_path))
        h_resized, w_resized = img_resized.shape[:2]
        
        results = yolo_model(img_resized, device='mps', verbose=False)
        detections = results[0].boxes.xyxy.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy()
        
        # 找最大的鸟
        bird_idx = -1
        max_area = 0
        for idx, (det, conf, cls) in enumerate(zip(detections, confidences, class_ids)):
            if int(cls) == config.ai.BIRD_CLASS_ID:
                x1, y1, x2, y2 = det
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    max_area = area
                    bird_idx = idx
        
        if bird_idx == -1:
            print("  ❌ 无鸟")
            continue
        
        # 获取bbox (在resized图上)
        x1, y1, x2, y2 = detections[bird_idx]
        x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
        
        # 缩放到原图尺寸
        scale_x = w_orig / w_resized
        scale_y = h_orig / h_resized
        x_orig = int(x * scale_x)
        y_orig = int(y * scale_y)
        w_orig_box = int(w * scale_x)
        h_orig_box = int(h * scale_y)
        
        # 确保边界有效
        x_orig = max(0, min(x_orig, w_orig - 1))
        y_orig = max(0, min(y_orig, h_orig - 1))
        w_orig_box = min(w_orig_box, w_orig - x_orig)
        h_orig_box = min(h_orig_box, h_orig - y_orig)
        
        # ===== 测试1: 整图关键点检测 =====
        img_rgb_full = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        kp_full = kp_detector.detect(img_rgb_full)
        
        # ===== 测试2: 裁剪区域关键点检测 =====
        crop = img[y_orig:y_orig+h_orig_box, x_orig:x_orig+w_orig_box]
        img_rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        kp_crop = kp_detector.detect(img_rgb_crop)
        
        # ===== 可视化 =====
        # 创建对比图
        vis_full = img.copy()
        vis_crop = crop.copy()
        
        def draw_keypoints(image, kp_result, label_prefix=""):
            """在图像上绘制关键点"""
            if kp_result is None:
                return
            
            h, w = image.shape[:2]
            
            # 左眼 (蓝色)
            lx, ly = int(kp_result.left_eye[0] * w), int(kp_result.left_eye[1] * h)
            vis_conf = kp_result.left_eye_vis
            color = (255, 0, 0) if vis_conf >= 0.5 else (100, 100, 100)
            cv2.circle(image, (lx, ly), 8, color, -1)
            cv2.putText(image, f"L:{vis_conf:.2f}", (lx+10, ly), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 右眼 (绿色)
            rx, ry = int(kp_result.right_eye[0] * w), int(kp_result.right_eye[1] * h)
            vis_conf = kp_result.right_eye_vis
            color = (0, 255, 0) if vis_conf >= 0.5 else (100, 100, 100)
            cv2.circle(image, (rx, ry), 8, color, -1)
            cv2.putText(image, f"R:{vis_conf:.2f}", (rx+10, ry), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 喙 (红色)
            bx, by = int(kp_result.beak[0] * w), int(kp_result.beak[1] * h)
            vis_conf = kp_result.beak_vis
            color = (0, 0, 255) if vis_conf >= 0.5 else (100, 100, 100)
            cv2.circle(image, (bx, by), 8, color, -1)
            cv2.putText(image, f"B:{vis_conf:.2f}", (bx+10, by), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 在整图上绘制
        draw_keypoints(vis_full, kp_full)
        # 绘制bbox
        cv2.rectangle(vis_full, (x_orig, y_orig), 
                     (x_orig + w_orig_box, y_orig + h_orig_box), (0, 255, 255), 3)
        
        # 添加标签
        cv2.putText(vis_full, f"FULL IMAGE - Eyes Hidden: {kp_full.both_eyes_hidden if kp_full else 'N/A'}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # 在裁剪图上绘制
        draw_keypoints(vis_crop, kp_crop)
        cv2.putText(vis_crop, f"CROP - Eyes Hidden: {kp_crop.both_eyes_hidden if kp_crop else 'N/A'}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 调整裁剪图大小以便并排显示
        target_h = 600
        scale_full = target_h / vis_full.shape[0]
        scale_crop = target_h / vis_crop.shape[0]
        
        vis_full_resized = cv2.resize(vis_full, None, fx=scale_full, fy=scale_full)
        vis_crop_resized = cv2.resize(vis_crop, None, fx=scale_crop, fy=scale_crop)
        
        # 创建并排对比图
        combined = np.hstack([vis_full_resized, vis_crop_resized])
        
        # 保存
        output_path = os.path.join(output_dir, f"compare_{jpg_path.stem}.jpg")
        cv2.imwrite(output_path, combined)
        
        # 记录结果
        full_hidden = kp_full.both_eyes_hidden if kp_full else True
        crop_hidden = kp_crop.both_eyes_hidden if kp_crop else True
        
        result = {
            'file': jpg_path.name,
            'full_left_vis': f"{kp_full.left_eye_vis:.2f}" if kp_full else "-",
            'full_right_vis': f"{kp_full.right_eye_vis:.2f}" if kp_full else "-",
            'full_hidden': full_hidden,
            'crop_left_vis': f"{kp_crop.left_eye_vis:.2f}" if kp_crop else "-",
            'crop_right_vis': f"{kp_crop.right_eye_vis:.2f}" if kp_crop else "-",
            'crop_hidden': crop_hidden,
            'match': full_hidden == crop_hidden
        }
        results_summary.append(result)
        
        full_status = "✅" if not full_hidden else "❌"
        crop_status = "✅" if not crop_hidden else "❌"
        match_status = "✓" if result['match'] else "✗ DIFF"
        
        print(f"  整图: L={result['full_left_vis']} R={result['full_right_vis']} {full_status}")
        print(f"  裁剪: L={result['crop_left_vis']} R={result['crop_right_vis']} {crop_status}")
        print(f"  匹配: {match_status}")
        print(f"  保存: {output_path}")
        print()
    
    # 统计
    print("\n" + "=" * 60)
    print("📊 统计摘要")
    print("=" * 60)
    
    total = len(results_summary)
    full_visible = sum(1 for r in results_summary if not r['full_hidden'])
    crop_visible = sum(1 for r in results_summary if not r['crop_hidden'])
    matches = sum(1 for r in results_summary if r['match'])
    
    print(f"总测试数: {total}")
    print(f"整图检测眼睛可见: {full_visible} ({full_visible/total*100:.1f}%)")
    print(f"裁剪检测眼睛可见: {crop_visible} ({crop_visible/total*100:.1f}%)")
    print(f"结果一致: {matches} ({matches/total*100:.1f}%)")
    print(f"\n输出目录: {output_dir}")


if __name__ == "__main__":
    # 使用测试目录的前10张图片
    image_dir = "/Users/jameszhenyu/Desktop/2025-10-18"
    output_dir = "/Users/jameszhenyu/Desktop/keypoint_comparison"
    
    run_comparison(image_dir, output_dir, num_images=10)
