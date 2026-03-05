'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { VideoDetail } from '@/components/VideoDetail';

interface Video {
  id: string;
  title: string;
  author: string;
  views: number;
  likes: number;
  cover: string;
  duration: number;
  publishedAt: string;
  transcript: string;
  videoUrl?: string;
}

export default function VideoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const videoId = params.id as string;
  const keyword = searchParams.get('keyword') || '';
  const city = searchParams.get('city') || '上海';

  const [video, setVideo] = useState<Video | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchVideo();
  }, [videoId]);

  const fetchVideo = async () => {
    setLoading(true);
    try {
      // 从视频列表API获取视频详情
      const res = await fetch(
        `/api/videos-simple?keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}`
      );
      const data = await res.json();
      
      const foundVideo = data.videos?.find((v: Video) => v.id === videoId);
      if (foundVideo) {
        setVideo(foundVideo);
      } else {
        setError('视频未找到');
      }
    } catch (err) {
      console.error('Failed to fetch video:', err);
      setError('获取视频失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    router.back();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">加载中...</div>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">{error || '视频不存在'}</p>
          <button
            onClick={handleBack}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  // 使用 VideoDetail 组件，包含拍同款功能
  return (
    <VideoDetail
      video={{
        ...video,
        description: video.transcript,
      }}
      onBack={handleBack}
      keyword={keyword}
      city={city}
    />
  );
}
