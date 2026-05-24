import { useEffect, useState, useRef } from 'react';
import { X, Loader2, CheckCircle2, Circle } from 'lucide-react';
import { apiConfig } from '@/utils/api';

interface ProgressData {
  step: number;
  total: number;
  percentage: number;
  stage: string;
  message: string;
}

interface ProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string;
}

const GENERATION_STEPS = [
  { id: 1, name: '初始化与分析', stage: '初始化' },
  { id: 2, name: 'AI生成内容', stage: 'AI生成' },
  { id: 3, name: '标题修正与渲染', stage: '标题修正' },
  { id: 4, name: 'PPTX生成', stage: '生成' },
  { id: 5, name: '质量检查', stage: '质检' },
  { id: 6, name: '生成完毕', stage: '完成' },
];

const STAGE_MAPPING: { [key: string]: number } = {
  '初始化': 0,
  '分析': 0,
  '规划': 0,
  '内容规划': 1,
  'AI生成': 1,
  'AI规划': 1,
  'AI 生成': 1,
  'AI生成内容': 1,
  'AI解析': 1,
  '转写解析': 1,
  '解析Excel': 1,
  '数据映射': 1,
  '标题修正': 2,
  '渲染': 2,
  '渲染幻灯片': 2,
  '生成幻灯片': 2,
  '生成': 3,
  '生成PPTX': 3,
  '生成 PPTX': 3,
  '美化': 3,
  '质检': 4,
  '质量检查': 4,
  '视觉检查': 4,
  '交叉验证': 4,
  '完成': 5,
};

