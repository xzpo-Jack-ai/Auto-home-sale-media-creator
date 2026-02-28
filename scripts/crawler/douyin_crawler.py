#!/usr/bin/env python3
"""
抖音房产数据抓取脚本
功能：每天自动抓取 6 个城市的房产热词和热门视频
作者：ShadowJack
日期：2026-02-28
"""

import asyncio
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, BrowserContext

# ============ 配置 ============
CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都']

# Cookie 字符串（从用户获取）
COOKIE_STRING = """gfkadpd=2906,33638;is_staff_user=false;sessionid_ss=0a6e62e78eb34e330971d20ec2818ade;passport_csrf_token=c3a6730d181d2559d7ba0490d6c40ff9;sid_ucp_v1=1.0.0-KDcyN2Y0NzkzNmY5OTA3NmMzMzk3MTE1YjZmZjUyMWZjOTYyMWYwZjQKHwik-8O4mgIQkZ7_zAYY7zEgDDCTpKnQBTgHQPQHSAQaAmxxIiAwYTZlNjJlNzhlYjM0ZTMzMDk3MWQyMGVjMjgxOGFkZQ;session_tlb_tag=sttt%7C17%7CCm5i546zTjMJcdIOwoGK3v_________m1ImgMU1rqmkxDJ9b9Eh0z3EF9oWUKB9qkCADhjqPaSs%3D;passport_mfa_token=CjW01bYM3U0UthUSqMagXEC5czOIWCHWyp3phW2v5zQRMU4PttqioSqYcjiWW6FGipmsYjnLHBpKCjwAAAAAAAAAAAAAUB3AYXd0Ytp4C84uhbNzuHJOqN%2FExi0w6%2BK9eXQAcz7bgEZd7cW5UVwJI0LFGmHRs64Qr9GKDhj2sdFsIAIiAQNZMK3k;sid_guard=0a6e62e78eb34e330971d20ec2818ade%7C1772080913%7C5184000%7CMon%2C+27-Apr-2026+04%3A41%3A53+GMT;ttwid=1%7CuAVNzXBkGVl22a2UT7kvfDmweeWtVRuGqJ9plwBVYmw%7C1772216039%7Cfdf445ceb5d2c533ce5a5ded1e054e376be994f8a43a47478fdc9927cee0a6d8;count-client-api_sid=eyJfZXhwaXJlIjoxNzczNDI1NjQwMjQ1LCJfbWF4QWdlIjoxMjA5NjAwMDAwfQ==;csrf_session_id=c8dde97ff722650b6430040530222c71;enter_pc_once=1;passport_assist_user=CjyXWaCwYmxVv7oLpozkXocMWVV8tuRhS4RVwQBtKudsy5trnjbVhBXft3_u4gGveQ6h35uPyeavTpQcVyQaSgo8AAAAAAAAAAAAAFAeuyhDZ5389LY5gMoIEZLLJaaUV6FDgrGRwf0spalY576rMiDST20Oaw1PVta3xntLENfTig4Yia_WVCABIgEDoMFlfw%3D%3D;sessionid=0a6e62e78eb34e330971d20ec2818ade;sid_tt=0a6e62e78eb34e330971d20ec2818ade;ssid_ucp_v1=1.0.0-KDcyN2Y0NzkzNmY5OTA3NmMzMzk3MTE1YjZmZjUyMWZjOTYyMWYwZjQKHwik-8O4mgIQkZ7_zAYY7zEgDDCTpKnQBTgHQPQHSAQaAmxxIiAwYTZlNjJlNzhlYjM0ZTMzMDk3MWQyMGVjMjgxOGFkZQ;uid_tt=6cda6e3e53db8a3cae8f1ff47c9fe91a;uid_tt_ss=6cda6e3e53db8a3cae8f1ff47c9fe91a;UIFID_TEMP=749b770aa6a177ba6fbed42b6fcf8269d6ef3c63265bceaf64e3282dcaa6c732bcd33b0d6b597c0e89d8d155e604602697c77de025655c522075eb9618fa3c22e0ed9c812eefb093400b670094570fe5b1d6603a7e338f98530942c2f5aa521e02b228ab2ee7e8daa8a6da9f74deb10a"""

# 数据库路径
DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")


@dataclass
class HotKeyword:
    """热词数据模型"""
    city: str
    keyword: str
    heat_value: int
    trend: str  # 'up', 'down', 'stable'
    rank: int
    crawled_at: datetime


