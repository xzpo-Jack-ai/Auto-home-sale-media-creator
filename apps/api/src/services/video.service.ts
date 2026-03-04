import { prisma } from '../lib/prisma';
import type { Video } from '@prisma/client';

export interface VideoData {
  externalId?: string;
  platform: 'douyin' | 'video_channel';
  title: string;
  author: string;
  authorId?: string;
  views: number;
  likes: number;
  shares?: number;
  comments?: number;
  coverUrl?: string;
  videoUrl?: string;
  duration?: number;
  transcript?: string;
  publishedAt: Date;
  keyword: string;
  city: string;
}

export interface VideoWithRank extends Video {
  rank?: number;
}

export class VideoDAO {
  /**
   * 获取关键词下的视频列表（按热度排序）
   */
  static async getByKeyword(
    keyword: string,
    city: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ videos: any[]; total: number }> {
    const skip = (page - 1) * pageSize;

    // 使用原始SQL查询避免Prisma字符编码问题
    const videos = await prisma.$queryRawUnsafe(
      `SELECT * FROM videos WHERE keyword = ? AND city = ? ORDER BY views DESC, likes DESC LIMIT ? OFFSET ?`,
      keyword, city, pageSize, skip
    );

    const countResult = await prisma.$queryRawUnsafe(
      `SELECT COUNT(*) as count FROM videos WHERE keyword = ? AND city = ?`,
      keyword, city
    );

    const total = Number((countResult as any)[0].count);

    return { videos: videos as any[], total };
  }

  /**
   * 获取视频详情
   */
  static async getById(id: string): Promise<Video | null> {
    return prisma.video.findUnique({
      where: { id },
    });
  }

  /**
   * 批量插入视频
   * 注意：SQLite 不支持 skipDuplicates，需要逐个插入并处理冲突
   */
  static async createMany(data: VideoData[]) {
    // SQLite 不支持 createMany + skipDuplicates，使用事务逐个插入
    const results = await prisma.$transaction(
      data.map((d) =>
        prisma.video.upsert({
          where: { externalId: d.externalId || `${d.platform}-${Date.now()}` },
          update: {
            title: d.title,
            transcript: d.transcript,
            views: d.views,
            likes: d.likes,
          },
          create: {
            ...d,
            externalId: d.externalId || `${d.platform}-${Date.now()}`,
            shares: d.shares ?? 0,
            comments: d.comments ?? 0,
          },
        })
      )
    );
    return { count: results.length };
  }

  /**
   * 更新视频文案
   */
  static async updateTranscript(id: string, transcript: string) {
    return prisma.video.update({
      where: { id },
      data: { transcript },
    });
  }
}
