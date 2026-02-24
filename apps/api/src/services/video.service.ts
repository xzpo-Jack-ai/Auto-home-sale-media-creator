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
  ): Promise<{ videos: Video[]; total: number }> {
    const skip = (page - 1) * pageSize;

    const [videos, total] = await Promise.all([
      prisma.video.findMany({
        where: {
          keyword: { contains: keyword },
          city,
        },
        orderBy: [{ views: 'desc' }, { likes: 'desc' }],
        skip,
        take: pageSize,
      }),
      prisma.video.count({
        where: {
          keyword: { contains: keyword },
          city,
        },
      }),
    ]);

    return { videos, total };
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
   */
  static async createMany(data: VideoData[]) {
    return prisma.video.createMany({
      data: data.map((d) => ({
        ...d,
        shares: d.shares ?? 0,
        comments: d.comments ?? 0,
      })),
      skipDuplicates: true,
    });
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
