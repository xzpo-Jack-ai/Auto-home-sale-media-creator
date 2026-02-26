#!/usr/bin/env python3
"""
抖音视频字幕提取 - 带新鲜Cookies获取

流程:
1. Playwright 登录抖音获取新鲜 cookies
2. 尝试 API 拦截提取字幕
3. 若无字幕，用 yt-dlp (带新鲜cookies) 下载音频
4. Whisper ASR 转写
"""

import asyncio
import json
import sys
import os
import tempfile
import subprocess

async def extract_with_fresh_cookies(video_url: str):
    from playwright.async_api import async_playwright
    
    cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    async with async_playwright() as p:
        # 启动浏览器（有头模式，可以看到登录页面）
        browser = await p.chromium.launch(
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print("🚀 打开抖音...")
        await page.goto("https://www.douyin.com/", timeout=60000)
        await asyncio.sleep(3)
        
        # 检查是否已登录
        try:
            avatar = await page.wait_for_selector("img[src*='avatar'], [data-e2e='user-avatar']", timeout=5000)
            if avatar:
                print("✅ 检测到已登录")
        except:
            print("⚠️  未登录，请在浏览器中扫码或登录")
            print("⏳ 等待60秒...")
            await asyncio.sleep(60)
        
        # 保存新鲜 cookies
        cookies = await context.cookies()
        cookie_lines = ["# Netscape HTTP Cookie File", "# Auto-generated", ""]
        
        for cookie in cookies:
            domain = cookie['domain']
            flag = "TRUE" if domain.startswith('.') else "FALSE"
            path = cookie['path']
            secure = "TRUE" if cookie['secure'] else "FALSE"
            expiration = str(int(cookie.get('expires', 0))) if cookie.get('expires') else "0"
            name = cookie['name']
            value = cookie['value']
            cookie_lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
        
        with open(cookies_path, 'w') as f:
            f.write('\n'.join(cookie_lines))
        print(f"✅ 已更新 cookies: {len(cookies)} 个")
        
        # 关闭浏览器
        await browser.close()
        
        # 现在用 API 拦截提取
        print("\n🎬 开始提取视频...")
        result = await extract_video(video_url, cookies_path)
        
        return result


async def extract_video(video_url: str, cookies_path: str):
    """提取视频信息"""
    from playwright.async_api import async_playwright
    
    result = {
        'url': video_url,
        'title': None,
        'author': None,
        'duration': None,
        'transcript': None,
        'source': None,
        'error': None
    }
    
    captured_data = {}
    audio_url_holder = [None]
    
    async def handle_route(route):
        url = route.request.url
        if '/aweme/v1/web/aweme/detail/' in url:
            response = await route.fetch()
            body = await response.body()
            try:
                data = json.loads(body)
                captured_data['video_detail'] = data
                aweme = data.get('aweme_detail', {})
                video = aweme.get('video', {})
                play_addr = video.get('play_addr', {})
                if play_addr.get('url_list'):
                    audio_url_holder[0] = play_addr['url_list'][0]
            except:
                pass
            await route.fulfill(response=response)
        else:
            await route.continue_()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # 无头模式更快
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        )
        
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        
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
        
        page = await context.new_page()
        await page.route("**/*", handle_route)
        
        print(f"🎯 正在提取: {video_url}")
        try:
            await page.goto(video_url, timeout=30000, wait_until='domcontentloaded')
        except:
            pass
        
        # 等待 API
        for i in range(10):
            if 'video_detail' in captured_data:
                break
            await asyncio.sleep(1)
        
        # 解析结果
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
                print(f"✅ 提取到自动字幕 ({len(subtitles)} 条)")
            elif audio_url_holder[0]:
                print("⚠️ 无自动字幕，尝试 ASR...")
                result['transcript'] = await asr_transcribe(audio_url_holder[0], cookies_path)
                if result['transcript']:
                    result['source'] = 'asr'
            else:
                result['error'] = '该视频没有自动字幕且无法获取音频'
        else:
            result['error'] = '未能获取视频信息'
        
        await browser.close()
    
    return result


async def asr_transcribe(audio_url: str, cookies_path: str) -> str:
    """使用 yt-dlp + Whisper 进行 ASR"""
    print("🎙️  ASR 转写中...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, 'audio')
        
        # 下载音频
        print("⬇️  下载音频...")
        try:
            cmd = [
                'yt-dlp',
                '-f', 'ba',
                '-o', audio_path,
                '--cookies', cookies_path,  # 使用新鲜 cookies
                '--no-warnings',
                '-q',
                audio_url
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            
            # 找到下载的文件
            downloaded = None
            for ext in ['.m4a', '.mp4', '.webm', '.mp3']:
                if os.path.exists(audio_path + ext):
                    downloaded = audio_path + ext
                    break
            
            if not downloaded or os.path.getsize(downloaded) < 10000:
                print("❌ 音频下载失败或文件太小")
                return None
            
            print(f"✅ 音频已下载: {os.path.getsize(downloaded)} bytes")
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return None
        
        # Whisper 转写
        print("📝 Whisper 转写...")
        try:
            import whisper
            
            model = whisper.load_model('base')
            result = model.transcribe(downloaded, language='zh', fp16=False, verbose=False)
            
            transcript = result.get('text', '').strip()
            print(f"✅ ASR 完成: {len(transcript)} 字符")
            return transcript
            
        except Exception as e:
            print(f"❌ ASR 失败: {e}")
            return None


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    try:
        result = await extract_with_fresh_cookies(url)
        
        output = {
            "success": bool(result.get('transcript')),
            **result
        }
        
        print("\n" + "="*50)
        print("📊 提取结果:")
        print(f"标题: {result['title']}")
        print(f"作者: {result['author']}")
        print(f"时长: {result['duration']}秒")
        print(f"来源: {result['source']}")
        print(f"字幕长度: {len(result['transcript']) if result['transcript'] else 0} 字符")
        
        if result['transcript']:
            print(f"\n📝 字幕预览:\n{result['transcript'][:300]}...")
        
        print("\n===JSON_START===")
        print(json.dumps(output, ensure_ascii=False))
        print("===JSON_END===")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
