import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  Space,
  Alert,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  WifiOutlined,
  ClockCircleOutlined,
  CloudDownloadOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { deviceAPI } from '../services/api';
import dayjs from 'dayjs';
import CLIConnection from './CLIConnection';

const { Option } = Select;

const DeviceList = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [form] = Form.useForm();
  // 添加测试连接加载状态
  const [testingConnections, setTestingConnections] = useState(new Set());
  // 添加快速备份加载状态
  const [quickBackupLoading, setQuickBackupLoading] = useState(new Set());
  // 添加CLI连接状态
  const [cliVisible, setCliVisible] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const data = await deviceAPI.getDevices();
      setDevices(data);
    } catch (error) {
      message.error('获取设备列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const testConnection = async (deviceId) => {
    // 设置测试状态
    setTestingConnections(prev => new Set(prev).add(deviceId));
    
    try {
      const result = await deviceAPI.testConnection(deviceId);
      if (result.success) {
        // 构建成功消息，包含延迟信息
        let successMessage = '连接测试成功';
        if (result.data?.latency_message) {
          successMessage += ` - ${result.data.latency_message}`;
        }
        message.success(successMessage);
        
        // 刷新设备列表以显示最新的延迟信息
        fetchDevices();
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
    } catch (error) {
      message.error('连接测试失败');
    } finally {
      // 清除测试状态
      setTestingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(deviceId);
        return newSet;
      });
    }
  };

  const quickBackup = async (deviceId) => {
    // 设置快速备份状态
    setQuickBackupLoading(prev => new Set(prev).add(deviceId));
    
    try {
      const result = await deviceAPI.quickBackup(deviceId);
      if (result.success) {
        message.success('快速备份执行成功');
        // 刷新设备列表以显示最新的备份信息
        fetchDevices();
      } else {
        message.error(`快速备份失败: ${result.message}`);
      }
    } catch (error) {
      message.error('快速备份失败');
    } finally {
      // 清除快速备份状态
      setQuickBackupLoading(prev => {
        const newSet = new Set(prev);
        newSet.delete(deviceId);
        return newSet;
      });
    }
  };

  const showModal = (device = null) => {
    setEditingDevice(device);
    if (device) {
      // 确保编辑时协议字段显示为SSH
      form.setFieldsValue({
        ...device,
        protocol: 'SSH'
      });
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 确保协议值为小写，与后端保持一致
      values.protocol = 'ssh';
      
      if (editingDevice) {
        await deviceAPI.updateDevice(editingDevice.id, values);
        message.success('设备更新成功');
      } else {
        await deviceAPI.createDevice(values);
        message.success('设备创建成功');
      }
      
      setModalVisible(false);
      fetchDevices();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleDelete = async (deviceId) => {
    try {
      await deviceAPI.deleteDevice(deviceId);
      message.success('设备删除成功');
      fetchDevices();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 渲染连接状态标签
  const renderConnectionStatus = (device) => {
    if (!device.connection_status || device.connection_status === 'unknown') {
      return <Tag color="default">未测试</Tag>;
    }
    
    if (device.connection_status === 'success') {
      return <Tag color="success">连接正常</Tag>;
    } else {
      return <Tag color="error">连接失败</Tag>;
    }
  };

  // 渲染延迟信息
  const renderLatency = (device) => {
    if (!device.last_latency) {
      return '-';
    }
    
    const latency = device.last_latency;
    let color = 'green';
    if (latency > 100) color = 'orange';
    if (latency > 500) color = 'red';
    
    return (
      <Tooltip title={`最后测试时间: ${device.last_test_time ? dayjs(device.last_test_time).format('YYYY-MM-DD HH:mm:ss') : '未知'}`}>
        <Tag color={color} icon={<ClockCircleOutlined />}>
          {latency}ms
        </Tag>
      </Tooltip>
    );
  };

  const columns = [
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            {record.ip_address}:22 (SSH)
          </div>
        </div>
      ),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 100,
    },
    {
      title: '连接状态',
      key: 'connection_status',
      width: 100,
      render: (_, record) => renderConnectionStatus(record),
    },
    {
      title: '网络延迟',
      key: 'latency',
      width: 100,
      render: (_, record) => renderLatency(record),
    },
    {
      title: '最近备份',
      key: 'last_backup',
      width: 140,
      render: (_, record) => {
        if (record.last_backup_time) {
          // 备份类型映射
          const backupTypeMap = {
            'running-config': '运行配置',
            'startup-config': '启动配置', 
            'ip-route': '路由表',
            'arp-table': 'ARP表',
            'mac-table': 'MAC表',
          };
          
          const displayType = backupTypeMap[record.last_backup_type] || record.last_backup_type || '运行配置';
          
          return (
            <div>
              <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                {dayjs(record.last_backup_time).format('YYYY-MM-DD HH:mm:ss')}
              </div>
              <div style={{ fontSize: '12px', color: '#1890ff' }}>
                {displayType}
              </div>
            </div>
          );
        }
        return <span style={{ color: '#d9d9d9' }}>暂无备份</span>;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 120,
      render: (text) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<WifiOutlined />}
            loading={testingConnections.has(record.id)}
            onClick={() => testConnection(record.id)}
          >
            测试连接
          </Button>
          <Button
            type="default"
            size="small"
            icon={<CloudDownloadOutlined />}
            loading={quickBackupLoading.has(record.id)}
            onClick={() => quickBackup(record.id)}
          >
            立即备份
          </Button>
          <Button
            type="default"
            size="small"
            icon={<CodeOutlined />}
            onClick={() => {
              setSelectedDevice(record);
              setCliVisible(true);
            }}
          >
            CLI连接
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => showModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个设备吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>设备管理</h2>
        <p>管理网络设备的SSH连接信息和配置</p>
      </div>

      <div className="action-bar">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => showModal()}
        >
          添加设备
        </Button>
      </div>

      <Table
        className="device-table"
        columns={columns}
        dataSource={devices}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      <Modal
        title={editingDevice ? '编辑设备' : '添加设备'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            port: 22,
            protocol: 'SSH',
          }}
        >
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="name"
              label="设备名称"
              rules={[{ required: true, message: '请输入设备名称' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="请输入设备名称" />
            </Form.Item>
            
            <Form.Item
              name="ip_address"
              label="IP地址"
              rules={[{ required: true, message: '请输入IP地址' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="请输入IP地址" />
            </Form.Item>
          </div>
          
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="protocol"
              label="连接协议"
              style={{ flex: 1 }}
            >
              <Input disabled />
            </Form.Item>
            
            <Form.Item
              name="port"
              label="端口"
              rules={[{ required: true, message: '请输入端口' }]}
              style={{ flex: 1 }}
            >
              <Input type="number" placeholder="端口号" />
            </Form.Item>
          </div>
          
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="username"
              label="用户名"
              rules={[{ required: true, message: '请输入用户名' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="请输入用户名" />
            </Form.Item>
            
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入密码' }]}
              style={{ flex: 1 }}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
          </div>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input placeholder="设备描述（可选）" />
          </Form.Item>
          
          <Alert
            message="智能备份配置"
            description="系统支持SSH连接，会自动检测设备类型（H3C、Cisco、华为等）并配置相应的备份命令，无需手动设置。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </Form>
      </Modal>

      {/* CLI连接组件 */}
      <CLIConnection
        visible={cliVisible}
        onClose={() => setCliVisible(false)}
        device={selectedDevice}
      />
    </div>
  );
};

export default DeviceList;
