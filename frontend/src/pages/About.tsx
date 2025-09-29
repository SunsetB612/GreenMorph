import React from 'react';
import { 
  Card, 
  Typography, 
  Row, 
  Col, 
  Space,
  Avatar,
  Timeline,
  Statistic
} from 'antd';
import { 
  TeamOutlined,
  BulbOutlined,
  HeartOutlined,
  EnvironmentOutlined,
  TrophyOutlined,
  RocketOutlined,
  GlobalOutlined,
  SafetyOutlined,
  RobotOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const About: React.FC = () => {
  const teamMembers = [
    {
      name: '张三',
      role: '项目负责人',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=1',
      description: '负责整体项目规划和团队管理'
    },
    {
      name: '李四',
      role: '前端开发',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=2',
      description: '负责用户界面设计和交互体验'
    },
    {
      name: '王五',
      role: '后端开发',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=3',
      description: '负责服务端架构和API开发'
    },
    {
      name: '赵六',
      role: 'AI算法工程师',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=4',
      description: '负责AI模型训练和优化'
    }
  ];

  const milestones = [
    {
      time: '2024年1月',
      title: '项目启动',
      description: 'GreenMorph项目正式启动，团队组建完成'
    },
    {
      time: '2024年2月',
      title: '需求分析',
      description: '深入调研用户需求，确定产品功能方向'
    },
    {
      time: '2024年3月',
      title: '技术选型',
      description: '选择React + FastAPI技术栈，开始架构设计'
    },
    {
      time: '2024年4月',
      title: 'MVP开发',
      description: '完成核心功能开发，发布第一个版本'
    }
  ];

  return (
    <div style={{ 
      minHeight: 'calc(100vh - 64px)', 
      padding: '24px',
      background: 'var(--background-color)'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <Title level={1} style={{ color: 'var(--primary-color)' }}>
          关于 GreenMorph
        </Title>
        <Paragraph style={{ fontSize: '18px', color: 'var(--text-secondary)', maxWidth: '800px', margin: '0 auto' }}>
          我们致力于通过AI技术推动环保理念，让旧物改造变得简单有趣，
          为地球的可持续发展贡献一份力量。
        </Paragraph>
      </div>

      {/* 平台介绍 */}
      <Card style={{ marginBottom: '32px' }}>
        <Row gutter={[32, 32]} align="middle">
          <Col xs={24} lg={12}>
            <Title level={2}>我们的使命</Title>
            <Paragraph style={{ fontSize: '16px', lineHeight: '1.8' }}>
              GreenMorph 是一个基于AI技术的旧物回收设计智能助手平台。
              我们相信，每一个被丢弃的物品都有重新焕发生机的可能。
              通过智能分析和创意建议，我们帮助用户将旧物转化为有用的新物品，
              减少浪费，保护环境，创造更美好的生活。
            </Paragraph>
            <Space size="large" style={{ marginTop: '24px' }}>
              <Statistic 
                title="服务用户" 
                value="10000+" 
                prefix={<TeamOutlined />}
                valueStyle={{ color: 'var(--primary-color)' }}
              />
              <Statistic 
                title="改造作品" 
                value="50000+" 
                prefix={<BulbOutlined />}
                valueStyle={{ color: 'var(--success-color)' }}
              />
              <Statistic 
                title="环保贡献" 
                value="1000+" 
                prefix={<HeartOutlined />}
                valueStyle={{ color: 'var(--error-color)' }}
                suffix="kg"
              />
            </Space>
          </Col>
          <Col xs={24} lg={12}>
            <div style={{ 
              background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--success-color) 100%)',
              borderRadius: '12px',
              padding: '40px',
              color: 'white',
              textAlign: 'center'
            }}>
              <EnvironmentOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <Title level={3} style={{ color: 'white', marginBottom: '16px' }}>
                环保理念
              </Title>
              <Paragraph style={{ color: 'rgba(255,255,255,0.9)', fontSize: '16px' }}>
                每一个创意改造，都是对地球的一份关爱
              </Paragraph>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 核心功能 */}
      <Card title="核心功能" style={{ marginBottom: '32px' }}>
        <Row gutter={[24, 24]}>
          <Col xs={24} sm={12} lg={6}>
            <div style={{ textAlign: 'center' }}>
              <RobotOutlined style={{ fontSize: '48px', color: 'var(--primary-color)', marginBottom: '16px' }} />
              <Title level={4}>AI智能分析</Title>
              <Paragraph>
                基于先进的AI技术，智能分析旧物特征，
                提供个性化的改造建议
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <div style={{ textAlign: 'center' }}>
              <BulbOutlined style={{ fontSize: '48px', color: 'var(--success-color)', marginBottom: '16px' }} />
              <Title level={4}>创意灵感</Title>
              <Paragraph>
                丰富的创意库和教程，激发您的改造灵感，
                让创意变得触手可及
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <div style={{ textAlign: 'center' }}>
              <TeamOutlined style={{ fontSize: '48px', color: 'var(--warning-color)', marginBottom: '16px' }} />
              <Title level={4}>社区分享</Title>
              <Paragraph>
                与环保爱好者交流经验，分享改造作品，
                共同成长进步
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <div style={{ textAlign: 'center' }}>
              <TrophyOutlined style={{ fontSize: '48px', color: 'var(--error-color)', marginBottom: '16px' }} />
              <Title level={4}>成就系统</Title>
              <Paragraph>
                通过改造作品获得积分和徽章，
                让环保行动更有成就感
              </Paragraph>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 团队介绍 */}
      <Card title="我们的团队" style={{ marginBottom: '32px' }}>
        <Row gutter={[24, 24]}>
          {teamMembers.map((member, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <Card 
                hoverable
                style={{ textAlign: 'center', height: '100%' }}
                bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
              >
                <Avatar size={80} src={member.avatar} style={{ marginBottom: '16px' }} />
                <Title level={4} style={{ marginBottom: '8px' }}>{member.name}</Title>
                <Paragraph style={{ color: 'var(--primary-color)', fontWeight: 'bold', marginBottom: '8px' }}>
                  {member.role}
                </Paragraph>
                <Paragraph style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                  {member.description}
                </Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 发展历程 */}
      <Card title="发展历程" style={{ marginBottom: '32px' }}>
        <Timeline>
          {milestones.map((milestone, index) => (
            <Timeline.Item 
              key={index}
              dot={<RocketOutlined style={{ fontSize: '16px' }} />}
            >
              <Title level={4} style={{ marginBottom: '8px' }}>
                {milestone.title}
              </Title>
              <Paragraph style={{ color: 'var(--text-secondary)', marginBottom: '4px' }}>
                {milestone.description}
              </Paragraph>
              <div style={{ color: 'var(--text-tertiary)', fontSize: '14px' }}>
                {milestone.time}
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </Card>

      {/* 联系我们 */}
      <Card title="联系我们">
        <Row gutter={[32, 32]}>
          <Col xs={24} lg={12}>
            <Title level={3}>联系方式</Title>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <GlobalOutlined style={{ marginRight: '8px', color: 'var(--primary-color)' }} />
                <span>官方网站：www.greenmorph.com</span>
              </div>
              <div>
                <TeamOutlined style={{ marginRight: '8px', color: 'var(--success-color)' }} />
                <span>邮箱：contact@greenmorph.com</span>
              </div>
              <div>
                <SafetyOutlined style={{ marginRight: '8px', color: 'var(--warning-color)' }} />
                <span>客服热线：400-123-4567</span>
              </div>
            </Space>
          </Col>
          <Col xs={24} lg={12}>
            <Title level={3}>加入我们</Title>
            <Paragraph>
              如果您对环保事业充满热情，对技术创新有独到见解，
              欢迎加入我们的团队，一起为地球的可持续发展贡献力量。
            </Paragraph>
            <div style={{ 
              background: 'var(--success-light)', 
              border: '1px solid var(--success-color)', 
              borderRadius: '8px', 
              padding: '16px',
              marginTop: '16px'
            }}>
              <Paragraph style={{ margin: 0, color: 'var(--success-color)' }}>
                <HeartOutlined style={{ marginRight: '8px' }} />
                我们相信，每一个小小的改变，都能为世界带来美好的变化。
              </Paragraph>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default About;
