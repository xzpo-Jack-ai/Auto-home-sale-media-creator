#!/usr/bin/env python3
"""
从ASR文案生成热词
使用DeepSeek AI分析文案，提取热词并更新数据库
"""

import sqlite3
import json
import subprocess
from pathlib import Path
from datetime import datetime

DB_PATH = Path("/Volumes/movespace/workspace/Auto-home-sale-media-creator/apps/api/dev.db")
DEEPSEEK_API_KEY = "sk-33541ab8928843a99ff27096df24d29f"


def get_shanghai_transcripts():
    """获取上海的ASR文案"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, author, transcript, likes
        FROM videos
        WHERE city = '上海' AND transcript != '' AND id LIKE 'dy_excel%'
        ORDER BY likes DESC
    ''')
    
    videos = []
    for row in cursor.fetchall():
        videos.append({
            'id': row[0],
            'author': row[1],
            'transcript': row[2],
            'likes': row[3]
        })
    
    conn.close()
    return videos


def analyze_with_deepseek(videos):
    """使用DeepSeek分析文案，提取热词"""
    # 构建提示词
    transcripts_text = "\n\n".join([
        f"视频{i+1} (作者: {v['author']}, 点赞: {v['likes']}):\n{v['transcript'][:300]}..."
        for i, v in enumerate(videos[:15])  # 取前15条
    ])
    
    prompt = f"""你是房产内容分析专家。请分析以下上海房产视频的文案，提取热门关键词。

## 文案内容：
{transcripts_text}

## 任务：
1. 从文案中提取5-10个最热门的房产相关关键词
2. 每个关键词给出热度分数（1-100，基于提及频率和重要性）
3. 关键词要具体，如"沪七条新政"、"外环限购放松"等

## 输出格式（JSON）：
{{
  "hot_keywords": [
    {{"keyword": "沪七条新政", "heat": 95}},
    {{"keyword": "外环限购放松", "heat": 88}},
    ...
  ]
}}

只输出JSON，不要其他解释。"""
    
    print("🤖 调用DeepSeek分析文案...")
    
    try:
        # 使用curl调用API
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是专业的房产内容分析助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        result = subprocess.run(
            [
                'curl', '-s', 'https://api.deepseek.com/v1/chat/completions',
                '-H', f'Authorization: Bearer {DEEPSEEK_API_KEY}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(payload)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        response = json.loads(result.stdout)
        content = response["choices"][0]["message"]["content"]
        
        # 解析JSON
        content = content.replace('```json', '').replace('```', '').strip()
        data = json.loads(content)
        
        return data.get("hot_keywords", [])
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return []


def save_keywords_to_db(keywords):
    """保存热词到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved = 0
    now = datetime.now().isoformat()
    
    for kw in keywords:
        keyword_text = kw.get("keyword", "")
        heat = kw.get("heat", 50)
        
        if not keyword_text:
            continue
        
        # 插入或更新
        cursor.execute('''
            INSERT INTO keywords (id, city, text, heat, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, text) DO UPDATE SET
                heat = excluded.heat,
                updatedAt = excluded.updatedAt
        ''', (
            f"kw_sh_{hash(keyword_text) % 1000000}_{int(datetime.now().timestamp())}",
            '上海',
            keyword_text,
            heat,
            now,
            now
        ))
        saved += 1
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ 保存 {saved} 个热词")


def main():
    print("=" * 70)
    print("🔥 从ASR文案生成上海热词")
    print("=" * 70)
    
    # 1. 获取文案
    videos = get_shanghai_transcripts()
    print(f"\n📊 找到 {len(videos)} 条有文案的视频")
    
    if len(videos) < 5:
        print("⚠️ 文案数量不足，无法生成热词")
        return
    
    # 2. AI分析
    keywords = analyze_with_deepseek(videos)
    
    if not keywords:
        print("⚠️ 未能提取热词")
        return
    
    print(f"\n✅ 提取了 {len(keywords)} 个热词:")
    for kw in keywords:
        print(f"   • {kw['keyword']} (热度: {kw['heat']})")
    
    # 3. 保存到数据库
    save_keywords_to_db(keywords)
    
    print("\n" + "=" * 70)
    print("✅ 热词生成完成！")
    print("=" * 70)
    print("\n现在可以访问前端查看上海热词并触发文案洗稿了:")
    print("   http://localhost:3000")


if __name__ == '__main__':
    main()
