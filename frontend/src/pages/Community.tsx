import React, { useState, useEffect } from 'react';
import { Image } from 'antd';
import {
  HeartFilled  // 添加这个
} from '@ant-design/icons';
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
import { useAuthStore } from '../store/authStore';
// 删除假的currentUser状态，使用真实的认证store

interface PostType {
  id: number;
  user_id: number;
  title: string;
  content: string;
  likes_count: number;
  comments_count: number;
  created_at: string;
  updated_at: string;
  images?: string[]; // 保持兼容性
  images_with_id?: Array<{ id: number; file_path: string }>; // 新增包含ID的图片数据
  is_liked?: boolean; // 添加点赞状态字段
  user_name?: string;
}

const Community: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
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
    const url = `${API_BASE_URL}/api/community/posts?category=${category}&page=${page}&size=${size}`;
    const res = await fetch(url);
    const data = await res.json();

    // 为每个帖子获取评论数和点赞状态
    const postsWithRealData = await Promise.all(
      (data.items || []).map(async (post: PostType) => {
        try {
          // 获取评论数
          const commentRes = await fetch(
            `${API_BASE_URL}/api/community/posts/${post.id}/comments?page=1&size=1`
          );
          const commentData = await commentRes.json();

          // 获取点赞状态 - 添加认证头
          const token = localStorage.getItem('auth_token');
          const likeStatusRes = await fetch(
            `${API_BASE_URL}/api/community/posts/${post.id}/like/status`,
            {
              headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            }
          );

          let is_liked = false;
          if (likeStatusRes.ok) {
            const likeStatusData = await likeStatusRes.json();
            is_liked = likeStatusData.is_liked;
          }

          return {
            ...post,
            comments_count: commentData.total || 0,
            is_liked: is_liked
          };
        } catch (error) {
          console.error(`获取帖子 ${post.id} 数据失败:`, error);
          return { ...post, is_liked: false };
        }
      })
    );

    setPosts(postsWithRealData);
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
// 在创建帖子的 handleCreatePost 函数中修改图片处理部分
const handleCreatePost = async (values: CreatePostFormValues) => {
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再发布帖子');
    return;
  }

  setCreateLoading(true);

  try {
    const token = localStorage.getItem('auth_token');

    // 创建帖子请求
    const postResponse = await fetch(`${API_BASE_URL}/api/community/posts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title: values.title,
        content: values.content
      }),
    });

    if (!postResponse.ok) {
      throw new Error('创建帖子失败');
    }

    const newPost = await postResponse.json();
    const postId = newPost.id;

    // 2. 上传图片（如果有）
    if (values.images && values.images.length > 0) {
      console.log('开始上传图片，数量:', values.images.length);

      const uploadPromises = values.images.map(async (fileObj) => {
        const file = fileObj.originFileObj;

        if (!file) {
          console.warn('文件对象不存在，跳过');
          return null;
        }

        const formData = new FormData();
        formData.append('file', file);

        const uploadResponse = await fetch(`${API_BASE_URL}/api/community/posts/${postId}/images`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
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

// 添加编辑时删除图片的函数
// 修改编辑时删除图片的函数
const handleDeletePostImageInEdit = async (postId: number, imageId: number, imageIndex: number) => {
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再操作');
    return;
  }

  confirm({
    title: '确认删除图片',
    icon: <ExclamationCircleFilled />,
    content: '确定要删除这张图片吗？此操作不可恢复。',
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          message.error('认证token不存在，请重新登录');
          return;
        }

        // 调用删除图片接口
        const response = await fetch(
          `${API_BASE_URL}/api/community/posts/${postId}/images/${imageId}`,
          {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('UNAUTHORIZED');
          }
          throw new Error('删除失败');
        }

        // 更新编辑中的帖子状态
        if (editingPost) {
          setEditingPost({
            ...editingPost,
            images: editingPost.images?.filter((_, i) => i !== imageIndex),
            images_with_id: editingPost.images_with_id?.filter((_, i) => i !== imageIndex)
          });
        }

        message.success('图片删除成功！');

      } catch (error) {
        if (error instanceof Error && error.message === 'UNAUTHORIZED') {
          message.error('登录已过期，请重新登录后继续操作');
        } else {
          message.error('删除图片失败，请稍后重试');
        }
        console.error('删除图片失败:', error);

        // 如果删除失败，重新获取帖子详情
        if (editingPost) {
          fetchPostDetail(editingPost.id);
        }
      }
    },
  });
};


  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingPost, setEditingPost] = useState<PostType | null>(null);
  const [newImages, setNewImages] = useState<File[]>([]); // 新上传的图片
  const [editForm] = Form.useForm();
// 修改获取帖子详情的函数
// 修改获取帖子详情的函数
const fetchPostDetail = async (postId: number) => {
  try {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${postId}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    const data = await response.json();

    // 处理新的数据结构
    const postData = {
      ...data,
      images: data.images || [],
      images_with_id: data.images || [] // 如果后端返回的是数组对象，直接使用
    };

    setEditingPost(postData);

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
  // 添加认证检查
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再编辑帖子');
    return;
  }

  // 添加作者权限检查
  if (post.user_id !== user.id) {
    message.error('无权编辑他人帖子');
    return;
  }



  fetchPostDetail(post.id);
};

const handleUpdatePost = async (values: CreatePostFormValues) => {
  if (!editingPost) return;

  // 双重权限检查
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再编辑帖子');
    return;
  }

  if (editingPost.user_id !== user.id) {
    message.error('无权编辑他人帖子');
    return;
  }

  try {
    // 获取token
    const token = localStorage.getItem('auth_token');

    // 1. 更新帖子文本内容 - 添加认证头
    const response = await fetch(`${API_BASE_URL}/api/community/posts/${editingPost.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`  // 添加认证头
      },
      body: JSON.stringify(values),
    });

    if (!response.ok) {
      // 如果是401错误，给出友好提示
      if (response.status === 401) {
        throw new Error('UNAUTHORIZED');
      }
      throw new Error('更新失败');
    }

    // 2. 上传新图片 - 添加认证头
    if (newImages.length > 0) {
      for (const file of newImages) {
        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('auth_token');

        await fetch(`${API_BASE_URL}/api/community/posts/${editingPost.id}/images`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`  // 添加认证头
          },
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
    // 友好的错误提示
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      message.error('登录已过期，请重新登录后继续操作');
    } else {
      message.error('更新失败，请稍后重试');
    }
    console.error('更新失败:', error);
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
  // 第一重权限检查
  if (!user) {
    message.warning('请先登录');
    return;
  }

  // 第二重权限检查：只有作者能删除
  if (post.user_id !== user.id) {
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
    // 获取token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      message.error('认证token不存在，请重新登录');
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/community/posts/${postId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`  // 添加认证头
      },
    });

    if (!response.ok) {
      // 如果是401错误，给出友好提示
      if (response.status === 401) {
        throw new Error('UNAUTHORIZED');
      }
      throw new Error('删除失败');
    }

    message.success('帖子删除成功！');
    fetchPosts(); // 刷新列表
  } catch (error) {
    // 友好的错误提示
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      message.error('登录已过期，请重新登录后继续操作');
    } else {
      message.error('删除失败，请稍后重试');
    }
    console.error('删除失败:', error);
  }
};

// 添加评论相关状态 - 放在这里
  // 定义评论类型
interface CommentType {
  id: number;
  post_id: number;
  user_id: number;
  content: string;
  created_at: string;
  user_name: string;
  user_avatar: string;
  images: string[];
  is_liked?: boolean;
  likes_count: number;
}

  const [comments, setComments] = useState<CommentType[]>([]);
  const [commentModalVisible, setCommentModalVisible] = useState(false);
  const [currentPostId, setCurrentPostId] = useState<number | null>(null);
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentPage, setCommentPage] = useState(1);
  const [commentTotal, setCommentTotal] = useState(0);



// 添加评论图片预览函数
const handleCommentPreview = (imgUrl: string, title:'') => {
  setPreviewImage(imgUrl); // 评论图片已经是完整URL，不需要拼接API_BASE_URL
  setPreviewTitle(title);
  setPreviewVisible(true);
};


// 获取评论列表
// 获取评论列表
const fetchComments = async (postId: number, page: number = 1) => {
  setCommentLoading(true);
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/community/posts/${postId}/comments?page=${page}&size=10`
    );
    const data = await response.json();

    // 获取token用于点赞状态查询
    const token = localStorage.getItem('auth_token');

    // 设置基础评论数据
    const basicComments = (data.items || []).map((comment: CommentType) => ({
      ...comment,
      is_liked: false, // 先设为false，后面会更新
      likes_count: comment.likes_count || 0
    }));

    setComments(basicComments);
    setCommentTotal(data.total || 0);

    // 批量查询点赞状态和点赞数
    if (data.items && data.items.length > 0) {
      const commentIds = data.items.map((comment: CommentType) => comment.id).join(",");

      try {
        const batchStatusResponse = await fetch(
          `${API_BASE_URL}/api/community/comments/like/status/batch?comment_ids=${commentIds}`,
          {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
          }
        );

        if (batchStatusResponse.ok) {
          const batchStatusData = await batchStatusResponse.json();

          // 更新状态
          setComments(prev => {
            const updated = prev.map(comment => ({
              ...comment,
              is_liked: batchStatusData.status_map[comment.id] || false,
              likes_count: batchStatusData.likes_count_map ?
                (batchStatusData.likes_count_map[comment.id] || 0) : 0
            }));
            return updated;
          });
        }
      } catch (error) {
        console.error('批量查询点赞状态失败:', error);
      }
    }

  } catch (error) {
    console.error('获取评论失败:', error);
  } finally {
    setCommentLoading(false);
  }
};

