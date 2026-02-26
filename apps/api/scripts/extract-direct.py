#!/usr/bin/env python3
"""
直接提取抖音视频信息（绕过 yt-dlp）
使用 Playwright 控制 Chrome 访问视频页面并提取信息
"""

import asyncio
import json
import re
import sys

async def extract_video_info(video_url: str):
    from playwright.async_api import async_playwright
    
    cookies_path = "/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/cookies/douyin.txt"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 加载 cookies
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        # 从文件加载 cookies
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
        
        print(f"🚀 打开视频页面: {video_url}")
        await page.goto(video_url, timeout=60000)
        await asyncio.sleep(5)  # 等待页面完全加载
        
        # 尝试提取视频信息
        video_info = {
            'url': video_url,
            'title': None,
            'author': None,
            'transcript': None
        }
        
        # 方法1: 从页面脚本提取 SSR 数据
        try:
            # 查找 RENDER_DATA
            render_data = await page.evaluate('''() => {
                const script = document.querySelector('script[id="RENDER_DATA"]');
                return script ? script.textContent : null;
            }''')
            
            if render_data:
                print("✅ 找到 RENDER_DATA")
                # 解析 JSON 数据
                try:
                    import urllib.parse
                    decoded = urllib.parse.unquote(render_data)
                    data = json.loads(decoded)
                    
                    # 调试: 保存数据结构
                    with open('/tmp/douyin_debug.json', 'w') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print("💾 数据结构已保存到 /tmp/douyin_debug.json")
                    
                    # 提取视频信息
                    app_data = data.get('app', {}) or data
                    print(f"🔍 数据键: {list(app_data.keys())[:10]}")
                    video_detail = app_data.get('videoDetail') or app_data.get('aweme_detail') or {}
                    
                    if video_detail:
                        video_info['title'] = video_detail.get('desc') or video_detail.get('title')
                        video_info['author'] = video_detail.get('author', {}).get('nickname')
                        video_info['duration'] = video_detail.get('duration')
                        
                        # 提取字幕
                        subtitles = video_detail.get('subtitleInfos', [])
                        if subtitles:
                            transcript_lines = []
                            for sub in sorted(subtitles, key=lambda x: x.get('startTime', 0)):
                                text = sub.get('content', '').strip()
                                if text:
                                    transcript_lines.append(text)
                            
                            video_info['transcript'] = '\n'.join(transcript_lines)
                            print(f"📝 提取到 {len(subtitles)} 条字幕")
                        
                        print(f"📄 标题: {video_info['title'][:50]}...")
                        print(f"👤 作者: {video_info['author']}")
                except Exception as e:
                    print(f"解析 RENDER_DATA 失败: {e}")
                    # 保存原始数据用于调试
                    with open('/tmp/douyin_render_data.json', 'w') as f:
                        f.write(decoded if 'decoded' in locals() else render_data)
                    print("💾 原始数据已保存到 /tmp/douyin_render_data.json")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"提取 RENDER_DATA 失败: {e}")
        
        # 方法2: 从页面 HTML 提取标题和作者
        try:
            title = await page.title()
            video_info['title'] = title
            print(f"📄 页面标题: {title}")
        except:
            pass
        
        # 方法3: 查找字幕按钮并点击
        try:
            # 寻找字幕/文案相关按钮
            subtitle_btn = await page.query_selector('[data-e2e="subtitle-btn"], .subtitle-btn, [class*="subtitle"]')
            if subtitle_btn:
                print("✅ 找到字幕按钮，点击...")
                await subtitle_btn.click()
                await asyncio.sleep(2)
                
                # 尝试获取字幕内容
                subtitle_text = await page.evaluate('''() => {
                    const elements = document.querySelectorAll('[class*="subtitle"] [class*="text"], .subtitle-content, [data-e2e="subtitle-text"]');
                    return Array.from(elements).map(el => el.textContent).join('\\n');
                }''')
                
                if subtitle_text:
                    video_info['transcript'] = subtitle_text
                    print(f"📝 提取到字幕: {subtitle_text[:200]}...")
        except Exception as e:
            print(f"提取字幕失败: {e}")
        
        # 保存当前 cookies（刷新后的）
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
            print(f"✅ 已更新 cookies: {len(current_cookies)} 个")
        except Exception as e:
            print(f"保存 cookies 失败: {e}")
        
        await browser.close()
        return video_info

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/od9jc8Ju4t8/"
    
    try:
        result = asyncio.run(extract_video_info(url))
        print("\n" + "="*50)
        print("提取结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
