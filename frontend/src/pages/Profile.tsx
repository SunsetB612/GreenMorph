import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Avatar, 
  Button, 
  Typography, 
  Space,
  Row,
  Col,
  Tabs,
  Tag,
  Statistic,
  Divider,
  Spin,
  Modal,
  Form,
  Input,
  message
} from 'antd';
import { 
  EditOutlined,
  HeartOutlined,
  MessageOutlined,
  TrophyOutlined,
  UserOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  LoginOutlined,
  CrownOutlined
} from '@ant-design/icons';

import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import {checkAndNotifyAchievements} from "../utils/achievementNotifier";

const API_BASE_URL = import.meta.env.VITE_API_URL;

const { Title, Paragraph } = Typography;
interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string | null;
  condition_type: string;
  condition_value: number;
  status: 'achieved' | 'locked';
  progress: number;
  target: number;
  progress_percentage: number;
  earned_at: string | null;
  is_completed: boolean;
}


interface UserAchievementResponse {
  code: number;
  message: string;
  data: {
    user_id: number;
    username: string;
    total_achievements: number;
    earned_count: number;
    achievements: Achievement[];
  };
}
interface UserRankingResponse {
  code: number;
  message: string;
  data: {
    user_id: number;
    username: string;
    points: number;
    skill_level: string;
    rank: number;
    total_users: number;
    percentile: number;
  };
}
interface LeaderboardUser {
  rank: number;
  user_id: number;
  username: string;
  points: number;
  skill_level: string;
}

interface LeaderboardResponse {
  code: number;
  message: string;
  data: {
    leaderboard: LeaderboardUser[];
    total_users: number;
    type: string;
    updated_at: string;
  };
}
// 用户统计接口类型
interface UserStatsData {
  user_id: number;
  posts_count: number;
  total_likes: number;
}

interface UserStatsResponse {
  code: number;
  message: string;
  data: UserStatsData;
}
interface Post {
  id: number;
  user_id: number;
  user_name: string;
  title: string;
  content: string;
  likes_count: number;
  comments_count: number;
  created_at: string;
  updated_at: string;
  images: string[];
}

interface PostsResponse {
  total: number;
  page: number;
  size: number;
  items: Post[];
}

const Profile: React.FC = () => {
  const [activeTab, setActiveTab] = useState('posts');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm] = Form.useForm();
  const {user, isAuthenticated, checkAuth} = useAuthStore();
  const navigate = useNavigate();
  const [userAchievements, setUserAchievements] = useState<Achievement[]>([]);
  const [achievementsLoading, setAchievementsLoading] = useState(false);
  const [userRanking, setUserRanking] = useState<any>(null);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [leaderboardLoading, setLeaderboardLoading] = useState<boolean>(false);
  const [userStats, setUserStats] = useState<UserStatsData | null>(null);
  const [statsLoading, setStatsLoading] = useState<boolean>(false);
  const [userPosts, setUserPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState<boolean>(false);
  const [likedPosts, setLikedPosts] = useState<Post[]>([]);
  const [likedPostsLoading, setLikedPostsLoading] = useState<boolean>(false);
  const [achievementStats, setAchievementStats] = useState({
    total: 0,
    earned: 0,
    progress: 0
  });


  // 打开编辑模态框
  const handleEditProfile = () => {
    editForm.setFieldsValue({
      bio: userInfo?.bio
    });
    setEditModalVisible(true);
  };

  // 保存编辑
  const handleSaveEdit = async (values: any) => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        message.error('请先登录');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(values)
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setUserInfo(updatedUser);
        setEditModalVisible(false);
        message.success('资料更新成功！');
      } else {
        message.error('更新失败，请重试');
      }
    } catch (error) {
      message.error('网络错误，请重试');
    }
  };

  const stats = {
    followers: 89,
    following: 156
  };
  // 成就图标映射
