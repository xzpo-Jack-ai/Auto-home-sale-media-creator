#!/usr/bin/env python3
"""
抖音视频字幕提取 + ASR 兜底方案

流程:
1. 尝试 API 拦截获取自动字幕
2. 若无字幕，下载音频并使用 Whisper ASR 转写

依赖:
- pip install playwright openai-whisper
- brew install ffmpeg (或 apt-get install ffmpeg)
"""

import asyncio
import json
import sys
import os
import tempfile
import subprocess
from pathlib import Path

# 抖音视频提取类
class DouyinExtractor:
    def __init__(self):
        self.cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
        
    async def extract(self, video_url: str, use_asr_fallback: bool = True) -> dict:
        """提取视频信息，无字幕时可选 ASR 兜底"""
        from playwright.async_api import async_playwright
        
        result = {
            'url': video_url,
            'title': None,
            'author': None,
            'duration': None,
            'transcript': None,
            'source': None,  # 'subtitle' | 'asr' | 'none'
            'error': None
        }
        
        captured_data = {}
        audio_url_holder = [None]  # 使用 list 来在闭包中修改
        
        async def handle_route(route):
            url = route.request.url
            
            # 拦截视频详情 API
            if '/aweme/v1/web/aweme/detail/' in url:
                print(f"🎯 拦截到详情 API")
                response = await route.fetch()
                body = await response.body()
                
                try:
                    data = json.loads(body)
                    captured_data['video_detail'] = data
                    
                    # 提取音频 URL
                    aweme = data.get('aweme_detail', {})
                    video = aweme.get('video', {})
                    play_addr = video.get('play_addr', {})
                    if play_addr.get('url_list'):
                        audio_url_holder[0] = play_addr['url_list'][0]
                        print(f"🎵 获取到音频 URL")
                        
                except Exception as e:
                    print(f"解析响应失败: {e}")
                
                await route.fulfill(response=response)
            else:
                await route.continue_()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # 使用无头模式加快提取
                executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(viewport={'width': 1280, 'height': 800})
            
            # 加载 cookies
            await self._load_cookies(context)
            
            page = await context.new_page()
            await page.route("**/*", handle_route)
            
            print(f"🚀 打开视频页面: {video_url}")
            try:
                await page.goto(video_url, timeout=30000, wait_until='domcontentloaded')
            except:
                pass
            
            # 等待 API 响应
            for i in range(10):
                if 'video_detail' in captured_data:
                    break
                await asyncio.sleep(1)
            
            # 解析视频信息
            if 'video_detail' in captured_data:
                aweme = captured_data['video_detail'].get('aweme_detail', {})
                result['title'] = aweme.get('desc')
                result['author'] = aweme.get('author', {}).get('nickname')
                duration = aweme.get('duration', 0)
                if duration > 1000:
                    duration = duration / 1000
                result['duration'] = int(duration)
                
                # 检查字幕
                subtitles = aweme.get('subtitle_infos', [])
                if subtitles:
                    lines = [s.get('content', '').strip() for s in sorted(subtitles, key=lambda x: x.get('start_time', 0))]
                    result['transcript'] = '\n'.join([l for l in lines if l])
                    result['source'] = 'subtitle'
                    print(f"✅ 成功提取自动字幕 ({len(subtitles)} 条)")
                elif use_asr_fallback and audio_url_holder[0]:
                    print("⚠️ 无自动字幕，启动 ASR 兜底...")
                    result['transcript'] = await self._asr_transcribe(audio_url_holder[0])
                    if result['transcript']:
                        result['source'] = 'asr'
                else:
                    result['error'] = '该视频没有自动字幕'
            else:
                result['error'] = '未能获取视频信息'
            
            await browser.close()
        
        return result
    
    async def _load_cookies(self, context):
        """加载 cookies"""
        try:
            with open(self.cookies_path, 'r') as f:
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
            
            if cookies:
                await context.add_cookies(cookies)
                print(f"✅ 已加载 {len(cookies)} 个 cookies")
        except Exception as e:
            print(f"⚠️ 加载 cookies 失败: {e}")
    
    async def _asr_transcribe(self, audio_url: str) -> str:
        """使用 Whisper 进行 ASR 转写"""
        print("🎙️  启动 Whisper ASR...")
        
        # 下载音频
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, 'audio.mp4')
            wav_path = os.path.join(tmpdir, 'audio.wav')
            
            # 下载
            print(f"⬇️  下载音频...")
            try:
                # 构建 curl headers
                headers = [
                    '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    '-H', 'Referer: https://www.douyin.com/',
                ]
                # 从 cookies 文件读取 sessionid
                session_id = None
                try:
                    with open(self.cookies_path, 'r') as f:
                        for line in f:
                            if 'sessionid' in line:
                                parts = line.strip().split('\t')
                                if len(parts) >= 7:
                                    session_id = parts[6]
                                    break
                except:
                    pass
                
                if session_id:
                    headers.extend(['-H', f'Cookie: sessionid={session_id}'])
                
                cmd = ['curl', '-L', '-o', audio_path, '--max-time', '60'] + headers + [audio_url]
                subprocess.run(cmd, check=True, capture_output=True, timeout=60)
                
                file_size = os.path.getsize(audio_path)
                print(f"✅ 音频已下载: {file_size} bytes")
                
                if file_size < 1000:
                    print(f"⚠️  文件太小，可能下载失败")
                    return None
                    
            except Exception as e:
                print(f"❌ 下载音频失败: {e}")
                return None
            
            # 转换为 WAV (Whisper 需要)
            print("🔄 转换音频格式...")
            try:
                subprocess.run(
                    ['ffmpeg', '-i', audio_path, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav_path, '-y'],
                    check=True,
                    capture_output=True,
                    timeout=30
                )
            except Exception as e:
                print(f"❌ FFmpeg 转换失败: {e}")
                # 尝试直接使用原文件
                wav_path = audio_path
            
            # Whisper 转写
            print("📝 Whisper 转写中...")
            try:
                import whisper
                
                # 加载模型 (base 模型速度快，small 更准确)
                model = whisper.load_model('base')
                
                result = model.transcribe(wav_path, language='zh', fp16=False)
                
                transcript = result.get('text', '').strip()
                print(f"✅ ASR 完成: {len(transcript)} 字符")
                
                return transcript
                
            except Exception as e:
                print(f"❌ Whisper 转写失败: {e}")
                return None


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    extractor = DouyinExtractor()
    result = await extractor.extract(url, use_asr_fallback=True)
    
    # 输出 JSON
    output = {
        "success": bool(result.get('transcript')),
        **result
    }
    
    print("\n===JSON_START===")
    print(json.dumps(output, ensure_ascii=False))
    print("===JSON_END===")


if __name__ == "__main__":
    asyncio.run(main())
