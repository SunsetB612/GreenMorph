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
  Tag,
  Spin,
  Image,
  Descriptions,
  Alert
} from 'antd';
import { 
  SendOutlined, 
  RobotOutlined,
  UploadOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

// 图片分析结果类型定义
interface ImageAnalysisResult {
  main_objects: string[];
  materials: string[];
  colors: string[];
  condition: string;
  features: string[];
  confidence: number;
  appearance?: string;
  structure?: string;
  status?: string;
  uploaded_file?: string;
  file_path?: string;
  input_number?: number;
}

const AIAssistant: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Array<{type: 'user' | 'ai', content: string, imageAnalysis?: ImageAnalysisResult}>>([]);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<UploadFile | null>(null);
  const [imageAnalyzing, setImageAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<ImageAnalysisResult | null>(null);

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

  // 图片上传处理
  const handleImageUpload: UploadProps['onChange'] = async (info) => {
    const { file } = info;
    
    if (file.status === 'uploading') {
      setImageAnalyzing(true);
      return;
    }
    
    if (file.status === 'done') {
      setUploadedFile(file);
      setImageAnalyzing(false);
      message.success('图片上传成功');
    } else if (file.status === 'error') {
      setImageAnalyzing(false);
      message.error('图片上传失败');
    }
  };

  // 自定义上传请求
  const customUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    
    try {
      setImageAnalyzing(true);
      
      const formData = new FormData();
      formData.append('file', file);
      
      // 调用后端API
      const response = await fetch('http://localhost:8000/api/redesign/analyze/image', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: ImageAnalysisResult = await response.json();
      
      // 设置分析结果
      setAnalysisResult(result);
      
      // 添加到消息列表
      const analysisMessage = {
        type: 'ai' as const,
        content: `我分析了您上传的图片，识别出这是：${result.main_objects.join('、')}。状态：${result.condition}，置信度：${(result.confidence * 100).toFixed(1)}%`,
        imageAnalysis: result
      };
      
      setMessages(prev => [...prev, analysisMessage]);
      
      onSuccess(result, file);
      message.success('图片分析完成！');
      
    } catch (error) {
      console.error('图片分析失败:', error);
      onError(error);
      message.error('图片分析失败，请重试');
    } finally {
      setImageAnalyzing(false);
    }
  };

  // 删除上传的图片
  const handleRemoveImage = () => {
    setUploadedFile(null);
    setAnalysisResult(null);
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
                      color: msg.type === 'user' ? 'white' : 'var(--text-color)',
                      padding: '12px',
                      borderRadius: '12px',
                      display: 'inline-block',
                      marginTop: '4px',
                      maxWidth: '80%',
                      boxShadow: msg.type === 'ai' ? 'var(--shadow)' : 'none'
                    }}>
                      <div>{msg.content}</div>
                      
                      {/* 显示图片分析详细结果 */}
                      {msg.imageAnalysis && (
                        <div style={{ marginTop: '12px', fontSize: '12px' }}>
                          <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>📊 详细分析结果：</div>
                          
                          {msg.imageAnalysis.appearance && (
                            <div style={{ marginBottom: '6px' }}>
                              <strong>外观描述：</strong> {msg.imageAnalysis.appearance}
                            </div>
                          )}
                          
                          {msg.imageAnalysis.structure && (
                            <div style={{ marginBottom: '6px' }}>
                              <strong>结构分析：</strong> {msg.imageAnalysis.structure}
                            </div>
                          )}
                          
                          {msg.imageAnalysis.status && (
                            <div style={{ marginBottom: '6px' }}>
                              <strong>状态评估：</strong> {msg.imageAnalysis.status}
                            </div>
                          )}
                          
                          <div style={{ marginTop: '8px', padding: '8px', background: 'rgba(82, 196, 26, 0.1)', borderRadius: '6px' }}>
                            <div>💡 <strong>改造建议：</strong></div>
                            <div style={{ marginTop: '4px' }}>
                              基于识别结果，这个{msg.imageAnalysis.main_objects.join('、')}
                              可以进行多种创意改造。您可以继续询问具体的改造方案！
                            </div>
                          </div>
                        </div>
                      )}
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
          <Card title="图片分析" style={{ marginBottom: '24px' }}>
            <Spin spinning={imageAnalyzing} tip="AI正在分析图片...">
              {!uploadedFile ? (
                <Upload
                  name="file"
                  listType="picture-card"
                  showUploadList={false}
                  onChange={handleImageUpload}
                  customRequest={customUpload}
                  accept="image/*"
                  maxCount={1}
                >
                  <div>
                    <UploadOutlined style={{ fontSize: '24px', color: 'var(--primary-color)' }} />
                    <div style={{ marginTop: '8px' }}>上传图片</div>
                  </div>
                </Upload>
              ) : (
                <div>
                  <div style={{ position: 'relative', marginBottom: '16px' }}>
                    <Image
                      width="100%"
                      height={200}
                      src={uploadedFile.thumbUrl || URL.createObjectURL(uploadedFile.originFileObj as File)}
                      style={{ objectFit: 'cover', borderRadius: '8px' }}
                      preview={{
                        mask: <EyeOutlined style={{ fontSize: '18px' }} />
                      }}
                    />
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={handleRemoveImage}
                      style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        background: 'rgba(0,0,0,0.5)',
                        color: 'white'
                      }}
                    />
                  </div>
                  
                  {analysisResult && (
                    <div>
                      <Alert
                        message="分析完成"
                        description={`识别置信度: ${(analysisResult.confidence * 100).toFixed(1)}%`}
                        type="success"
                        showIcon
                        style={{ marginBottom: '16px' }}
                      />
                      
                      <Descriptions size="small" column={1} bordered>
                        <Descriptions.Item label="识别物体">
                          {analysisResult.main_objects.map(obj => (
                            <Tag key={obj} color="green">{obj}</Tag>
                          ))}
                        </Descriptions.Item>
                        <Descriptions.Item label="材质">
                          {analysisResult.materials.map(material => (
                            <Tag key={material} color="blue">{material}</Tag>
                          ))}
                        </Descriptions.Item>
                        <Descriptions.Item label="主要颜色">
                          {analysisResult.colors.map(color => (
                            <Tag key={color} color="orange">{color}</Tag>
                          ))}
                        </Descriptions.Item>
                        <Descriptions.Item label="物品状态">
                          <Tag color={analysisResult.condition === '良好' ? 'green' : 'orange'}>
                            {analysisResult.condition}
                          </Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="关键特征">
                          <div style={{ fontSize: '12px' }}>
                            {analysisResult.features.join('、')}
                          </div>
                        </Descriptions.Item>
                      </Descriptions>
                    </div>
                  )}
                </div>
              )}
            </Spin>
            
            <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              支持 JPG、PNG、WEBP 格式，最大 10MB
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
