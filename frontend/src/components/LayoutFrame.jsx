import React, { useState } from 'react';
import { Layout, Menu, Typography, Avatar, Dropdown, Space } from 'antd';
import { 
  DashboardOutlined, 
  VideoCameraAddOutlined, 
  UserOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  PlaySquareOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content, Footer } = Layout;
const { Title, Text } = Typography;

const LayoutFrame = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  // Menu items config
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Thư viện bài giảng',
    },
    {
      key: '/create',
      icon: <VideoCameraAddOutlined />,
      label: 'Tạo bài giảng mới',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        width={250}
        theme="dark"
        style={{ 
          boxShadow: '2px 0 8px 0 rgba(29,35,41,.05)',
          background: '#001529' 
        }}
      >
        {/* LOGO AREA */}
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <PlaySquareOutlined style={{ fontSize: '28px', color: '#1890ff', marginRight: collapsed ? 0 : 10 }} />
          {!collapsed && (
            <Title level={4} style={{ color: '#fff', margin: 0, fontWeight: 700 }}>
              EduRender AI
            </Title>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 20 }}
        />
      </Sider>

      <Layout className="site-layout">
        <Header style={{ padding: '0 24px', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 1px 4px rgba(0,21,41,.08)' }}>
          {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
            className: 'trigger',
            style: { fontSize: '18px', cursor: 'pointer' },
            onClick: () => setCollapsed(!collapsed),
          })}
          
          <Space>
            <Text strong>Giảng viên: Ts.Phạm Văn Hưởng</Text>
            <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
          </Space>
        </Header>

        <Content style={{ margin: '24px 16px', padding: 24, minHeight: 280, background: '#f0f2f5' }}>
          {children}
        </Content>

        <Footer style={{ textAlign: 'center', color: '#888' }}>
          EduRender AI ©2025 Created by Group 04 - TTCS
        </Footer>
      </Layout>
    </Layout>
  );
};

export default LayoutFrame;