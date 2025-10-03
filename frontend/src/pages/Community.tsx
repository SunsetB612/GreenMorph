import React, { useState, useEffect } from 'react';

import {
  Card, Input, Button, Typography, Space, Tag, Avatar, Row, Col, Tabs, message,Upload
} from 'antd';
import { Pagination,Modal, Form} from 'antd';
const { TextArea } = Input;

import {
  SearchOutlined, PlusOutlined, HeartOutlined, MessageOutlined, ShareAltOutlined, FireOutlined, ClockCircleOutlined,UploadOutlined
} from '@ant-design/icons';
import { EditOutlined } from '@ant-design/icons';
// 添加删除相关状态
import { DeleteOutlined, ExclamationCircleFilled } from '@ant-design/icons';

const { Title, Paragraph } = Typography;
const { TabPane } = Tabs;
const API_BASE_URL = 'http://localhost:8000';
interface PostType {
  id: number;
  user_id: number;
  title: string;
  content: string;
  likes_count: number;
  comments_count: number;
  created_at: string;
  updated_at: string;
  images?: string[]; // 添加图片URL数组
}

const Community: React.FC = () => {
  const [searchValue, setSearchValue] = useState('');
  const [posts, setPosts] = useState<PostType[]>([]);
  const [category, setCategory] = useState('popular'); //popular / latest / following
  const [page, setPage] = useState(1);
  const size = 10;
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0); // 后端返回总数
  // 在组件内部添加发布相关的状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [form] = Form.useForm();

const fetchPosts = async () => {
  setLoading(true);
  try {
    const url =  `${API_BASE_URL}/api/community/posts?category=${category}&page=${page}&size=${size}`;
    const res = await fetch(url);
    const data = await res.json();


    setPosts(data.items || []);
    setTotal(data.total || 0);
  } catch (error) {
    console.error('请求失败:', error);
    message.error('帖子显示失败');
  } finally {
    setLoading(false);
  }
};

useEffect(() => {
  fetchPosts();
}, [category, page]);



// 在文件顶部定义接口
interface UploadFile {
  uid: string;
  name: string;
  status?: string;
  originFileObj?: File;
  url?: string;
}

interface CreatePostFormValues {
  title: string;
  content: string;
  images?: UploadFile[];
}

// 创建帖子
const handleCreatePost = async (values: CreatePostFormValues) => {
  setCreateLoading(true);
  console.log('提交的表单值:', values);

  try {
    // 1. 先创建帖子
    const postResponse = await fetch(`${API_BASE_URL}/api/community/posts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: values.title,
        content: values.content
      }),
    });

    if (!postResponse.ok) {
      throw new Error('创建帖子失败');
    }

    const newPost = await postResponse.json();
    console.log('创建的帖子:', newPost);
    const postId = newPost.id;

    // 2. 上传图片（如果有）
    if (values.images && values.images.length > 0) {
      console.log('开始上传图片，数量:', values.images.length);

      const uploadPromises = values.images.map(async (fileObj) => {
        // 直接使用 originFileObj，它的类型就是 File | undefined
        const file = fileObj.originFileObj;

        if (!file) {
          console.warn('文件对象不存在，跳过');
          return null;
        }

        const formData = new FormData();
        formData.append('file', file);

        const uploadResponse = await fetch(`${API_BASE_URL}/api/community/posts/${postId}/images`, {
          method: 'POST',
          body: formData,
        });

        if (!uploadResponse.ok) {
          const errorText = await uploadResponse.text();
          console.error('图片上传失败:', errorText);
        }

        return uploadResponse;
      });

      await Promise.allSettled(uploadPromises);
      console.log('所有图片上传完成');
    }

    message.success('发布成功！');
    setCreateModalVisible(false);
    form.resetFields();

    // 重置到第一页并刷新
    setPage(1);
    await fetchPosts();

  } catch (error) {
    console.error('发布失败详情:', error);
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    message.error('发布失败：' + errorMessage);
  } finally {
    setCreateLoading(false);
  }
};
const [previewVisible, setPreviewVisible] = useState(false);
const [previewImage, setPreviewImage] = useState<string | null>(null);
const [previewTitle, setPreviewTitle] = useState<string>('');
const handlePreview = (imgUrl: string, title: string) => {
  setPreviewImage(`${API_BASE_URL}/${imgUrl}`);
  setPreviewTitle(title);
  setPreviewVisible(true);
};//放大图片


  const [currentUser, setCurrentUser] = useState<{ id: number } | null>({ id: 1 }); // 暂时用假数据
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingPost, setEditingPost] = useState<PostType | null>(null);
  const [newImages, setNewImages] = useState<File[]>([]); // 新上传的图片
  const [editForm] = Form.useForm();
// 获取帖子详情用于编辑
const fetchPostDetail = async (postId: number) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${postId}`);
    const data = await response.json();
    setEditingPost(data);

    // 填充表单
    editForm.setFieldsValue({
      title: data.title,
      content: data.content
    });

    setEditModalVisible(true);
  } catch (error) {
    message.error('获取帖子详情失败');
  }
};

