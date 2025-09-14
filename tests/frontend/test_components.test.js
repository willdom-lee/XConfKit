import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { message } from 'antd';
import DeviceList from '../../frontend/src/components/DeviceList';
import BackupManagement from '../../frontend/src/components/BackupManagement';

// Mock API服务
jest.mock('../../frontend/src/services/api', () => ({
  deviceAPI: {
    getDevices: jest.fn(),
    createDevice: jest.fn(),
    updateDevice: jest.fn(),
    deleteDevice: jest.fn(),
    testConnection: jest.fn(),
  },
  backupAPI: {
    getBackups: jest.fn(),
    executeBackup: jest.fn(),
    deleteBackup: jest.fn(),
  },
}));

// Mock antd message
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  message: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
  },
}));

// 包装组件以提供路由上下文
const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('DeviceList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders device management page', () => {
    renderWithRouter(<DeviceList />);
    
    expect(screen.getByText('设备管理')).toBeInTheDocument();
    expect(screen.getByText('管理网络设备的连接信息和配置')).toBeInTheDocument();
    expect(screen.getByText('添加设备')).toBeInTheDocument();
  });

  test('shows loading state when fetching devices', async () => {
    const { deviceAPI } = require('../../frontend/src/services/api');
    deviceAPI.getDevices.mockImplementation(() => new Promise(() => {})); // 永不解析的Promise
    
    renderWithRouter(<DeviceList />);
    
    // 应该显示加载状态
    await waitFor(() => {
      expect(deviceAPI.getDevices).toHaveBeenCalled();
    });
  });

  test('displays devices when API call succeeds', async () => {
    const { deviceAPI } = require('../../frontend/src/services/api');
    const mockDevices = [
      {
        id: 1,
        name: '测试设备1',
        ip_address: '192.168.1.1',
        protocol: 'ssh',
        username: 'admin',
        port: 22,
        description: '测试设备',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: '测试设备2',
        ip_address: '192.168.1.2',
        protocol: 'ssh',
        username: 'admin',
        port: 22,
        description: '测试设备2',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      },
    ];
    
    deviceAPI.getDevices.mockResolvedValue(mockDevices);
    
    renderWithRouter(<DeviceList />);
    
    await waitFor(() => {
      expect(screen.getByText('测试设备1')).toBeInTheDocument();
      expect(screen.getByText('测试设备2')).toBeInTheDocument();
    });
  });

  test('shows error message when API call fails', async () => {
    const { deviceAPI } = require('../../frontend/src/services/api');
    deviceAPI.getDevices.mockRejectedValue(new Error('API Error'));
    
    renderWithRouter(<DeviceList />);
    
    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('获取设备列表失败');
    });
  });

  test('opens create device modal when add button is clicked', () => {
    const { deviceAPI } = require('../../frontend/src/services/api');
    deviceAPI.getDevices.mockResolvedValue([]);
    
    renderWithRouter(<DeviceList />);
    
    const addButton = screen.getByText('添加设备');
    fireEvent.click(addButton);
    
    expect(screen.getByText('添加设备')).toBeInTheDocument();
    expect(screen.getByLabelText('设备名称')).toBeInTheDocument();
    expect(screen.getByLabelText('IP地址')).toBeInTheDocument();
  });

  test('creates device successfully', async () => {
    const { deviceAPI } = require('../../frontend/src/services/api');
    deviceAPI.getDevices.mockResolvedValue([]);
    deviceAPI.createDevice.mockResolvedValue({
      id: 1,
      name: '新设备',
      ip_address: '192.168.1.1',
      protocol: 'ssh',
      username: 'admin',
      password: 'test_password',
      port: 22,
      description: '新设备描述',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    });
    
    renderWithRouter(<DeviceList />);
    
    // 打开创建模态框
    const addButton = screen.getByText('添加设备');
    fireEvent.click(addButton);
    
    // 填写表单
    fireEvent.change(screen.getByLabelText('设备名称'), {
      target: { value: '新设备' },
    });
    fireEvent.change(screen.getByLabelText('IP地址'), {
      target: { value: '192.168.1.1' },
    });
    fireEvent.change(screen.getByLabelText('用户名'), {
      target: { value: 'admin' },
    });
    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'password123' },
    });
    
    // 提交表单
    const submitButton = screen.getByText('确定');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(deviceAPI.createDevice).toHaveBeenCalledWith({
        name: '新设备',
        ip_address: '192.168.1.1',
        protocol: 'ssh',
        username: 'admin',
        password: 'test_password',
        port: 22,
        description: undefined,
      });
      expect(message.success).toHaveBeenCalledWith('设备创建成功');
    });
  });
});

describe('BackupManagement Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders backup management page', () => {
    renderWithRouter(<BackupManagement />);
    
    expect(screen.getByText('备份管理')).toBeInTheDocument();
    expect(screen.getByText('执行设备配置备份和查看备份记录')).toBeInTheDocument();
  });

  test('loads devices and backups on mount', async () => {
    const { deviceAPI, backupAPI } = require('../../frontend/src/services/api');
    deviceAPI.getDevices.mockResolvedValue([]);
    backupAPI.getBackups.mockResolvedValue([]);
    
    renderWithRouter(<BackupManagement />);
    
    await waitFor(() => {
      expect(deviceAPI.getDevices).toHaveBeenCalled();
      expect(backupAPI.getBackups).toHaveBeenCalled();
    });
  });

  test('executes backup when device is selected and backup button is clicked', async () => {
    const { deviceAPI, backupAPI } = require('../../frontend/src/services/api');
    const mockDevices = [
      {
        id: 1,
        name: '测试设备',
        ip_address: '192.168.1.1',
        protocol: 'ssh',
        username: 'admin',
        port: 22,
      },
    ];
    
    deviceAPI.getDevices.mockResolvedValue(mockDevices);
    backupAPI.getBackups.mockResolvedValue([]);
    backupAPI.executeBackup.mockResolvedValue({
      success: true,
      message: '备份成功',
      backup_id: 1,
      file_path: '/path/to/backup.txt',
    });
    
    renderWithRouter(<BackupManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('测试设备 (192.168.1.1)')).toBeInTheDocument();
    });
    
    // 选择设备
    const deviceSelect = screen.getByText('请选择设备');
    fireEvent.click(deviceSelect);
    
    const deviceOption = screen.getByText('测试设备 (192.168.1.1)');
    fireEvent.click(deviceOption);
    
    // 点击执行备份按钮
    const backupButton = screen.getByText('执行备份');
    fireEvent.click(backupButton);
    
    await waitFor(() => {
      expect(backupAPI.executeBackup).toHaveBeenCalledWith(1, 'running-config');
      expect(message.success).toHaveBeenCalledWith('备份执行成功');
    });
  });

  test('shows warning when trying to backup without selecting device', async () => {
    const { deviceAPI, backupAPI } = require('../../frontend/src/services/api');
    deviceAPI.getDevices.mockResolvedValue([]);
    backupAPI.getBackups.mockResolvedValue([]);
    
    renderWithRouter(<BackupManagement />);
    
    // 直接点击执行备份按钮，不选择设备
    const backupButton = screen.getByText('执行备份');
    fireEvent.click(backupButton);
    
    await waitFor(() => {
      expect(message.warning).toHaveBeenCalledWith('请先选择设备');
    });
  });
});
