#!/usr/bin/env python3
"""
阿里云 DashScope ASR - 使用 Qwen-Omni 模型

使用通义千问多模态模型进行视频音频转写
API文档: https://help.aliyun.com/document_detail/2712543.html

配置:
    export DASHSCOPE_API_KEY=sk-b70f29eb4e674f13ba76375625d3887a
"""

import os
import sys
import json
import requests

def transcribe_video(file_url: str, model: str = "qwen-omni-turbo") -> dict:
    """
    使用 DashScope Qwen-Omni 模型转写视频
    
    Args:
        file_url: 视频/音频 URL（需要公网可访问）
        model: 模型名称
    
    Returns:
        dict: {success, transcript, duration, cost, error}
    """
    
    api_key = os.environ.get('DASHSCOPE_API_KEY') or "sk-b70f29eb4e674f13ba76375625d3887a"
    
    if not api_key:
        return {
            'success': False,
            'error': 'DASHSCOPE_API_KEY not set'
        }
    
    try:
        print(f"🚀 调用 DashScope {model}...")
        print(f"   URL: {file_url[:60]}...")
        
        # DashScope API endpoint
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Qwen-Omni 请求格式
        # 参考: https://help.aliyun.com/document_detail/2712543.html
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个语音识别助手。请将音频内容转写为中文文本。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio",  # 音频输入
                                "audio": file_url
                            },
                            {
                                "type": "text",
                                "text": "请转写这段音频内容，输出纯文本。"
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }
        
        # 如果URL是视频，使用video类型
        if any(ext in file_url.lower() for ext in ['.mp4', '.mov', '.avi', '.webm']):
            payload["input"]["messages"][1]["content"][0]["type"] = "video"
            payload["input"]["messages"][1]["content"][0]["video"] = file_url
            del payload["input"]["messages"][1]["content"][0]["audio"]
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text[:500]
            print(f"❌ API error: {error_text}")
            return {
                'success': False,
                'error': f'API error {response.status_code}: {error_text}'
            }
        
        result = response.json()
        print(f"📦 Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
        
        # 解析响应
        if result.get('output') and result['output'].get('choices'):
            choice = result['output']['choices'][0]
            message = choice.get('message', {})
            content = message.get('content', '')
            
            # 提取文本
            transcript = ""
            if isinstance(content, str):
                transcript = content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        # 处理 {"text": "..."} 格式
                        if 'text' in item:
                            transcript += item['text']
            
            # 获取用量
            usage = result.get('usage', {})
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            
            # 费用估算 (qwen-omni-turbo)
            # 输入: ¥0.003/1K tokens, 输出: ¥0.006/1K tokens
            cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.006)
            
            return {
                'success': True,
                'transcript': transcript.strip(),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': round(cost, 4),
                'model': model
            }
        else:
            return {
                'success': False,
                'error': f'No output in response: {result}'
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Exception: {str(e)}'
        }


def test_with_sample():
    """使用测试音频URL测试"""
    # 使用一个公开的测试音频
    test_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world.wav"
    
    print("="*50)
    print("🧪 使用测试音频测试 DashScope API")
    print("="*50)
    
    result = transcribe_video(test_url, "qwen-omni-turbo")
    
    print("\n" + "="*50)
    if result['success']:
        print(f"✅ 测试成功!")
        print(f"模型: {result.get('model')}")
        print(f"Token: {result.get('input_tokens', 0)} in / {result.get('output_tokens', 0)} out")
        print(f"费用: ¥{result.get('cost', 0)}")
        print(f"\n📝 转写结果:\n{result['transcript']}")
    else:
        print(f"❌ 测试失败: {result['error']}")
    
    return result


def main():
    """主函数"""
    file_url = sys.argv[1] if len(sys.argv) > 1 else None
    # 使用用户指定的模型，或默认 qwen-omni-turbo
    model = sys.argv[2] if len(sys.argv) > 2 else "qwen3-omni-30b-a3b-captioner"
    
    # 使用内置 API Key
    if not os.environ.get('DASHSCOPE_API_KEY'):
        os.environ['DASHSCOPE_API_KEY'] = "sk-b70f29eb4e674f13ba76375625d3887a"
        print("💡 使用内置 API Key")
    
    if not file_url or file_url == "test":
        # 运行测试
        result = test_with_sample()
    else:
        # 转写指定URL
        result = transcribe_video(file_url, model)
        
        print("\n" + "="*50)
        if result['success']:
            print(f"✅ 转写成功")
            print(f"模型: {result.get('model')}")
            print(f"Token: {result.get('input_tokens', 0)} in / {result.get('output_tokens', 0)} out")
            print(f"费用: ¥{result.get('cost', 0)}")
            print(f"\n📝 转写结果:\n{result['transcript'][:500]}...")
        else:
            print(f"❌ 转写失败: {result['error']}")
    
    print("\n===JSON_START===")
    print(json.dumps(result, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == '__main__':
    main()
