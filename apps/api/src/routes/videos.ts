import { Router } from 'express';
import { VideoDAO } from '../services/video.service';

const router = Router();

// GET /api/videos?keyword=xxx&city=xxx&page=1
router.get('/', async (req, res) => {
  try {
    const { keyword, city, page = '1' } = req.query;
    const pageNum = parseInt(page as string, 10);
    const pageSize = 20;

    const { videos, total } = await VideoDAO.getByKeyword(
      (keyword as string) || '',
      (city as string) || '北京',
      pageNum,
      pageSize
    );

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
      videos: videos.map((v, i) => ({
        id: v.id,
        title: v.title,
        author: v.author,
        views: v.views,
        likes: v.likes,
        cover: v.coverUrl || `https://picsum.photos/300/400?random=${v.id}`,
        duration: v.duration || 60,
        publishedAt: v.publishedAt,
        transcript: v.transcript, // 返回文案供前端使用
        rank: i + 1,
      })),
      pagination: {
        page: pageNum,
        pageSize,
        total,
        hasMore: pageNum * pageSize < total,
      },
    });
  } catch (error) {
    console.error('Failed to fetch videos:', error);
    res.status(500).json({ error: 'Failed to fetch videos' });
  }
});

// GET /api/videos/:id
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const video = await VideoDAO.getById(id);

    if (!video) {
      res.status(404).json({ error: 'Video not found' });
      return;
    }

    res.json({
      id: video.id,
      title: video.title,
      author: video.author,
      views: video.views,
      likes: video.likes,
      cover: video.coverUrl || `https://picsum.photos/300/400?random=${video.id}`,
      duration: video.duration || 60,
      publishedAt: video.publishedAt,
      description: '这是一个热门房产视频，点击拍同款获取文案和拍摄指导',
      transcript:
        video.transcript ||
        '大家好，今天给大家带来一套超值房源。这套房子位于市中心，交通便利，周边配套齐全。业主因为换房急售，价格比同小区便宜20%。房子是三室两厅，南北通透，采光非常好。',
    });
  } catch (error) {
    console.error('Failed to fetch video:', error);
    res.status(500).json({ error: 'Failed to fetch video' });
  }
});

export { router as videoRoutes };
