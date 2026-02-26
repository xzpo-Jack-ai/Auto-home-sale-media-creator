#!/usr/bin/env python3
"""
Playwright 下载抖音视频 + DashScope ASR

流程:
1. Playwright 获取视频页面
2. 拦截视频下载 URL
3. 直接下载视频数据
4. DashScope ASR 转写
"""

import asyncio
import os
import sys
import json
import tempfile
import requests

async def download_video_and_transcribe(video_url: str):
    from playwright.async_api import async_playwright
    
    api_key = os.environ.get('DASHSCOPE_API_KEY') or "sk-b70f29eb4e674f13ba76375625d3887a"
    cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    result = {
        'success': False,
        'transcript': None,
        'cost': 0,
        'error': None
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        )
        
        context = await browser.new_context()
        
        # 加载 cookies
        try:
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
        except Exception as e:
            result['error'] = f'加载 cookies 失败: {e}'
            return result
        
        # 拦截视频下载
        video_url_holder = [None]
        
        async def handle_route(route):
            url = route.request.url
            # 拦截视频请求
            if 'douyinvod.com' in url and ('video' in url or '.mp4' in url):
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
        
        # 等待视频加载
        await asyncio.sleep(5)
        
        # 尝试点击播放触发视频加载
        try:
            play_btn = await page.query_selector('video, [data-e2e="video-player"], .xgplayer')
            if play_btn:
                await play_btn.click()
                await asyncio.sleep(3)
        except:
            pass
        
        await browser.close()
        
        if not video_url_holder[0]:
            result['error'] = '无法获取视频 URL'
            return result
        
        print(f"⬇️  下载视频...")
        
        # 下载视频（使用 requests + cookies）
        try:
            session = requests.Session()
            
            # 从 cookies 文件构建 cookie 字典
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
            }
            
            # 转换 cookies 为字符串
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
            headers['Cookie'] = cookie_str
            
            response = session.get(video_url_holder[0], headers=headers, timeout=60, stream=True)
            
            if response.status_code == 200:
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                    video_file = f.name
                
                file_size = os.path.getsize(video_file)
                print(f"✅ 视频下载完成: {file_size/1024/1024:.1f}MB")
                
                # DashScope ASR
                print(f"🎙️  DashScope ASR 转写...")
                transcript = await transcribe_with_dashscope(video_file, api_key)
                
                if transcript:
                    result['success'] = True
                    result['transcript'] = transcript
                    # 估算费用 (约 ¥0.003/分钟)
                    result['cost'] = round((file_size / 1024 / 1024) * 0.001, 4)
                else:
                    result['error'] = 'ASR 转写失败'
                
                # 清理临时文件
                os.unlink(video_file)
            else:
                result['error'] = f'下载失败: HTTP {response.status_code}'
                
        except Exception as e:
            result['error'] = f'下载异常: {str(e)}'
    
    return result


async def transcribe_with_dashscope(video_file: str, api_key: str) -> str:
    """使用 DashScope ASR 转写视频"""
    import base64
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 读取视频文件（限制10MB）
    with open(video_file, 'rb') as f:
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
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
                
                return transcript.strip()
        
        return None
        
    except Exception as e:
        print(f"ASR error: {e}")
        return None


async def main():
    video_url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    if not os.environ.get('DASHSCOPE_API_KEY'):
        os.environ['DASHSCOPE_API_KEY'] = "sk-b70f29eb4e674f13ba76375625d3887a"
    
    result = await download_video_and_transcribe(video_url)
    
    print("\n" + "="*50)
    if result['success']:
        print(f"✅ 转写成功!")
        print(f"费用: ¥{result['cost']}")
        print(f"\n📝 结果:\n{result['transcript'][:500]}...")
    else:
        print(f"❌ 失败: {result['error']}")
    
    print("\n===JSON_START===")
    print(json.dumps(result, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == '__main__':
    asyncio.run(main())