// 点击评论按钮
const handleComment = (postId: number) => {
  // 添加认证检查
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再发表评论');
    return;
  }

  setCurrentPostId(postId);
  setCommentModalVisible(true);
  setCommentPage(1);
  fetchComments(postId);
};

// 加载更多评论
const loadMoreComments = async () => {
  if (!currentPostId) return;

  const nextPage = commentPage + 1;
  setCommentLoading(true);

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/community/posts/${currentPostId}/comments?page=${nextPage}&size=10`
    );
    const data = await response.json();

    setComments(prev => [...prev, ...(data.items || [])]);
    setCommentPage(nextPage);
  } catch (error) {
    console.error('加载更多评论失败:', error);
    message.error('加载更多评论失败');
  } finally {
    setCommentLoading(false);
  }
};
   const [commentContent, setCommentContent] = useState(''); // 评论输入内容
  const [submittingComment, setSubmittingComment] = useState(false); // 提交状态
  // 添加图片相关状态
const [commentImages, setCommentImages] = useState<File[]>([]);
const [uploadingImages, setUploadingImages] = useState(false);

// 创建评论
const handleSubmitComment = async () => {
  // 添加认证检查
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再发表评论');
    return;
  }

  if (!currentPostId || (!commentContent.trim() && commentImages.length === 0)) {
    message.warning('请输入评论内容或选择图片');
    return;
  }

  setSubmittingComment(true);
  try {
    // 获取token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      message.error('认证token不存在，请重新登录');
      return;
    }

    // 1. 先创建评论 - 添加认证头
    const commentResponse = await fetch(`${API_BASE_URL}/api/community/posts/${currentPostId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`  // 添加认证头
      },
      body: JSON.stringify({
        content: commentContent.trim()
      }),
    });

    if (!commentResponse.ok) {
      // 如果是401错误，给出友好提示
      if (commentResponse.status === 401) {
        throw new Error('UNAUTHORIZED');
      }
      throw new Error('评论发布失败');
    }
    const newComment = await commentResponse.json();

    // 2. 如果有图片，上传图片到评论 - 添加认证头
    if (commentImages.length > 0) {
      setUploadingImages(true);
      for (const imageFile of commentImages) {
        const formData = new FormData();
        formData.append('file', imageFile);

        const uploadResponse = await fetch(
          `${API_BASE_URL}/api/community/comments/${newComment.id}/images`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`  // 添加认证头
            },
            body: formData,
          }
        );

        if (!uploadResponse.ok) {
          console.error('图片上传失败:', await uploadResponse.text());
        }
      }
      setUploadingImages(false);
    }

    // 3. 重要：重新获取评论列表，确保包含图片
    await fetchComments(currentPostId!);

    // 4. 刷新帖子列表的评论数
    fetchPosts();

    // 5. 清空输入
    setCommentContent('');
    setCommentImages([]);

    message.success('评论发布成功！');
  } catch (error) {
    // 友好的错误提示
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      message.error('登录已过期，请重新登录后继续操作');
    } else {
      message.error('评论发布失败');
    }
    console.error('发布评论失败:', error);
  } finally {
    setSubmittingComment(false);
  }
};