// 编辑按钮点击事件
const handleEdit = (post: PostType) => {
  // TODO: 检查当前用户是否是帖子作者
  fetchPostDetail(post.id);
};

// 编辑帖子函数
const handleUpdatePost = async (values: CreatePostFormValues) => {
  if (!editingPost) return;

  try {
    // 1. 更新帖子文本内容
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${editingPost.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });

    if (!response.ok) throw new Error('更新失败');

    // 2. 上传新图片
    if (newImages.length > 0) {
      for (const file of newImages) {
        const formData = new FormData();
        formData.append('file', file);
        await fetch(`${API_BASE_URL}/api/community/posts/${editingPost.id}/images`, {
          method: 'POST',
          body: formData,
        });
      }
    }

    message.success('更新成功！');
    setEditModalVisible(false);
    setEditingPost(null);
    setNewImages([]);
    editForm.resetFields();
    fetchPosts();
  } catch (error) {
    message.error('更新失败');
  }
};

// 处理新图片上传
const handleNewImageUpload = (file: File) => {
  setNewImages(prev => [...prev, file]);
  return false; // 阻止自动上传
};



const { confirm } = Modal;

// 删除帖子函数
const handleDelete = (post: PostType) => {
  if (!currentUser) {
    message.warning('请先登录');
    return;
  }

  if (post.user_id !== currentUser.id) {
    message.error('无权删除他人帖子');
    return;
  }

  confirm({
    title: '确认删除',
    icon: <ExclamationCircleFilled />,
    content: '确定要删除这个帖子吗？此操作不可恢复。',
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      deletePost(post.id);
    },
  });
};

// 调用删除接口
const deletePost = async (postId: number) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${postId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('删除失败');
    }

    message.success('帖子删除成功！');
    fetchPosts(); // 刷新列表
  } catch (error) {
    console.error('删除失败:', error);
    message.error('删除失败');
  }
};



  const handleLike = (postId: number) => console.log('点赞帖子:', postId);
  const handleComment = (postId: number) => console.log('评论帖子:', postId);
  const handleShare = (postId: number) => console.log('分享帖子:', postId);

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', padding: '24px', background: 'var(--background-color)' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <FireOutlined style={{ marginRight: '8px', color: 'var(--error-color)' }} />
          社区分享
        </Title>
        <Paragraph>与环保爱好者交流创意，分享您的旧物改造经验</Paragraph>
      </div>

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
  onClick={() => setCreateModalVisible(true)}
>
  发布创意
</Button>
          </Col>
        </Row>
      </Card>
  {/* 发布弹窗 */}
