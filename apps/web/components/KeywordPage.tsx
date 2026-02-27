'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { TrendingUp, MapPin, ChevronDown } from 'lucide-react';

interface Keyword {
  id: string;
  text: string;
  heat: number;
}

interface HotTrendData {
  city: string;
  trends: Array<{
    id: string;
    keyword: string;
    heat: number;
    rank: number;
  }>;
  updatedAt?: string;
  message?: string;
}

const CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都'];

export function KeywordPage() {
  const router = useRouter();
  const [selectedCity, setSelectedCity] = useState('北京');
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCityDropdown, setShowCityDropdown] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<string>('');
  const [dataMessage, setDataMessage] = useState<string>('');
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [updateMessage, setUpdateMessage] = useState<string>('');
  const [updateTime, setUpdateTime] = useState<string>('');
  const [dataSource, setDataSource] = useState<'douyin' | 'local'>('local');

  useEffect(() => {
    fetchKeywords(selectedCity);
  }, [selectedCity]);

  const fetchKeywords = async (city: string) => {
    setLoading(true);
    setDataMessage('');
    try {
      // 使用新的热词趋势 API
      const res = await fetch(`/api/hot-trends?city=${encodeURIComponent(city)}&limit=20`);
      const data: HotTrendData = await res.json();

      if (data.trends && data.trends.length > 0) {
        // 转换为 Keyword 格式
        setKeywords(data.trends.map((t) => ({
          id: t.id,
          text: t.keyword,
          heat: t.heat,
        })));
        setUpdatedAt(data.updatedAt || '');
      } else {
        // 如果没有热词数据，显示提示
        setKeywords([]);
        setDataMessage(data.message || '暂无热词数据');
      }
    } catch (error) {
      console.error('Failed to fetch keywords:', error);
      setKeywords([]);
      setDataMessage('获取数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">房产自媒体助手</h1>
          
          {/* City Selector */}
          <div className="relative">
            <button
              onClick={() => setShowCityDropdown(!showCityDropdown)}
              className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 rounded-full text-sm font-medium text-gray-700 hover:bg-gray-200 transition"
            >
              <MapPin className="w-4 h-4" />
              {selectedCity}
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {showCityDropdown && (
              <div className="absolute right-0 mt-2 w-32 bg-white rounded-lg shadow-lg border py-1 z-20">
                {CITIES.map((city) => (
                  <button
                    key={city}
                    onClick={() => {
                      setSelectedCity(city);
                      setShowCityDropdown(false);
                    }}
                    className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-50 ${
                      selectedCity === city ? 'text-orange-600 font-medium' : 'text-gray-700'
                    }`}
                  >
                    {city}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-md mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="w-6 h-6 text-orange-500" />
            <h2 className="text-lg font-bold text-gray-900">今日房产热词</h2>
          </div>

          {dataMessage && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-700">{dataMessage}</p>
              <p className="text-xs text-yellow-600 mt-1">每天 08:00 自动更新</p>
            </div>
          )}

          {updatedAt && (
            <p className="text-xs text-gray-400 mb-4">
              更新时间: {new Date(updatedAt).toLocaleString('zh-CN')}
            </p>
          )}

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {keywords.map((keyword, index) => (
                <button
                  key={keyword.id}
                  onClick={() => router.push(`/hot/${encodeURIComponent(keyword.text)}?city=${encodeURIComponent(selectedCity)}`)}
                  className="w-full flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-orange-50 transition group"
                >
                  <span
                    className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                      index === 0
                        ? 'bg-red-500 text-white'
                        : index === 1
                        ? 'bg-orange-500 text-white'
                        : index === 2
                        ? 'bg-yellow-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {index + 1}
                  </span>
                  <span className="flex-1 text-left font-medium text-gray-900 group-hover:text-orange-600">
                    {keyword.text}
                  </span>
                  <span className="text-sm text-gray-400">{keyword.heat}°</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Tips */}
        <div className="mt-6 text-center text-sm text-gray-500">
          💡 点击热词查看相关爆款视频
        </div>
      </main>
    </div>
  );
}
