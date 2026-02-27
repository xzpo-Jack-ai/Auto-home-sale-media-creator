/**
 * 抖音热榜服务
 * 封装 douyin-hot-trend skill，提供房产热词过滤和城市分类
 */

import { execFile } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execFileAsync = promisify(execFile);

// 房产关键词库
export const REAL_ESTATE_KEYWORDS = [
  // 核心房产词
  '房', '楼盘', '小区', '房价', '买房', '卖房', '购房',
  '租房', '地产', '楼市', '房源', '房产', '住房',
  // 房屋类型
  '公寓', '住宅', '商铺', '写字楼', '豪宅', '别墅', '洋房',
  '大平层', 'loft', '四合院', '学区房',
  // 交易相关
  '首付', '贷款', '月供', '契税', '过户', '网签', '摇号',
  '认筹', '开盘', '交房', '入住', '装修',
  // 区域特征
  '地铁房', '江景房', '海景房', '湖景房', '山景房',
  '市中心', '郊区', '新城', '开发区',
  // 市场动态
  '降价', '涨价', '暴跌', '暴涨', '抄底', '高位接盘',
  '限购', '限售', '限贷', '调控', '政策',
];

// 城市关键词映射
export const CITY_KEYWORDS: Record<string, string[]> = {
  '北京': ['北京', '帝都', '京城', '北平'],
  '上海': ['上海', '魔都', '沪'],
  '广州': ['广州', '羊城', '穗'],
  '深圳': ['深圳', '鹏城', '深'],
  '杭州': ['杭州', '杭城', '西湖'],
  '南京': ['南京', '金陵', '宁'],
  '苏州': ['苏州', '姑苏', '苏'],
  '成都': ['成都', '蓉城', '蓉'],
  '武汉': ['武汉', '江城', '汉'],
  '西安': ['西安', '长安', '镐'],
  '重庆': ['重庆', '山城', '渝'],
  '天津': ['天津', '津门', '津'],
};

// 抖音热榜原始数据项
export interface DouyinHotItem {
  rank: number;
  title: string;
  popularity: number;
  link: string;
  label?: string | null;
  type?: string;
}

// 房产热词数据项
export interface RealEstateHotItem extends DouyinHotItem {
  matchedKeywords: string[]; // 匹配到的房产关键词
  city?: string; // 归属城市
}

// 城市热词映射
export interface CityHotMap {
  [city: string]: RealEstateHotItem[];
}

/**
 * 解析 douyin-hot-trend 的输出文本
 */
function parseDouyinOutput(stdout: string): DouyinHotItem[] {
  const items: DouyinHotItem[] = [];
  const lines = stdout.split('\n');

  let currentRank = 0;
  let currentTitle = '';
  let currentHeat = 0;
  let currentLink = '';
  let currentLabel: string | null = null;

  for (const line of lines) {
    const trimmed = line.trim();

    // 匹配排名和标题: "1. 四六级查分"
    const rankMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (rankMatch) {
      // 保存上一个条目
      if (currentRank > 0 && currentTitle) {
        items.push({
          rank: currentRank,
          title: currentTitle,
          popularity: currentHeat,
          link: currentLink,
          label: currentLabel,
        });
      }

      currentRank = parseInt(rankMatch[1], 10);
      currentTitle = rankMatch[2];
      currentHeat = 0;
      currentLink = '';
      currentLabel = null;
      continue;
    }

    // 匹配热度: "🔥 热度: 12,162,417"
    const heatMatch = trimmed.match(/热度:\s*([\d,]+)/);
    if (heatMatch) {
      currentHeat = parseInt(heatMatch[1].replace(/,/g, ''), 10);
      continue;
    }

    // 匹配标签: "🏷️  标签: 3"
    const labelMatch = trimmed.match(/标签:\s*(\d+)/);
    if (labelMatch) {
      currentLabel = labelMatch[1];
      continue;
    }

    // 匹配链接: "🔗 链接: https://..."
    const linkMatch = trimmed.match(/链接:\s*(https:\/\/\S+)/);
    if (linkMatch) {
      currentLink = linkMatch[1];
      continue;
    }
  }

  // 保存最后一个条目
  if (currentRank > 0 && currentTitle) {
    items.push({
      rank: currentRank,
      title: currentTitle,
      popularity: currentHeat,
      link: currentLink,
      label: currentLabel,
    });
  }

  return items;
}

