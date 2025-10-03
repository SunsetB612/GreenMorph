import React, { useState } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Tag,
  Avatar,
  Row,
  Col,
  Tabs,
} from 'antd';
import { 
  SearchOutlined, 
  PlusOutlined,
  HeartOutlined,
  MessageOutlined,
  ShareAltOutlined,
  FireOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const Community: React.FC = () => {
  const [searchValue, setSearchValue] = useState('');

  // 模拟社区数据
  const posts = [
    {
      id: 1,
      user: '环保达人小李',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=1',
      title: '旧牛仔裤改造收纳袋',
      content: '用旧牛仔裤做了一个超实用的收纳袋，既环保又实用！',
      images: ['https://via.placeholder.com/300x200'],
      likes: 24,
      comments: 8,
      shares: 3,
      tags: ['旧物改造', '收纳', '牛仔裤'],
      time: '2小时前',
      isLiked: false
    },
    {
      id: 2,
      user: '创意小能手',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=2',
      title: '塑料瓶变身花瓶',
      content: '用废弃的塑料瓶制作了漂亮的花瓶，放在家里很有艺术感！',
      images: ['https://via.placeholder.com/300x200'],
      likes: 18,
      comments: 5,
      shares: 2,
      tags: ['塑料瓶', '花瓶', '装饰'],
      time: '4小时前',
      isLiked: true
    },
    {
      id: 3,
      user: '绿色生活家',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=3',
      title: '纸箱制作书架',
      content: '用快递纸箱制作了一个简易书架，既省钱又环保！',
      images: ['https://via.placeholder.com/300x200'],
      likes: 31,
      comments: 12,
      shares: 6,
      tags: ['纸箱', '书架', '收纳'],
      time: '1天前',
      isLiked: false
    }
  ];

  const handleLike = (postId: number) => {
    // 这里应该调用API来更新点赞状态
    console.log('点赞帖子:', postId);
  };

  const handleComment = (postId: number) => {
    // 这里应该打开评论对话框
    console.log('评论帖子:', postId);
  };

  const handleShare = (postId: number) => {
    // 这里应该实现分享功能
    console.log('分享帖子:', postId);
  };

  return (
    <div style={{ 
      minHeight: 'calc(100vh - 64px)', 
      padding: '24px',
      background: 'var(--background-color)'
    }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <FireOutlined style={{ marginRight: '8px', color: 'var(--error-color)' }} />
          社区分享
        </Title>
        <Paragraph>
          与环保爱好者交流创意，分享您的旧物改造经验
        </Paragraph>
      </div>

      {/* 搜索和发布区域 */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={16}>
            <Input
              placeholder="搜索创意、用户或话题..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              size="large"
            />
          </Col>
          <Col xs={24} sm={8}>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              size="large" 
              block
            >
              发布创意
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 内容区域 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Tabs 
            defaultActiveKey="hot"
            items={[
              {
                key: 'hot',
                label: '热门',
                children: (
                  <div>
                    {posts.map(post => (
                      <Card 
                        key={post.id} 
                        style={{ marginBottom: '16px' }}
                        hoverable
                      >
                        <div style={{ marginBottom: '12px' }}>
                          <Space>
                            <Avatar src={post.avatar} />
                            <div>
                              <div style={{ fontWeight: 'bold' }}>{post.user}</div>
                              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                <ClockCircleOutlined /> {post.time}
                              </div>
                            </div>
                          </Space>
                        </div>

                        <Title level={4} style={{ marginBottom: '8px' }}>
                          {post.title}
                        </Title>

                        <Paragraph style={{ marginBottom: '12px' }}>
                          {post.content}
                        </Paragraph>

                        <div style={{ marginBottom: '12px' }}>
                          <img 
                            src={post.images[0]} 
                            alt="post" 
                            style={{ 
                              width: '100%', 
                              maxWidth: '300px',
                              borderRadius: '8px' 
                            }} 
                          />
                        </div>

                        <div style={{ marginBottom: '12px' }}>
                          {post.tags.map(tag => (
                            <Tag key={tag} color="blue">{tag}</Tag>
                          ))}
                        </div>

                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          borderTop: '1px solid var(--border-color)',
                          paddingTop: '12px'
                        }}>
                          <Button 
                            type="text" 
                            icon={<HeartOutlined />}
                            onClick={() => handleLike(post.id)}
                            style={{ color: post.isLiked ? 'var(--error-color)' : 'var(--text-secondary)' }}
                          >
                            {post.likes}
                          </Button>
                          <Button 
                            type="text" 
                            icon={<MessageOutlined />}
                            onClick={() => handleComment(post.id)}
                          >
                            {post.comments}
                          </Button>
                          <Button 
                            type="text" 
                            icon={<ShareAltOutlined />}
                            onClick={() => handleShare(post.id)}
                          >
                            {post.shares}
                          </Button>
                        </div>
                      </Card>
                    ))}
                  </div>
                )
              },
              {
                key: 'latest',
                label: '最新',
                children: (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                    最新内容加载中...
                  </div>
                )
              },
              {
                key: 'following',
                label: '关注',
                children: (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                    关注的内容将在这里显示
                  </div>
                )
              }
            ]}
          />
        </Col>

        <Col xs={24} lg={8}>
          <Card title="热门话题" style={{ marginBottom: '24px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Tag color="red" style={{ fontSize: '14px', padding: '4px 8px' }}>
                #旧物改造
              </Tag>
              <Tag color="blue" style={{ fontSize: '14px', padding: '4px 8px' }}>
                #环保生活
              </Tag>
              <Tag color="green" style={{ fontSize: '14px', padding: '4px 8px' }}>
                #创意手工
              </Tag>
              <Tag color="orange" style={{ fontSize: '14px', padding: '4px 8px' }}>
                #收纳整理
              </Tag>
              <Tag color="purple" style={{ fontSize: '14px', padding: '4px 8px' }}>
                #DIY教程
              </Tag>
            </Space>
          </Card>

          <Card title="推荐用户">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Space>
                  <Avatar size="small" src="https://api.dicebear.com/7.x/miniavs/svg?seed=4" />
                  <span>环保达人</span>
                </Space>
                <Button size="small">关注</Button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Space>
                  <Avatar size="small" src="https://api.dicebear.com/7.x/miniavs/svg?seed=5" />
                  <span>创意大师</span>
                </Space>
                <Button size="small">关注</Button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Space>
                  <Avatar size="small" src="https://api.dicebear.com/7.x/miniavs/svg?seed=6" />
                  <span>手工达人</span>
                </Space>
                <Button size="small">关注</Button>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Community;
