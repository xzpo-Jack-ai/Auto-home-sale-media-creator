// Shared types for Auto Home Sale Media Creator

export interface Keyword {
  id: string;
  city: string;
  text: string;
  heat: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface Video {
  id: string;
  externalId?: string;
  platform: 'douyin' | 'video_channel';
  title: string;
  author: string;
  authorId?: string;
  views: number;
  likes: number;
  shares: number;
  comments: number;
  coverUrl?: string;
  videoUrl?: string;
  duration?: number;
  transcript?: string;
  publishedAt: Date;
  keyword: string;
  city: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface User {
  id: string;
  phone?: string;
  nickname?: string;
  avatar?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface PublishLog {
  id: string;
  userId: string;
  platform: 'douyin' | 'video_channel';
  videoUrl: string;
  title: string;
  description?: string;
  tags: string[];
  status: 'pending' | 'published' | 'failed';
  externalUrl?: string;
  publishedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// 视频链接解析
export * from './video-parser';
