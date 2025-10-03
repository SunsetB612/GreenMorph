import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Input, Button, Tabs, message, Spin } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import './AuthPage.css';


const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { login, register, isLoading, isAuthenticated } = useAuthStore();

  // 如果已登录，重定向到首页
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const showToast = (msg: string) => {
    // 使用antd的message组件
    message.error(msg);
  };

  const validateForm = () => {
    if (!isLogin) {
      if (formData.password !== formData.confirmPassword) {
        showToast('两次输入的密码不一致');
        return false;
      }
      if (formData.password.length < 6) {
        showToast('密码长度至少6位');
        return false;
      }
      if (formData.username.length < 3) {
        showToast('用户名长度至少3位');
        return false;
      }
      if (!/^[a-zA-Z0-9]+$/.test(formData.username)) {
        showToast('用户名只能包含字母和数字');
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      if (isLogin) {
        await login({
          email: formData.email,
          password: formData.password,
        });
        // 登录成功，跳转到首页
        navigate('/');
      } else {
        await register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        });
        // 注册成功，跳转到首页
        navigate('/');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `${isLogin ? '登录' : '注册'}失败`;
      showToast(errorMessage);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    });
    form.resetFields();
  };

  if (isLoading) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <Spin size="large" />
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <Card className="auth-card">
          <div className="auth-header">
            <h1>GreenMorph</h1>
            <p>智能旧物改造助手</p>
          </div>

          <Tabs
            activeKey={isLogin ? 'login' : 'register'}
            onChange={switchMode}
            centered
            className="auth-tabs"
            items={[
              {
                key: 'login',
                label: '登录',
                children: (
                  <Form
                    form={form}
                    name="login"
                    onFinish={handleSubmit}
                    layout="vertical"
                    size="large"
                  >
                    <Form.Item
                      name="email"
                      rules={[
                        { required: true, message: '请输入邮箱' },
                        { type: 'email', message: '请输入有效的邮箱地址' }
                      ]}
                    >
                      <Input
                        prefix={<MailOutlined />}
                        placeholder="邮箱"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item
                      name="password"
                      rules={[
                        { required: true, message: '请输入密码' },
                        { min: 6, message: '密码长度至少6位' }
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined />}
                        placeholder="密码"
                        value={formData.password}
                        onChange={(e) => handleInputChange('password', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        className="auth-button"
                        loading={isLoading}
                        block
                      >
                        登录
                      </Button>
                    </Form.Item>
                  </Form>
                )
              },
              {
                key: 'register',
                label: '注册',
                children: (
                  <Form
                    form={form}
                    name="register"
                    onFinish={handleSubmit}
                    layout="vertical"
                    size="large"
                  >
                    <Form.Item
                      name="username"
                      rules={[
                        { required: true, message: '请输入用户名' },
                        { min: 3, message: '用户名长度至少3位' },
                        { pattern: /^[a-zA-Z0-9]+$/, message: '用户名只能包含字母和数字' }
                      ]}
                    >
                      <Input
                        prefix={<UserOutlined />}
                        placeholder="用户名"
                        value={formData.username}
                        onChange={(e) => handleInputChange('username', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item
                      name="email"
                      rules={[
                        { required: true, message: '请输入邮箱' },
                        { type: 'email', message: '请输入有效的邮箱地址' }
                      ]}
                    >
                      <Input
                        prefix={<MailOutlined />}
                        placeholder="邮箱"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item
                      name="password"
                      rules={[
                        { required: true, message: '请输入密码' },
                        { min: 6, message: '密码长度至少6位' }
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined />}
                        placeholder="密码"
                        value={formData.password}
                        onChange={(e) => handleInputChange('password', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item
                      name="confirmPassword"
                      rules={[
                        { required: true, message: '请确认密码' },
                        {
                          validator: (_, value) => {
                            if (value && value !== formData.password) {
                              return Promise.reject(new Error('两次输入的密码不一致'));
                            }
                            return Promise.resolve();
                          },
                        },
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined />}
                        placeholder="确认密码"
                        value={formData.confirmPassword}
                        onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        className="auth-button"
                        loading={isLoading}
                        block
                      >
                        注册
                      </Button>
                    </Form.Item>
                  </Form>
                )
              }
            ]}
          />
        </Card>
      </div>
    </div>
  );
};

export default AuthPage;
