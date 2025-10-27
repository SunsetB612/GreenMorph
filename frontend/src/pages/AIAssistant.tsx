import React, { useState } from 'react';
import { 
  Card, 
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
  Alert,
  Steps,
  List,
  Tabs
} from 'antd';
import { 
  ToolOutlined,
  UploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  SafetyOutlined,
  BulbOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import { checkAndNotifyAchievements } from '../utils/achievementNotifier';
import { useAuthStore } from '../store/authStore';
const { Title, Paragraph, Text } = Typography;

const API_BASE_URL = import.meta.env.VITE_API_URL;

// 改造方案类型定义
interface RedesignStep {
  title: string;
  description: string;
  materials_needed: string[];
  tools_needed: string[];
  estimated_time: string;
  difficulty: string;
  safety_notes: string;
  image_prompt?: string;
}

interface RedesignPlan {
  title: string;
  description: string;
  steps: RedesignStep[];
  total_cost: string;
  sustainability_score: number;
  tips: string[];
  final_image?: string;
  step_images?: string[];
}

const AIAssistant: React.FC = () => {
  const [uploadedFile, setUploadedFile] = useState<UploadFile | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [redesignPlan, setRedesignPlan] = useState<RedesignPlan | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  // 图片上传处理
  const handleImageUpload: UploadProps['onChange'] = async (info) => {
    const { file } = info;
    
    if (file.status === 'uploading') {
      setAnalyzing(true);
      return;
    }
    
    if (file.status === 'done') {
      setUploadedFile(file);
      setAnalyzing(false);
      message.success('图片上传成功');
    } else if (file.status === 'error') {
      setAnalyzing(false);
      message.error('图片上传失败');
    }
  };

  // 自定义上传请求 - 图片分析
  const customUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    
    try {
      setAnalyzing(true);
      
      const formData = new FormData();
      formData.append('file', file);
      
      // 调用后端图片分析API
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/redesign/analyze/image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setAnalysisResult(result);
      onSuccess(result, file);
      message.success('图片分析完成！');
      
    } catch (error) {
      console.error('图片分析失败:', error);
      onError(error);
      message.error('图片分析失败，请重试');
    } finally {
      setAnalyzing(false);
    }
  };

  // 生成改造方案
  const handleGenerateRedesign = async () => {
    if (!analysisResult) {
      message.error('请先上传并分析图片');
      return;
    }

    try {
      setGenerating(true);
      
      // 准备请求数据
      const requestData = {
        input_image_id: parseInt(analysisResult.input_number),
        user_requirements: '请根据物品特征自主设计改造方案',
        target_style: 'modern',
        target_materials: analysisResult.materials || ['wood']
      };
      
      console.log('发送的请求数据:', requestData);
      console.log('analysisResult:', analysisResult);
      
      // 调用后端改造方案生成API
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/redesign/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API错误响应:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      
      const result = await response.json();
      
      // 映射后端字段到前端期望的字段
      const mappedResult = {
        title: result.title || '智能改造方案',
        description: result.description || '基于AI分析的个性化改造方案',
        steps: result.redesign_guide || [],
        total_cost: result.total_cost_estimate || '待评估',
        sustainability_score: result.sustainability_score || 7,
        tips: result.tips || [],
        final_image: result.final_image_url ? `${API_BASE_URL.replace('/api', '')}${result.final_image_url}` : undefined,
step_images: result.step_images ? result.step_images.map((url: string) => `${API_BASE_URL.replace('/api', '')}${url}`) : []
      };
      
      setRedesignPlan(mappedResult);
      message.success('改造方案生成完成！');

      const { user } = useAuthStore.getState();
    if (user?.id) {
      await checkAndNotifyAchievements(user.id);
    }
      
    } catch (error) {
      console.error('改造方案生成失败:', error);
      message.error('改造方案生成失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  // 删除上传的图片
  const handleRemoveImage = () => {
    setUploadedFile(null);
    setAnalysisResult(null);
    setRedesignPlan(null);
    setCurrentStep(0);
  };


  // 获取难度颜色
  const getDifficultyColor = (difficulty: string) => {
    const level = parseInt(difficulty.split('/')[0]);
    if (level <= 3) return 'green';
    if (level <= 6) return 'orange';
    return 'red';
  };

  // 优化材料清单 - 简单去重
  const optimizeMaterialsList = (materials: string[]) => {
    if (!materials || materials.length === 0) return [];
    
    // 简单去重，保持顺序
    return materials.filter((material, index, arr) => arr.indexOf(material) === index);
  };

  // 优化工具清单 - 简单去重
  const optimizeToolsList = (tools: string[]) => {
    if (!tools || tools.length === 0) return [];
    
    // 简单去重，保持顺序
    return tools.filter((tool, index, arr) => arr.indexOf(tool) === index);
  };

  return (
    <div style={{ 
      minHeight: 'calc(100vh - 64px)', 
      padding: '24px',
      background: 'var(--background-color)'
    }}>
      <div style={{ marginBottom: '16px' }}>
        <Title level={2} style={{ marginBottom: '0' }}>
          <ToolOutlined style={{ marginRight: '8px', color: 'var(--primary-color)' }} />
          智能改造助手
        </Title>
      </div>

      <Row gutter={[24, 24]}>
        {/* 左侧：上传和分析区域 */}
        <Col xs={24} lg={8}>
          <Card title="📸 上传旧物照片" style={{ marginBottom: '24px' }}>
            <Spin spinning={analyzing} tip="AI正在分析图片...">
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
                          {analysisResult.main_objects.map((obj: string) => (
                            <Tag key={obj} color="green">{obj}</Tag>
                          ))}
                        </Descriptions.Item>
                        <Descriptions.Item label="材质">
                          {analysisResult.materials.map((material: string) => (
                            <Tag key={material} color="blue">{material}</Tag>
                          ))}
                        </Descriptions.Item>
                        <Descriptions.Item label="物品状态">
                          <Tag color={analysisResult.condition === '良好' ? 'green' : 'orange'}>
                            {analysisResult.condition}
                          </Tag>
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

          {/* 生成按钮 */}
          {analysisResult && !redesignPlan && (
            <Card>
              <Button 
                type="primary" 
                size="large" 
                block 
                onClick={handleGenerateRedesign}
                loading={generating}
                icon={<ToolOutlined />}
              >
                {generating ? '正在生成改造方案...' : '生成改造方案'}
              </Button>
            </Card>
          )}
        </Col>

        {/* 右侧：改造方案展示 */}
        <Col xs={24} lg={16}>
          {!redesignPlan ? (
            <Card>
              <div style={{ 
                textAlign: 'center', 
                padding: '60px 20px',
                color: 'var(--text-tertiary)'
              }}>
                <ToolOutlined style={{ fontSize: '64px', marginBottom: '16px' }} />
                <Title level={3}>等待改造方案</Title>
                <Paragraph>
                  请先上传旧物照片，AI将为您生成详细的改造方案
                </Paragraph>
              </div>
            </Card>
          ) : (
            <div>
              {/* 改造方案概览 */}
              <Card title="🎨 改造方案概览" style={{ marginBottom: '24px' }}>
                <Row gutter={[16, 16]}>
                  {/* 左侧：最终效果图 */}
                  <Col span={16}>
                    
                    {redesignPlan?.tips && redesignPlan.tips.length > 0 && (
                      <div style={{ marginBottom: '16px' }}>
                        <Text strong>💡 改造小贴士：</Text>
                        <List
                          size="small"
                          dataSource={redesignPlan?.tips}
                          renderItem={(tip) => (
                            <List.Item>
                              <BulbOutlined style={{ color: 'var(--primary-color)', marginRight: '8px' }} />
                              {tip}
                            </List.Item>
                          )}
                        />
                      </div>
                    )}
                    
                    {/* 最终效果图 */}
                    {redesignPlan?.final_image && (
                      <div>
                        <Image
                          width="100%"
                          height={300}
                          src={redesignPlan.final_image}
                          style={{ objectFit: 'cover', borderRadius: '8px' }}
                          preview={{
                            mask: <EyeOutlined style={{ fontSize: '18px' }} />
                          }}
                        />
                      </div>
                    )}
                  </Col>
                  
                  {/* 右侧：成本评估和环保评分 */}
                  <Col span={8}>
                    <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                      <DollarOutlined style={{ fontSize: '24px', color: 'var(--primary-color)' }} />
                      <div style={{ marginTop: '8px' }}>
                        <Text strong>预估成本</Text>
                        <div style={{ fontSize: '18px', color: 'var(--primary-color)' }}>
                          {redesignPlan?.total_cost}
                        </div>
                      </div>
                    </div>
                    
                    <div style={{ textAlign: 'center' }}>
                      <CheckCircleOutlined style={{ fontSize: '24px', color: 'green' }} />
                      <div style={{ marginTop: '8px' }}>
                        <Text strong>可持续性评分</Text>
                        <div style={{ fontSize: '18px', color: 'green' }}>
                          {redesignPlan?.sustainability_score}/10
                        </div>
                      </div>
                    </div>
                  </Col>
                </Row>
              </Card>

              {/* 改造步骤 */}
              <Card title="📋 详细改造步骤">
                <Tabs 
                  defaultActiveKey="steps"
                  items={[
                    {
                      key: 'steps',
                      label: '改造步骤',
                      children: (
                        <Steps
                          direction="vertical"
                          current={currentStep}
                          onChange={setCurrentStep}
                          items={redesignPlan?.steps?.map((step, index) => ({
                            title: step.title,
                            description: (
                              <div>
                                <Paragraph>{step.description}</Paragraph>
                                <Space wrap>
                                  <Tag icon={<ClockCircleOutlined />} color="blue">
                                    {step.estimated_time}
                                  </Tag>
                                  <Tag color={getDifficultyColor(step.difficulty)}>
                                    难度: {step.difficulty}
                                  </Tag>
                                </Space>
                              </div>
                            ),
                            status: index <= currentStep ? 'finish' : 'wait'
                          }))}
                        />
                      )
                    },
                    {
                      key: 'materials',
                      label: '材料清单',
                      children: (
                        <div>
                          <Row gutter={[16, 16]}>
                            <Col span={12}>
                              <Card size="small" title="所需材料" style={{ height: '100%' }}>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                  {optimizeMaterialsList(redesignPlan?.steps?.flatMap(step => step.materials_needed || []) || [])
                                    .map((material: string, i: number) => (
                                      <Tag key={i} color="green" style={{ marginBottom: '4px' }}>
                                        {material}
                                      </Tag>
                                    ))}
                                </div>
                              </Card>
                            </Col>
                            <Col span={12}>
                              <Card size="small" title="所需工具" style={{ height: '100%' }}>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                  {optimizeToolsList(redesignPlan?.steps?.flatMap(step => step.tools_needed || []) || [])
                                    .map((tool: string, i: number) => (
                                      <Tag key={i} color="blue" style={{ marginBottom: '4px' }}>
                                        {tool}
                                      </Tag>
                                    ))}
                                </div>
                              </Card>
                            </Col>
                          </Row>
                        </div>
                      )
                    },
                    {
                      key: 'safety',
                      label: '安全注意事项',
                      children: (
                        <div>
                          {redesignPlan?.steps?.some(step => step.safety_notes) ? (
                            <Row gutter={[16, 16]}>
                              {redesignPlan.steps
                                .filter(step => step.safety_notes)
                                .map((step, index) => (
                                  <Col span={24} key={index}>
                                    <Card size="small" title={`${step.title} - 安全注意事项`}>
                                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                                        <SafetyOutlined style={{ color: 'red', fontSize: '18px', marginTop: '2px' }} />
                                        <div>
                                          <Text style={{ color: 'var(--text-primary)', fontSize: '14px' }}>
                                            {step.safety_notes}
                                          </Text>
                                        </div>
                                      </div>
                                    </Card>
                                  </Col>
                                ))}
                            </Row>
                          ) : (
                            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
                              <SafetyOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                              <div>暂无安全注意事项</div>
                            </div>
                          )}
                        </div>
                      )
                    },
                    {
                      key: 'images',
                      label: '步骤展示',
                      children: (
                        <Row gutter={[16, 16]}>
                          {redesignPlan?.step_images && redesignPlan.step_images.length > 0 ? (
                            redesignPlan.step_images.map((image, index) => (
                              <Col span={12} key={index}>
                                <Card size="small" title={`步骤 ${index + 1}`}>
                                  <Image
                                    width="100%"
                                    height={200}
                                    src={image}
                                    style={{ objectFit: 'cover', borderRadius: '8px' }}
                                    preview={{
                                      mask: <EyeOutlined style={{ fontSize: '18px' }} />
                                    }}
                                    fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                                    onError={(e) => {
                                      console.error('步骤图片加载失败:', e);
                                      console.log('步骤图片URL:', image);
                                    }}
                                  />
                                </Card>
                              </Col>
                            ))
                          ) : (
                            <Col span={24}>
                              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
                                <Text>暂无步骤图片</Text>
                              </div>
                            </Col>
                          )}
                        </Row>
                      )
                    }
                  ]}
                />
              </Card>
            </div>
          )}
        </Col>
      </Row>

    </div>
  );
};

export default AIAssistant;