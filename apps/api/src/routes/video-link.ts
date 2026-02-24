import { Router } from 'express';
import { parseVideoLink, extractLinkFromText, type ParsedVideoLink } from '@auto-home/shared';
import { VideoDAO } from '../services/video.service';
import { KeywordDAO } from '../services/keyword.service';
import { prisma } from '../lib/prisma';

const router = Router();

/**
 * POST /api/video-link/parse
 * 解析视频链接并录入
 * Body: { 
 *   link: string,           // 抖音/视频号分享链接
 *   city: string,           // 城市
 *   transcript?: string,    // 视频文案（手动提供）
 *   keyword?: string        // 关键词分类
 * }
 */
router.post('/parse', async (req, res) => {
  try {
    const { link, city, transcript, keyword } = req.body;

    if (!link || !city) {
      res.status(400).json({ error: 'Missing link or city parameter' });
      return;
    }

    // 1. 提取并解析链接
    const linkToParse = extractLinkFromText(link) || link;
    const parsed = parseVideoLink(linkToParse);

    if (!parsed) {
      res.status(400).json({ 
        error: 'Invalid video link', 
        message: '无法识别链接格式，请提供抖音或视频号分享链接' 
      });
      return;
    }

    // 2. 检查是否已存在
    const existingVideo = await prisma.video.findUnique({
      where: { externalId: `${parsed.platform}-${parsed.shortCode}` },
    });

    if (existingVideo) {
      res.json({
        success: true,
        message: '视频已存在',
        video: existingVideo,
        isNew: false,
      });
      return;
    }

    // 3. 如果没有提供文案，提示用户
    if (!transcript) {
      res.json({
        success: false,
        needsTranscript: true,
        message: '链接已解析，但需要提供视频文案才能使用AI洗稿功能',
        parsed: {
          platform: parsed.platform,
          shortCode: parsed.shortCode,
          fullUrl: parsed.fullUrl,
        },
      });
      return;
    }

    // 4. 生成标题（从文案前20字或用户提供）
    const title = transcript.substring(0, 30) + '...';

    // 5. 创建视频记录
    const video = await prisma.video.create({
      data: {
        externalId: `${parsed.platform}-${parsed.shortCode}`,
        platform: parsed.platform,
        title: title,
        author: '用户录入', // 后续可以从文案中识别
        views: 0, // 无法获取真实数据
        likes: 0,
        shares: 0,
        comments: 0,
        coverUrl: `https://picsum.photos/300/400?random=${parsed.shortCode}`,
        transcript: transcript,
        publishedAt: new Date(),
        keyword: keyword || `${city}房产`,
        city: city,
      },
    });

    // 6. 确保关键词存在
    await KeywordDAO.upsertMany([
      {
        city,
        text: keyword || `${city}房产`,
        heat: 80,
      },
    ]);

    res.json({
      success: true,
      message: '视频录入成功',
      video: {
        id: video.id,
        title: video.title,
        city: video.city,
        keyword: video.keyword,
      },
      isNew: true,
    });

  } catch (error) {
    console.error('Parse video link error:', error);
    res.status(500).json({ error: 'Failed to parse video link' });
  }
});

/**
 * GET /api/video-link/extract
 * 仅提取链接信息（不入库）
 * Query: { link: string }
 */
router.get('/extract', (req, res) => {
  const { link } = req.query;

  if (!link || typeof link !== 'string') {
    res.status(400).json({ error: 'Missing link parameter' });
    return;
  }

  const linkToParse = extractLinkFromText(link) || link;
  const parsed = parseVideoLink(linkToParse);

  if (!parsed) {
    res.status(400).json({ error: 'Invalid video link format' });
    return;
  }

  res.json({
    success: true,
    platform: parsed.platform,
    shortCode: parsed.shortCode,
    fullUrl: parsed.fullUrl,
  });
});

export { router as videoLinkRoutes };
