import { Router } from 'express';
import { parseVideoLink, extractLinkFromText, type ParsedVideoLink } from '@auto-home/shared';
import { VideoDAO } from '../services/video.service';
import { KeywordDAO } from '../services/keyword.service';
import { prisma } from '../lib/prisma';
import { extractDouyinSubtitle, SubtitleResult } from '../services/subtitle-extractor';

const router = Router();

/**
 * POST /api/video-link/parse
 * 解析视频链接并录入
 * Body: { 
 *   link: string,           // 抖音/视频号分享链接
 *   city: string,           // 城市
 *   transcript?: string,    // 视频文案（手动提供，可选）
 *   keyword?: string,       // 关键词分类
 *   autoExtract?: boolean   // 是否自动提取字幕（默认true）
 * }
 */
router.post('/parse', async (req, res) => {
  try {
    const { link, city, transcript, keyword, autoExtract = true } = req.body;

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

    // 3. 自动提取字幕（如果用户未提供且开启自动提取）
    let extractedTranscript = transcript;
    let extractResult: SubtitleResult | null = null;

    if (!extractedTranscript && autoExtract && parsed.platform === 'douyin') {
      console.log(`[Subtitle Extract] Starting extraction for ${parsed.shortCode}`);
      extractResult = await extractDouyinSubtitle(linkToParse);
      
      if (extractResult.success && extractResult.transcript) {
        extractedTranscript = extractResult.transcript;
        console.log(`[Subtitle Extract] Success - ${extractedTranscript.length} chars`);
      } else {
        console.log(`[Subtitle Extract] Failed - ${extractResult.error}`);
      }
    }

    // 4. 如果没有文案（自动提取失败且用户未提供），提示用户
    if (!extractedTranscript) {
      res.json({
        success: false,
        needsTranscript: true,
        message: extractResult?.error 
          ? `自动提取失败: ${extractResult.error}，请手动粘贴视频文案`
          : '链接已解析，但需要提供视频文案才能使用AI洗稿功能',
        parsed: {
          platform: parsed.platform,
          shortCode: parsed.shortCode,
          fullUrl: parsed.fullUrl,
        },
        extractInfo: extractResult ? {
          attempted: true,
          title: extractResult.title,
          author: extractResult.author,
          duration: extractResult.duration,
          source: extractResult.source,
          error: extractResult.error,
        } : undefined,
      });
      return;
    }

    // 5. 生成标题（优先使用提取的标题，否则从文案前30字）
    const title = extractResult?.title 
      ? extractResult.title.substring(0, 50)
      : extractedTranscript!.substring(0, 30) + '...';

    // 6. 创建视频记录
    const video = await prisma.video.create({
      data: {
        externalId: `${parsed.platform}-${parsed.shortCode}`,
        platform: parsed.platform,
        title: title,
        author: extractResult?.author || '自动提取', // 使用提取的作者名
        views: 0, // 无法获取真实数据
        likes: 0,
        shares: 0,
        comments: 0,
        coverUrl: `https://picsum.photos/300/400?random=${parsed.shortCode}`,
        transcript: extractedTranscript,
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

/**
 * POST /api/video-link/extract-subtitle
 * 仅提取字幕，不入库（测试用）
 * Body: { link: string }
 */
router.post('/extract-subtitle', async (req, res) => {
  try {
    const { link } = req.body;

    if (!link) {
      res.status(400).json({ error: 'Missing link parameter' });
      return;
    }

    const linkToParse = extractLinkFromText(link) || link;
    const parsed = parseVideoLink(linkToParse);

    if (!parsed) {
      res.status(400).json({ error: 'Invalid video link format' });
      return;
    }

    if (parsed.platform !== 'douyin') {
      res.status(400).json({ 
        error: 'Unsupported platform',
        message: '目前仅支持抖音平台字幕提取' 
      });
      return;
    }

    console.log(`[API] Extracting subtitle for ${parsed.shortCode}`);
    const startTime = Date.now();
    
    const result = await extractDouyinSubtitle(linkToParse);
    
    const duration = Date.now() - startTime;
    console.log(`[API] Extraction completed in ${duration}ms`);

    res.json({
      success: result.success,
      duration: `${duration}ms`,
      platform: parsed.platform,
      videoId: parsed.shortCode,
      data: result.success ? {
        transcript: result.transcript,
        transcriptLength: result.transcript?.length,
        title: result.title,
        author: result.author,
        duration: result.duration,
        source: result.source,
      } : {
        error: result.error,
        source: result.source,
      }
    });

  } catch (error) {
    console.error('Extract subtitle API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : '未知错误'
    });
  }
});

export { router as videoLinkRoutes };
