#!/usr/bin/env python3
"""调试 ASR 问题"""

import os
import base64
import requests

api_key = "sk-b70f29eb4e674f13ba76375625d3887a"

# 使用已知的音频文件测试
audio_path = "/tmp/test_audio.mp3"

# 先创建一个小的测试音频（如果存在）
if not os.path.exists(audio_path):
    print("创建测试音频...")
    import subprocess
    subprocess.run([
        'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=5',
        '-acodec', 'libmp3lame', audio_path, '-y'
    ], capture_output=True)

print(f"测试音频: {audio_path}")
print(f"音频大小: {os.path.getsize(audio_path)} bytes")

with open(audio_path, 'rb') as f:
    audio_data = f.read()
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

print(f"Base64 长度: {len(audio_base64)}")

url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "qwen-omni-turbo",
    "input": {
        "messages": [
            {"role": "system", "content": "语音识别助手"},
            {"role": "user", "content": [
                {"type": "audio", "audio": f"data:audio/mp3;base64,{audio_base64}"},
                {"type": "text", "text": "转写这段音频"}
            ]}
        ]
    }
}

print("\n发送请求...")
response = requests.post(url, headers=headers, json=payload, timeout=30)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:500]}")
