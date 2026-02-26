#!/usr/bin/env python3
"""
抖音视频字幕提取 - API拦截版
使用 Playwright 拦截视频详情 API 请求获取字幕
"""

import asyncio
import json
import sys
from urllib.parse import urlparse, parse_qs

async def extract_video_info(video_url: str):
    from playwright.async_api import async_playwright, Route
    
    cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    # 存储捕获的数据
    captured_data = {}
    
    async def handle_route(route: Route):
        url = route.request.url
        
        # 拦截视频详情 API
        if '/aweme/v1/web/aweme/detail/' in url or '/aweme/v1/aweme/detail/' in url:
            print(f"🎯 拦截到 API: {url[:80]}...")
            
            # 继续请求并获取响应
            response = await route.fetch()
            body = await response.body()
            
            try:
                data = json.loads(body)
                captured_data['video_detail'] = data
                print("✅ 捕获到视频详情数据")
                
                # 提取字幕
                aweme = data.get('aweme_detail', {})
                subtitles = aweme.get('subtitle_infos', [])
                if subtitles:
                    print(f"📝 找到 {len(subtitles)} 条字幕")
                
            except Exception as e:
                print(f"解析响应失败: {e}")
            
            await route.fulfill(response=response)
        else:
            await route.continue_()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
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
            
            if cookies:
                await context.add_cookies(cookies)
                print(f"✅ 已加载 {len(cookies)} 个 cookies")
        except Exception as e:
            print(f"⚠️  加载 cookies 失败: {e}")
        
        page = await context.new_page()
        
        # 设置路由拦截
        await page.route("**/*", handle_route)
        
        print(f"🚀 打开视频页面: {video_url}")
        try:
            await page.goto(video_url, timeout=30000, wait_until='domcontentloaded')
        except:
            pass  # 超时也继续
        
        # 等待API请求完成
        for i in range(10):
            if 'video_detail' in captured_data:
                print("✅ 数据已捕获，继续处理...")
                break
            await asyncio.sleep(1)
        
        # 如果没有捕获到数据，尝试点击播放触发加载
        if not captured_data:
            print("⏳ 未捕获到数据，尝试点击播放...")
            try:
                play_btn = await page.query_selector('[data-e2e="video-play"] button, .video-play-button, [class*="play"]')
                if play_btn:
                    await play_btn.click()
                    await asyncio.sleep(5)
            except:
                pass
        
        # 提取结果
        result = {
            'url': video_url,
            'title': None,
            'author': None,
            'transcript': None,
            'duration': None
        }
        
        if 'video_detail' in captured_data:
            data = captured_data['video_detail']
            aweme = data.get('aweme_detail', {})
            
            # 提取标题
            result['title'] = aweme.get('desc')
            # 时长可能是毫秒，转换为秒
            duration = aweme.get('duration', 0)
            if duration > 1000:
                duration = duration / 1000
            result['duration'] = int(duration)
            
            # 提取作者
            author = aweme.get('author', {})
            result['author'] = author.get('nickname')
            
            # 提取字幕
            subtitles = aweme.get('subtitle_infos', [])
            if subtitles:
                transcript_lines = []
                for sub in sorted(subtitles, key=lambda x: x.get('start_time', 0)):
                    text = sub.get('content', '').strip()
                    if text:
                        transcript_lines.append(text)
                
                result['transcript'] = '\n'.join(transcript_lines)
                print(f"✅ 成功提取 {len(transcript_lines)} 行字幕")
            else:
                print("⚠️  该视频没有字幕")
        else:
            print("❌ 未能捕获到视频详情数据")
        
        # 更新 cookies
        try:
            current_cookies = await context.cookies()
            cookie_lines = ["# Netscape HTTP Cookie File", "# Auto-generated", ""]
            
            for cookie in current_cookies:
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
        except:
            pass
        
        await browser.close()
        return result

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    try:
        result = asyncio.run(extract_video_info(url))
        
        # 输出 JSON 格式供 Node.js 解析
        output = {
            "success": bool(result.get('transcript')),
            "title": result.get('title'),
            "author": result.get('author'),
            "duration": result.get('duration'),
            "transcript": result.get('transcript'),
            "transcriptLength": len(result['transcript']) if result.get('transcript') else 0
        }
        
        print("\n===JSON_START===")
        print(json.dumps(output, ensure_ascii=False))
        print("===JSON_END===")
        
    except Exception as e:
        error_output = {
            "success": False,
            "error": str(e)
        }
        print("\n===JSON_START===")
        print(json.dumps(error_output, ensure_ascii=False))
        print("===JSON_END===")
        sys.exit(1)
