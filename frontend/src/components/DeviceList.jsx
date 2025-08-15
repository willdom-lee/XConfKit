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
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  WifiOutlined,
} from '@ant-design/icons';
import { deviceAPI } from '../services/api';
import dayjs from 'dayjs';

const { Option } = Select;

const DeviceList = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [form] = Form.useForm();

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
    try {
      const result = await deviceAPI.testConnection(deviceId);
      if (result.success) {
        message.success('连接测试成功');
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
    } catch (error) {
      message.error('连接测试失败');
    }
  };

  const showModal = (device = null) => {
    setEditingDevice(device);
    if (device) {
      form.setFieldsValue(device);
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
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

  const columns = [
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            {record.ip_address}:{record.port} (SSH)
          </div>
        </div>
      ),
    },

    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<WifiOutlined />}
            onClick={() => testConnection(record.id)}
          >
            测试连接
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
        columns={columns}
        dataSource={devices}
        rowKey="id"
        loading={loading}
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
              <Input value="ssh" disabled />
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
    </div>
  );
};

export default DeviceList;
