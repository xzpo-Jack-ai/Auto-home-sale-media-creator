import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: '房产自媒体助手',
  description: '为房产经纪人提供热词追踪、爆款视频分析和AI文案改写',
  manifest: '/manifest.json',
  themeColor: '#f97316',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: '房产自媒体助手',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