/**
 * 调用 douyin-hot-trend skill 获取原始热榜数据
 */
export async function fetchHotTrends(limit: number = 50): Promise<DouyinHotItem[]> {
  const skillPath = '/Volumes/movespace/openclaw/code/skills/douyin-hot-trend/scripts/douyin.js';

  try {
    console.log('[DouyinHot] Fetching hot trends...');
    const startTime = Date.now();

    const { stdout } = await execFileAsync(
      'node',
      [skillPath, 'hot', limit.toString()],
      {
        timeout: 30000,
        maxBuffer: 10 * 1024 * 1024,
      }
    );

    // 解析输出（从格式化文本中提取数据）
    const items = parseDouyinOutput(stdout);

    if (items.length === 0) {
      throw new Error('No data parsed from output');
    }
    const duration = Date.now() - startTime;

    console.log(`[DouyinHot] Fetched ${items.length} items in ${duration}ms`);
    return items;
  } catch (error) {
    console.error('[DouyinHot] Failed to fetch:', error);
    throw new Error('Failed to fetch Douyin hot trends');
  }
}

/**
 * 过滤房产相关热词
 */
export function filterRealEstate(items: DouyinHotItem[]): RealEstateHotItem[] {
  const result: RealEstateHotItem[] = [];

  for (const item of items) {
    const matchedKeywords: string[] = [];

    // 检查是否包含房产关键词
    for (const keyword of REAL_ESTATE_KEYWORDS) {
      if (item.title.includes(keyword)) {
        matchedKeywords.push(keyword);
      }
    }

    // 如果匹配到至少一个房产关键词，保留
    if (matchedKeywords.length > 0) {
      result.push({
        ...item,
        matchedKeywords,
      });
    }
  }

  console.log(`[DouyinHot] Filtered ${result.length}/${items.length} real estate items`);
  return result;
}

/**
 * 按城市分类热词
 */
export function classifyByCity(items: RealEstateHotItem[]): CityHotMap {
  const cityMap: CityHotMap = {};

  // 初始化所有城市为空数组
  for (const city of Object.keys(CITY_KEYWORDS)) {
    cityMap[city] = [];
  }

  for (const item of items) {
    let matchedCity: string | undefined;

    // 检查标题中包含哪个城市关键词
    for (const [city, keywords] of Object.entries(CITY_KEYWORDS)) {
      for (const keyword of keywords) {
        if (item.title.includes(keyword)) {
          matchedCity = city;
          break;
        }
      }
      if (matchedCity) break;
    }

    // 如果匹配到城市，归类；否则标记为"全国"
    if (matchedCity) {
      cityMap[matchedCity].push({
        ...item,
        city: matchedCity,
      });
    } else {
      if (!cityMap['全国']) {
        cityMap['全国'] = [];
      }
      cityMap['全国'].push({
        ...item,
        city: '全国',
      });
    }
  }

  // 清理空城市
  for (const city of Object.keys(cityMap)) {
    if (cityMap[city].length === 0 && city !== '全国') {
      delete cityMap[city];
    }
  }

  console.log(`[DouyinHot] Classified into ${Object.keys(cityMap).length} cities`);
  return cityMap;
}

/**
 * 完整流程：获取 → 过滤 → 分类
 */
export async function getRealEstateHotTrends(
  limit: number = 50
): Promise<CityHotMap> {
  // 1. 获取原始数据
  const rawItems = await fetchHotTrends(limit);

  // 2. 过滤房产相关
  const realEstateItems = filterRealEstate(rawItems);

  // 3. 按城市分类
  const cityMap = classifyByCity(realEstateItems);

  return cityMap;
}

/**
 * 保存热词到数据库（由 job 调用）
 */
export async function saveHotTrendsToDatabase(cityMap: CityHotMap): Promise<void> {
  const { prisma } = await import('../lib/prisma');

  const now = new Date();

  for (const [city, items] of Object.entries(cityMap)) {
    for (const item of items) {
      await prisma.hotTrend.upsert({
        where: {
          city_keyword_fetchedAt: {
            city,
            keyword: item.title,
            fetchedAt: now,
          },
        },
        update: {
          heat: item.popularity,
          rank: item.rank,
        },
        create: {
          city,
          keyword: item.title,
          heat: item.popularity,
          rank: item.rank,
          source: 'douyin',
          fetchedAt: now,
        },
      });
    }
  }

  console.log(`[DouyinHot] Saved hot trends to database`);
}
