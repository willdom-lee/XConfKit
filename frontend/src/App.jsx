import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DesktopOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  RobotOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

import Dashboard from './components/Dashboard';
import DeviceList from './components/DeviceList';
import BackupManagement from './components/BackupManagement';
import StrategyManagement from './components/StrategyManagement';
import SystemConfig from './components/SystemConfig';
import AIConfigAnalysis from './components/AIConfigAnalysis';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

const { Header, Sider, Content } = Layout;

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/devices',
      icon: <DesktopOutlined />,
      label: '设备管理',
    },
    {
      key: '/backups',
      icon: <CloudUploadOutlined />,
      label: '备份管理',
    },
    {
      key: '/strategies',
      icon: <ClockCircleOutlined />,
      label: '备份策略',
    },
    {
      key: '/analysis',
      icon: <RobotOutlined />,
      label: 'AI分析',
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: '系统配置',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center', 
        background: '#001529',
        padding: '0 24px'
      }}>
        <div style={{ 
          color: 'white', 
          fontSize: '20px', 
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <SettingOutlined />
          XConfKit
        </div>
      </Header>
      
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Sider>
        
        <Layout style={{ padding: '0 24px 24px' }}>
          <Content style={{
            background: '#fff',
            padding: 24,
            margin: 0,
            minHeight: 280,
            borderRadius: '8px',
            marginTop: '24px'
          }}>
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/devices" element={<DeviceList />} />
                <Route path="/backups" element={<BackupManagement />} />
                <Route path="/strategies" element={<StrategyManagement />} />
                <Route path="/analysis" element={<AIConfigAnalysis />} />
                <Route path="/config" element={<SystemConfig />} />
              </Routes>
            </ErrorBoundary>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
