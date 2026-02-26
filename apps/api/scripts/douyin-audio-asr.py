#!/usr/bin/env python3
"""
抖音视频提取 + DashScope ASR - 音频提取版

使用 FFmpeg 从视频提取音频（文件更小）
"""

import asyncio
import os
import sys
import json
import tempfile
import subprocess
import requests
import base64

async def extract_audio_and_transcribe(video_url: str):
    """提取音频并使用 DashScope ASR"""
    
    api_key = "sk-b70f29eb4e674f13ba76375625d3887a"
    cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        )
        
        context = await browser.new_context()
        
        # 加载 cookies
        with open(cookies_path, 'r') as f:
            lines = f.readlines()
        
        cookies = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                cookies.append({
                    'domain': parts[0],
                    'path': parts[2],
                    'name': parts[5],
                    'value': parts[6],
                    'secure': parts[3].upper() == 'TRUE',
                    'httpOnly': False,
                    'sameSite': 'Lax'
                })
        
        await context.add_cookies(cookies)
        print(f"✅ 已加载 {len(cookies)} 个 cookies")
        
        # 拦截视频 URL
        video_url_holder = [None]
        
        async def handle_route(route):
            url = route.request.url
            if 'douyinvod.com' in url and 'video' in url:
                if not video_url_holder[0]:
                    video_url_holder[0] = url
                    print(f"🎥 获取到视频 URL")
            await route.continue_()
        
        page = await context.new_page()
        await page.route("**/*", handle_route)
        
        print(f"🚀 打开视频页面...")
        try:
            await page.goto(video_url, timeout=30000, wait_until='domcontentloaded')
        except:
            pass
        
        await asyncio.sleep(5)
        
        try:
            play_btn = await page.query_selector('video')
            if play_btn:
                await play_btn.click()
                await asyncio.sleep(3)
        except:
            pass
        
        await browser.close()
        
        if not video_url_holder[0]:
            return {'success': False, 'error': '无法获取视频 URL'}
        
        print(f"⬇️  下载视频...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, 'video.mp4')
            audio_path = os.path.join(tmpdir, 'audio.mp3')
            
            # 下载视频
            try:
                session = requests.Session()
                cookie_dict = {}
                for line in open(cookies_path):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('\t')
                        if len(parts) >= 7:
                            cookie_dict[parts[5]] = parts[6]
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': 'https://www.douyin.com/',
                    'Cookie': '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
                }
                
                response = session.get(video_url_holder[0], headers=headers, timeout=60, stream=True)
                
                if response.status_code == 200:
                    with open(video_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = os.path.getsize(video_path)
                    print(f"✅ 视频下载完成: {file_size/1024/1024:.1f}MB")
                else:
                    return {'success': False, 'error': f'下载失败: HTTP {response.status_code}'}
                    
            except Exception as e:
                return {'success': False, 'error': f'下载异常: {str(e)}'}
            
            # 提取音频 (前2分钟)
            print(f"🎵 提取音频...")
            try:
                subprocess.run([
                    'ffmpeg', '-i', video_path,
                    '-t', '120',  # 只取前2分钟
                    '-vn',  # 无视频
                    '-acodec', 'libmp3lame',
                    '-ar', '16000',
                    '-ac', '1',
                    '-b:a', '32k',  # 低码率减小文件
                    audio_path,
                    '-y'
                ], check=True, capture_output=True, timeout=30)
                
                audio_size = os.path.getsize(audio_path)
                print(f"✅ 音频提取完成: {audio_size/1024:.1f}KB")
                
            except Exception as e:
                return {'success': False, 'error': f'FFmpeg 失败: {str(e)}'}
            
            # DashScope ASR
            print(f"🎙️  DashScope ASR...")
            try:
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "qwen-omni-turbo",
                    "input": {
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个语音识别助手。请将音频转写为中文文本。"
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "audio",
                                        "audio": f"data:audio/mp3;base64,{audio_base64}"
                                    },
                                    {
                                        "type": "text",
                                        "text": "请转写这段音频内容。"
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    
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
                
                return {'success': False, 'error': f'ASR API 错误: {response.status_code}'}
                
            except Exception as e:
                return {'success': False, 'error': f'ASR 异常: {str(e)}'}


async def main():
    video_url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    result = await extract_audio_and_transcribe(video_url)
    
    print("\n" + "="*50)
    if result['success']:
        print(f"✅ 转写成功!")
        print(f"费用: ¥{result['cost']}")
        print(f"\n📝 结果:\n{result['transcript']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    print("\n===JSON_START===")
    print(json.dumps(result, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == '__main__':
    asyncio.run(main())
