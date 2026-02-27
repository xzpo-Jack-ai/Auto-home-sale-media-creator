'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Play, TrendingUp, Eye, Heart } from 'lucide-react';

interface Video {
  id: string;
  title: string;
  author: string;
  views: number;
  likes: number;
  cover: string;
  duration: number;
  publishedAt: string;
}

export default function HotTrendVideosPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();

  const keyword = decodeURIComponent(params.keyword as string);
  const city = searchParams.get('city') || '北京';

  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchVideos();
  }, [keyword, city]);

  const fetchVideos = async () => {
    setLoading(true);
    setError('');

    try {
      const res = await fetch(
        `/api/hot-trends/${encodeURIComponent(keyword)}/videos?city=${encodeURIComponent(city)}&limit=20`
      );
      const data = await res.json();

      if (data.videos) {
        setVideos(data.videos);
      } else {
        setError('暂无相关视频');
      }
    } catch (err) {
      console.error('Failed to fetch videos:', err);
      setError('获取视频失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleVideoClick = (videoId: string) => {
    // 跳转到视频详情页（复用现有路由）
    router.push(`/video/${videoId}?keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}`);
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w';
    }
    return num.toString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-gray-900 truncate">{keyword}</h1>
            <p className="text-xs text-gray-500">{city} · 相关视频</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-md mx-auto px-4 py-6">
        {/* Keyword Info */}
        <div className="bg-white rounded-2xl shadow-sm p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-orange-500" />
            </div>
            <div className="flex-1">
              <h2 className="font-bold text-gray-900">{keyword}</h2>
              <p className="text-sm text-gray-500">点击查看相关爆款视频</p>
            </div>
          </div>
        </div>

        {/* Videos List */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl p-4">
                <div className="flex gap-4">
                  <div className="w-24 h-32 bg-gray-200 rounded-lg animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded animate-pulse" />
                    <div className="h-3 bg-gray-200 rounded w-2/3 animate-pulse" />
                    <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-gray-500">{error}</p>
            <button
              onClick={fetchVideos}
              className="mt-4 px-4 py-2 bg-orange-500 text-white rounded-lg text-sm"
            >
              重试
            </button>
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">暂无相关视频</p>
            <p className="text-sm text-gray-400 mt-2">该热词下还没有收录视频</p>
          </div>
        ) : (
          <div className="space-y-4">
            {videos.map((video, index) => (
              <button
                key={video.id}
                onClick={() => handleVideoClick(video.id)}
                className="w-full bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition text-left"
              >
                <div className="flex gap-4">
                  {/* Cover */}
                  <div className="relative w-24 h-32 flex-shrink-0">
                    <img
                      src={video.cover}
                      alt={video.title}
                      className="w-full h-full object-cover rounded-lg"
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/20 rounded-lg opacity-0 hover:opacity-100 transition">
                      <Play className="w-8 h-8 text-white" />
                    </div>
                    <span className="absolute top-1 left-1 w-6 h-6 bg-orange-500 text-white text-xs font-bold rounded flex items-center justify-center">
                      {index + 1}
                    </span>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">
                      {video.title}
                    </h3>
                    <p className="text-sm text-gray-500 mb-2">@{video.author}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {formatNumber(video.views)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3" />
                        {formatNumber(video.likes)}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