const getAchievementIcon = (name: string) => {
  const iconMap: { [key: string]: string } = {
    '新手改造师': '🌱',
    '小有名气': '❤️',
    '创意大师': '🎨',
    '改造达人': '🔧',
    '热心评论家': '💬',
    '热心观众': '🗣️',
    '社区明星': '🌟',
    '创意启蒙者': '📚',
  };
  return iconMap[name] || '🏆';
};


 const fetchUserAchievements = async (userId: number) => {
  setAchievementsLoading(true);
  try {
    // 先自动检查并发放成就
    const checkResponse = await fetch(`${API_BASE_URL}/gamification/achievements/check/${userId}`, {
      method: 'POST'
    });
    const checkResult = await checkResponse.json();

    if (checkResult.code === 200 && checkResult.data.new_achievements.length > 0) {
      message.success(`获得了 ${checkResult.data.new_achievements.length} 个新成就！`);
    }

    // 再获取最新的成就状态
    const response = await fetch(`${API_BASE_URL}/gamification/achievements/user/${userId}`);
    const result: UserAchievementResponse = await response.json();

    if (result.code === 200) {
      // 精细排序：未获得的在前，已获得的在后
      const sortedAchievements = [...result.data.achievements].sort((a, b) => {
        // 未获得的成就排在前面的
        if (a.status !== 'achieved' && b.status === 'achieved') return -1;
        if (a.status === 'achieved' && b.status !== 'achieved') return 1;

        // 都是未获得的，按进度百分比倒序（进度高的在前）
        if (a.status !== 'achieved' && b.status !== 'achieved') {
          return b.progress_percentage - a.progress_percentage;
        }

        // 都是已获得的，按获得时间正序（最早获得的在前）
        return new Date(a.earned_at!).getTime() - new Date(b.earned_at!).getTime();
      });

      setUserAchievements(sortedAchievements);
      const earned = result.data.achievements.filter(a => a.status === 'achieved').length;
      const total = result.data.achievements.length;
      setAchievementStats({
        total,
        earned,
        progress: total > 0 ? Math.round((earned / total) * 100) : 0
      });
    } else {
      message.error('获取用户成就失败');
    }
  } catch (error) {
    console.error('获取用户成就失败:', error);
    message.error('获取用户成就失败');
  } finally {
    setAchievementsLoading(false);
  }
};

// 获取排行榜
const fetchLeaderboard = async (limit: number = 10): Promise<void> => {
  setLeaderboardLoading(true);
  try {
    const response = await fetch(`${API_BASE_URL}/gamification/leaderboard?limit=${limit}`);
    const result: LeaderboardResponse = await response.json();

    if (result.code === 200) {
      setLeaderboard(result.data.leaderboard);
    } else {
      message.error('获取排行榜失败');
    }
  } catch (error) {
    console.error('获取排行榜失败:', error);
    message.error('获取排行榜失败');
  } finally {
    setLeaderboardLoading(false);
  }
};

// 获取用户排名
const fetchUserRanking = async (userId: number): Promise<void> => {
  setRankingLoading(true);
  try {
    // 先获取排行榜数据来计算准确排名
    const response = await fetch(`${API_BASE_URL}/gamification/leaderboard?limit=100`);
    const result: LeaderboardResponse = await response.json();

    if (result.code === 200) {
      // 在排行榜中查找当前用户的准确排名
      const currentUserRank = result.data.leaderboard.findIndex(
        user => user.user_id === userId
      );

      if (currentUserRank !== -1) {
        // 找到用户，排名是索引+1
        const userData = result.data.leaderboard[currentUserRank];
        setUserRanking({
          user_id: userId,
          username: userData.username,
          points: userData.points,
          skill_level: userData.skill_level,
          rank: currentUserRank + 1,
          total_users: result.data.total_users,
          percentile: result.data.total_users > 0 ?
            Math.round(((result.data.total_users - (currentUserRank + 1)) / result.data.total_users) * 100) : 0
        });
      } else {
        // 用户不在前100名，需要单独查询
        const userResponse = await fetch(`${API_BASE_URL}/gamification/leaderboard/user/${userId}`);
        const userResult: UserRankingResponse = await userResponse.json();

        if (userResult.code === 200) {
          setUserRanking(userResult.data);
        } else {
          message.error('获取用户排名失败');
        }
      }
    } else {
      message.error('获取排行榜失败');
    }
  } catch (error) {
    console.error('获取用户排名失败:', error);
    message.error('获取用户排名失败');
  } finally {
    setRankingLoading(false);
  }
};
useEffect(() => {
  const loadUserInfo = async (): Promise<void> => {
    if (isAuthenticated && user) {
      setUserInfo(user);
      // 先获取所有数据
      await Promise.all([
        fetchUserAchievements(user.id),
        fetchUserRanking(user.id),
        fetchLeaderboard(10),
        fetchUserStats(user.id),
        fetchUserPosts(user.id),
        fetchLikedPosts(user.id)
      ]);
      // 然后再检查成就
      await checkAndNotifyAchievements(user.id, () => {
        fetchUserAchievements(user.id);
      });
      setLoading(false);
    } else {
      await checkAuth();
      setLoading(false);
    }
  };

  loadUserInfo();
}, [isAuthenticated, user, checkAuth]);

