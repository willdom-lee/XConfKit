import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Switch,
  message,
  Popconfirm,
  Tag,
  Space,
  Card,
  Row,
  Col,
  Typography,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { deviceAPI, strategyAPI } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const StrategyManagement = () => {
  const [strategies, setStrategies] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState(null);
  const [form] = Form.useForm();

  // 获取设备列表
  const fetchDevices = async () => {
    try {
      const data = await deviceAPI.getDevices();
      setDevices(data);
    } catch (error) {
      message.error('获取设备列表失败');
    }
  };

  // 获取策略列表
  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const data = await strategyAPI.getStrategies();
      setStrategies(data);
    } catch (error) {
      message.error('获取策略列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    fetchStrategies();
  }, []);

  // 显示模态框
  const showModal = (strategy = null) => {
    setEditingStrategy(strategy);
    if (strategy) {
      // 编辑模式，设置表单初始值
      const initialValues = {
        ...strategy,
        scheduled_time: strategy.scheduled_time ? dayjs(strategy.scheduled_time) : null,
        start_time: strategy.start_time ? dayjs(strategy.start_time) : null,
        end_time: strategy.end_time ? dayjs(strategy.end_time) : null,
      };
      form.setFieldsValue(initialValues);
    } else {
      // 新建模式，重置表单
      form.resetFields();
      
      // 设置默认时间为1小时后（本地时间）
      const defaultTime = dayjs().add(1, 'hour');
      
      form.setFieldsValue({
        strategy_type: 'one-time',
        backup_type: 'running-config',
        is_active: true,
        scheduled_time: defaultTime,
        start_time: defaultTime,
      });
    }
    setModalVisible(true);
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      console.log('表单值:', values);
      
      // 处理时间字段 - 直接使用北京时间
      const strategyData = {
        ...values,
        scheduled_time: values.scheduled_time ? values.scheduled_time.format('YYYY-MM-DDTHH:mm:ss') : null,
        start_time: values.start_time ? values.start_time.format('YYYY-MM-DDTHH:mm:ss') : null,
        end_time: values.end_time ? values.end_time.format('YYYY-MM-DDTHH:mm:ss') : null,
      };
      
      console.log('发送的策略数据:', strategyData);
      
      if (editingStrategy) {
        console.log('更新策略:', editingStrategy.id);
        const result = await strategyAPI.updateStrategy(editingStrategy.id, strategyData);
        console.log('更新结果:', result);
        message.success('策略更新成功');
      } else {
        console.log('创建策略');
        const result = await strategyAPI.createStrategy(strategyData);
        console.log('创建结果:', result);
        message.success('策略创建成功');
      }
      
      setModalVisible(false);
      fetchStrategies();
    } catch (error) {
      console.error('策略操作失败:', error);
      console.error('错误详情:', error.response?.data);
      message.error(`操作失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 删除策略
  const handleDelete = async (strategyId) => {
    try {
      await strategyAPI.deleteStrategy(strategyId);
      message.success('策略删除成功');
      fetchStrategies();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 切换策略状态
  const toggleStatus = async (strategyId) => {
    try {
      await strategyAPI.toggleStrategyStatus(strategyId);
      message.success('状态切换成功');
      fetchStrategies();
    } catch (error) {
      message.error('状态切换失败');
    }
  };

  // 立即执行策略（不影响调度）
  const executeStrategyNow = async (strategyId) => {
    try {
      const result = await strategyAPI.executeStrategyNow(strategyId);
      if (result.success) {
        message.success('策略立即执行成功');
      } else {
        message.error(`策略执行失败: ${result.message}`);
      }
      fetchStrategies();
    } catch (error) {
      message.error('策略执行失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            {record.description || '无描述'}
          </div>
        </div>
      ),
    },
    {
      title: '设备',
      dataIndex: 'device',
      key: 'device',
      render: (device) => device?.name || '-',
    },
    {
      title: '策略类型',
      dataIndex: 'strategy_type',
      key: 'strategy_type',
      render: (type) => {
        const typeMap = {
          'one-time': { color: 'blue', text: '一次性' },
          'recurring': { color: 'green', text: '周期性' },
        };
        const config = typeMap[type] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '备份类型',
      dataIndex: 'backup_type',
      key: 'backup_type',
      render: (type) => {
        const typeMap = {
          'running-config': '运行配置',
          'startup-config': '启动配置',
          'ip-route': '路由表',
          'arp-table': 'ARP表',
          'mac-table': 'MAC表',
        };
        return typeMap[type] || type;
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '下次执行',
      dataIndex: 'next_execution',
      key: 'next_execution',
      render: (time) => {
        if (!time) return '-';
        return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
      },
    },
    {
      title: '最后执行',
      dataIndex: 'last_execution',
      key: 'last_execution',
      render: (time) => {
        if (!time) return '-';
        return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={record.is_active ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => toggleStatus(record.id)}
          >
            {record.is_active ? '禁用' : '启用'}
          </Button>
          <Button
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={() => executeStrategyNow(record.id)}
            disabled={!record.is_active}
            type="primary"
          >
            立即执行
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => showModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个策略吗？"
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
        <Title level={2}>备份策略</Title>
        <Text type="secondary">管理设备的自动备份策略</Text>
      </div>

      <div className="action-bar">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => showModal()}
        >
          新增策略
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={strategies}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      {/* 策略编辑模态框 */}
      <Modal
        title={editingStrategy ? '编辑策略' : '新增策略'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="策略名称"
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input placeholder="请输入策略名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="device_id"
                label="选择设备"
                rules={[{ required: true, message: '请选择设备' }]}
              >
                <Select placeholder="请选择设备">
                  {devices.map(device => (
                    <Option key={device.id} value={device.id}>
                      {device.name} ({device.ip_address})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="strategy_type"
                label="策略类型"
                rules={[{ required: true, message: '请选择策略类型' }]}
              >
                <Select>
                  <Option value="one-time">一次性策略</Option>
                  <Option value="recurring">周期性策略</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="backup_type"
                label="备份类型"
                rules={[{ required: true, message: '请选择备份类型' }]}
              >
                <Select>
                  <Option value="running-config">运行配置</Option>
                  <Option value="startup-config">启动配置</Option>
                  <Option value="ip-route">路由表</Option>
                  <Option value="arp-table">ARP表</Option>
                  <Option value="mac-table">MAC表</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="策略描述"
          >
            <TextArea placeholder="策略描述（可选）" rows={3} />
          </Form.Item>

          <Divider>时间配置</Divider>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.strategy_type !== currentValues.strategy_type}
          >
            {({ getFieldValue }) => {
              const strategyType = getFieldValue('strategy_type');
              
              if (strategyType === 'one-time') {
                return (
                  <Form.Item
                    name="scheduled_time"
                    label="计划执行时间"
                    rules={[{ required: true, message: '请设置计划执行时间' }]}
                  >
                    <DatePicker
                      showTime
                      format="YYYY-MM-DD HH:mm:ss"
                      placeholder="选择执行时间"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                );
              }
              
              if (strategyType === 'recurring') {
                return (
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item
                        name="frequency_type"
                        label="频率类型"
                        rules={[{ required: true, message: '请选择频率类型' }]}
                      >
                        <Select>
                          <Option value="hour">小时</Option>
                          <Option value="day">天</Option>
                          <Option value="month">月</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="frequency_value"
                        label="频率值"
                        rules={[{ required: true, message: '请输入频率值' }]}
                      >
                        <Input type="number" placeholder="频率值" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="start_time"
                        label="开始时间"
                        rules={[{ required: true, message: '请设置开始时间' }]}
                      >
                        <DatePicker
                          showTime
                          format="YYYY-MM-DD HH:mm:ss"
                          placeholder="选择开始时间"
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                );
              }
              
              return null;
            }}
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.strategy_type !== currentValues.strategy_type}
          >
            {({ getFieldValue }) => {
              const strategyType = getFieldValue('strategy_type');
              
              if (strategyType === 'recurring') {
                return (
                  <Form.Item
                    name="end_time"
                    label="结束时间"
                  >
                    <DatePicker
                      showTime
                      format="YYYY-MM-DD HH:mm:ss"
                      placeholder="选择结束时间（可选）"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                );
              }
              
              return null;
            }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default StrategyManagement;
