#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISO 锐度归一化 A/B 测试脚本

用途：对比修改算法前后对同一批照片的锐度和星级变化
"""

import os
import sys
import subprocess
import math
import cv2
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Note: We don't need to import core modules for this simple test
# The test uses standalone sharpness calculation

# ============ ISO 归一化配置 ============
BASE_ISO = 800          # 基准 ISO（此值及以下不惩罚）
PENALTY_FACTOR = 0.05   # 每翻一倍 ISO 扣 5%
MIN_FACTOR = 0.5        # 最低系数（最多扣 50%）

def get_iso_factor(iso_value: int) -> float:
    """计算 ISO 归一化系数"""
    if iso_value is None or iso_value <= BASE_ISO:
        return 1.0
    
    # penalty = 0.05 * log₂(ISO / 800)
    penalty = PENALTY_FACTOR * math.log2(iso_value / BASE_ISO)
    factor = max(MIN_FACTOR, 1.0 - penalty)
    return factor

def read_iso(filepath: str) -> int:
    """从 EXIF 读取 ISO 值"""
    try:
        result = subprocess.run(
            ['exiftool', '-ISO', '-s', '-s', '-s', filepath],
            capture_output=True, text=True, timeout=5
        )
        iso_str = result.stdout.strip()
        if iso_str:
            return int(iso_str)
    except Exception as e:
        pass
    return None

def calculate_sharpness_tenengrad(image: np.ndarray, mask: np.ndarray = None) -> float:
    """
    计算锐度（复制自 keypoint_detector.py）
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Tenengrad 算子
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = gx ** 2 + gy ** 2
    
    if mask is not None and mask.sum() > 0:
        mask_pixels = mask > 0
        raw_sharpness = float(gradient_magnitude[mask_pixels].mean())
    else:
        raw_sharpness = float(gradient_magnitude.mean())
    
    # 对数归一化到 0-1000
    MIN_VAL = 100.0
    MAX_VAL = 154016.0
    
    if raw_sharpness <= MIN_VAL:
        return 0.0
    if raw_sharpness >= MAX_VAL:
        return 1000.0
    
    log_val = math.log(raw_sharpness) - math.log(MIN_VAL)
    log_max = math.log(MAX_VAL) - math.log(MIN_VAL)
    
    return (log_val / log_max) * 1000.0

def get_star_rating(sharpness: float, threshold: float = 400) -> int:
    """简化版星级判定（仅基于锐度）"""
    if sharpness >= threshold:
        return 3
    elif sharpness >= threshold * 0.7:
        return 2
    elif sharpness >= threshold * 0.4:
        return 1
    else:
        return 0

def run_ab_test(test_dir: str, sharpness_threshold: float = 400):
    """
    运行 A/B 测试
    
    Args:
        test_dir: 测试图片目录
        sharpness_threshold: 3星锐度阈值
    """
    print(f"\n{'='*80}")
    print(f"ISO 锐度归一化 A/B 测试")
    print(f"测试目录: {test_dir}")
    print(f"基准 ISO: {BASE_ISO}")
    print(f"惩罚系数: 每翻一倍 ISO 扣 {PENALTY_FACTOR*100:.0f}%")
    print(f"锐度阈值: {sharpness_threshold}")
    print(f"{'='*80}\n")
    
    # 支持的图片格式
    extensions = {'.jpg', '.jpeg', '.nef', '.arw', '.cr3', '.cr2', '.raf', '.orf', '.rw2'}
    
    # 收集测试文件
    test_files = []
    for f in os.listdir(test_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in extensions:
            test_files.append(os.path.join(test_dir, f))
    
    if not test_files:
        print(f"❌ 目录中没有找到图片文件")
        return
    
    print(f"找到 {len(test_files)} 个测试文件\n")
    
    # 结果表格
    results = []
    
    for filepath in sorted(test_files):
        filename = os.path.basename(filepath)
        
        # 读取 ISO
        iso = read_iso(filepath)
        iso_str = str(iso) if iso else "N/A"
        
        # 读取图片（如果是 RAW 需要转换）
        ext = os.path.splitext(filepath)[1].lower()
        if ext in {'.nef', '.arw', '.cr3', '.cr2', '.raf', '.orf', '.rw2'}:
            # 尝试找对应的 JPEG
            base = os.path.splitext(filepath)[0]
            jpeg_path = None
            for je in ['.jpg', '.jpeg', '.JPG', '.JPEG']:
                if os.path.exists(base + je):
                    jpeg_path = base + je
                    break
            
            if jpeg_path:
                img = cv2.imread(jpeg_path)
            else:
                print(f"  ⚠️ {filename}: 无对应 JPEG，跳过")
                continue
        else:
            img = cv2.imread(filepath)
        
        if img is None:
            print(f"  ⚠️ {filename}: 无法读取图片")
            continue
        
        # 计算原始锐度（全图）
        original_sharpness = calculate_sharpness_tenengrad(img)
        
        # 计算 ISO 归一化系数
        iso_factor = get_iso_factor(iso) if iso else 1.0
        
        # 计算归一化后锐度
        normalized_sharpness = original_sharpness * iso_factor
        
        # 计算星级
        original_star = get_star_rating(original_sharpness, sharpness_threshold)
        new_star = get_star_rating(normalized_sharpness, sharpness_threshold)
        
        # 变化标记
        if new_star < original_star:
            change = f"⬇️ {original_star}→{new_star}"
        elif new_star > original_star:
            change = f"⬆️ {original_star}→{new_star}"
        else:
            change = "无变化"
        
        results.append({
            'filename': filename,
            'iso': iso_str,
            'original_sharpness': original_sharpness,
            'iso_factor': iso_factor,
            'normalized_sharpness': normalized_sharpness,
            'original_star': original_star,
            'new_star': new_star,
            'change': change
        })
    
    # 输出结果表格
    print(f"\n{'='*100}")
    print(f"{'文件名':<30} {'ISO':>8} {'原锐度':>10} {'系数':>8} {'新锐度':>10} {'原星级':>6} {'新星级':>6} {'变化':>12}")
    print(f"{'='*100}")
    
    for r in results:
        print(f"{r['filename']:<30} {r['iso']:>8} {r['original_sharpness']:>10.1f} {r['iso_factor']:>8.2f} {r['normalized_sharpness']:>10.1f} {r['original_star']:>6}★ {r['new_star']:>6}★ {r['change']:>12}")
    
    print(f"{'='*100}")
    
    # 统计
    downgrades = sum(1 for r in results if r['new_star'] < r['original_star'])
    upgrades = sum(1 for r in results if r['new_star'] > r['original_star'])
    unchanged = sum(1 for r in results if r['new_star'] == r['original_star'])
    
    print(f"\n📊 统计:")
    print(f"  - 降级: {downgrades} 张")
    print(f"  - 升级: {upgrades} 张")
    print(f"  - 无变化: {unchanged} 张")
    print(f"  - 总计: {len(results)} 张")


if __name__ == '__main__':
    # 默认测试目录
    default_dir = "/Users/jameszhenyu/Downloads/佳能测试/focus_test"
    
    if len(sys.argv) > 1:
        test_dir = sys.argv[1]
    else:
        test_dir = default_dir
    
    if not os.path.isdir(test_dir):
        print(f"❌ 目录不存在: {test_dir}")
        sys.exit(1)
    
    run_ab_test(test_dir)
