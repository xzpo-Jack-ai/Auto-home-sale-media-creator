#!/usr/bin/env python3
"""
处理 Excel 视频数据文件
从抖音导出的 Excel 中提取音频链接，进行 ASR 识别
"""

import zipfile
import re
import json
import sqlite3
import html
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 配置
DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ASR 脚本路径
DASHSCOPE_ASR_SCRIPT = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/scripts/douyin-audio-asr.py")


def extract_excel_data(file_path: str) -> List[Dict]:
    """从 Excel 文件中提取数据"""
    print(f"📖 读取 Excel: {file_path}")
    
    with zipfile.ZipFile(file_path) as z:
        # 读取共享字符串
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
            # 提取所有文本内容
            shared_strings = re.findall(r'<t[^>]*>([^<]+)</t>', ss_xml)
        
        # 读取 sheet1
        sheet_xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
        
        # 找到表头位置
        headers = []
        header_indices = {}
        
        # 关键字段映射
        key_fields = {
            '账号昵称': 'author',
            '作者粉丝数': 'fans_count',
            '发布时间': 'publish_time',
            '获赞数': 'likes',
            '收藏数': 'favorites',
            '评论数': 'comments',
            '分享数': 'shares',
            '热搜词': 'hot_keywords',
            '作品链接': 'video_url',
            '封面链接': 'cover_url',
            '音频链接': 'audio_url',
            '作品时长': 'duration',
            '关联话题': 'topics',
        }
        
        # 解析表头（前24个字符串通常是表头）
        for i, s in enumerate(shared_strings[:24]):
            if s in key_fields:
                header_indices[key_fields[s]] = i
                headers.append(key_fields[s])
        
        print(f"   发现字段: {list(header_indices.keys())}")
        
        # 解析数据行
        # 简单方法：按行提取所有 <v> 标签的值（引用共享字符串的索引）
        videos = []
        
        # 找到所有行
        rows = re.findall(r'<row[^>]*>(.*?)</row>', sheet_xml, re.DOTALL)
        
        print(f"   总行数: {len(rows)}")
        
        for row_idx, row_xml in enumerate(rows[1:], 2):  # 跳过表头行
            try:
                # 提取该行的所有单元格值
                # <c ...><v>数字</v></c> 表示引用 sharedStrings 的索引
                cell_values = re.findall(r'<c[^>]*>(?:<is>.*?<t>([^<]+)</t>.*?</is>|<v>([^<]+)</v>)</c>', row_xml)
                
                # 合并匹配结果
                values = [v[0] if v[0] else v[1] for v in cell_values]
                
                # 构建视频数据
                video = {}
                for field, idx in header_indices.items():
                    if idx < len(values):
                        value = values[idx]
                        # 如果是数字索引，从 shared_strings 获取
                        if value.isdigit():
                            si = int(value)
                            if si < len(shared_strings):
                                value = shared_strings[si]
                        # 解码 HTML 实体（如 &#38738; → 青）
                        value = html.unescape(value)
                        video[field] = value
                
                # 只保留有音频链接的记录
                if video.get('audio_url') or video.get('video_url'):
                    videos.append(video)
                    
            except Exception as e:
                print(f"   解析第{row_idx}行出错: {e}")
                continue
        
        print(f"   ✅ 成功提取 {len(videos)} 条视频记录")
        return videos


def extract_audio_asr(audio_url: str) -> Optional[str]:
    """使用 ASR 提取音频文案"""
    if not audio_url:
        return None
    
    try:
        print(f"      🎙️ ASR识别音频...")
        
        # 下载音频并识别
        # 这里需要实现音频下载 + ASR 的逻辑
        # 暂时返回空，后续可以集成 DashScope ASR
        
        return ""
        
    except Exception as e:
        print(f"      ❌ ASR失败: {e}")
        return None


