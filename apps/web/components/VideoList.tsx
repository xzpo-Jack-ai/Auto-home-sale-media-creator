'use client';

import { useState, useEffect } from 'react';
import { VideoDetail } from './VideoDetail';
import { ArrowLeft, Play, Eye, Heart } from 'lucide-react';

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

interface VideoListProps {
  keyword: string;
  city: string;
  onBack: () => void;
}

export function VideoList({ keyword, city, onBack }: VideoListProps) {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchVideos();
  }, [keyword, city, page]);

  const fetchVideos = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/videos?keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(
          city
        )}&page=${page}`
      );
      const data = await res.json();
      setVideos(data.videos || []);
    } catch (error) {
      console.error('Failed to fetch videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w';
    }
    return num.toString();
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (selectedVideo) {
    return (
      <VideoDetail
        video={selectedVideo}
        onBack={() => setSelectedVideo(null)}
        keyword={keyword}
        city={city}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-gray-900">{keyword}</h1>
            <p className="text-xs text-gray-500">{city} · 近一个月热门</p>
          </div>
        </div>
      </header>

      {/* Video List */}
      <main className="max-w-md mx-auto px-4 py-4">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-xl h-32 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {videos.map((video, index) => (
              <div
                key={video.id}
                onClick={() => setSelectedVideo(video)}
                className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition cursor-pointer"
              >
                <div className="flex gap-3 p-3">
                  {/* Cover */}
                  <div className="relative flex-shrink-0 w-28 h-36 bg-gray-200 rounded-lg overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                    <span className="absolute bottom-2 right-2 text-white text-xs bg-black/50 px-1.5 py-0.5 rounded">
                      {formatDuration(video.duration)}
                    </span>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Play className="w-8 h-8 text-white opacity-80" />
                    </div>
                    {/* Rank badge */}
                    {index < 3 && (
                      <span
                        className={`absolute top-2 left-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index === 0
                            ? 'bg-red-500 text-white'
                            : index === 1
                            ? 'bg-orange-500 text-white'
                            : 'bg-yellow-500 text-white'
                        }`}
                      >
                        {index + 1}
                      </span>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 flex flex-col justify-between py-1">
                    <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                      {video.title}
                    </h3>
                    <div>
                      <p className="text-xs text-gray-500 mb-2">@{video.author}</p>
                      <div className="flex items-center gap-4 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5" />
                          {formatNumber(video.views)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Heart className="w-3.5 h-3.5" />
                          {formatNumber(video.likes)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