<Modal
  title="发布新创意"
  open={createModalVisible}
  onCancel={() => {
    setCreateModalVisible(false);
    form.resetFields();
  }}
  footer={null}
  destroyOnClose
  confirmLoading={createLoading}
>
  <Form form={form} layout="vertical" onFinish={handleCreatePost}>
    <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
      <Input placeholder="请输入创意标题" />
    </Form.Item>
    <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入内容' }]}>
      <TextArea
        rows={6}
        placeholder="分享您的创意想法、改造经验或环保心得..."
        showCount
        maxLength={1000}
      />
    </Form.Item>
    <Form.Item
  name="images"
  label="上传图片"
  valuePropName="fileList"
  getValueFromEvent={(e) => {
    if (Array.isArray(e)) {
      return e;
    }
    return e?.fileList;
  }}
>
  <Upload
    multiple
    listType="picture"
    beforeUpload={() => false} // 阻止自动上传
    accept="image/jpeg,image/png,image/webp"
    maxCount={9}
  >
    <Button icon={<UploadOutlined />}>选择图片（最多9张）</Button>
  </Upload>
</Form.Item>
    <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
      <Space>
        <Button onClick={() => setCreateModalVisible(false)}>取消</Button>
        <Button type="primary" htmlType="submit">发布</Button>
      </Space>
    </Form.Item>
  </Form>
</Modal>
      <Modal
  title="编辑帖子"
  open={editModalVisible}
  onCancel={() => {
    setEditModalVisible(false);
    setEditingPost(null);
    setNewImages([]);
    editForm.resetFields();
  }}
  footer={null}
  width={700}
  destroyOnClose
>
  <Form form={editForm} layout="vertical" onFinish={handleUpdatePost}>
    <Form.Item name="title" label="标题" rules={[{ required: true }]}>
      <Input placeholder="请输入帖子标题" />
    </Form.Item>

    <Form.Item name="content" label="内容" rules={[{ required: true }]}>
      <TextArea rows={6} placeholder="请输入帖子内容" showCount maxLength={1000} />
    </Form.Item>

    {/* 显示现有图片（只读，不能删除） */}
    {editingPost?.images && editingPost.images.length > 0 && (
      <Form.Item label="现有图片">
        <div style={{ fontSize: '12px', color: '#999', marginBottom: 8 }}>
          当前图片（暂不支持删除）
        </div>
        <Row gutter={[8, 8]}>
          {editingPost.images.map((imgUrl, index) => (
            <Col key={index} xs={8}>
              <img
                src={`${API_BASE_URL}/${imgUrl}`}
                alt={`现有图片 ${index + 1}`}
                style={{
                  width: '100%',
                  height: '100px',
                  objectFit: 'cover',
                  borderRadius: '8px'
                }}
              />
            </Col>
          ))}
        </Row>
      </Form.Item>
    )}

    {/* 上传新图片 */}
    <Form.Item label="添加新图片">
      <Upload
        multiple
        listType="picture"
        beforeUpload={(file) => {
          setNewImages(prev => [...prev, file]);
          return false; // 阻止自动上传
        }}
        accept="image/jpeg,image/png,image/webp"
        showUploadList={false}
      >
        <Button icon={<UploadOutlined />}>选择新图片</Button>
      </Upload>
      {newImages.length > 0 && (
        <div style={{ marginTop: 8, padding: '8px 12px', background: '#f5f5f5', borderRadius: '4px' }}>
          <div>📸 已选择 {newImages.length} 张新图片：</div>
          {newImages.map((file, index) => (
            <div key={index} style={{ fontSize: '12px', marginTop: 4 }}>
              • {file.name}
            </div>
          ))}
        </div>
      )}
    </Form.Item>

    <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
      <Space>
        <Button onClick={() => setEditModalVisible(false)}>取消</Button>
        <Button type="primary" htmlType="submit">更新帖子</Button>
      </Space>
    </Form.Item>
  </Form>
