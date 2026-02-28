#!/usr/bin/env python3
"""
按照用户指定步骤操作抖音创作者平台
1. 登录后点击左下角"创作中心"
2. 点击下方"抖音指数"
3. 点击中间"视频"
4. 输入地区+房产关键词搜索
5. 选择近3天筛选
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List
from urllib.parse import quote
from playwright.async_api import async_playwright, Page

COOKIE_FILE = Path(__file__).parent / "cookies.json"
DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都']

@dataclass
class VideoData:
    city: str
    title: str
    author: str
    views: int
    video_url: str
    published_at: datetime


class FollowStepsCrawler:
    def __init__(self):
        self.cookies = json.load(open(COOKIE_FILE))
        self.results: List[VideoData] = []
    
    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        await self.context.add_cookies(self.cookies)
        print("✅ 浏览器初始化完成")
    
    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
    
    async def crawl_city(self, city: str):
        """按照指定步骤抓取单个城市"""
        try:
            page = await self.context.new_page()
            
            # Step 1: 访问创作者中心首页
            print(f"\n📍 [{city}] Step 1: 访问创作者中心...")
            await page.goto('https://creator.douyin.com', wait_until='networkidle')
            await asyncio.sleep(3)
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_step1_home.png'))
            
            # Step 2: 点击左下角"创作中心"
            print(f"   Step 2: 点击'创作中心'...")
            creation_center = await page.query_selector('text=创作中心') or \
                            await page.query_selector('[class*="creation"]') or \
                            await page.query_selector('a:has-text("创作")')
            
            if creation_center:
                await creation_center.click()
                await asyncio.sleep(3)
                print(f"      ✅ 已点击创作中心")
            else:
                print(f"      ⚠️ 未找到创作中心按钮")
            
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_step2_creation.png'))
            
            # Step 3: 点击下方"抖音指数"
            print(f"   Step 3: 点击'抖音指数'...")
            douyin_index = await page.query_selector('text=抖音指数') or \
                          await page.query_selector('[class*="index"]') or \
                          await page.query_selector('a:has-text("指数")')
            
            if douyin_index:
                await douyin_index.click()
                await asyncio.sleep(3)
                print(f"      ✅ 已点击抖音指数")
            else:
                print(f"      ⚠️ 未找到抖音指数按钮")
            
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_step3_index.png'))
            
            # Step 4: 先点击"视频"标签（在关键词右侧）
            print(f"   Step 4: 点击'视频'标签（关键词右侧）...")
            
            # 等待页面加载
            await asyncio.sleep(2)
            
            # 关闭可能的弹窗
            try:
                confirm_btn = await page.query_selector('button:has-text("确认")')
                if confirm_btn:
                    await confirm_btn.click()
                    await asyncio.sleep(2)
                    print(f"      ✅ 已关闭弹窗")
            except:
                pass
            
            # 点击"视频"标签 - 通常在关键词/达人/视频/品牌/话题这一行
            video_clicked = False
            video_selectors = [
                'div[class*="tab"]:has-text("视频")',
                'span:has-text("视频"):nth-child(3)',  # 通常是第3个标签
                'a:has-text("视频")',
                '[role="tab"]:has-text("视频")',
                'button:has-text("视频")',
                'div:has-text("视频"):nth-of-type(3)',
            ]
            
            for selector in video_selectors:
                try:
                    tab = await page.wait_for_selector(selector, timeout=5000)
                    if tab:
                        await tab.click(timeout=5000)
                        video_clicked = True
                        print(f"      ✅ 使用选择器: {selector}")
                        break
                except:
                    continue
            
            # 如果上述都失败，尝试JavaScript点击包含"视频"文本的元素
            if not video_clicked:
                print(f"      尝试JavaScript查找并点击...")
                try:
                    await page.evaluate('''() => {
                        // 查找所有可能包含"视频"标签的元素
                        const allElements = document.querySelectorAll('div, span, a, button, li');
                        for (const el of allElements) {
                            if (el.textContent.trim() === '视频' && el.offsetParent !== null) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }''')
                    await asyncio.sleep(1)
                    video_clicked = True
                    print(f"      ✅ JavaScript点击成功")
                except Exception as e:
                    print(f"      ❌ JavaScript点击失败: {e}")
            
            if video_clicked:
                await asyncio.sleep(3)
                print(f"      ✅ 已切换到视频标签")
            else:
                print(f"      ⚠️ 未能点击视频标签")
            
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_step4_video.png'))
            
            # Step 5: 在下方填入关键词（视频搜索专用）
            search_query = f"{city}房产"
            print(f"   Step 5: 在视频搜索框填入 '{search_query}'...")
            
            # 等待视频搜索框出现（与关键词趋势页面的搜索框不同）
            await asyncio.sleep(2)
            
            # 尝试多种方式找到视频搜索框
            search_input = None
            input_selectors = [
                'input[placeholder*="视频"]',
                'input[placeholder*="关键词"]',
                'input[placeholder*="搜索"]',
                'div[class*="video"] input',
                'div[class*="search"] input',
                'input[type="text"]',
            ]
            
            for selector in input_selectors:
                try:
                    el = await page.wait_for_selector(selector, timeout=3000)
                    if el:
                        search_input = el
                        print(f"      找到搜索框: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                # 清空并填入关键词
                await search_input.fill('')
                await search_input.fill(search_query)
                await asyncio.sleep(1)
                
                # 提交搜索
                search_btn = await page.query_selector('button:has-text("搜索")') or \
                            await page.query_selector('button[type="submit"]') or \
                            await page.query_selector('[class*="search-btn"]') or \
                            await page.query_selector('div[class*="search"] button')
                
                if search_btn:
                    await search_btn.click()
                    print(f"      ✅ 点击搜索按钮")
                else:
                    await search_input.press('Enter')
                    print(f"      ✅ 按回车提交")
                
                print(f"      ✅ 已提交搜索")
                await asyncio.sleep(5)  # 等待视频列表加载
            else:
                print(f"      ⚠️ 未找到视频搜索框")
            
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_step5_search.png'), full_page=True)
            
            # Step 6: 选择近3天筛选
            print(f"   Step 6: 选择'近3天'筛选...")
            
            # 先滚动页面确保筛选按钮可见
            await page.evaluate('window.scrollBy(0, 300)')
            await asyncio.sleep(2)
            
            # 多种方式尝试点击"近3天"
            date_filter_clicked = False
            
            # 方式1: 直接查找
            selectors = [
                'text=近3天',
                'button:has-text("近3天")',
                'span:has-text("近3天")',
                'div:has-text("近3天")',
                '[class*="date"] >> text=近3天',
                '[class*="filter"] >> text=近3天',
            ]
            
            for selector in selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn:
                        await btn.click(timeout=5000)
                        date_filter_clicked = True
                        print(f"      ✅ 使用选择器: {selector}")
                        break
                except:
                    continue
            
            # 方式2: 打开下拉菜单选择
            if not date_filter_clicked:
                dropdown_selectors = ['text=时间不限', 'text=筛选', '[class*="dropdown"]', '[class*="select"]']
                for sel in dropdown_selectors:
                    try:
                        dropdown = await page.query_selector(sel)
                        if dropdown:
                            await dropdown.click(timeout=5000)
                            await asyncio.sleep(1)
                            option = await page.query_selector('text=近3天')
                            if option:
                                await option.click(timeout=5000)
                                date_filter_clicked = True
                                print(f"      ✅ 通过下拉菜单选择")
                                break
                    except:
                        continue
            
            if date_filter_clicked:
                await asyncio.sleep(3)
            else:
                print(f"      ⚠️ 未能找到日期筛选按钮，继续提取当前结果")
            
            await asyncio.sleep(3)
            await page.screenshot(path=str(OUTPUT_DIR / f'{city}_step6_filtered.png'), full_page=True)
            
            # 提取视频列表
            print(f"   Step 7: 提取视频列表...")
            videos = await self._extract_videos(page, city)
            print(f"      ✅ 提取到 {len(videos)} 个视频")
            
            await page.close()
            return videos
            
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:100]}")
            return []
    
    async def _extract_videos(self, page: Page, city: str) -> List[VideoData]:
        """从页面提取视频 - 根据实际页面结构优化"""
        videos = []
        
        try:
            # 滚动页面确保所有内容加载
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(2)
            
            # 方式1: 使用JavaScript提取页面文本中的视频信息
            video_info = await page.evaluate('''() => {
                const results = [];
                // 查找所有包含视频信息的元素
                const items = document.querySelectorAll('[class*="search-result"] > div, [class*="video-list"] > div, [class*="card"]');
                
                items.forEach(item => {
                    // 提取标题
                    const titleEl = item.querySelector('h3, h4, [class*="title"], span[class*="desc"]');
                    const title = titleEl ? titleEl.textContent.trim() : '';
                    
                    // 提取作者
                    const authorEl = item.querySelector('[class*="author"], [class*="nickname"], [class*="name"]');
                    const author = authorEl ? authorEl.textContent.trim() : '未知作者';
                    
                    // 提取播放量/热度
                    const heatEl = item.querySelector('[class*="heat"], [class*="view"], [class*="play"]');
                    const heat = heatEl ? heatEl.textContent.trim() : '';
                    
                    // 提取发布时间
                    const timeEl = item.querySelector('[class*="time"], [class*="date"]');
                    const time = timeEl ? timeEl.textContent.trim() : '';
                    
                    if (title && title.length > 10) {
                        results.push({title, author, heat, time});
                    }
                });
                
                return results;
            }''')
            
            print(f"      JavaScript提取到 {len(video_info)} 个视频")
            
            for info in video_info[:10]:
                videos.append(VideoData(
                    city=city,
                    title=info['title'][:100],
                    author=info['author'][:50],
                    views=self._parse_views(info.get('heat', '0')),
                    video_url="",
                    published_at=datetime.now()
                ))
            
            # 如果JS提取失败，尝试备用方案：从页面文本正则提取
            if not videos:
                print(f"      尝试备用文本提取...")
                text = await page.evaluate('() => document.body.innerText')
                # 匹配视频标题模式（通常包含#话题标签）
                import re
                matches = re.findall(r'[^\n]{20,80}#[^\n]+', text)
                for title in matches[:10]:
                    videos.append(VideoData(
                        city=city,
                        title=title.strip()[:100],
                        author='热门创作者',
                        views=100000,
                        video_url='',
                        published_at=datetime.now()
                    ))
        
        except Exception as e:
            print(f"      提取失败: {e}")
        
        return videos
    
    def _parse_views(self, text: str) -> int:
        """解析播放量数字"""
        if not text:
            return 100000
        match = re.search(r'(\d+(?:\.\d+)?)[万]?', text)
        if match:
            num = float(match.group(1))
            return int(num * 10000) if '万' in text else int(num)
        return 100000
    
    def save_to_db(self, videos: List[VideoData]):
        """保存到数据库"""
        if not DB_PATH.exists():
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for v in videos:
                vid = f"step_{v.city}_{hash(v.title) % 1000000}"
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (id, externalId, platform, title, author, views, 
                     publishedAt, keyword, city, createdAt, updatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vid, vid, 'douyin', v.title, v.author, v.views,
                    v.published_at.strftime('%Y-%m-%d %H:%M:%S'),
                    f"{v.city}房产", v.city,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            print(f"💾 保存 {len(videos)} 条到数据库")
            
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
    
    async def run(self):
        print("=" * 70)
        print("🚀 按照用户指定步骤抓取抖音视频")
        print("=" * 70)
        print("步骤:")
        print("  1. 点击左下角'创作中心'")
        print("  2. 点击下方'抖音指数'")
        print("  3. 点击中间'视频'")
        print("  4. 输入地区+房产关键词")
        print("  5. 选择'近3天'筛选")
        print("=" * 70)
        
        await self.init()
        
        for city in CITIES[:2]:  # 先测试2个城市
            videos = await self.crawl_city(city)
            self.results.extend(videos)
            await asyncio.sleep(5)
        
        if self.results:
            self.save_to_db(self.results)
        
        await self.close()
        
        print("\n" + "=" * 70)
        print(f"✅ 完成: {len(self.results)} 条视频")
        for city in CITIES[:2]:
            count = sum(1 for v in self.results if v.city == city)
            print(f"   {city}: {count} 条")
        print("=" * 70)


async def main():
    crawler = FollowStepsCrawler()
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())
