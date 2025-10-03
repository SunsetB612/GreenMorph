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
  LoginOutlined
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

const Profile: React.FC = () => {
  const [activeTab, setActiveTab] = useState('posts');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm] = Form.useForm();
  
  const { user, isAuthenticated, checkAuth } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const loadUserInfo = async () => {
      if (isAuthenticated && user) {
        setUserInfo(user);
        setLoading(false);
      } else {
        // 尝试检查认证状态
        await checkAuth();
        setLoading(false);
      }
    };
    
    loadUserInfo();
  }, [isAuthenticated, user, checkAuth]);

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
      
      const response = await fetch('http://localhost:8000/api/auth/me', {
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
    posts: 24,
    likes: 186,
    followers: 89,
    following: 156
  };

  const myPosts = [
    {
      id: 1,
      title: '旧牛仔裤改造收纳袋',
      content: '用旧牛仔裤做了一个超实用的收纳袋...',
      likes: 24,
      comments: 8,
      time: '2天前',
      tags: ['旧物改造', '收纳']
    },
    {
      id: 2,
      title: '塑料瓶变身花瓶',
      content: '用废弃的塑料瓶制作了漂亮的花瓶...',
      likes: 18,
      comments: 5,
      time: '5天前',
      tags: ['塑料瓶', '花瓶']
    }
  ];

  const achievements = [
    { name: '环保新手', icon: '🌱', description: '发布第一个创意', earned: true },
    { name: '改造达人', icon: '🔧', description: '发布10个改造作品', earned: true },
    { name: '社区活跃', icon: '💬', description: '获得50个点赞', earned: true },
    { name: '创意大师', icon: '🎨', description: '发布50个创意', earned: false },
    { name: '环保专家', icon: '🏆', description: '获得1000积分', earned: false }
  ];

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
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>
            <UserOutlined style={{ marginRight: '8px', color: 'var(--primary-color)' }} />
            个人中心
          </Title>
        </div>
        
        <Card>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <UserOutlined style={{ fontSize: '64px', color: 'var(--text-secondary)', marginBottom: '16px' }} />
            <Title level={3} style={{ marginBottom: '16px' }}>
              请先登录
            </Title>
            <Paragraph style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
              登录后即可查看您的个人资料、作品和成就
            </Paragraph>
            <Button 
              type="primary" 
              size="large" 
              icon={<LoginOutlined />}
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
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <UserOutlined style={{ marginRight: '8px', color: 'var(--primary-color)' }} />
          个人中心
        </Title>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          {/* 用户信息卡片 */}
          <Card style={{ marginBottom: '24px' }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <Avatar 
                size={80} 
                src={userInfo.avatar || `https://api.dicebear.com/7.x/miniavs/svg?seed=${userInfo.username}`}
                style={{ marginBottom: '16px' }}
              />
              <Title level={3} style={{ marginBottom: '8px' }}>
                {userInfo.username}
              </Title>
              <Paragraph style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                {userInfo.bio || '还没有设置个人简介'}
              </Paragraph>
              <Button type="primary" icon={<EditOutlined />} onClick={handleEditProfile}>
                编辑个人简介
              </Button>
            </div>

            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic 
                  title="发布作品" 
                  value={stats.posts} 
                  prefix={<EditOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="获得点赞" 
                  value={stats.likes} 
                  prefix={<HeartOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="粉丝" 
                  value={stats.followers} 
                  prefix={<UserOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="关注" 
                  value={stats.following} 
                  prefix={<UserOutlined />}
                />
              </Col>
            </Row>

            <Divider />

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Space>
                  <EnvironmentOutlined style={{ color: 'var(--text-secondary)' }} />
                  <span>{userInfo.location || '未设置'}</span>
                </Space>
              </Col>
              <Col span={12}>
                <Space>
                  <CalendarOutlined style={{ color: 'var(--text-secondary)' }} />
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
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {myPosts.map((item) => (
                        <div key={item.id} style={{ 
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
                            {item.title}
                          </div>
                          <div style={{ 
                            color: 'var(--text-secondary)',
                            marginBottom: '12px',
                            lineHeight: '1.5'
                          }}>
                            {item.content}
                          </div>
                          <div style={{ marginBottom: '12px' }}>
                            {item.tags.map(tag => (
                              <Tag key={tag} style={{ marginRight: '4px', marginBottom: '4px' }}>
                                {tag}
                              </Tag>
                            ))}
                          </div>
                          <div style={{ 
                            color: 'var(--text-secondary)', 
                            fontSize: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '16px'
                          }}>
                            <span><HeartOutlined /> {item.likes}</span>
                            <span><MessageOutlined /> {item.comments}</span>
                            <span>{item.time}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                },
                {
                  key: 'likes',
                  label: '点赞',
                  children: (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                      暂无点赞内容
                    </div>
                  )
                }
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* 等级和积分 */}
          <Card title="等级信息" style={{ marginBottom: '24px' }}>
            <div style={{ textAlign: 'center' }}>
              <TrophyOutlined style={{ fontSize: '32px', color: 'var(--warning-color)', marginBottom: '8px' }} />
              <Title level={4} style={{ marginBottom: '8px' }}>
                {userInfo.skill_level === 'beginner' ? '环保新手' : 
                 userInfo.skill_level === 'intermediate' ? '改造达人' : '创意大师'}
              </Title>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                  等级根据积分自动计算
                </span>
              </div>
              <div style={{ marginBottom: '16px' }}>
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
                    width: `${Math.min((userInfo.points || 0) / 2000 * 100, 100)}%`
                  }} />
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {userInfo.points || 0} / 2000 积分
                </div>
              </div>
            </div>
          </Card>

          {/* 成就系统 */}
          <Card title="成就徽章">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {achievements.map((achievement, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  padding: '12px',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  backgroundColor: 'var(--card-background)'
                }}>
                  <span style={{ fontSize: '24px', marginRight: '12px' }}>
                    {achievement.icon}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      marginBottom: '4px'
                    }}>
                      <span style={{ fontWeight: 500, fontSize: '16px' }}>
                        {achievement.name}
                      </span>
                      <Tag color={achievement.earned ? 'green' : 'default'}>
                        {achievement.earned ? '已获得' : '未获得'}
                      </Tag>
                    </div>
                    <div style={{ 
                      color: 'var(--text-secondary)', 
                      fontSize: '14px',
                      lineHeight: '1.4'
                    }}>
                      {achievement.description}
                    </div>
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
            rules={[{ max: 200, message: '个人简介不能超过200个字符' }]}
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