def save_to_database(videos: List[Dict]):
    """保存到数据库"""
    if not DB_PATH.exists():
        print(f"⚠️ 数据库不存在: {DB_PATH}")
        return False
    
    print("\n💾 保存到数据库...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for v in videos:
            external_id = f"dy_excel_{hash(v.get('video_url', '')) % 1000000}_{int(datetime.now().timestamp())}"
            
            # 处理发布时间
            publish_time = v.get('publish_time', '')
            if not publish_time or publish_time == 'None':
                publish_time = datetime.now().isoformat()
            
            # 处理城市和关键词
            keyword = v.get('hot_keywords', '')
            if not keyword or keyword == 'None':
                keyword = '房产综合'
            
            # 从热词、作者、话题推断城市（默认上海）
            city = '上海'  # 根据用户输入，这批数据都是上海的
            author = v.get('author', '')
            topics = v.get('topics', '')
            
            # 如果明确提到其他城市，再修改
            if '北京' in keyword or '北京' in author or '北京' in topics:
                city = '北京'
            elif '深圳' in keyword or '深圳' in author or '深圳' in topics:
                city = '深圳'
            elif '杭州' in keyword or '杭州' in author or '杭州' in topics:
                city = '杭州'
            elif '广州' in keyword or '广州' in author or '广州' in topics:
                city = '广州'
            
            cursor.execute('''
                INSERT OR REPLACE INTO videos (
                    id, externalId, platform, title, author, authorId,
                    views, likes, shares, comments, coverUrl, videoUrl,
                    duration, transcript, publishedAt, keyword, city, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                external_id,
                external_id,
                'douyin',
                keyword[:150] if len(keyword) > 150 else keyword,
                v.get('author', '未知作者')[:50],
                '',
                0,
                int(float(v.get('likes', 0))) if v.get('likes') and str(v.get('likes')).replace('.','').isdigit() else 0,
                int(float(v.get('shares', 0))) if v.get('shares') and str(v.get('shares')).replace('.','').isdigit() else 0,
                int(float(v.get('comments', 0))) if v.get('comments') and str(v.get('comments')).replace('.','').isdigit() else 0,
                v.get('cover_url', ''),
                v.get('video_url', ''),
                v.get('duration', ''),
                v.get('transcript', '')[:2000],
                publish_time,
                keyword[:50],
                city,
                datetime.now().isoformat()
            ))
            saved += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ 保存 {saved} 条视频")
        return True
        
    except Exception as e:
        print(f"❌ 数据库错误: {e}")
        return False


def generate_report(videos: List[Dict], output_file: str):
    """生成处理报告"""
    report = {
        'date': datetime.now().isoformat(),
        'total_videos': len(videos),
        'with_audio': sum(1 for v in videos if v.get('audio_url')),
        'with_transcript': sum(1 for v in videos if v.get('transcript')),
        'videos': [
            {
                'author': v.get('author', ''),
                'hot_keywords': v.get('hot_keywords', ''),
                'video_url': v.get('video_url', ''),
                'audio_url': v.get('audio_url', ''),
                'transcript_preview': v.get('transcript', '')[:100] if v.get('transcript') else None
            }
            for v in videos[:20]  # 只显示前20个
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 报告已生成: {output_file}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 process_excel_videos.py <excel文件>")
        print("\n示例:")
        print("  python3 process_excel_videos.py weekly_videos.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    print("=" * 70)
    print("📊 Excel 视频数据处理")
    print("=" * 70)
    
    # 1. 提取数据
    videos = extract_excel_data(excel_file)
    
    # 2. 显示样本
    print("\n📋 数据样本（前3条）:")
    for i, v in enumerate(videos[:3], 1):
        print(f"\n{i}. 作者: {v.get('author', 'N/A')}")
        print(f"   热词: {v.get('hot_keywords', 'N/A')}")
        print(f"   视频: {v.get('video_url', 'N/A')[:60]}...")
        print(f"   音频: {v.get('audio_url', 'N/A')[:60]}..." if v.get('audio_url') else "   音频: 无")
    
    # 3. 保存到数据库
    save_to_database(videos)
    
    # 4. 生成报告
    report_file = OUTPUT_DIR / f"excel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    generate_report(videos, str(report_file))
    
    print("\n" + "=" * 70)
    print("✅ 处理完成")
    print("=" * 70)
    print(f"总视频数: {len(videos)}")
    print(f"有音频链接: {sum(1 for v in videos if v.get('audio_url'))}")
    print(f"报告: {report_file}")


if __name__ == '__main__':
    main()