</Modal>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Tabs activeKey={category} onChange={(key) => { setCategory(key); setPage(1); }}>
            {['popular', 'latest', 'following'].map(tabKey => (
              <TabPane
  tab={tabKey === 'popular' ? '热门' : tabKey === 'latest' ? '最新' : '关注'}
  key={tabKey}
>
  {loading ? (
    <div>加载中...</div>
  ) : tabKey === 'following' ? (
    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)' }}>
      关注的内容将在这里显示
    </div>
  ) : (
    <>
      {posts.map(post => (
        <Card key={post.id} style={{ marginBottom: '16px' }} hoverable>
          <div style={{ marginBottom: '12px' }}>
            <Space>
              <Avatar src={`https://api.dicebear.com/7.x/miniavs/svg?seed=${post.user_id}`} />
              <div>
                <div style={{ fontWeight: 'bold' }}>用户 {post.user_id}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
                  <ClockCircleOutlined /> {new Date(post.created_at).toLocaleString()}
                </div>
              </div>
            </Space>
          </div>

          <Title level={4} style={{ marginBottom: '8px' }}>{post.title}</Title>
          <Paragraph style={{ marginBottom: '12px' }}>{post.content}</Paragraph>
          {/* 显示图片 */}
{post.images?.map((imgUrl, index) => (
  <Col key={index} xs={8}>
    <img
      src={`${API_BASE_URL}/${imgUrl}`}
      alt={`帖子图片 ${index + 1}`}
      style={{
        width: '100%',
        height: '100px',
        objectFit: 'cover',
        borderRadius: '8px',
        cursor: 'pointer'
      }}
      onClick={() => handlePreview(imgUrl, post.title)}
    />
  </Col>
))}
<Modal
  visible={previewVisible}
  title={previewTitle}
  footer={null}
  onCancel={() => setPreviewVisible(false)}
>
  {previewImage && (
    <img
      alt={previewTitle}
      style={{ width: '100%' }}
      src={previewImage}
    />
  )}
</Modal>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            borderTop: '1px solid var(--border-color)',
            paddingTop: '12px'
          }}>
            <Button type="text" icon={<HeartOutlined/>} onClick={() => handleLike(post.id)}>
              {post.likes_count}
            </Button>
            <Button type="text" icon={<MessageOutlined/>} onClick={() => handleComment(post.id)}>
              {post.comments_count}
            </Button>

{/* 只有帖子作者才能看到编辑和删除按钮 */}
  {currentUser && post.user_id === currentUser.id && (
    <>
      <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(post)}>
        编辑
      </Button>
      <Button
        type="text"
        danger
        icon={<DeleteOutlined />}
        onClick={() => handleDelete(post)}
      >
        删除
      </Button>
    </>
  )}
            <Button type="text" icon={<ShareAltOutlined/>} onClick={() => handleShare(post.id)}>分享</Button>
          </div>
        </Card>
      ))}

      {/* 分页器 */}
      <Pagination
          current={page}
          pageSize={size}
          total={total}
          onChange={(p) => setPage(p)}
          style={{marginTop: '16px', textAlign: 'center'}}
      />
    </>
  )}
              </TabPane>

            ))}
          </Tabs>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="热门话题" style={{marginBottom: '24px'}}>
            <Space direction="vertical" style={{width: '100%'}}>
              {['#旧物改造', '#环保生活', '#创意手工', '#收纳整理', '#DIY教程'].map(tag => <Tag key={tag}>{tag}</Tag>)}
            </Space>
          </Card>

          <Card title="推荐用户">
            <Space direction="vertical" style={{ width: '100%' }}>
              {[4,5,6].map(id => (
                <div key={id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Space>
                    <Avatar size="small" src={`https://api.dicebear.com/7.x/miniavs/svg?seed=${id}`} />
                    <span>用户{id}</span>
                  </Space>
                  <Button size="small">关注</Button>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Community;
