#!/usr/bin/env python3
"""
AI 热词分析器
使用 DeepSeek API 智能分析视频标题，提取热词并归类
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Dict, Tuple
import asyncio
import subprocess

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-33541ab8928843a99ff27096df24d29f")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


@dataclass
class Video:
    city: str
    title: str
    url: str
    transcript: str = ""


@dataclass
class HotKeyword:
    keyword: str
    category: str
    videos: List[Video]
    heat_score: int = 0


class AIHotKeywordAnalyzer:
    """AI 热词分析器"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
    
    async def analyze_titles(self, videos: List[Video]) -> List[HotKeyword]:
        """
        使用 DeepSeek 分析所有标题，提取热词
        """
        # 构建提示词
        titles_text = "\n".join([
            f"{i+1}. [{v.city}] {v.title}"
            for i, v in enumerate(videos)
        ])
        
        prompt = f"""你是一个房产领域的内容分析专家。请分析以下视频标题，提取热词并归类。

## 视频标题列表：
{titles_text}

## 任务要求：
1. 从标题中提取房产相关热词（如：学区房、新房开盘、房贷利率、限购政策等）
2. 为每个热词标注分类（如：政策类、房源类、区域类、投资类等）
3. 返回每个热词对应的视频编号列表
4. 评估每个热词的热度分数（1-100，基于提及频率和重要性）

## 输出格式（JSON）：
{{
  "hot_keywords": [
    {{
      "keyword": "学区房",
      "category": "房源类",
      "video_indices": [1, 5, 8],
      "heat_score": 85
    }},
    ...
  ]
}}

注意：
- 只输出 JSON，不要其他解释
- 确保 video_indices 是有效的编号（从1开始）
- 热度分数要合理反映实际重要性
"""
        
        print("🤖 调用 DeepSeek API 分析热词...")
        
        try:
            # 使用 curl 调用 API
            import subprocess
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个专业的房产内容分析助手，擅长从视频标题中提取热词和趋势。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            result = subprocess.run(
                [
                    'curl', '-s', self.api_url,
                    '-H', f'Authorization: Bearer {self.api_key}',
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(payload)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"❌ API 调用失败: {result.stderr}")
                return []
            
            response_data = json.loads(result.stdout)
            content = response_data["choices"][0]["message"]["content"]
            
            # 解析 JSON
            try:
                # 清理可能的 markdown 代码块
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                
                data = json.loads(content.strip())
                keywords_data = data.get("hot_keywords", [])
                
                # 转换为 HotKeyword 对象
                hot_keywords = []
                for kw_data in keywords_data:
                    indices = kw_data.get("video_indices", [])
                    keyword_videos = [
                        videos[i-1] for i in indices
                        if 1 <= i <= len(videos)
                    ]
                    
                    hot_keywords.append(HotKeyword(
                        keyword=kw_data.get("keyword", "未知"),
                        category=kw_data.get("category", "其他"),
                        videos=keyword_videos,
                        heat_score=kw_data.get("heat_score", 50)
                    ))
                
                print(f"   ✅ AI 提取了 {len(hot_keywords)} 个热词")
                return hot_keywords
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析错误: {e}")
                print(f"原始内容: {content[:500]}...")
                return []
                        
        except Exception as e:
            print(f"❌ API 调用失败: {e}")
            return []
    
    async def analyze_with_fallback(self, videos: List[Video]) -> List[HotKeyword]:
        """
        AI 分析，失败时回退到规则匹配
        """
        ai_result = await self.analyze_titles(videos)
        
        if ai_result:
            return ai_result
        
        print("⚠️ AI 分析失败，使用规则匹配回退...")
        return self._rule_based_analysis(videos)
    
    def _rule_based_analysis(self, videos: List[Video]) -> List[HotKeyword]:
        """
        基于规则的热词分析（回退方案）
        """
        keyword_patterns = {
            "学区房": ["学区", "学校", "教育", "名校"],
            "新房开盘": ["新房", "开盘", "楼盘", "预售"],
            "二手房": ["二手", "置换", "改善", "挂牌"],
            "房价走势": ["房价", "涨跌", "价格", "暴跌", "暴涨"],
            "购房政策": ["政策", "限购", "调控", "松绑", "放开"],
            "房贷利率": ["房贷", "利率", "贷款", "公积金"],
            "投资理财": ["投资", "升值", "回报", "抄底"],
            "区域分析": ["海淀", "朝阳", "浦东", "徐汇", "南山"],
            "买房避坑": ["避坑", "陷阱", "套路", "骗局"],
            "看房攻略": ["看房", "选房", "攻略", "技巧"],
        }
        
        keyword_map: Dict[str, List[Video]] = {}
        
        for video in videos:
            title = video.title.lower()
            matched = False
            
            for keyword, patterns in keyword_patterns.items():
                for pattern in patterns:
                    if pattern in title:
                        city_keyword = f"{video.city}-{keyword}"
                        if city_keyword not in keyword_map:
                            keyword_map[city_keyword] = []
                        keyword_map[city_keyword].append(video)
                        matched = True
                        break
            
            if not matched:
                # 未匹配到任何关键词
                default_keyword = f"{video.city}-房产综合"
                if default_keyword not in keyword_map:
                    keyword_map[default_keyword] = []
                keyword_map[default_keyword].append(video)
        
        # 转换为 HotKeyword 列表
        hot_keywords = []
        for keyword, vids in sorted(keyword_map.items(), key=lambda x: len(x[1]), reverse=True):
            parts = keyword.split("-", 1)
            city = parts[0]
            kw = parts[1] if len(parts) > 1 else keyword
            
            # 计算热度分数
            heat = min(100, len(vids) * 10 + 20)
            
            hot_keywords.append(HotKeyword(
                keyword=kw,
                category="规则匹配",
                videos=vids,
                heat_score=heat
            ))
        
        return hot_keywords
    
    def generate_summary(self, hot_keywords: List[HotKeyword]) -> Dict:
        """
        生成热词分析报告
        """
        # 按热度排序
        sorted_keywords = sorted(hot_keywords, key=lambda x: x.heat_score, reverse=True)
        
        summary = {
            "total_keywords": len(hot_keywords),
            "top_keywords": [
                {
                    "keyword": kw.keyword,
                    "category": kw.category,
                    "video_count": len(kw.videos),
                    "heat_score": kw.heat_score,
                    "cities": list(set(v.city for v in kw.videos))
                }
                for kw in sorted_keywords[:10]
            ],
            "category_distribution": {},
            "city_distribution": {}
        }
        
        # 分类统计
        for kw in hot_keywords:
            cat = kw.category
            summary["category_distribution"][cat] = summary["category_distribution"].get(cat, 0) + len(kw.videos)
        
        # 城市统计
        for kw in hot_keywords:
            for v in kw.videos:
                city = v.city
                summary["city_distribution"][city] = summary["city_distribution"].get(city, 0) + 1
        
        return summary


async def test_analyzer():
    """测试分析器"""
    # 模拟视频数据
    videos = [
        Video("北京", "北京学区房购买全攻略2026", "url1"),
        Video("北京", "海淀学区房价走势分析", "url2"),
        Video("北京", "西城学区房还值得买吗？", "url3"),
        Video("上海", "上海浦东新房测评", "url4"),
        Video("上海", "上海房贷利率最新政策解读", "url5"),
        Video("深圳", "深圳南山房价跌了？", "url6"),
        Video("深圳", "深圳买房避坑指南", "url7"),
    ]
    
    analyzer = AIHotKeywordAnalyzer()
    
    print("=" * 70)
    print("🧪 AI 热词分析器测试")
    print("=" * 70)
    
    hot_keywords = await analyzer.analyze_with_fallback(videos)
    
    print("\n📊 分析结果:")
    for kw in hot_keywords[:5]:
        print(f"\n🔥 {kw.keyword} (热度: {kw.heat_score})")
        print(f"   分类: {kw.category}")
        print(f"   视频数: {len(kw.videos)}")
        for v in kw.videos[:3]:
            print(f"     - [{v.city}] {v.title}")
    
    # 生成摘要
    summary = analyzer.generate_summary(hot_keywords)
    print("\n📈 统计摘要:")
    print(f"   总热词数: {summary['total_keywords']}")
    print(f"   分类分布: {summary['category_distribution']}")
    print(f"   城市分布: {summary['city_distribution']}")


if __name__ == '__main__':
    asyncio.run(test_analyzer())
