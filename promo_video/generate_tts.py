#!/usr/bin/env python3
"""批量生成 TTS 语音"""

import requests
import base64
import os

API_URL = "http://localhost:8765/qwen3/tts"
OUTPUT_DIR = "/Users/jameszhenyu/Documents/JamesAPPS/SuperPicky2026/promo_video/audio"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# TTS 文案段落 - v4 最终版本
segments = [
    ("01_hook", "拍片一时爽，选片火葬场"),
    ("02_problem", "拍了一天鸟，回来8000张照片，哪张最锐？眼睛都看花了"),
    ("03_solution", "让AI帮你，3分钟全部搞定"),
    ("04_feature1", "自动检测鸟眼位置，锐度不够的直接淘汰"),
    ("05_feature2", "还能识别鸟的种类，自动写入照片信息"),
    ("06_feature3", "飞版照片单独标记，想找飞版一秒筛出来"),
    ("07_feature4", "按质量自动分成0到3星，精品照片一目了然"),
    ("08_result", "从此选片不头疼，张张都是能打的"),
    ("09_platform", "苹果电脑、Windows都能用"),
    ("10_free", "真开源、真免费，没有VIP、不要会员、绝对没套路"),
    ("11_cta", "搜索 SuperPicky 慧眼选鸟，从此拍鸟无烦恼！"),
]

def generate_tts(filename, text):
    """调用 TTS API 生成语音"""
    payload = {
        "text": text,
        "language": "Chinese",
        "speaker": "Eric",  # 四川方言男声
        "output_format": "wav"
    }

    print(f"生成: {filename} - {text}")

    response = requests.post(API_URL, json=payload)
    result = response.json()

    if result.get("success"):
        # 解码 base64 音频并保存
        audio_data = base64.b64decode(result["audio_base64"])
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.wav")
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"  ✓ 已保存: {output_path} (时长: {result.get('duration', 0):.2f}秒)")
        return result.get("duration", 0)
    else:
        print(f"  ✗ 失败: {result.get('message', 'Unknown error')}")
        return 0

if __name__ == "__main__":
    total_duration = 0

    print("=" * 50)
    print("开始生成 TTS 语音")
    print("=" * 50)

    for filename, text in segments:
        duration = generate_tts(filename, text)
        total_duration += duration

    print("=" * 50)
    print(f"完成! 总时长: {total_duration:.2f}秒")
    print(f"音频文件保存在: {OUTPUT_DIR}")
    print("=" * 50)
