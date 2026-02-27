/**
 * 热词趋势 API 路由
 */

import { Router } from 'express';
import { prisma } from '../lib/prisma';
import { manualUpdate } from '../jobs/update-hot-trends.job';

const router = Router();

/**
 * GET /api/hot-trends?city=北京&limit=20
 * 获取指定城市的热词列表（按热度降序）
 */
router.get('/', async (req, res) => {
  try {
    const { city, limit = '20' } = req.query;
    const limitNum = parseInt(limit as string, 10);

    if (!city || typeof city !== 'string') {
      res.status(400).json({ error: 'Missing or invalid city parameter' });
      return;
    }

    // 获取今天的日期（用于筛选当天数据）
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 查询数据库
    const hotTrends = await prisma.hotTrend.findMany({
      where: {
        city,
        fetchedAt: {
          gte: today,
        },
      },
      orderBy: {
        heat: 'desc',
      },
      take: limitNum,
    });

    // 如果没有今天的数据，返回空数组并提示
    if (hotTrends.length === 0) {
      res.json({
        city,
        trends: [],
        message: '今日暂无热词数据，请稍后重试或联系管理员',
        nextUpdate: '明天 08:00',
      });
      return;
    }

    res.json({
      city,
      trends: hotTrends.map((trend, index) => ({
        id: trend.id,
        rank: index + 1,
        keyword: trend.keyword,
        heat: trend.heat,
        source: trend.source,
        updatedAt: trend.fetchedAt,
      })),
      total: hotTrends.length,
      updatedAt: hotTrends[0]?.fetchedAt,
    });

  } catch (error) {
    console.error('[HotTrends API] Error:', error);
    res.status(500).json({
      error: 'Failed to fetch hot trends',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * GET /api/hot-trends/:keyword/videos?city=北京
 * 获取与热词相关的视频列表
 */
router.get('/:keyword/videos', async (req, res) => {
  try {
    const { keyword } = req.params;
    const { city, page = '1', pageSize = '20' } = req.query;

    if (!city || typeof city !== 'string') {
      res.status(400).json({ error: 'Missing or invalid city parameter' });
      return;
    }

    const pageNum = parseInt(page as string, 10);
    const pageSizeNum = parseInt(pageSize as string, 10);

    // 查询与该热词相关的视频
    // 匹配逻辑：视频.keyword 包含热词关键词
    const videos = await prisma.video.findMany({
      where: {
        city,
        OR: [
          { keyword: { contains: keyword } },
          { title: { contains: keyword } },
        ],
      },
      orderBy: {
        views: 'desc', // 按播放量降序
      },
      skip: (pageNum - 1) * pageSizeNum,
      take: pageSizeNum,
    });

    const total = await prisma.video.count({
      where: {
        city,
        OR: [
          { keyword: { contains: keyword } },
          { title: { contains: keyword } },
        ],
      },
    });

    res.json({
      keyword,
      city,
      videos: videos.map(v => ({
        id: v.id,
        title: v.title,
        author: v.author,
        views: v.views,
        likes: v.likes,
        cover: v.coverUrl || `https://picsum.photos/300/400?random=${v.id}`,
        duration: v.duration || 60,
        publishedAt: v.publishedAt,
      })),
      pagination: {
        page: pageNum,
        pageSize: pageSizeNum,
        total,
        hasMore: pageNum * pageSizeNum < total,
      },
    });

  } catch (error) {
    console.error('[HotTrends API] Error:', error);
    res.status(500).json({
      error: 'Failed to fetch videos',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * POST /api/hot-trends/update
 * 手动触发热词更新（管理员接口）
 */
router.post('/update', async (req, res) => {
  try {
    console.log('[HotTrends API] Manual update triggered');

    // 异步执行更新，不等待完成
    manualUpdate().catch(error => {
      console.error('[HotTrends API] Manual update failed:', error);
    });

    res.json({
      success: true,
      message: 'Hot trends update started',
      note: 'Update runs in background, check logs for results',
    });

  } catch (error) {
    console.error('[HotTrends API] Error:', error);
    res.status(500).json({
      error: 'Failed to start update',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * GET /api/hot-trends/status
 * 获取热词更新状态
 */
router.get('/status', async (req, res) => {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 统计今天各城市的热词数量
    const cityStats = await prisma.hotTrend.groupBy({
      by: ['city'],
      where: {
        fetchedAt: {
          gte: today,
        },
      },
      _count: {
        id: true,
      },
    });

    // 计算下次更新时间
    const now = new Date();
    const nextUpdate = new Date();
    nextUpdate.setHours(8, 0, 0, 0);
    if (now.getHours() >= 8) {
      nextUpdate.setDate(nextUpdate.getDate() + 1);
    }

    res.json({
      status: 'active',
      schedule: 'Every day at 08:00 (Asia/Shanghai)',
      lastUpdate: cityStats.length > 0 ? 'Today' : 'Never',
      nextUpdate: nextUpdate.toISOString(),
      cityStats: cityStats.map(stat => ({
        city: stat.city,
        count: stat._count.id,
      })),
    });

  } catch (error) {
    console.error('[HotTrends API] Error:', error);
    res.status(500).json({
      error: 'Failed to fetch status',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export { router as hotTrendRoutes };