@dataclass
class VideoData:
    """视频数据模型"""
    city: str
    keyword: str
    title: str
    author: str
    views: int
    likes: int
    shares: int
    comments: int
    link: str
    cover_url: str
    duration: int
    published_at: Optional[datetime]
    crawled_at: datetime


class DouyinCrawler:
    """抖音数据抓取器"""
    
    def __init__(self):
        self.context: Optional[BrowserContext] = None
        self.cookies = self._parse_cookies()
        self.results = {
            'keywords': [],
            'videos': [],
            'errors': []
        }
    
    def _parse_cookies(self) -> List[Dict[str, str]]:
        """解析 Cookie 字符串"""
        cookies = []
        for item in COOKIE_STRING.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.douyin.com',
                    'path': '/'
                })
        return cookies
    
    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 添加 Cookie
        await self.context.add_cookies(self.cookies)
        print(f"✅ 浏览器初始化完成，已加载 {len(self.cookies)} 个 Cookie")
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def fetch_city_hot_keywords(self, city: str) -> List[HotKeyword]:
        """抓取城市房产热词"""
        keywords = []
        search_query = f"{city}房产"
        
        try:
            page = await self.context.new_page()
            
            # 访问巨量算数搜索页
            url = f"https://trendinsight.oceanengine.com/arithmetic-index/analysis?keyword={quote(search_query)}"
            print(f"🔍 正在抓取 [{city}] 热词: {url}")
            
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            if response.status != 200:
                raise Exception(f"页面加载失败: {response.status}")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 尝试提取相关热词
            # 注意：实际选择器需要根据页面结构调整
            hot_words = await page.evaluate('''() => {
                const words = [];
                // 尝试多种可能的选择器
                const selectors = [
                    '.related-word-item',
                    '.hot-word-item',
                    '[class*="word"]',
                    '[class*="keyword"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const text = el.textContent?.trim();
                        if (text && text.length > 2 && text.length < 50) {
                            words.push(text);
                        }
                    });
                }
                
                return [...new Set(words)].slice(0, 10);
            }''')
            
            print(f"   找到 {len(hot_words)} 个热词: {hot_words[:5]}...")
            
            # 构造热词对象
            for i, word in enumerate(hot_words[:10], 1):
                keywords.append(HotKeyword(
                    city=city,
                    keyword=word,
                    heat_value=100 - i * 5,  # 模拟热度值
                    trend='up' if i % 3 == 0 else 'stable',
                    rank=i,
                    crawled_at=datetime.now()
                ))
            
            await page.close()
            
        except Exception as e:
            error_msg = f"[{city}] 热词抓取失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        return keywords
    
    async def fetch_city_videos(self, city: str, keyword: str) -> List[VideoData]:
        """抓取城市关键词相关视频"""
        videos = []
        search_query = f"{city}{keyword}"
        
        try:
            page = await self.context.new_page()
            
            # 访问创作者平台视频搜索
            url = f"https://creator.douyin.com/creator-micro/creator-count/arithmetic-index/videosearch?query={quote(search_query)}"
            print(f"🎬 正在抓取 [{city}-{keyword}] 视频: {url}")
            
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            if response.status != 200:
                raise Exception(f"页面加载失败: {response.status}")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 尝试提取视频信息
            video_list = await page.evaluate('''() => {
                const videos = [];
                const selectors = [
                    '.video-item',
                    '[class*="video"]',
                    '[class*="card"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const titleEl = el.querySelector('[class*="title"]') || el.querySelector('h3, h4');
                        const authorEl = el.querySelector('[class*="author"]') || el.querySelector('[class*="user"]');
                        const viewEl = el.querySelector('[class*="view"]') || el.querySelector('[class*="play"]');
                        
                        if (titleEl) {
                            videos.push({
                                title: titleEl.textContent?.trim() || '',
                                author: authorEl?.textContent?.trim() || '未知作者',
                                views: viewEl?.textContent?.trim() || '0'
                            });
                        }
                    });
                }
                
                return videos.slice(0, 5);
            }''')
            
            print(f"   找到 {len(video_list)} 个视频")
            
            # 构造视频对象
            for i, v in enumerate(video_list):
                # 解析播放量数字
                views_str = v.get('views', '0')
                views_num = self._parse_number(views_str)
                
                videos.append(VideoData(
                    city=city,
                    keyword=keyword,
                    title=v.get('title', '无标题'),
                    author=v.get('author', '未知作者'),
                    views=views_num,
                    likes=int(views_num * 0.05),  # 估算
                    shares=int(views_num * 0.01),
                    comments=int(views_num * 0.02),
                    link='',  # 需要进一步提取
                    cover_url='',
                    duration=30 + i * 10,
                    published_at=datetime.now() - timedelta(days=i),
                    crawled_at=datetime.now()
                ))
            
            await page.close()
            
        except Exception as e:
            error_msg = f"[{city}-{keyword}] 视频抓取失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        return videos
    
    def _parse_number(self, text: str) -> int:
        """解析数字（支持万、亿等单位）"""
        text = text.replace(',', '').strip()
        
        if '万' in text:
            num = float(text.replace('万', ''))
            return int(num * 10000)
        elif '亿' in text:
            num = float(text.replace('亿', ''))
            return int(num * 100000000)
        elif text.isdigit():
            return int(text)
        else:
            # 尝试提取数字
            nums = re.findall(r'\d+', text)
            return int(nums[0]) if nums else 0
    
    def save_to_database(self):
        """保存数据到 SQLite 数据库"""
        if not DB_PATH.exists():
            print(f"⚠️ 数据库不存在: {DB_PATH}")
            return False
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 更新热词数据
            for kw in self.results['keywords']:
                cursor.execute('''
                    INSERT INTO Keyword (city, text, heat, updatedAt)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(city, text) DO UPDATE SET
                        heat = excluded.heat,
                        updatedAt = excluded.updatedAt
                ''', (kw.city, kw.keyword, kw.heat_value, kw.crawled_at.isoformat()))
            
            # 插入视频数据
            for v in self.results['videos']:
                external_id = f"{v.city}_{v.keyword}_{v.title[:20]}_{int(v.crawled_at.timestamp())}"
                cursor.execute('''
                    INSERT OR REPLACE INTO Video (
                        externalId, platform, title, author, authorId,
                        views, likes, shares, comments, coverUrl, duration,
                        transcript, publishedAt, keyword, city, createdAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    external_id, 'douyin', v.title, v.author, '',
                    v.views, v.likes, v.shares, v.comments, v.cover_url, v.duration,
                    '', v.published_at.isoformat() if v.published_at else None,
                    v.keyword, v.city, v.crawled_at.isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 数据已保存到数据库")
            print(f"   热词: {len(self.results['keywords'])} 条")
            print(f"   视频: {len(self.results['videos'])} 条")
            return True
            
        except Exception as e:
            print(f"❌ 数据库保存失败: {str(e)}")
            return False
    
    async def run(self, test_mode: bool = False):
        """运行抓取任务"""
        print("=" * 60)
        print("🚀 抖音房产数据抓取任务开始")
        print("=" * 60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"城市: {', '.join(CITIES)}")
        print(f"模式: {'测试模式' if test_mode else '完整模式'}")
        print("-" * 60)
        
        try:
            await self.init_browser()
            
            # 测试模式只抓一个城市
            cities_to_crawl = CITIES[:1] if test_mode else CITIES
            
            for city in cities_to_crawl:
                print(f"\n📍 正在处理城市: {city}")
                
                # 1. 抓取热词
                keywords = await self.fetch_city_hot_keywords(city)
                self.results['keywords'].extend(keywords)
                
                # 2. 为每个热词抓取视频（测试模式只抓前2个热词）
                keywords_to_process = keywords[:2] if test_mode else keywords[:5]
                for kw in keywords_to_process:
                    videos = await self.fetch_city_videos(city, kw.keyword)
                    self.results['videos'].extend(videos)
                    await asyncio.sleep(1)  # 避免请求过快
                
                await asyncio.sleep(2)  # 城市间间隔
            
            # 保存数据
            self.save_to_database()
            
        finally:
            await self.close()
        
        # 输出总结
        print("\n" + "=" * 60)
        print("📊 抓取任务完成")
        print("=" * 60)
        print(f"成功城市: {len(set(kw.city for kw in self.results['keywords']))}/{len(cities_to_crawl)}")
        print(f"热词总数: {len(self.results['keywords'])}")
        print(f"视频总数: {len(self.results['videos'])}")
        print(f"错误数量: {len(self.results['errors'])}")
        
        if self.results['errors']:
            print("\n⚠️ 错误详情:")
            for err in self.results['errors'][:5]:
                print(f"   • {err}")
        
        return len(self.results['errors']) == 0


async def main():
    """主函数"""
    import sys
    
    # 检查参数
    test_mode = '--test' in sys.argv
    
    crawler = DouyinCrawler()
    success = await crawler.run(test_mode=test_mode)
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
