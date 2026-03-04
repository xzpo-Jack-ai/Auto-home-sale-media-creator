'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Play, Heart, Eye, Sparkles } from 'lucide-react';

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
  const [rewriting, setRewriting] = useState(false);
  const [rewrittenText, setRewrittenText] = useState('');

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

  const handleRewrite = async () => {
    if (!video?.transcript) return;
    
    setRewriting(true);
    try {
      const res = await fetch('/api/ai/rewrite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: video.transcript,
          style: 'professional'
        })
      });
      const data = await res.json();
      setRewrittenText(data.rewritten || data.text || '改写失败');
    } catch (err) {
      console.error('Rewrite failed:', err);
      setRewrittenText('改写服务暂时不可用');
    } finally {
      setRewriting(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) return (num / 10000).toFixed(1) + 'w';
    return num.toString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">{error || '视频不存在'}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

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
          <h1 className="text-lg font-bold text-gray-900 truncate">视频详情</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-md mx-auto px-4 py-6">
        {/* Video Info Card */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden mb-6">
          {/* Cover */}
          <div className="relative aspect-video">
            <img
              src={video.cover}
              alt={video.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/30">
              <Play className="w-16 h-16 text-white" />
            </div>
          </div>

          {/* Info */}
          <div className="p-4">
            <h2 className="font-bold text-lg text-gray-900 mb-2">
              {video.title && video.title !== '[]' && !video.title.startsWith('http')
                ? video.title
                : `${video.author}的视频`}
            </h2>
            <p className="text-gray-500 mb-3">@{video.author}</p>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span className="flex items-center gap-1">
                <Eye className="w-4 h-4" />
                {formatNumber(video.views)}
              </span>
              <span className="flex items-center gap-1">
                <Heart className="w-4 h-4" />
                {formatNumber(video.likes)}
              </span>
            </div>
          </div>
        </div>

        {/* Original Transcript */}
        <div className="bg-white rounded-2xl shadow-sm p-4 mb-6">
          <h3 className="font-bold text-gray-900 mb-3">原视频文案</h3>
          <p className="text-gray-600 text-sm leading-relaxed whitespace-pre-wrap">
            {video.transcript || '暂无文案'}
          </p>
        </div>

        {/* AI Rewrite */}
        <div className="bg-white rounded-2xl shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-gray-900">AI 文案改写</h3>
            <button
              onClick={handleRewrite}
              disabled={rewriting || !video.transcript}
              className="flex items-center gap-1 px-3 py-1.5 bg-orange-500 text-white text-sm rounded-lg disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {rewriting ? '改写中...' : '生成新文案'}
            </button>
          </div>
          
          {rewrittenText ? (
            <div className="bg-orange-50 rounded-lg p-3">
              <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                {rewrittenText}
              </p>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">点击上方按钮生成改写文案</p>
          )}
        </div>
      </main>
    </div>
  );
}
