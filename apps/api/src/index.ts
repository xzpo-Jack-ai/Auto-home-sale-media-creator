import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';

dotenv.config();

import { keywordRoutes } from './routes/keywords';
import { videoRoutes } from './routes/videos';
import { aiRoutes } from './routes/ai';
import { uploadRoutes } from './routes/upload';
import { videoLinkRoutes } from './routes/video-link';
import { hotTrendRoutes } from './routes/hot-trends';
import { startHotTrendScheduler } from './jobs/update-hot-trends.job';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(morgan('dev'));
app.use(express.json({ limit: '10mb' }));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Routes
app.use('/api/keywords', keywordRoutes);
app.use('/api/videos', videoRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/video-link', videoLinkRoutes);
app.use('/api/hot-trends', hotTrendRoutes);

// Error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`🚀 API server running on port ${PORT}`);

  // 启动热词定时更新任务
  startHotTrendScheduler();
  console.log('📅 Hot trend scheduler started (daily at 08:00)');
});
