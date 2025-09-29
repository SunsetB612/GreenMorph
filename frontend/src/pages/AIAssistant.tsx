import React, { useState } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Upload, 
  message,
  Row,
  Col,
  Tag
} from 'antd';
import { 
  SendOutlined, 
  CameraOutlined, 
  RobotOutlined 
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const AIAssistant: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Array<{type: 'user' | 'ai', content: string}>>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    const userMessage = { type: 'user' as const, content: inputValue };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    // 模拟AI回复
    setTimeout(() => {
      const aiMessage = { 
        type: 'ai' as const, 
        content: '这是一个模拟的AI回复。在实际应用中，这里会调用您的后端API来获取AI助手的真实回复。' 
      };
      setMessages(prev => [...prev, aiMessage]);
      setLoading(false);
    }, 1000);
  };

  const handleImageUpload = (info: any) => {
    if (info.file.status === 'done') {
      message.success('图片上传成功');
    } else if (info.file.status === 'error') {
      message.error('图片上传失败');
    }
  };

  return (
    <div style={{ 
      minHeight: 'calc(100vh - 64px)', 
      padding: '24px',
      background: 'var(--background-color)'
    }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <RobotOutlined style={{ marginRight: '8px', color: 'var(--primary-color)' }} />
          AI智能助手
        </Title>
        <Paragraph>
          上传您的旧物照片或描述，AI将为您提供创意改造建议
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card title="对话区域" style={{ height: '500px' }}>
            <div style={{ 
              height: '350px', 
              overflowY: 'auto', 
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '16px',
              background: 'var(--card-background)'
            }}>
              {messages.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  color: 'var(--text-tertiary)',
                  marginTop: '100px' 
                }}>
                  <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                  <p>开始与AI助手对话吧！</p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div key={index} style={{ 
                    marginBottom: '16px',
                    textAlign: msg.type === 'user' ? 'right' : 'left'
                  }}>
                    <Tag color={msg.type === 'user' ? 'blue' : 'green'}>
                      {msg.type === 'user' ? '您' : 'AI助手'}
                    </Tag>
                    <div style={{
                      background: msg.type === 'user' ? 'var(--primary-color)' : 'var(--card-background)',
                      color: msg.type === 'user' ? 'white' : 'black',
                      padding: '8px 12px',
                      borderRadius: '12px',
                      display: 'inline-block',
                      marginTop: '4px',
                      maxWidth: '80%'
                    }}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div style={{ textAlign: 'left' }}>
                  <Tag color="green">AI助手</Tag>
                  <div style={{
                    background: 'var(--card-background)',
                    padding: '8px 12px',
                    borderRadius: '12px',
                    display: 'inline-block',
                    marginTop: '4px'
                  }}>
                    正在思考中...
                  </div>
                </div>
              )}
            </div>

            <Space.Compact style={{ width: '100%' }}>
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="描述您的旧物或输入问题..."
                autoSize={{ minRows: 2, maxRows: 4 }}
                onPressEnter={(e) => {
                  if (e.shiftKey) return;
                  e.preventDefault();
                  handleSend();
                }}
              />
              <Button 
                type="primary" 
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={loading}
                disabled={!inputValue.trim()}
              >
                发送
              </Button>
            </Space.Compact>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="上传图片" style={{ marginBottom: '24px' }}>
            <Upload
              name="image"
              listType="picture-card"
              showUploadList={false}
              onChange={handleImageUpload}
              beforeUpload={() => false}
            >
              <div>
                <CameraOutlined style={{ fontSize: '24px' }} />
                <div style={{ marginTop: '8px' }}>上传照片</div>
              </div>
            </Upload>
            <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--text-tertiary)' }}>
              支持 JPG、PNG 格式，最大 5MB
            </div>
          </Card>

          <Card title="快速开始">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                block 
                onClick={() => setInputValue('我有一个旧牛仔裤，能改造成什么？')}
              >
                旧衣物改造
              </Button>
              <Button 
                block 
                onClick={() => setInputValue('空瓶子有什么创意用途？')}
              >
                瓶子再利用
              </Button>
              <Button 
                block 
                onClick={() => setInputValue('纸箱可以做什么手工？')}
              >
                纸箱手工
              </Button>
              <Button 
                block 
                onClick={() => setInputValue('废旧电子产品如何处理？')}
              >
                电子废物处理
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AIAssistant;
