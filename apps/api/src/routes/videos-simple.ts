import { Router } from 'express';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

const router = Router();

// 简单的视频查询路由 - 使用SQLite直接查询绕过Prisma问题
router.get('/', async (req, res) => {
  try {
    const { keyword, city, page = '1' } = req.query;
    const pageNum = parseInt(page as string, 10);
    const pageSize = 20;
    const skip = (pageNum - 1) * pageSize;

    // 打开数据库连接
    const db = await open({
      filename: process.env.DATABASE_URL?.replace('file:', '') || './dev.db',
      driver: sqlite3.Database
    });

    // 查询视频
    const videos = await db.all(
      `SELECT * FROM videos WHERE keyword = ? AND city = ? ORDER BY views DESC, likes DESC LIMIT ? OFFSET ?`,
      [keyword, city, pageSize, skip]
    );

    // 查询总数
    const countResult = await db.get(
      `SELECT COUNT(*) as count FROM videos WHERE keyword = ? AND city = ?`,
      [keyword, city]
    );

    await db.close();

    const total = countResult?.count || 0;

    // 如果没有找到视频，返回提示
    if (videos.length === 0) {
      res.json({
        videos: [],
        pagination: {
          page: pageNum,
          pageSize,
          total: 0,
          hasMore: false,
        },
        message: '该城市暂无视频数据，请先录入',
      });
      return;
    }

    res.json({
      videos: videos.map((v: any, i: number) => ({
        id: v.id,
        title: v.title,
        author: v.author,
        views: v.views,
        likes: v.likes,
        cover: v.coverUrl || `https://picsum.photos/300/400?random=${v.id}`,
        duration: v.duration || 60,
        publishedAt: v.publishedAt,
        transcript: v.transcript,
        rank: i + 1,
      })),
      pagination: {
        page: pageNum,
        pageSize,
        total,
        hasMore: total > pageNum * pageSize,
      },
    });
  } catch (error) {
    console.error('Failed to fetch videos:', error);
    res.status(500).json({ error: 'Failed to fetch videos', details: (error as Error).message });
  }
});

export { router as videoSimpleRoutes };
