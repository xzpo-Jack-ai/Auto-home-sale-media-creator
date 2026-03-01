#!/usr/bin/env python3
"""
批量视频导入工具
用户提供抖音分享链接列表，自动提取视频信息并保存到数据库

使用方法:
1. 创建视频列表文件 videos.txt，格式：城市|关键词|链接
   示例：
   北京|学区房|https://v.douyin.com/i5Q8Q9Q9/
   上海|新房|https://v.douyin.com/i5Q8Q9Q8/

2. 运行：python3 batch_video_import.py videos.txt
"""

import asyncio
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

# 配置
DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ASR 提取脚本路径
API_INTERCEPT_SCRIPT = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/scripts/extract-api-intercept.py")
DASHSCOPE_ASR_SCRIPT = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/scripts/douyin-audio-asr.py")


@dataclass
class VideoData:
    city: str
    keyword: str
    title: str
    author: str
    author_id: str
    views: int
    likes: int
    shares: int
    comments: int
    video_url: str
    cover_url: str
    duration: int
    transcript: str
    published_at: str
    crawled_at: str


class BatchVideoImporter:
    """批量视频导入器"""
    
    def __init__(self):
        self.results: List[VideoData] = []
        self.errors: List[str] = []
    
    def extract_video_info(self, share_url: str) -> Optional[Dict]:
        """使用 API 拦截脚本提取视频信息"""
        try:
            print(f"   🔍 提取信息...")
            
            # 调用 Python 脚本
            result = subprocess.run(
                ['python3', str(API_INTERCEPT_SCRIPT), share_url],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout
            
            # 解析 JSON 输出
            json_match = re.search(r'===JSON_START===(.+?)===JSON_END===', output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data
            else:
                # 尝试直接解析整个输出
                try:
                    return json.loads(output)
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"   ❌ 提取失败: {e}")
            return None
    
    def extract_with_asr(self, share_url: str) -> Optional[Dict]:
        """使用 DashScope ASR 提取视频文案"""
        try:
            print(f"   🎙️ ASR 提取...")
            
            result = subprocess.run(
                ['python3', str(DASHSCOPE_ASR_SCRIPT), share_url],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stdout
            
            # 查找转写结果
            for line in output.split('\n'):
                if '转写文本:' in line:
                    text = line.split('转写文本:', 1)[1].strip()
                    return {'transcript': text}
                elif '"text"' in line or "'text'" in line:
                    match = re.search(r'["\']text["\']\s*:\s*["\'](.+?)["\']', line)
                    if match:
                        return {'transcript': match.group(1)}
            
            return None
            
        except Exception as e:
            print(f"   ❌ ASR 失败: {e}")
            return None
    
    def process_video(self, share_url: str, city: str = "未知", keyword: str = "房产") -> Optional[VideoData]:
        """处理单个视频"""
        
        # 第一步：尝试 API 拦截获取基本信息
        info = self.extract_video_info(share_url)
        
        if not info:
            print(f"   ⚠️ API 拦截失败，尝试 ASR...")
            info = {}
        
        # 如果没有字幕，尝试 ASR
        transcript = info.get('transcript', '')
        if not transcript or len(transcript) < 10:
            asr_result = self.extract_with_asr(share_url)
            if asr_result and asr_result.get('transcript'):
                transcript = asr_result['transcript']
                print(f"   ✅ ASR 成功 ({len(transcript)} 字符)")
        else:
            print(f"   ✅ 已有字幕 ({len(transcript)} 字符)")
        
        # 构造 VideoData
        title = (info or {}).get('title', '无标题') or '无标题'
        video = VideoData(
            city=city,
            keyword=keyword,
            title=title[:150],
            author=(info or {}).get('author', '未知作者') or '未知作者',
            author_id=(info or {}).get('author_id', '') or '',
            views=(info or {}).get('views', 0) or 0,
            likes=(info or {}).get('likes', 0) or 0,
            shares=(info or {}).get('shares', 0) or 0,
            comments=(info or {}).get('comments', 0) or 0,
            video_url=share_url,
            cover_url=(info or {}).get('cover_url', '') or '',
            duration=(info or {}).get('duration', 0) or 0,
            transcript=transcript[:2000] if transcript else '',  # 限制长度
            published_at=(info or {}).get('published_at', datetime.now().isoformat()) or datetime.now().isoformat(),
            crawled_at=datetime.now().isoformat()
        )
        
        return video
    
    def save_to_database(self, videos: List[VideoData]):
        """保存到数据库"""
        if not DB_PATH.exists():
            print(f"⚠️ 数据库不存在: {DB_PATH}")
            return False
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            saved = 0
            for v in videos:
                external_id = f"dy_{v.city}_{hash(v.title) % 1000000}_{int(datetime.now().timestamp())}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO videos (
                        id, externalId, platform, title, author, authorId,
                        views, likes, shares, comments, coverUrl, videoUrl,
                        duration, transcript, publishedAt, keyword, city, createdAt, updatedAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    external_id, external_id, 'douyin', v.title, v.author, v.author_id,
                    v.views, v.likes, v.shares, v.comments, v.cover_url, v.video_url,
                    v.duration, v.transcript, v.published_at, v.keyword, v.city,
                    v.crawled_at, v.crawled_at
                ))
                saved += 1
            
            conn.commit()
            conn.close()
            print(f"💾 数据库保存: {saved} 条视频")
            return True
            
        except Exception as e:
            print(f"❌ 数据库错误: {e}")
            return False
    
    def run(self, video_list_file: str):
        """运行导入"""
        print("=" * 70)
        print("📥 批量视频导入工具")
        print("=" * 70)
        
        # 读取视频列表
        file_path = Path(video_list_file)
        if not file_path.exists():
            print(f"❌ 文件不存在: {video_list_file}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            videos_input = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"📄 从文件加载: {len(videos_input)} 个视频\n")
        
        for i, line in enumerate(videos_input, 1):
            parts = line.split('|')
            
            if len(parts) >= 3:
                city, keyword, url = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                city, url = parts[0], parts[1]
                keyword = "房产"
            elif len(parts) == 1:
                url = parts[0]
                city, keyword = "未知", "房产"
            else:
                print(f"[{i}] ❌ 格式错误: {line}")
                continue
            
            print(f"\n[{i}/{len(videos_input)}] {city}-{keyword}")
            print(f"   URL: {url[:60]}...")
            
            video = self.process_video(url.strip(), city.strip(), keyword.strip())
            if video:
                self.results.append(video)
                print(f"   ✅ {video.title[:50]}...")
            else:
                print(f"   ❌ 处理失败")
        
        # 保存结果
        if self.results:
            self.save_to_database(self.results)
            
            # JSON 备份
            json_path = OUTPUT_DIR / f"batch_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(v) for v in self.results], f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON备份: {json_path}")
        
        # 总结
        print("\n" + "=" * 70)
        print("📊 导入完成")
        print("=" * 70)
        print(f"成功: {len(self.results)}/{len(videos_input)}")
        print(f"有字幕: {sum(1 for v in self.results if v.transcript)}")
        
        # 按城市统计
        city_stats = {}
        for v in self.results:
            city_stats[v.city] = city_stats.get(v.city, 0) + 1
        if city_stats:
            print(f"\n城市分布:")
            for city, count in sorted(city_stats.items()):
                print(f"   {city}: {count} 条")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 batch_video_import.py <视频列表文件>")
        print("\n视频列表文件格式（每行一个）:")
        print("  城市|关键词|链接")
        print("  示例: 北京|学区房|https://v.douyin.com/i5Q8Q9Q9/")
        sys.exit(1)
    
    importer = BatchVideoImporter()
    importer.run(sys.argv[1])
