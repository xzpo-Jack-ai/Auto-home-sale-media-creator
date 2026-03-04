import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';

dotenv.config();

import { keywordRoutes } from './routes/keywords';
import { videoRoutes } from './routes/videos';
import { aiRoutes } from './routes/ai';
import { uploadRoutes } from './routes/upload';
import { videoLinkRoutes } from './routes/video-link';
import { hotTrendRoutes } from './routes/hot-trends';
import { startHotTrendScheduler } from './jobs/update-hot-trends.job';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(morgan('dev'));
app.use(express.json({ limit: '10mb' }));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 简单的视频查询端点 - 绕过Prisma问题
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

app.get('/api/videos-simple', async (req, res) => {
  try {
    const { keyword, city } = req.query;
    
    if (!keyword || !city) {
      return res.status(400).json({ error: 'Missing keyword or city' });
    }

    // 使用Prisma但只选择基本字段，避免字符编码问题
    const videos = await prisma.$queryRaw`
      SELECT id, title, author, views, likes, "coverUrl", duration, "publishedAt", transcript 
      FROM videos 
      WHERE keyword = ${keyword as string} AND city = ${city as string}
      ORDER BY likes DESC
      LIMIT 20
    `;

    res.json({
      videos: (videos as any[]).map((v, i) => ({
        id: v.id,
        title: v.title,
        author: v.author,
        views: v.views || 0,
        likes: v.likes || 0,
        cover: v.coverUrl || `https://picsum.photos/300/400?random=${v.id}`,
        duration: v.duration || 60,
        publishedAt: v.publishedAt,
        transcript: v.transcript,
        rank: i + 1,
      })),
      pagination: {
        page: 1,
        pageSize: 20,
        total: (videos as any[]).length,
        hasMore: false,
      },
    });
  } catch (error) {
    console.error('Failed to fetch videos:', error);
    res.status(500).json({ error: 'Failed to fetch videos' });
  }
});

// Routes
app.use('/api/keywords', keywordRoutes);
app.use('/api/videos', videoRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/video-link', videoLinkRoutes);
app.use('/api/hot-trends', hotTrendRoutes);

// Error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`🚀 API server running on port ${PORT}`);

  // 启动热词定时更新任务
  startHotTrendScheduler();
  console.log('📅 Hot trend scheduler started (daily at 08:00)');
});
