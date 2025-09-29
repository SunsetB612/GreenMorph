import React, { useState } from 'react';
import { Layout as AntLayout, Menu, Button, Drawer } from 'antd';
import { 
  MenuOutlined, 
  HomeOutlined, 
  RobotOutlined, 
  TeamOutlined, 
  UserOutlined, 
  InfoCircleOutlined 
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/ai-assistant',
      icon: <RobotOutlined />,
      label: 'AI助手',
    },
    {
      key: '/community',
      icon: <TeamOutlined />,
      label: '社区',
    },
    {
      key: '/profile',
      icon: <UserOutlined />,
      label: '个人中心',
    },
    {
      key: '/about',
      icon: <InfoCircleOutlined />,
      label: '关于我们',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    setMobileMenuVisible(false);
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      {/* 桌面端侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="desktop-sider"
        style={{
          background: 'var(--card-background)',
          boxShadow: 'var(--shadow)',
        }}
      >
        <div className="logo" style={{ 
          height: '64px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid var(--border-color)'
        }}>
          <h2 style={{ margin: 0, color: 'var(--primary-color)' }}>
            {collapsed ? 'GM' : 'GreenMorph'}
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <AntLayout>
        {/* 头部 */}
        <Header style={{ 
          background: 'var(--card-background)', 
          padding: '0 16px',
          boxShadow: 'var(--shadow)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="desktop-menu-trigger"
            />
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setMobileMenuVisible(true)}
              className="mobile-menu-trigger"
              style={{ display: 'none' }}
            />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', color: 'var(--primary-color)' }}>
              旧物回收设计智能助手
            </h1>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content style={{ 
          margin: 0,
          padding: 0,
          background: 'var(--background-color)',
          minHeight: 'calc(100vh - 64px)',
          width: '100%',
          overflow: 'auto'
        }}>
          {children}
        </Content>
      </AntLayout>

      {/* 移动端抽屉菜单 */}
      <Drawer
        title="菜单"
        placement="left"
        onClose={() => setMobileMenuVisible(false)}
        open={mobileMenuVisible}
        width={250}
      >
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Drawer>
    </AntLayout>
  );
};

export default Layout;