// 删除评论函数
const deleteComment = async (commentId: number) => {
  try {
    // 获取token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      message.error('认证token不存在，请重新登录');
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/community/comments/${commentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`  // 添加认证头
      },
    });

    if (!response.ok) {
      // 如果是401错误，给出友好提示
      if (response.status === 401) {
        throw new Error('UNAUTHORIZED');
      }
      throw new Error('删除评论失败');
    }

    const result = await response.json();

    // 从评论列表中移除已删除的评论
    setComments(prev => prev.filter(comment => comment.id !== commentId));
    setCommentTotal(prev => prev - 1);

    // 刷新帖子列表的评论数
    fetchPosts();

    message.success('评论删除成功！');
  } catch (error) {
    // 友好的错误提示
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      message.error('登录已过期，请重新登录后继续操作');
    } else {
      message.error('删除评论失败，请稍后重试');
    }
    console.error('删除评论失败:', error);
  }
};


// 添加点赞状态管理
const [likeStatus, setLikeStatus] = useState<{[postId: number]: boolean}>({});

// 智能点赞函数
// 智能点赞函数
const handleLike = async (postId: number) => {
  // 添加认证检查
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再点赞');
    return;
  }

  try {
    const currentPost = posts.find(post => post.id === postId);
    const isCurrentlyLiked = currentPost?.is_liked || false;
    const method = isCurrentlyLiked ? 'DELETE' : 'POST';

    // 获取token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      message.error('认证token不存在，请重新登录');
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/community/posts/${postId}/like`, {
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`  // 添加认证头
      },
    });

    if (!response.ok) {
      // 如果是401错误，给出友好提示
      if (response.status === 401) {
        throw new Error('UNAUTHORIZED');
      }
      throw new Error('操作失败');
    }

    const result = await response.json();

    // 更新帖子列表中的状态
    setPosts(prev => prev.map(post =>
      post.id === postId
        ? {
            ...post,
            likes_count: result.likes_count,
            is_liked: !isCurrentlyLiked
          }
        : post
    ));

    message.success(result.message);
  } catch (error) {
    // 友好的错误提示
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      message.error('登录已过期，请重新登录后继续操作');
    } else {
      message.error('操作失败');
    }
    console.error('操作失败:', error);
  }
};

// 智能评论点赞函数
// 智能评论点赞函数
const handleLikeComment = async (commentId: number) => {
  // 添加认证检查
  if (!isAuthenticated || !user) {
    message.warning('请先登录后再点赞');
    return;
  }

  try {
    const comment = comments.find(c => c.id === commentId);
    const isCurrentlyLiked = comment?.is_liked || false;
    const method = isCurrentlyLiked ? 'DELETE' : 'POST';

    // 获取token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      message.error('认证token不存在，请重新登录');
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/community/comments/${commentId}/like`, {
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`  // 添加认证头
      },
    });

    if (!response.ok) {
      // 如果是401错误，给出友好提示
      if (response.status === 401) {
        throw new Error('UNAUTHORIZED');
      }
      throw new Error('操作失败');
    }

    const result = await response.json();
    // 关键修复：确保更新点赞数
    setComments(prev => prev.map(comment => {
      if (comment.id === commentId) {
        console.log(`🔄 更新评论 ${commentId}: 点赞数 ${comment.likes_count} -> ${result.likes_count}`);
        return {
          ...comment,
          is_liked: !isCurrentlyLiked,
          likes_count: result.likes_count // 强制使用后端返回的点赞数
        };
      }
      return comment;
    }));

    message.success(result.message);
  } catch (error) {
    // 友好的错误提示
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      message.error('登录已过期，请重新登录后继续操作');
    } else {
      message.error('操作失败');
    }
    console.error('操作失败:', error);
  }
};
// 删除新图片的函数
const handleDeleteNewImage = (index: number) => {
  confirm({
    title: '确认删除图片',
    icon: <ExclamationCircleFilled />,
    content: '确定要删除这张新上传的图片吗？',
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      setNewImages(prev => prev.filter((_, i) => i !== index));
      message.success('图片已移除');
    },
  });
};
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
  onClick={() => {
    if (!isAuthenticated) {
      message.warning('请先登录后再发布帖子');
      return;
    }
    setCreateModalVisible(true);
  }}
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
    listType="picture-card"  // 改为 picture-card 显示更好
    beforeUpload={() => false} // 阻止自动上传
    accept="image/jpeg,image/png,image/webp"
    maxCount={9}
    fileList={form.getFieldValue('images') || []}
    onRemove={(file) => {
      // 处理删除临时图片
      const fileList = form.getFieldValue('images') || [];
      const newFileList = fileList.filter((item: UploadFile) => item.uid !== file.uid);
      form.setFieldsValue({ images: newFileList });
      return true;
    }}
    onPreview={(file) => {
      // 预览临时图片
      if (file.originFileObj) {
        const url = URL.createObjectURL(file.originFileObj);
        setPreviewImage(url);
        setPreviewTitle(file.name);
        setPreviewVisible(true);
      }
    }}
  >
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传图片</div>
    </div>
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

    {/* 现有图片（已保存到数据库的） */}
    {editingPost?.images_with_id && editingPost.images_with_id.length > 0 && (
      <Form.Item label="现有图片">
        <div style={{ fontSize: '12px', color: '#999', marginBottom: 8 }}>
          已保存的图片
        </div>
        <Row gutter={[8, 8]}>
          {editingPost.images_with_id.map((img, index) => (
            <Col key={img.id} xs={8} style={{ position: 'relative' }}>
              <img
                src={`${API_BASE_URL}/${img.file_path}`}
                alt={`现有图片 ${index + 1}`}
                style={{
                  width: '100%',
                  height: '100px',
                  objectFit: 'cover',
                  borderRadius: '8px'
                }}
                onClick={() => handlePreview(img.file_path, '')}
              />
              <Button
                type="primary"
                danger
                size="small"
                icon={<DeleteOutlined />}
                style={{
                  position: 'absolute',
                  top: '4px',
                  right: '4px',
                  minWidth: '24px',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: 0
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeletePostImageInEdit(editingPost.id, img.id, index);
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
      return false;
    }}
    accept="image/jpeg,image/png,image/webp"
    showUploadList={false}
  >
    <Button icon={<UploadOutlined />}>选择新图片</Button>
  </Upload>

  {newImages.length > 0 && (
    <div style={{ marginTop: 8 }}>
      <div style={{ marginBottom: 8, fontSize: '12px', color: '#999' }}>
        新选择的图片（保存帖子后会上传）
      </div>
      <Row gutter={[8, 8]}>
        {newImages.map((file, index) => (
          <Col key={index} xs={8} style={{ position: 'relative' }}>
            <img
              src={URL.createObjectURL(file)}
              alt={`新图片 ${index + 1}`}
              style={{
                width: '100%',
                height: '100px',
                objectFit: 'cover',
                borderRadius: '8px'
              }}
              onClick={() => {
                const url = URL.createObjectURL(file);
                setPreviewImage(url);
                setPreviewTitle(file.name);
                setPreviewVisible(true);
              }}
            />
            <Button
              type="primary"
              danger
              size="small"
              icon={<DeleteOutlined />}
              style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                minWidth: '24px',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 0
              }}
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteNewImage(index);
              }}
            />
            <div style={{
              fontSize: '12px',
              color: '#666',
              textAlign: 'center',
              marginTop: '4px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {file.name}
            </div>
          </Col>
        ))}
      </Row>
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
      {/* 评论弹窗 - 插入在这里 */}
<Modal
  title={`评论 (${commentTotal})`}
  open={commentModalVisible}
  onCancel={() => {
    setCommentModalVisible(false);
    setCurrentPostId(null);
    // setComments([]);
    setCommentContent(''); // 只清空输入框
    setCommentImages([]);  // 只清空待上传的图片
    setCommentPage(1);
  }}
  footer={null}
  width={650}
  destroyOnClose={false}
>
  {commentLoading && comments.length === 0 ? (
    <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
  ) : (
      <div>
        <div style={{maxHeight: '400px', overflowY: 'auto', marginBottom: '16px'}}>
          {comments.length > 0 ? (
              comments.map((comment) => (
                  <div
                      key={comment.id}
                      style={{
                        padding: '12px 0',
                        borderBottom: '1px solid #f0f0f0',
                        display: 'flex',
                        alignItems: 'flex-start'
                      }}
                  >
                    <Avatar
                        size="default"
                        src={comment.user_avatar}
                        style={{marginRight: '12px'}}
                    />
                    <div style={{flex: 1}}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        marginBottom: '6px'
                      }}>
                        <div style={{fontWeight: 'bold', fontSize: '14px', color: '#1890ff'}}>
                          {comment.user_name}
                        </div>
                        <div style={{fontSize: '12px', color: '#999'}}>
                          {new Date(comment.created_at).toLocaleString()}
                        </div>
                        {/* 评论点赞按钮 */}
<Button
  type="link"
  size="small"
  icon={comment.is_liked ? <HeartFilled /> : <HeartOutlined />}
  onClick={() => handleLikeComment(comment.id)}
  style={{
    color: comment.is_liked ? '#ff4d4f' : 'inherit',
    padding: '0 4px'
  }}
>
  {comment.likes_count || 0}
</Button>
                        {/* 删除按钮 - 只有评论作者能看到 */}
{user && comment.user_id === user.id && (  // 将 currentUser 改为 user
  <Button
    type="link"
    danger
    size="small"
    icon={<DeleteOutlined />}
    onClick={() => {
      Modal.confirm({
        title: '确认删除',
        icon: <ExclamationCircleFilled />,
        content: '确定要删除这条评论吗？',
        okText: '确认删除',
        okType: 'danger',
        cancelText: '取消',
        onOk: () => deleteComment(comment.id),
      });
    }}
  >
    删除
  </Button>
)}
                      </div>
                      <div style={{
                        fontSize: '14px',
                        lineHeight: '1.5',
                        color: '#333',
                        background: '#f8f9fa',
                        padding: '8px 12px',
                        borderRadius: '6px'
                      }}>
                        {comment.content}
                        {comment.images && comment.images.length > 0 && (
  <div style={{ marginTop: '8px' }}>
    <Row gutter={[8, 8]}>
      {comment.images.map((imgUrl, index) => (
        <Col key={index} xs={8}>
          <img
            src={imgUrl}
            alt={`评论图片 ${index + 1}`}
            style={{
              width: '100%',
              height: '80px',
              objectFit: 'cover',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
            onClick={() => handleCommentPreview(imgUrl,"")}
          />
        </Col>
      ))}
    </Row>
  </div>
)}
                      </div>
                    </div>
                  </div>
              ))
          ) : (
              <div style={{textAlign: 'center', padding: '60px 20px', color: '#999'}}>
                <div style={{fontSize: '48px', marginBottom: '16px'}}>💬</div>
                <div>暂无评论</div>
                <div style={{fontSize: '12px', marginTop: '8px'}}>成为第一个评论的人吧~</div>
              </div>
          )}
        </div>

        {comments.length > 0 && comments.length < commentTotal && (
            <div style={{textAlign: 'center', marginBottom: '16px'}}>
              <Button
                  type="link"
                  onClick={loadMoreComments}
                  loading={commentLoading}
              >
                加载更多评论 ({comments.length}/{commentTotal})
              </Button>
            </div>
        )}

        <div style={{
          borderTop: '1px solid #e8e8e8',
          paddingTop: '16px',
        }}>
          {/* 图片上传区域 */}
  <div style={{ marginBottom: '12px' }}>
    <Upload
      multiple
      listType="picture"
      beforeUpload={(file) => {
        setCommentImages(prev => [...prev, file]);
        return false; // 阻止自动上传
      }}
      accept="image/jpeg,image/png,image/webp"
      showUploadList={false}
    >
      <Button icon={<UploadOutlined />}>添加图片</Button>
    </Upload>

    {/* 显示已选择的图片 */}
    {commentImages.length > 0 && (
      <div style={{ marginTop: '8px', padding: '8px 12px', background: '#f5f5f5', borderRadius: '4px' }}>
        <div>📸 已选择 {commentImages.length} 张图片：</div>
        {commentImages.map((file, index) => (
          <div key={index} style={{ fontSize: '12px', marginTop: '4px', display: 'flex', justifyContent: 'space-between' }}>
            <span>• {file.name}</span>
            <Button
              type="link"
              danger
              size="small"
              onClick={() => setCommentImages(prev => prev.filter((_, i) => i !== index))}
            >
              删除
            </Button>
          </div>
        ))}
      </div>
    )}
  </div>
          <Space.Compact style={{width: '100%'}}>
            <Input
                placeholder="写下你的评论..."
                value={commentContent}
                onChange={(e) => setCommentContent(e.target.value)}
                size="large"
                style={{flex: 1}}
                onPressEnter={handleSubmitComment}  // 按回车也可以发送
            />
            <Button
                type="primary"
                size="large"
                onClick={handleSubmitComment}
                loading={submittingComment}
            >
              发布
            </Button>
          </Space.Compact>
        </div>
      </div>
  )}
</Modal>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Tabs activeKey={category} onChange={(key) => {
            setCategory(key);
            setPage(1);
          }}>
            {['popular', 'latest', 'following'].map(tabKey => (
                <TabPane
                    tab={tabKey === 'popular' ? '热门' : tabKey === 'latest' ? '最新' : '关注'}
                    key={tabKey}
                >
                  {loading ? (
                      <div>加载中...</div>
                  ) : tabKey === 'following' ? (
                      <div style={{textAlign: 'center', padding: '40px', color: 'var(--text-tertiary)'}}>
                        关注的内容将在这里显示
                      </div>
  ) : (
    <>
      {posts.map(post => (
        <Card key={post.id} style={{ marginBottom: '16px' }} hoverable>
          <div style={{marginBottom: '12px'}}>
            <Space>
              <Avatar src={`https://api.dicebear.com/7.x/miniavs/svg?seed=${post.user_id}`}/>
              <div>
                <div style={{fontWeight: 'bold'}}>
                  {post.user_name}
                </div>
                <div style={{fontSize: '12px', color: 'var(--text-tertiary)'}}>
                  <ClockCircleOutlined/> {new Date(post.created_at).toLocaleString()}
                </div>
              </div>
            </Space>
          </div>

          <Title level={4} style={{marginBottom: '8px'}}>{post.title}</Title>
          <Paragraph style={{marginBottom: '12px'}}>{post.content}</Paragraph>
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
<Image
  width={0} // 设置为0让图片自适应
  style={{ display: 'none' }}
  src={previewImage || ''}
  preview={{
    visible: previewVisible,
    onVisibleChange: (visible) => {
      setPreviewVisible(visible);
      if (!visible) {
        // 关闭时释放临时图片URL
        if (previewImage && previewImage.startsWith('blob:')) {
          URL.revokeObjectURL(previewImage);
        }
        setPreviewImage(null);
      }
    },
    zIndex: 9999
  }}
/>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            borderTop: '1px solid var(--border-color)',
            paddingTop: '12px'
          }}>


<Button
  type="text"
  icon={post.is_liked ? <HeartFilled /> : <HeartOutlined />}
  onClick={() => handleLike(post.id)}
  style={{
    color: post.is_liked ? '#ff4d4f' : 'inherit'
  }}
>
  {post.likes_count}
</Button>
            <Button type="text" icon={<MessageOutlined/>} onClick={() => handleComment(post.id)}>
              {post.comments_count}
            </Button>

{/* 只有帖子作者才能看到编辑和删除按钮 */}
{user && post.user_id === user.id && (
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