export function ProgressModal({ isOpen, onClose, taskId }: ProgressModalProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!isOpen || !taskId) return;

    let ws: WebSocket | null = null;
    let cancelled = false;

    const handleProgress = (event: MessageEvent) => {
      if (cancelled) return;
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          const safePercentage = Math.min(Math.max(data.percentage, 0), 100);

          setProgress({
            step: data.step,
            total: data.total,
            percentage: safePercentage,
            stage: data.stage,
            message: data.message,
          });

          if (data.stage === '完成' && safePercentage >= 98) {
            if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
            closeTimerRef.current = setTimeout(() => onCloseRef.current(), 2000);
          }
        }
      } catch {
      }
    };

    const connect = async () => {
      try {
        const baseUrl = await apiConfig.baseUrl;
        const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
        ws = new WebSocket(`${wsUrl}/api/v1/ws/progress/${taskId}`);

        ws.onopen = () => {
          if (!cancelled) setConnectionStatus('connected');
        };

        ws.onmessage = handleProgress;

        ws.onerror = () => {
          if (!cancelled) setConnectionStatus('error');
        };

        ws.onclose = () => {
          if (!cancelled) setConnectionStatus('error');
        };
      } catch {
        if (!cancelled) setConnectionStatus('error');
      }
    };

    setTimeout(connect, 0);

    return () => {
      cancelled = true;
      if (ws) ws.close();
      if (closeTimerRef.current) {
        clearTimeout(closeTimerRef.current);
      }
    };
  }, [isOpen, taskId]);

  // 根据stage名称确定当前步骤索引
  const getCurrentStepIndex = () => {
    if (!progress) return 0;
    
    // 首先尝试根据stage名称匹配
    const stageName = progress.stage;
    if (STAGE_MAPPING[stageName] !== undefined) {
      return STAGE_MAPPING[stageName];
    }
    
    // 如果无法匹配，使用step值
    return Math.min(progress.step, GENERATION_STEPS.length - 1);
  };

  if (!isOpen) return null;

  const currentStepIndex = getCurrentStepIndex();
  const percentage = progress?.percentage ?? 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 w-full max-w-lg mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">生成进度</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Connection Status */}
        {connectionStatus === 'connecting' && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <span className="ml-3 text-gray-500">连接中...</span>
          </div>
        )}

        {connectionStatus === 'error' && (
          <div className="text-center py-8 text-red-500">
            <p>连接失败，将在后台继续生成</p>
          </div>
        )}

        {/* 当连接成功但还没有收到进度数据时，显示默认进度界面 */}
        {connectionStatus === 'connected' && !progress && (
          <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
            {/* Percentage Display */}
            <div className="flex items-center justify-between text-lg font-semibold">
              <span className="text-gray-600">生成进度</span>
              <span className="text-blue-600 text-2xl">0%</span>
            </div>

            {/* Animated Progress Bar */}
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden relative">
              <div className="h-full bg-gradient-to-r from-blue-500 to-blue-600 w-0 animate-pulse" />
            </div>

            {/* Steps List */}
            <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">生成步骤</h3>
              <div className="space-y-3">
                {GENERATION_STEPS.map((step) => (
                  <div key={step.id} className="flex items-center space-x-3">
                    <div className="flex-shrink-0 w-8 h-8">
                      <Circle className="w-8 h-8 text-gray-300" />
                    </div>
                    <div className="flex-1 py-1 text-gray-400">
                      {step.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Current Stage Info */}
            <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 text-center">
              <p className="text-blue-600 dark:text-blue-400 font-medium">正在等待服务器响应...</p>
            </div>
          </div>
        )}

        {connectionStatus === 'connected' && progress && (
          <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
            {/* Percentage Display */}
            <div className="flex items-center justify-between text-lg font-semibold">
              <span className="text-gray-600">生成进度</span>
              <span className="text-blue-600 text-2xl">{percentage}%</span>
            </div>

            {/* Animated Progress Bar */}
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden relative">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
                style={{ width: `${percentage}%` }}>
                {/* Scrolling light effect */}
                <div className="absolute inset-0 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-200/50 to-transparent animate-shimmer" />
                </div>
              </div>
              {/* Scrolling indicator */}
              <div 
                className="absolute h-4 w-16 bg-white/30 rounded-r-full shadow-lg"
                style={{ 
                  left: `${Math.max(0, percentage - 12)}%`,
                  transition: 'left 0.5s ease-out'
                }} />
            </div>

            {/* Steps List */}
            <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">生成步骤</h3>
              <div className="space-y-3">
                {GENERATION_STEPS.map((step, index) => {
                  const isCompleted = index < currentStepIndex;
                  const isActive = index === currentStepIndex;

                  return (
                    <div key={step.id} className="flex items-center space-x-3">
                      {/* Status Icon */}
                      <div className="flex-shrink-0 w-8 h-8">
                        {isCompleted ? (
                          <CheckCircle2 className="w-8 h-8 text-green-500" />
                        ) : isActive ? (
                          <div className="relative">
                            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                            <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-30" />
                          </div>
                        ) : (
                          <Circle className="w-8 h-8 text-gray-300" />
                        )}
                      </div>

                      {/* Step Text */}
                      <div className={`flex-1 py-1 ${
                        isCompleted ? 'text-gray-500 line-through' : 
                        isActive ? 'text-blue-600 font-medium' : 
                        'text-gray-400'
                      }`}>
                        {step.name}
                        {isActive && progress.message && (
                          <p className="text-xs text-gray-500 mt-1">{progress.message}</p>
                        )}
                      </div>

                      {/* Percentage indicator for active step */}
                      {isActive && (
                        <div className="flex-shrink-0 text-sm font-medium text-blue-500">
                          {percentage}%
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Current Stage Info */}
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3">
                <span className="text-gray-500 dark:text-gray-400">当前阶段</span>
                <p className="font-semibold text-blue-600 dark:text-blue-400">{progress.stage}</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <span className="text-gray-500 dark:text-gray-400">总体进度</span>
                <p className="font-semibold text-gray-800 dark:text-gray-200">
                  {currentStepIndex + 1} / {GENERATION_STEPS.length}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
