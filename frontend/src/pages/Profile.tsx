import React, { useState } from 'react';
import { 
  Card, 
  Avatar, 
  Button, 
  Typography, 
  Space,
  Row,
  Col,
  Tabs,
  List,
  Tag,
  Statistic,
  Divider
} from 'antd';
import { 
  EditOutlined,
  SettingOutlined,
  HeartOutlined,
  MessageOutlined,
  TrophyOutlined,
  UserOutlined,
  EnvironmentOutlined,
  CalendarOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;
const { TabPane } = Tabs;

const Profile: React.FC = () => {
  const [activeTab, setActiveTab] = useState('posts');

  // 模拟用户数据
  const userInfo = {
    name: '环保达人小李',
    avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=1',
    bio: '热爱环保生活，喜欢旧物改造，分享创意生活',
    location: '北京市',
    joinDate: '2024年1月',
    level: '环保达人',
    points: 1250
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
                src={userInfo.avatar}
                style={{ marginBottom: '16px' }}
              />
              <Title level={3} style={{ marginBottom: '8px' }}>
                {userInfo.name}
              </Title>
              <Paragraph style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                {userInfo.bio}
              </Paragraph>
              <Space>
                <Button type="primary" icon={<EditOutlined />}>
                  编辑资料
                </Button>
                <Button icon={<SettingOutlined />}>
                  设置
                </Button>
              </Space>
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
                  <EnvironmentOutlined style={{ color: 'var(--text-tertiary)' }} />
                  <span>{userInfo.location}</span>
                </Space>
              </Col>
              <Col span={12}>
                <Space>
                  <CalendarOutlined style={{ color: 'var(--text-tertiary)' }} />
                  <span>加入于 {userInfo.joinDate}</span>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 内容标签页 */}
          <Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <TabPane tab="我的作品" key="posts">
                <List
                  dataSource={myPosts}
                  renderItem={(item) => (
                  <List.Item key={item.id}>
                    <List.Item.Meta
                      title={item.title}
                      description={
                        <div>
                          <Paragraph ellipsis={{ rows: 2 }}>
                            {item.content}
                          </Paragraph>
                          <div style={{ marginTop: '8px' }}>
                            {item.tags.map(tag => (
                              <Tag key={tag}>{tag}</Tag>
                            ))}
                          </div>
                          <div style={{ marginTop: '8px', color: 'var(--text-tertiary)', fontSize: '12px' }}>
                            <Space>
                              <span><HeartOutlined /> {item.likes}</span>
                              <span><MessageOutlined /> {item.comments}</span>
                              <span>{item.time}</span>
                            </Space>
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
                />
              </TabPane>
              <TabPane tab="收藏" key="favorites">
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
                  暂无收藏内容
                </div>
              </TabPane>
              <TabPane tab="点赞" key="likes">
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
                  暂无点赞内容
                </div>
              </TabPane>
            </Tabs>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* 等级和积分 */}
          <Card title="等级信息" style={{ marginBottom: '24px' }}>
            <div style={{ textAlign: 'center' }}>
              <TrophyOutlined style={{ fontSize: '32px', color: 'var(--warning-color)', marginBottom: '8px' }} />
              <Title level={4} style={{ marginBottom: '8px' }}>
                {userInfo.level}
              </Title>
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
                    width: '75%'
                  }} />
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
                  {userInfo.points} / 2000 积分
                </div>
              </div>
            </div>
          </Card>

          {/* 成就系统 */}
          <Card title="成就徽章">
            <List
              dataSource={achievements}
              renderItem={(achievement) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<span style={{ fontSize: '24px' }}>{achievement.icon}</span>}
                    title={
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between' 
                      }}>
                        <span>{achievement.name}</span>
                        <Tag color={achievement.earned ? 'green' : 'default'}>
                          {achievement.earned ? '已获得' : '未获得'}
                        </Tag>
                      </div>
                    }
                    description={achievement.description}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Profile;
