#!/usr/bin/env python3
"""
测试 DashScope 视频上传大小限制
"""

import os
import base64
import requests
import json

api_key = "sk-b70f29eb4e674f13ba76375625d3887a"

# 测试不同大小的视频
for size_mb in [1, 5, 10, 20]:
    print(f"\n测试 {size_mb}MB...")
    
    # 创建测试数据
    test_data = b'\x00' * (size_mb * 1024 * 1024)
    base64_data = base64.b64encode(test_data).decode('utf-8')
    
    print(f"Base64 大小: {len(base64_data)/1024/1024:.1f}MB")
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-omni-turbo",
        "input": {
            "messages": [
                {"role": "user", "content": [{"type": "video", "video": f"data:video/mp4;base64,{base64_data}"}, {"type": "text", "text": "test"}]}
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"错误: {response.text[:200]}")
    except Exception as e:
        print(f"异常: {e}")
