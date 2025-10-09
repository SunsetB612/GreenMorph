// utils/achievementNotifier.tsx
import { notification, Modal } from 'antd';

// 定义成就类型
interface Achievement {
  id: number;
  name: string;
  description: string;
  condition_type: string;
  condition_value: number;
}

interface CheckAchievementsResponse {
  code: number;
  message: string;
  data: {
    new_achievements: Achievement[];
    total_earned: number;
    user_progress: Record<string, number>;
  };
}

// 成就图标映射
const getAchievementIcon = (name: string): string => {
  const iconMap: Record<string, string> = {
    '新手改造师': '🌱',
    '创意启蒙者': '🚀',
    '小有名气': '❤️',
    '改造达人': '🔧',
    '社区明星': '🌟',
    '热心观众': '💬',
    '热心评论家': '🗣️',
    '创意大师': '🎨'
  };
  return iconMap[name] || '🏆';
};

// 检查并通知成就
export const checkAndNotifyAchievements = async (userId: number, onAchievementsUpdated?: () => void): Promise<void> => {
  try {
    const response = await fetch(`http://localhost:8000/api/gamification/achievements/check/${userId}`, {
      method: 'POST',
    });

    const result: CheckAchievementsResponse = await response.json();

    if (result.code === 200 && result.data.new_achievements.length > 0) {
      // 显示所有新获得的成就
      result.data.new_achievements.forEach((achievement: Achievement) => {
        showAchievementNotification(achievement);
      });

      // 🎯 新增：如果有新成就，延迟刷新成就列表
      if (onAchievementsUpdated) {
        setTimeout(() => {
          onAchievementsUpdated();
        }, 2000);
      }
    }
  } catch (error) {
    console.error('检查成就失败:', error);
  }
};

// 显示成就通知 - 绿色环保主题
const showAchievementNotification = (achievement: Achievement): void => {
  // 1. 轻量Toast通知
  notification.success({
    message: '🎉 成就达成！',
    description: `${achievement.name} - ${achievement.description}`,
    duration: 3,
    placement: 'topRight' as const,
    style: {
      border: '1px solid #52c41a',
      borderRadius: '8px',
    }
  });

  // 2. 绿色主题弹窗（延迟显示）
  setTimeout(() => {
    Modal.success({
      title: null,
      icon: null,
      closable: false,
      content: (
        <div style={{
          textAlign: 'center',
          padding: '40px 30px',
          background: 'linear-gradient(135deg, #f6ffed 0%, #e6f7ff 100%)',
          borderRadius: '16px',
          border: '2px solid #b7eb8f',
          boxShadow: '0 8px 32px rgba(82, 196, 26, 0.2)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* 装饰性背景元素 */}
          <div style={{
            position: 'absolute',
            top: '-50px',
            right: '-50px',
            width: '120px',
            height: '120px',
            background: 'rgba(82, 196, 26, 0.1)',
            borderRadius: '50%',
            zIndex: 0
          }} />
          <div style={{
            position: 'absolute',
            bottom: '-30px',
            left: '-30px',
            width: '80px',
            height: '80px',
            background: 'rgba(135, 208, 104, 0.1)',
            borderRadius: '50%',
            zIndex: 0
          }} />

          {/* 主要内容 */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{
              fontSize: '72px',
              marginBottom: '20px',
              filter: 'drop-shadow(0 4px 8px rgba(82, 196, 26, 0.3))'
            }}>
              {getAchievementIcon(achievement.name)}
            </div>

            <div style={{
              fontSize: '14px',
              background: 'linear-gradient(135deg, #52c41a, #73d13d)',
              color: 'white',
              padding: '8px 20px',
              borderRadius: '20px',
              display: 'inline-block',
              marginBottom: '20px',
              fontWeight: '600',
              letterSpacing: '0.5px',
              boxShadow: '0 4px 12px rgba(82, 196, 26, 0.3)'
            }}>
              🎊 环保成就解锁
            </div>

            <h3 style={{
              marginBottom: '12px',
              fontSize: '26px',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #389e0d, #52c41a)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              color: 'transparent'
            }}>
              {achievement.name}
            </h3>

            <p style={{
              color: '#595959',
              marginBottom: '30px',
              fontSize: '16px',
              lineHeight: '1.6',
              maxWidth: '320px',
              margin: '0 auto 30px'
            }}>
              {achievement.description}
            </p>

            <div style={{
              background: 'rgba(82, 196, 26, 0.1)',
              padding: '12px 20px',
              borderRadius: '12px',
              fontSize: '14px',
              color: '#389e0d',
              border: '1px solid rgba(82, 196, 26, 0.3)',
              display: 'inline-block'
            }}>
              🌿 为环保事业贡献力量！
            </div>
          </div>
        </div>
      ),
      okText: '继续努力 🚀',
      width: 480,
      centered: true,
      maskStyle: {
        backgroundColor: 'rgba(0, 0, 0, 0.4)'
      },
      bodyStyle: {
        padding: '0',
        background: 'transparent'
      },
      okButtonProps: {
        style: {
          background: 'linear-gradient(135deg, #52c41a, #73d13d)',
          border: 'none',
          borderRadius: '8px',
          fontWeight: '600',
          height: '40px',
          padding: '0 24px',
          boxShadow: '0 4px 12px rgba(82, 196, 26, 0.3)'
        }
      },
      style: {
        borderRadius: '16px',
        overflow: 'hidden'
      }
    });
  }, 500);
};