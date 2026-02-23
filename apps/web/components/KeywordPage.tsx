'use client';

import { useState, useEffect } from 'react';
import { VideoList } from './VideoList';
import { TrendingUp, MapPin, ChevronDown } from 'lucide-react';

interface Keyword {
  id: string;
  text: string;
  heat: number;
}

const CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都'];

export function KeywordPage() {
  const [selectedCity, setSelectedCity] = useState('北京');
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [showCityDropdown, setShowCityDropdown] = useState(false);

  useEffect(() => {
    fetchKeywords(selectedCity);
  }, [selectedCity]);

  const fetchKeywords = async (city: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/keywords?city=${encodeURIComponent(city)}`);
      const data = await res.json();
      setKeywords(data.keywords || []);
    } catch (error) {
      console.error('Failed to fetch keywords:', error);
    } finally {
      setLoading(false);
    }
  };

  if (selectedKeyword) {
    return (
      <VideoList
        keyword={selectedKeyword}
        city={selectedCity}
        onBack={() => setSelectedKeyword(null)}
      />
    );
  }

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
                  onClick={() => setSelectedKeyword(keyword.text)}
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
