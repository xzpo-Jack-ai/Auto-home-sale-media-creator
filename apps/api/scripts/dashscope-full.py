#!/usr/bin/env python3
"""
阿里云 DashScope ASR - 完整流程
1. yt-dlp 下载视频
2. DashScope ASR 转写
"""

import os
import sys
import json
import tempfile
import subprocess
import requests

def download_and_transcribe(video_url: str, cookies_path: str = None) -> dict:
    """
    下载视频并使用 DashScope ASR 转写
    """
    
    api_key = os.environ.get('DASHSCOPE_API_KEY') or "sk-b70f29eb4e674f13ba76375625d3887a"
    
    if not api_key:
        return {'success': False, 'error': 'DASHSCOPE_API_KEY not set'}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, 'video.mp4')
        
        # 步骤1: 下载视频
        print(f"⬇️  下载视频...")
        try:
            cmd = ['yt-dlp', '-f', 'best[height<=720]', '-o', video_path]
            if cookies_path and os.path.exists(cookies_path):
                cmd.extend(['--cookies', cookies_path])
            else:
                cmd.extend(['--cookies-from-browser', 'chrome'])
            cmd.extend(['--no-warnings', '-q', video_url])
            
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            
            # 找到下载的文件
            downloaded = None
            for ext in ['.mp4', '.webm', '.mov']:
                if os.path.exists(video_path + ext):
                    downloaded = video_path + ext
                    break
            
            if not downloaded:
                return {'success': False, 'error': '视频下载失败'}
            
            file_size = os.path.getsize(downloaded)
            print(f"✅ 视频已下载: {file_size/1024/1024:.1f}MB")
            
            if file_size < 10000:
                return {'success': False, 'error': '视频文件太小'}
                
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else ''
            if 'cookie' in stderr.lower() or 'sign' in stderr.lower():
                return {'success': False, 'error': 'Cookies 失效，请重新登录抖音'}
            return {'success': False, 'error': f'下载失败: {stderr[:200]}'}
        except Exception as e:
            return {'success': False, 'error': f'下载异常: {str(e)}'}
        
        # 步骤2: DashScope ASR
        print(f"🚀 调用 DashScope ASR...")
        
        try:
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 读取视频文件并转为 base64 (只取前10MB避免过大)
            with open(downloaded, 'rb') as f:
                video_data = f.read(10*1024*1024)
                video_base64 = base64.b64encode(video_data).decode('utf-8')
            
            payload = {
                "model": "qwen-omni-turbo",
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个语音识别助手。请将视频中的语音转写为中文文本。"
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "video",
                                    "video": f"data:video/mp4;base64,{video_base64}"
                                },
                                {
                                    "type": "text",
                                    "text": "请转写这段视频中的语音内容，输出纯文本。"
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'API error {response.status_code}: {response.text[:300]}'}
            
            result = response.json()
            
            # 解析响应
            if result.get('output') and result['output'].get('choices'):
                choice = result['output']['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', [])
                
                transcript = ""
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            transcript += item['text']
                elif isinstance(content, str):
                    transcript = content
                
                usage = result.get('usage', {})
                cost = (usage.get('input_tokens', 0) / 1000 * 0.003) + \
                       (usage.get('output_tokens', 0) / 1000 * 0.006)
                
                return {
                    'success': True,
                    'transcript': transcript.strip(),
                    'cost': round(cost, 4)
                }
            else:
                return {'success': False, 'error': f'No output: {result}'}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'ASR异常: {str(e)}'}


def main():
    video_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not video_url:
        print("用法: python3 dashscope-full.py <视频URL>")
        sys.exit(1)
    
    if not os.environ.get('DASHSCOPE_API_KEY'):
        os.environ['DASHSCOPE_API_KEY'] = "sk-b70f29eb4e674f13ba76375625d3887a"
    
    cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    result = download_and_transcribe(video_url, cookies_path)
    
    print("\n" + "="*50)
    if result['success']:
        print(f"✅ 转写成功")
        print(f"费用: ¥{result['cost']}")
        print(f"\n📝 结果:\n{result['transcript'][:500]}...")
    else:
        print(f"❌ 失败: {result['error']}")
    
    print("\n===JSON_START===")
    print(json.dumps(result, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == '__main__':
    main()
