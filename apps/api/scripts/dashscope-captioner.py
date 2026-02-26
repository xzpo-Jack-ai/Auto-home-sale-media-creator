#!/usr/bin/env python3
"""
阿里云 DashScope - 使用 Qwen3-Omni Captioner 模型

专用模型: qwen3-omni-30b-a3b-captioner
用于视频字幕生成
"""

import os
import sys
import json
import requests

def caption_video(video_url: str) -> dict:
    """
    使用 Qwen3-Omni Captioner 生成视频字幕
    
    Args:
        video_url: 视频 URL
    
    Returns:
        dict: {success, transcript, cost, error}
    """
    
    api_key = os.environ.get('DASHSCOPE_API_KEY') or "sk-b70f29eb4e674f13ba76375625d3887a"
    model = "qwen3-omni-30b-a3b-captioner"
    
    if not api_key:
        return {'success': False, 'error': 'DASHSCOPE_API_KEY not set'}
    
    try:
        print(f"🚀 调用 DashScope {model}...")
        print(f"   视频: {video_url[:60]}...")
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Captioner 模型专用格式
        payload = {
            "model": model,
            "input": {
                "prompt": "请为这段视频生成字幕，转写其中的语音内容。",
                "media": {
                    "type": "video",
                    "url": video_url
                }
            },
            "parameters": {
                "result_format": "text",
                "use_raw_prompt": True
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text[:500]
            return {
                'success': False,
                'error': f'API error {response.status_code}: {error_text}'
            }
        
        result = response.json()
        print(f"📦 Response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        
        # 解析响应
        output = result.get('output', {})
        text = output.get('text', '')
        
        usage = result.get('usage', {})
        cost = usage.get('total_tokens', 0) / 1000 * 0.01  # 估算费用
        
        return {
            'success': bool(text),
            'transcript': text.strip(),
            'cost': round(cost, 4),
            'model': model
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Exception: {str(e)}'}


def main():
    video_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not video_url:
        print("用法: python3 dashscope-captioner.py <视频URL>")
        sys.exit(1)
    
    if not os.environ.get('DASHSCOPE_API_KEY'):
        os.environ['DASHSCOPE_API_KEY'] = "sk-b70f29eb4e674f13ba76375625d3887a"
    
    result = caption_video(video_url)
    
    print("\n" + "="*50)
    if result['success']:
        print(f"✅ 字幕生成成功")
        print(f"费用: ¥{result['cost']}")
        print(f"\n📝 字幕:\n{result['transcript']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    print("\n===JSON_START===")
    print(json.dumps(result, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == '__main__':
    main()
