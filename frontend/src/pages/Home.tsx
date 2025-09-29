import React from 'react';
import { Card, Row, Col, Button, Typography, Space } from 'antd';
import { 
  RobotOutlined, 
  TeamOutlined, 
  BulbOutlined, 
  EnvironmentOutlined 
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const Home: React.FC = () => {
  return (
    <div style={{ 
      minHeight: 'calc(100vh - 64px)', 
      padding: '24px',
      background: 'var(--background-color)'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <Title level={1} style={{ color: 'var(--primary-color)' }}>
          欢迎使用 GreenMorph
        </Title>
        <Paragraph style={{ fontSize: '18px', color: 'var(--text-secondary)' }}>
          智能旧物回收设计助手，让环保变得简单有趣
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            hoverable
            style={{ height: '200px', textAlign: 'center' }}
            bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
          >
            <RobotOutlined style={{ fontSize: '48px', color: 'var(--primary-color)', marginBottom: '16px' }} />
            <Title level={3}>AI助手</Title>
            <Paragraph>智能分析您的旧物，提供创意改造建议</Paragraph>
            <Button type="primary" size="large" style={{ marginTop: '16px' }}>
              开始体验
            </Button>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card 
            hoverable
            style={{ height: '200px', textAlign: 'center' }}
            bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
          >
            <TeamOutlined style={{ fontSize: '48px', color: 'var(--success-color)', marginBottom: '16px' }} />
            <Title level={3}>社区分享</Title>
            <Paragraph>与环保爱好者交流创意，分享改造经验</Paragraph>
            <Button type="primary" size="large" style={{ marginTop: '16px' }}>
              加入社区
            </Button>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card 
            hoverable
            style={{ height: '200px', textAlign: 'center' }}
            bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
          >
            <BulbOutlined style={{ fontSize: '48px', color: 'var(--warning-color)', marginBottom: '16px' }} />
            <Title level={3}>创意灵感</Title>
            <Paragraph>发现更多旧物改造的创意想法</Paragraph>
            <Button type="primary" size="large" style={{ marginTop: '16px' }}>
              探索灵感
            </Button>
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: '40px' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: '24px' }}>
          平台特色
        </Title>
        <Row gutter={[24, 24]}>
          <Col xs={24} md={12}>
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <EnvironmentOutlined style={{ fontSize: '32px', color: 'var(--primary-color)' }} />
                <Title level={4}>环保理念</Title>
                <Paragraph>
                  我们致力于推广环保理念，通过智能技术帮助用户更好地利用旧物，
                  减少浪费，保护环境。
                </Paragraph>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <RobotOutlined style={{ fontSize: '32px', color: 'var(--success-color)' }} />
                <Title level={4}>AI驱动</Title>
                <Paragraph>
                  基于先进的AI技术，为您的旧物提供个性化的改造建议，
                  让创意设计变得简单易行。
                </Paragraph>
              </Space>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default Home;
