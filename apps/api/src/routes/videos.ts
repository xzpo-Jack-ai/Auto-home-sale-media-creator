import { Router } from 'express';

const router = Router();

// 模拟视频数据
const mockVideos = [
  {
    id: '1',
    title: '北京这套房降了200万，业主急售！',
    author: '北京房产小李',
    views: 1250000,
    likes: 45000,
    cover: 'https://via.placeholder.com/300x400/FF6B6B/fff?text=视频1',
    duration: 45,
    publishedAt: '2024-02-20',
  },
  {
    id: '2',
    title: '海淀妈妈都在抢的学区房，到底值不值？',
    author: '学区房专家王姐',
    views: 890000,
    likes: 32000,
    cover: 'https://via.placeholder.com/300x400/4ECDC4/fff?text=视频2',
    duration: 62,
    publishedAt: '2024-02-19',
  },
  {
    id: '3',
    title: '2024年北京买房，这三个区域最有潜力',
    author: '房产投资老张',
    views: 2100000,
    likes: 78000,
    cover: 'https://via.placeholder.com/300x400/45B7D1/fff?text=视频3',
    duration: 88,
    publishedAt: '2024-02-18',
  },
  {
    id: '4',
    title: '北漂5年，终于凑够首付买了第一套房',
    author: '北漂青年阿杰',
    views: 560000,
    likes: 21000,
    cover: 'https://via.placeholder.com/300x400/96CEB4/fff?text=视频4',
    duration: 120,
    publishedAt: '2024-02-17',
  },
  {
    id: '5',
    title: '朝阳公园旁边的豪宅，带你看房',
    author: '豪宅顾问Lisa',
    views: 340000,
    likes: 12000,
    cover: 'https://via.placeholder.com/300x400/DDA0DD/fff?text=视频5',
    duration: 95,
    publishedAt: '2024-02-16',
  },
];

// GET /api/videos?keyword=xxx&city=xxx&page=1
router.get('/', (req, res) => {
  const { keyword, city, page = '1' } = req.query;
  const pageNum = parseInt(page as string, 10);
  const pageSize = 20;

  // 返回模拟数据，实际项目中从数据库/第三方API获取
  const videos = Array(20)
    .fill(null)
    .map((_, i) => ({
      ...mockVideos[i % mockVideos.length],
      id: `${pageNum}-${i}`,
      title: `${city || '北京'}${keyword || '房产'} - 视频${i + 1}`,
    }));

  res.json({
    videos,
    pagination: {
      page: pageNum,
      pageSize,
      total: 100,
      hasMore: pageNum < 5,
    },
  });
});

// GET /api/videos/:id
router.get('/:id', (req, res) => {
  const { id } = req.params;
  const video = mockVideos.find((v) => v.id === id) || mockVideos[0];

  res.json({
    ...video,
    id,
    description: '这是一个热门房产视频，点击拍同款获取文案和拍摄指导',
    transcript: '大家好，今天给大家带来一套超值房源。这套房子位于市中心，交通便利，周边配套齐全。业主因为换房急售，价格比同小区便宜20%。房子是三室两厅，南北通透，采光非常好。',
  });
});

export { router as videoRoutes };
