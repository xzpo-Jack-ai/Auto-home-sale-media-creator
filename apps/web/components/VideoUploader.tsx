'use client';

import { useState, useRef } from 'react';
import { Upload, Camera, X, FileVideo, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VideoUploaderProps {
  onUploadComplete?: (file: File, videoUrl: string) => void;
  className?: string;
}

export function VideoUploader({ onUploadComplete, className }: VideoUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file: File) => {
    // 验证文件类型
    if (!file.type.startsWith('video/')) {
      alert('请上传视频文件');
      return;
    }

    // 验证文件大小 (100MB)
    if (file.size > 100 * 1024 * 1024) {
      alert('文件大小不能超过100MB');
      return;
    }

    setUploadedFile(file);
    
    // 创建预览URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // 模拟上传
    simulateUpload(file);
  };

  const simulateUpload = async (file: File) => {
    setUploading(true);
    
    // 模拟上传延迟
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 实际项目中这里调用 /api/upload/video
    // const formData = new FormData();
    // formData.append('video', file);
    // const response = await fetch('/api/upload/video', {
    //   method: 'POST',
    //   body: formData,
    // });
    // const data = await response.json();
    
    setUploading(false);
    
    // 触发回调
    if (onUploadComplete) {
      onUploadComplete(file, previewUrl || '');
    }
  };

  const clearFile = () => {
    setUploadedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  if (uploadedFile) {
    return (
      <div className={cn("bg-white rounded-xl p-4", className)}>
        <div className="flex items-start gap-3">
          <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <FileVideo className="w-8 h-8 text-gray-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {uploadedFile.name}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
            {uploading ? (
              <div className="flex items-center gap-2 mt-2">
                <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-orange-500">上传中...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 mt-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-xs text-green-600">上传成功</span>
              </div>
            )}
          </div>
          <button
            onClick={clearFile}
            className="p-1 hover:bg-gray-100 rounded-full"
            disabled={uploading}
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "border-2 border-dashed rounded-xl p-8 text-center transition-colors",
        isDragging ? "border-orange-500 bg-orange-50" : "border-gray-300 bg-white",
        className
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={handleFileInput}
      />
      
      <div className="w-16 h-16 bg-orange-50 rounded-full flex items-center justify-center mx-auto mb-4">
        <Upload className="w-8 h-8 text-orange-500" />
      </div>
      
      <p className="text-sm font-medium text-gray-900 mb-2">
        点击或拖拽上传视频
      </p>
      <p className="text-xs text-gray-500 mb-4">
        支持 MP4、MOV 格式，最大 100MB
      </p>
      
      <div className="flex gap-3 justify-center">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-4 py-2 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600 transition"
        >
          选择文件
        </button>
        <button
          onClick={() => alert('拍摄功能需要接入摄像头API')}
          className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition flex items-center gap-2"
        >
          <Camera className="w-4 h-4" />
          拍摄
        </button>
      </div>
    </div>
  );
}
