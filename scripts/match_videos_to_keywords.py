#!/usr/bin/env python3
"""
将视频与新的热词匹配
基于ASR文案内容，将视频归类到正确的热词下
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")

# 热词关键词映射
KEYWORD_MAPPING = {
    '沪七条新政': ['沪七条', '新政', '政策', '出台', '松绑'],
    '限购放松': ['限购', '放松', '放开', '取消', '松绑', '放宽'],
    '外环购房': ['外环', '外环内', '外环外', '环线'],
    '社保年限调整': ['社保', '年限', '三年', '一年', '居住证'],
    '公积金贷款': ['公积金', '贷款', '房贷', '利率', '贴息'],
}


def get_shanghai_videos():
    """获取上海的所有视频"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, author, transcript, title
        FROM videos
        WHERE city = '上海' AND transcript != ''
    ''')
    
    videos = []
    for row in cursor.fetchall():
        videos.append({
            'id': row[0],
            'author': row[1],
            'transcript': row[2] or '',
            'title': row[3] or ''
        })
    
    conn.close()
    return videos


def match_video_to_keyword(video):
    """根据文案内容匹配热词"""
    text = (video['transcript'] + ' ' + video['title']).lower()
    
    scores = {}
    for keyword, patterns in KEYWORD_MAPPING.items():
        score = 0
        for pattern in patterns:
            if pattern in text:
                score += 1
        if score > 0:
            scores[keyword] = score
    
    # 返回得分最高的热词
    if scores:
        return max(scores, key=scores.get)
    return '上海房产综合'


def update_video_keyword(video_id, keyword):
    """更新视频的keyword字段"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE videos SET keyword = ?, updatedAt = ? WHERE id = ?
    ''', (keyword, datetime.now().isoformat(), video_id))
    
    conn.commit()
    conn.close()


def main():
    print("=" * 70)
    print("🎯 视频热词匹配")
    print("=" * 70)
    
    # 获取视频
    videos = get_shanghai_videos()
    print(f"\n📊 找到 {len(videos)} 条有文案的上海视频")
    
    # 统计
    keyword_counts = {}
    
    # 匹配并更新
    for i, video in enumerate(videos, 1):
        keyword = match_video_to_keyword(video)
        
        print(f"\n[{i}/{len(videos)}] {video['author'][:20]}...")
        print(f"   匹配热词: {keyword}")
        
        # 更新数据库
        update_video_keyword(video['id'], keyword)
        
        # 统计
        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    
    print("\n" + "=" * 70)
    print("📊 匹配结果")
    print("=" * 70)
    for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {keyword}: {count} 个视频")
    
    print("\n✅ 视频热词匹配完成！")


if __name__ == '__main__':
    main()