// 根据积分实时计算等级
const calculateRealTimeLevel = (points: number): string => {
  if (points >= 200) return "advanced";
  if (points >= 100) return "intermediate";
  return "beginner";
};

// 等级显示函数
const getLevelName = (skillLevel: string, points?: number): string => {
  // 如果提供了积分，优先使用实时计算的等级
  if (points !== undefined) {
    const realTimeLevel = calculateRealTimeLevel(points);
    const levelMap: Record<string, string> = {
      'beginner': '✨ 新秀',
      'intermediate': '🌟 精英',
      'advanced': '💎 大师'
    };
    return levelMap[realTimeLevel] || '未知等级';
  }

  // 否则使用数据库中的等级
  const levelMap: Record<string, string> = {
    'beginner': '✨ 新秀',
    'intermediate': '🌟 精英',
    'advanced': '💎 大师'
  };
  return levelMap[skillLevel] || '未知等级';
};

// 积分进度计算函数（根据实际积分规则）
const calculatePointsProgress = (points: number) => {
  // 根据你的积分等级规则计算进度
  if (points >= 200) return 100; // 进阶，满进度
  if (points >= 100) return 50 + ((points - 100) / 100) * 50; // 中级到进阶的进度
  return (points / 100) * 50; // 新手到中级的进度
};
// 获取用户统计
const fetchUserStats = async (userId: number): Promise<void> => {
  setStatsLoading(true);
  try {
    const response = await fetch(`${API_BASE_URL}/community/users/${userId}/stats`);
    const result: UserStatsResponse = await response.json();

    if (result.code === 200) {
      setUserStats(result.data);
    } else {
      message.error('获取用户统计失败');
    }
  } catch (error) {
    console.error('获取用户统计失败:', error);
    message.error('获取用户统计失败');
  } finally {
    setStatsLoading(false);
  }
};
// 获取用户帖子
const fetchUserPosts = async (userId: number): Promise<void> => {
  setPostsLoading(true);
  try {
    const response = await fetch(`${API_BASE_URL}/community/users/${userId}/posts`);
    const result: PostsResponse = await response.json();

    if (result.items) {
      console.log('获取到的用户帖子:', {
        total: result.total,
        postsCount: result.items.length,
        posts: result.items
      });
      setUserPosts(result.items);
    } else {
      message.error('获取用户帖子失败');
    }
  } catch (error) {
    console.error('获取用户帖子失败:', error);
    message.error('获取用户帖子失败');
  } finally {
    setPostsLoading(false);
  }
};
const fetchLikedPosts = async (userId: number): Promise<void> => {
  setLikedPostsLoading(true);
  try {
    const response = await fetch(`${API_BASE_URL}/community/users/${userId}/liked-posts`);
    const result: PostsResponse = await response.json();

    if (result.items) {
      console.log('获取到的点赞帖子:', {
        total: result.total,
        postsCount: result.items.length,
        posts: result.items
      });
      setLikedPosts(result.items);
    } else {
      message.error('获取点赞帖子失败');
    }
  } catch (error) {
    console.error('获取点赞帖子失败:', error);
    message.error('获取点赞帖子失败');
  } finally {
    setLikedPostsLoading(false);
  }
};

  // 如果正在加载
  if (loading) {
    return (
      <div style={{ 
        minHeight: 'calc(100vh - 64px)', 
        padding: '24px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <Spin size="large" />
      </div>
    );
  }

  // 如果未登录
  if (!isAuthenticated || !userInfo) {
    return (
        <div style={{
          minHeight: 'calc(100vh - 64px)',
          padding: '24px',
          background: 'var(--background-color)'
        }}>
          <div style={{marginBottom: '24px'}}>
            <Title level={2}>
              <UserOutlined style={{marginRight: '8px', color: 'var(--primary-color)'}}/>
              个人中心
            </Title>
          </div>

          <Card>
            <div style={{textAlign: 'center', padding: '40px'}}>
              <UserOutlined style={{fontSize: '64px', color: 'var(--text-secondary)', marginBottom: '16px'}}/>
              <Title level={3} style={{marginBottom: '16px'}}>
                请先登录
              </Title>
              <Paragraph style={{color: 'var(--text-secondary)', marginBottom: '24px'}}>
                登录后即可查看您的个人资料、作品和成就
              </Paragraph>
              <Button
                  type="primary"
                  size="large"
                  icon={<LoginOutlined/>}
                  onClick={() => navigate('/auth')}
              >
                立即登录
              </Button>
            </div>
          </Card>
        </div>
    );
  }

  return (
      <div style={{
        minHeight: 'calc(100vh - 64px)',
        padding: '24px',
        background: 'var(--background-color)'
      }}>
        <div style={{marginBottom: '24px'}}>
          <Title level={2}>
            <UserOutlined style={{marginRight: '8px', color: 'var(--primary-color)'}}/>
            个人中心
          </Title>
        </div>

        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            {/* 用户信息卡片 */}
            <Card style={{marginBottom: '24px'}}>
              <div style={{textAlign: 'center', marginBottom: '24px'}}>
                <Avatar
                    size={80}
                    src={userInfo.avatar || `https://api.dicebear.com/7.x/miniavs/svg?seed=${userInfo.username}`}
                    style={{marginBottom: '16px'}}
                />
                <Title level={3} style={{marginBottom: '8px'}}>
                  {userInfo.username}
                </Title>
                <Paragraph style={{color: 'var(--text-secondary)', marginBottom: '16px'}}>
                  {userInfo.bio || '还没有设置个人简介'}
                </Paragraph>
                <Button type="primary" icon={<EditOutlined/>} onClick={handleEditProfile}>
                  编辑个人简介
                </Button>
              </div>

              <Row gutter={[16, 16]}>
                <Col span={6}>
                  <Statistic
                      title="发布作品"
                      value={userStats?.posts_count || 0}
                      prefix={<EditOutlined/>}
                      loading={statsLoading}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                      title="获得点赞"
                      value={userStats?.total_likes || 0}
                      prefix={<HeartOutlined/>}
                      loading={statsLoading}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                      title="粉丝"
                      value={stats.followers}
                      prefix={<UserOutlined/>}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                      title="关注"
                      value={stats.following}
                      prefix={<UserOutlined/>}
                  />
                </Col>
              </Row>

              <Divider/>

              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Space>
                    <EnvironmentOutlined style={{color: 'var(--text-secondary)'}}/>
                    <span>{userInfo.location || '未设置'}</span>
                  </Space>
                </Col>
                <Col span={12}>
                  <Space>
                    <CalendarOutlined style={{color: 'var(--text-secondary)'}}/>
                    <span>加入于 {new Date(userInfo.created_at).toLocaleDateString()}</span>
                  </Space>
                </Col>
              </Row>
            </Card>

            {/* 内容标签页 */}
            <Card>
              <Tabs
                  activeKey={activeTab}
                  onChange={setActiveTab}
                  items={[
                    {
                      key: 'posts',
                      label: '我的作品',
                      children: (
                          <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
                            {postsLoading ? (
                                <div style={{textAlign: 'center', padding: '40px'}}>
                                  <Spin size="large"/>
                                </div>
                            ) : userPosts.length > 0 ? (
                                userPosts.map((post) => (
                                    <div key={post.id} style={{
                                      padding: '16px',
                                      border: '1px solid var(--border-color)',
                                      borderRadius: '8px',
                                      backgroundColor: 'var(--card-background)'
                                    }}>
                                      <div style={{
                                        fontWeight: 500,
                                        fontSize: '16px',
                                        marginBottom: '8px',
                                        color: 'var(--text-color)'
                                      }}>
                                        {post.title}
                                      </div>
                                      <div style={{
                                        color: 'var(--text-secondary)',
                                        marginBottom: '12px',
                                        lineHeight: '1.5'
                                      }}>
                                        {post.content}
                                      </div>

                                      {/* 显示帖子图片 - 修复URL */}
                                      {post.images && post.images.length > 0 && (
                                          <div style={{
                                            marginBottom: '12px',
                                            display: 'flex',
                                            gap: '8px',
                                            flexWrap: 'wrap'
                                          }}>
                                            {post.images.slice(0, 3).map((image, index) => (
                                                <img
                                                    key={index}
                                                    src={image.startsWith('http') ? image : `${API_BASE_URL.replace('/api', '')}/${image}`}
                                                    alt={`帖子图片 ${index + 1}`}
                                                    style={{
                                                      width: '80px',
                                                      height: '80px',
                                                      objectFit: 'cover',
                                                      borderRadius: '6px'
                                                    }}
                                                    onError={(e) => {
                                                      // 图片加载失败时隐藏
                                                      (e.target as HTMLImageElement).style.display = 'none';
                                                    }}
                                                />
                                            ))}
                                            {post.images.length > 3 && (
                                                <div style={{
                                                  width: '80px',
                                                  height: '80px',
                                                  background: 'var(--card-background)',
                                                  borderRadius: '6px',
                                                  display: 'flex',
                                                  alignItems: 'center',
                                                  justifyContent: 'center',
                                                  color: 'var(--text-secondary)',
                                                  fontSize: '12px',
                                                  border: '1px dashed var(--border-color)'
                                                }}>
                                                  +{post.images.length - 3}
                                                </div>
                                            )}
                                          </div>
                                      )}

                                      <div style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: '12px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '16px'
                                      }}>
                                        <span><HeartOutlined/> {post.likes_count}</span>
                                        <span><MessageOutlined/> {post.comments_count}</span>
                                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                                      </div>
                                    </div>
                                ))
                            ) : (
                                <div style={{
                                  textAlign: 'center',
                                  padding: '40px',
                                  color: 'var(--text-secondary)'
                                }}>
                                  还没有发布任何作品
                                </div>
                            )}
                          </div>
                      )
                    },
                    {
                      key: 'likes',
                      label: '点赞',
                      children: (
                          <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
                            {likedPostsLoading ? (
                                <div style={{textAlign: 'center', padding: '40px'}}>
                                  <Spin size="large"/>
                                </div>
                            ) : likedPosts.length > 0 ? (
                                likedPosts.map((post) => (
                                    <div key={post.id} style={{
                                      padding: '16px',
                                      border: '1px solid var(--border-color)',
                                      borderRadius: '8px',
                                      backgroundColor: 'var(--card-background)'
                                    }}>
                                      <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        marginBottom: '8px'
                                      }}>
                                        <UserOutlined style={{marginRight: '8px', color: 'var(--text-secondary)'}}/>
                                        <span style={{fontSize: '14px', color: 'var(--text-secondary)'}}>
                {post.user_name}
              </span>
                                      </div>

                                      <div style={{
                                        fontWeight: 500,
                                        fontSize: '16px',
                                        marginBottom: '8px',
                                        color: 'var(--text-color)'
                                      }}>
                                        {post.title}
                                      </div>
                                      <div style={{
                                        color: 'var(--text-secondary)',
                                        marginBottom: '12px',
                                        lineHeight: '1.5'
                                      }}>
                                        {post.content}
                                      </div>

                                      {/* 显示帖子图片 */}
                                      {post.images && post.images.length > 0 && (
                                          <div style={{
                                            marginBottom: '12px',
                                            display: 'flex',
                                            gap: '8px',
                                            flexWrap: 'wrap'
                                          }}>
                                            {post.images.slice(0, 3).map((image, index) => (
                                                <img
                                                    key={index}
                                                    src={image.startsWith('http') ? image : `${API_BASE_URL.replace('/api', '')}/${image}`}
                                                    alt={`帖子图片 ${index + 1}`}
                                                    style={{
                                                      width: '80px',
                                                      height: '80px',
                                                      objectFit: 'cover',
                                                      borderRadius: '6px'
                                                    }}
                                                    onError={(e) => {
                                                      (e.target as HTMLImageElement).style.display = 'none';
                                                    }}
                                                />
                                            ))}
                                            {post.images.length > 3 && (
                                                <div style={{
                                                  width: '80px',
                                                  height: '80px',
                                                  background: 'var(--card-background)',
                                                  borderRadius: '6px',
                                                  display: 'flex',
                                                  alignItems: 'center',
                                                  justifyContent: 'center',
                                                  color: 'var(--text-secondary)',
                                                  fontSize: '12px',
                                                  border: '1px dashed var(--border-color)'
                                                }}>
                                                  +{post.images.length - 3}
                                                </div>
                                            )}
                                          </div>
                                      )}

                                      <div style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: '12px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '16px'
                                      }}>
                                        <span><HeartOutlined style={{color: 'red'}}/> {post.likes_count}</span>
                                        <span><MessageOutlined/> {post.comments_count}</span>
                                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                                      </div>
                                    </div>
                                ))
                            ) : (
                                <div style={{
                                  textAlign: 'center',
                                  padding: '40px',
                                  color: 'var(--text-secondary)'
                                }}>
                                  还没有点赞过任何帖子
                                </div>
                            )}
                          </div>
                      )
                    }
                  ]}
              />
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            {/* 成就统计 */}
            <Card title="成就统计" style={{marginBottom: '24px'}}>
              <div style={{textAlign: 'center'}}>
                <TrophyOutlined style={{fontSize: '32px', color: 'var(--warning-color)', marginBottom: '8px'}}/>
                <Title level={4} style={{marginBottom: '8px'}}>
                  已获得 {achievementStats.earned} / {achievementStats.total} 个成就
                </Title>
                <div style={{marginBottom: '8px'}}>
        <span style={{color: 'var(--text-secondary)', fontSize: '12px'}}>
          成就完成度
        </span>
                </div>
                <div style={{marginBottom: '16px'}}>
                  <div style={{
                    background: 'var(--card-background)',
                    borderRadius: '10px',
                    height: '20px',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      background: 'linear-gradient(90deg, var(--success-color), var(--primary-color))',
                      borderRadius: '10px',
                      height: '100%',
                      width: `${achievementStats.progress}%`
                    }}/>
                  </div>
                  <div style={{fontSize: '12px', color: 'var(--text-secondary)'}}>
                    {achievementStats.progress}% 完成
                  </div>
                </div>
              </div>
            </Card>
            {/* 等级和积分 */}
            <Card title="等级信息" style={{marginBottom: '24px'}} loading={rankingLoading}>
              <div style={{textAlign: 'center'}}>
                <CrownOutlined style={{fontSize: '32px', color: '#ffd700', marginBottom: '8px'}}/>
                <Title level={4} style={{marginBottom: '8px'}}>
                  {userInfo ? getLevelName(userInfo.skill_level, userInfo.points) : '加载中...'}
                </Title>

                {/* 显示排名信息 */}
                {userRanking && (
                    <div style={{marginBottom: '8px'}}>
        <span style={{color: 'var(--primary-color)', fontWeight: 500}}>
          全站排名: 第{userRanking.rank}名
        </span>
                      <div style={{fontSize: '12px', color: 'var(--text-secondary)'}}>
                        击败了 {userRanking.percentile}% 的用户
                      </div>
                    </div>
                )}

                <div style={{marginBottom: '8px'}}>
      <span style={{color: 'var(--text-secondary)', fontSize: '12px'}}>
        等级根据积分自动计算
      </span>
                </div>

                <div style={{marginBottom: '16px'}}>
                  <div style={{
                    background: 'var(--card-background)',
                    borderRadius: '10px',
                    height: '20px',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      background: 'linear-gradient(90deg, var(--success-color), var(--primary-color))',
                      borderRadius: '10px',
                      height: '100%',
                      width: `${userInfo ? calculatePointsProgress(userInfo.points || 0) : 0}%`
                    }}/>
                  </div>
                  <div style={{fontSize: '12px', color: 'var(--text-secondary)'}}>
                    {userInfo?.points || 0} 积分
                    {userRanking && ` • 全站第${userRanking.rank}名`}
                  </div>
                </div>

                {/* 等级规则说明 */}
                <div style={{fontSize: '12px', color: 'var(--text-secondary)'}}>
                  <div>0-99分: ✨ 新秀</div>
                  <div>100-199分: 🌟 精英</div>
                  <div>200分以上: 💎 大师</div>
                </div>
              </div>
            </Card>
            {/* 排行榜 */}
            <Card
                title="积分排行榜"
                style={{marginBottom: '24px'}}
                loading={leaderboardLoading}
            >
              <div style={{maxHeight: '300px', overflowY: 'auto'}}>
                {leaderboard.map((user) => (
                    <div
                        key={user.user_id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          padding: '8px 12px',
                          marginBottom: '8px',
                          borderRadius: '6px',
                          backgroundColor: user.user_id === userInfo?.id ? 'var(--primary-color-light)' : 'transparent'
                        }}
                    >
                      {/* 排名 - 修复前三名颜色 */}
                      <div style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        background:
                            user.rank === 1 ? '#ffd700' : // 金牌 - 金色
                                user.rank === 2 ? '#c0c0c0' : // 银牌 - 银色
                                    user.rank === 3 ? '#cd7f32' : // 铜牌 - 古铜色
                                        'var(--card-background)',
                        color: user.rank <= 3 ? '#000' : 'var(--text-color)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        marginRight: '12px',
                        border: user.rank <= 3 ? '2px solid transparent' : 'none'
                      }}>
                        {user.rank}
                      </div>

                      {/* 用户信息 */}
                      <div style={{flex: 1}}>
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
            <span style={{
              fontWeight: user.user_id === userInfo?.id ? 'bold' : 'normal'
            }}>
              {user.username}
              {user.user_id === userInfo?.id && ' (我)'}
            </span>
                          <span style={{fontSize: '12px', color: 'var(--text-secondary)'}}>
              {user.points}分
            </span>
                        </div>
                        <div style={{
                          fontSize: '12px',
                          color: 'var(--text-secondary)',
                          marginTop: '2px'
                        }}>
                          {getLevelName(user.skill_level)}
                          {user.rank <= 3 && (
                              <span style={{
                                marginLeft: '8px',
                                color:
                                    user.rank === 1 ? '#ffd700' :
                                        user.rank === 2 ? '#c0c0c0' :
                                            '#cd7f32',
                                fontWeight: 'bold'
                              }}>
                {user.rank === 1 ? '🥇' : user.rank === 2 ? '🥈' : '🥉'}
              </span>
                          )}
                        </div>
                      </div>
                    </div>
                ))}
              </div>
            </Card>

            {/* 成就徽章 */}
            <Card title="成就徽章" loading={achievementsLoading}>
              <div style={{
                maxHeight: '400px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                paddingRight: '8px',
              }}>
                {userAchievements.map((achievement) => (
                    <div key={achievement.id} style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '12px',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      backgroundColor: 'var(--card-background)',
                      flexShrink: 0,
                    }}>
          <span style={{fontSize: '24px', marginRight: '12px'}}>
            {getAchievementIcon(achievement.name)}
          </span>
                      <div style={{flex: 1}}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '4px'
                        }}>
              <span style={{fontWeight: 500, fontSize: '16px'}}>
                {achievement.name}
              </span>
                          <Tag color={achievement.status === 'achieved' ? 'green' : 'default'}>
                            {achievement.status === 'achieved' ? '已获得' : '未获得'}
                          </Tag>
                        </div>
                        <div style={{
                          color: 'var(--text-secondary)',
                          fontSize: '14px',
                          lineHeight: '1.4'
                        }}>
                          {achievement.description}
                        </div>
                        {/* 进度条显示 */}
                        <div style={{marginTop: '8px'}}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '12px',
                            marginBottom: '4px',
                            color: 'var(--text-secondary)'
                          }}>
                            <span>进度: {achievement.progress} / {achievement.target}</span>
                            <span>{achievement.progress_percentage}%</span>
                          </div>
                          <div style={{
                            background: 'var(--card-background)',
                            borderRadius: '10px',
                            height: '6px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              background: achievement.status === 'achieved' ?
                                  'var(--success-color)' : 'var(--primary-color)',
                              borderRadius: '10px',
                              height: '100%',
                              width: `${achievement.progress_percentage}%`,
                              transition: 'width 0.3s ease'
                            }}/>
                          </div>
                        </div>
                        {/* 获得时间 */}
                        {achievement.earned_at && (
                            <div style={{
                              marginTop: '4px',
                              fontSize: '12px',
                              color: 'var(--success-color)'
                            }}>
                              获得时间: {new Date(achievement.earned_at).toLocaleDateString()}
                            </div>
                        )}
                      </div>
                    </div>
                ))}
              </div>
            </Card>
          </Col>
        </Row>

        {/* 编辑资料模态框 */}
        <Modal
            title="编辑个人资料"
            open={editModalVisible}
            onCancel={() => setEditModalVisible(false)}
            onOk={() => editForm.submit()}
            okText="保存"
            cancelText="取消"
        >
          <Form
              form={editForm}
              layout="vertical"
              onFinish={handleSaveEdit}
          >
            <Form.Item
                name="bio"
                label="个人简介"
                rules={[{max: 200, message: '个人简介不能超过200个字符'}]}
            >
              <Input.TextArea
                  placeholder="介绍一下自己吧..."
                  rows={4}
                  showCount
                  maxLength={200}
              />
            </Form.Item>
          </Form>
        </Modal>
      </div>
  );
};

export default Profile;
