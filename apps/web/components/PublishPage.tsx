'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ArrowLeft, Sparkles, Copy, CheckCircle, Send, Hash } from 'lucide-react';
import { VideoUploader } from './VideoUploader';
import { cn } from '@/lib/utils';

interface PublishPageProps {
  onBack?: () => void;
}

export function PublishPage({ onBack }: PublishPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const videoId = searchParams.get('videoId');
  const transcript = searchParams.get('transcript') || '';

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [inputTag, setInputTag] = useState('');
  const [platform, setPlatform] = useState<'douyin' | 'video_channel'>('douyin');
  const [published, setPublished] = useState(false);
  const [loading, setLoading] = useState(false);
  const [videoFile, setVideoFile] = useState<File | null>(null);

  // 基于文案自动生成标签
  useEffect(() => {
    if (transcript) {
      generateTags(transcript);
    }
  }, [transcript]);

  const generateTags = async (text: string) => {
    try {
      const res = await fetch('/api/ai/generate-tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });
      const data = await res.json();
      setTags(data.tags || ['房产', '买房攻略', '杭州买房']);
    } catch (error) {
      setTags(['房产', '买房攻略', '杭州买房', '捡漏', '刚需']);
    }
  };

  const addTag = () => {
    if (inputTag && !tags.includes(inputTag)) {
      setTags([...tags, inputTag]);
      setInputTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handlePublish = async () => {
    if (!title) {
      alert('请输入标题');
      return;
    }

    setLoading(true);

    // 模拟发布
    await new Promise(resolve => setTimeout(resolve, 2000));

    setLoading(false);
    setPublished(true);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('已复制到剪贴板');
  };

  if (published) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 text-center max-w-sm w-full">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">发布成功！</h2>
          <p className="text-sm text-gray-500 mb-6">
            您的视频已准备好，请复制以下内容到{platform === 'douyin' ? '抖音' : '视频号'}发布
          </p>
          
          <div className="bg-gray-50 rounded-lg p-4 text-left mb-4">
            <p className="text-sm font-medium text-gray-900 mb-2">标题：</p>
            <p className="text-sm text-gray-700 mb-4">{title}</p>
            
            <p className="text-sm font-medium text-gray-900 mb-2">标签：</p>
            <p className="text-sm text-gray-700">
              {tags.map(t => `#${t}`).join(' ')}
            </p>
          </div>

          <button
            onClick={() => copyToClipboard(`${title}\n\n${tags.map(t => `#${t}`).join(' ')}`)}
            className="w-full py-3 bg-orange-500 text-white rounded-xl font-medium flex items-center justify-center gap-2"
          >
            <Copy className="w-5 h-5" />
            复制发布内容
          </button>
          
          <button
            onClick={() => router.push('/')}
            className="w-full py-3 mt-3 text-gray-600 font-medium"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center gap-3">
          <button
            onClick={onBack || (() => router.back())}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <h1 className="text-lg font-bold text-gray-900">发布视频</h1>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-6 pb-24">
        {/* 平台选择 */}
        <div className="bg-white rounded-xl p-4 mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">选择发布平台</h3>
          <div className="flex gap-3">
            <button
              onClick={() => setPlatform('douyin')}
              className={cn(
                "flex-1 py-3 rounded-lg text-sm font-medium transition",
                platform === 'douyin'
                  ? "bg-black text-white"
                  : "bg-gray-100 text-gray-600"
              )}
            >
              抖音
            </button>
            <button
              onClick={() => setPlatform('video_channel')}
              className={cn(
                "flex-1 py-3 rounded-lg text-sm font-medium transition",
                platform === 'video_channel'
                  ? "bg-green-500 text-white"
                  : "bg-gray-100 text-gray-600"
              )}
            >
              视频号
            </button>
          </div>
        </div>

        {/* 视频上传 */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">上传视频</h3>
          <VideoUploader
            onUploadComplete={(file, url) => setVideoFile(file)}
          />
        </div>

        {/* 标题 */}
        <div className="bg-white rounded-xl p-4 mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">视频标题</h3>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="输入吸引人的标题..."
            className="w-full px-4 py-3 bg-gray-50 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>

        {/* 描述 */}
        <div className="bg-white rounded-xl p-4 mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">视频描述</h3>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="添加视频描述..."
            rows={4}
            className="w-full px-4 py-3 bg-gray-50 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none"
          />
        </div>

        {/* 标签 */}
        <div className="bg-white rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Hash className="w-4 h-4 text-orange-500" />
            <h3 className="text-sm font-medium text-gray-700">推荐标签</h3>
            <span className="text-xs text-gray-400">(点击添加)</span>
          </div>
          
          <div className="flex flex-wrap gap-2 mb-3">
            {tags.map((tag) => (
              <button
                key={tag}
                onClick={() => removeTag(tag)}
                className="px-3 py-1.5 bg-orange-50 text-orange-600 text-sm rounded-full flex items-center gap-1 hover:bg-orange-100 transition"
              >
                #{tag}
                <span className="text-orange-400">×</span>
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={inputTag}
              onChange={(e) => setInputTag(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTag()}
              placeholder="添加自定义标签"
              className="flex-1 px-4 py-2 bg-gray-50 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <button
              onClick={addTag}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition"
            >
              添加
            </button>
          </div>
        </div>

        {/* AI 生成提示 */}
        <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-orange-500" />
            <span className="text-sm font-medium text-orange-800">AI 智能优化</span>
          </div>
          <p className="text-xs text-orange-600">
            基于热门视频文案，AI 已为您生成推荐标签。发布后可提升视频曝光率。
          </p>
        </div>
      </main>

      {/* 发布按钮 */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t px-4 py-4">
        <div className="max-w-md mx-auto">
          <button
            onClick={handlePublish}
            disabled={loading || !title || !videoFile}
            className={cn(
              "w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition",
              loading || !title || !videoFile
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : "bg-gradient-to-r from-orange-500 to-red-500 text-white"
            )}
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                发布中...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                发布到{platform === 'douyin' ? '抖音' : '视频号'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
