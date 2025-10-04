import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '../store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    // 检查认证状态
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // 如果加载完成且未认证，重定向到登录页
    if (!isLoading && !isAuthenticated) {
      navigate('/auth');
    }
  }, [isLoading, isAuthenticated, navigate]);

  // 显示加载状态
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  // 如果未认证，不渲染内容（会重定向到登录页）
  if (!isAuthenticated) {
    return null;
  }

  // 如果已认证，渲染受保护的内容
  return <>{children}</>;
};

export default ProtectedRoute;
