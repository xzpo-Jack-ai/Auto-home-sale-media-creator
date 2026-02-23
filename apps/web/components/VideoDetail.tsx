'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Copy, Camera, Upload, Sparkles, RefreshCw, CheckCircle } from 'lucide-react';

interface Video {
  id: string;
  title: string;
  author: string;
  views: number;
  likes: number;
  cover: string;
  duration: number;
  publishedAt: string;
  description?: string;
  transcript?: string;
}

interface VideoDetailProps {
  video: Video;
  onBack: () => void;
  keyword: string;
  city: string;
}

interface RewriteResult {
  versions: string[];
  shootingTips: string[];
  suggestedTags: string[];
}

export function VideoDetail({ video, onBack, keyword, city }: VideoDetailProps) {
  const [showGuide, setShowGuide] = useState(false);
  const [rewriteResult, setRewriteResult] = useState<RewriteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'rewrite' | 'tips'>('rewrite');

  const handleRewrite = async () => {
    setShowGuide(true);
    setLoading(true);

    try {
      const res = await fetch('/api/ai/rewrite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: video.transcript || '这是一套位于市中心的优质房源，南北通透，采光好',
        }),
      });
      const data = await res.json();
      setRewriteResult(data);
    } catch (error) {
      console.error('Rewrite failed:', error);
      // 使用模拟数据
      setRewriteResult({
        versions: [
          '【专业版】这套房源位于城市核心区域，三室两厅两卫，南北通透格局。小区周边配套成熟，地铁500米直达。业主诚意出售，价格可谈。',
          '【亲和版】家人们！今天这套房子真的绝了！三室两厅，阳光超级好～楼下就是地铁，买菜逛街都方便。业主急卖，价格好商量！',
          '【悬念版】什么样的房子能让买家看完当场下定？这套三居室告诉你答案...南北通透+地铁口+学区房，错过再等一年！',
        ],
        shootingTips: [
          '开场用广角镜头展示客厅全景，配合"今天这套房绝了"的口播',
          '中间切换到卧室特写，语速放慢强调"南北通透"卖点',
          '结尾用小区外景收尾，BGM渐强营造紧迫感',
        ],
        suggestedTags: ['房产', '买房攻略', '好房推荐', city + '买房', '二手房'],
      });
    } finally {
      setLoading(false);
    }
  };

  const copyText = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopied(index);
    setTimeout(() => setCopied(null), 2000);
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) return (num / 10000).toFixed(1) + 'w';
    return num.toString();
  };

  // Guide Page
  if (showGuide) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm sticky top-0 z-10">
          <div className="max-w-md mx-auto px-4 py-4 flex items-center gap-3">
            <button onClick={() => setShowGuide(false)} className="p-2 hover:bg-gray-100 rounded-full">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <h1 className="text-lg font-bold text-gray-900">拍同款指导</h1>
          </div>
        </header>

        <main className="max-w-md mx-auto px-4 py-4 pb-24">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 text-orange-500 animate-spin mb-4" />
              <p className="text-gray-600">AI正在生成文案...</p>
            </div>
          ) : (
            <>
              {/* Original Script */}
              <div className="bg-white rounded-xl p-4 mb-4">
                <h3 className="text-sm font-medium text-gray-500 mb-2">原视频文案</h3>
                <p className="text-gray-800 text-sm leading-relaxed">
                  {video.transcript || '暂无文案'}
                </p>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setActiveTab('rewrite')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${
                    activeTab === 'rewrite'
                      ? 'bg-orange-500 text-white'
                      : 'bg-white text-gray-600'
                  }`}
                >
                  <Sparkles className="w-4 h-4 inline mr-1" />
                  AI洗稿
                </button>
                <button
                  onClick={() => setActiveTab('tips')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${
                    activeTab === 'tips'
                      ? 'bg-orange-500 text-white'
                      : 'bg-white text-gray-600'
                  }`}
                >
                  <Camera className="w-4 h-4 inline mr-1" />
                  拍摄建议
                </button>
              </div>

              {/* Content */}
              {activeTab === 'rewrite' ? (
                <div className="space-y-4">
                  {rewriteResult?.versions.map((version, i) => (
                    <div key={i} className="bg-white rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-orange-500">
                          版本 {i + 1}
                        </span>
                        <button
                          onClick={() => copyText(version, i)}
                          className="flex items-center gap-1 text-xs text-gray-500 hover:text-orange-500"
                        >
                          {copied === i ? (
                            <>
                              <CheckCircle className="w-3.5 h-3.5" />
                              已复制
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              复制
                            </>
                          )}
                        </button>
                      </div>
                      <p className="text-gray-800 text-sm leading-relaxed">{version}</p>
                    </div>
                  ))}

                  {/* Suggested Tags */}
                  <div className="bg-white rounded-xl p-4">
                    <h3 className="text-sm font-medium text-gray-500 mb-3">推荐标签</h3>
                    <div className="flex flex-wrap gap-2">
                      {rewriteResult?.suggestedTags.map((tag) => (
                        <span
                          key={tag}
                          className="px-3 py-1 bg-orange-50 text-orange-600 text-xs rounded-full"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {rewriteResult?.shootingTips.map((tip, i) => (
                    <div key={i} className="bg-white rounded-xl p-4">
                      <div className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                          {i + 1}
                        </span>
                        <p className="text-gray-800 text-sm">{tip}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </main>

        {/* Bottom Actions */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t px-4 py-3">
          <div className="max-w-md mx-auto flex gap-3">
            <button className="flex-1 flex items-center justify-center gap-2 py-3 bg-gray-900 text-white rounded-xl font-medium">
              <Camera className="w-5 h-5" />
              拍摄视频
            </button>
            <button className="flex-1 flex items-center justify-center gap-2 py-3 bg-orange-500 text-white rounded-xl font-medium">
              <Upload className="w-5 h-5" />
              上传视频
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Video Detail Page
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-10 p-4">
        <button
          onClick={onBack}
          className="p-2 bg-black/30 backdrop-blur rounded-full text-white"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
      </header>

      {/* Video Player Placeholder */}
      <div className="aspect-[3/4] bg-gray-800 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="w-20 h-20 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <Camera className="w-8 h-8" />
          </div>
          <p className="text-gray-400">视频播放器</p>
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <h1 className="text-white text-lg font-bold mb-2">{video.title}</h1>
        <p className="text-gray-400 text-sm mb-4">
          @{video.author} · {formatNumber(video.views)}播放 · {formatNumber(video.likes)}赞
        </p>

        {/* CTA */}
        <button
          onClick={handleRewrite}
          className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-2"
        >
          <Sparkles className="w-5 h-5" />
          拍同款
        </button>
      </div>
    </div>
  );
}
