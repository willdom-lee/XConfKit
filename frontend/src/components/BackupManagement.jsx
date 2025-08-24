import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Select,
  message,
  Popconfirm,
  Tag,
  Space,
  Card,
  Row,
  Col,
  Typography,
  Modal,
  Tooltip,
  Divider,
} from 'antd';
import {
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  CopyOutlined,
  InfoCircleOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { deviceAPI, backupAPI } from '../services/api';
import dayjs from 'dayjs';
import QuickAnalysisModal from './common/QuickAnalysisModal';

const { Title, Text } = Typography;
const { Option } = Select;

const BackupManagement = () => {
  const [devices, setDevices] = useState([]);
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [backupType, setBackupType] = useState('running-config');
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [backupContent, setBackupContent] = useState('');
  const [contentLoading, setContentLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  // 筛选相关状态
  const [filterDevice, setFilterDevice] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [filterType, setFilterType] = useState(null);
  
  // AI分析相关状态
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const [selectedAnalysisBackup, setSelectedAnalysisBackup] = useState(null);

  // 备份类型映射（与系统保持一致）
  const backupTypeMap = {
    'running-config': '运行配置',
    'startup-config': '启动配置', 
    'ip-route': '路由表',
    'arp-table': 'ARP表',
    'mac-table': 'MAC表',
  };

  // 备份类型对应的命令信息
  const backupCommandMap = {
    'running-config': {
      h3c: 'display current-configuration',
      cisco: 'show running-config',
      huawei: 'display current-configuration',
      description: '获取设备当前运行的配置信息'
    },
    'startup-config': {
      h3c: 'display saved-configuration',
      cisco: 'show startup-config', 
      huawei: 'display saved-configuration',
      description: '获取设备启动配置信息'
    },
    'ip-route': {
      h3c: 'display ip routing-table',
      cisco: 'show ip route',
      huawei: 'display ip routing-table',
      description: '获取设备路由表信息'
    },
    'arp-table': {
      h3c: 'display arp',
      cisco: 'show arp',
      huawei: 'display arp',
      description: '获取设备ARP表信息'
    },
    'mac-table': {
      h3c: 'display mac-address',
      cisco: 'show mac address-table',
      huawei: 'display mac-address',
      description: '获取设备MAC地址表信息'
    },
  };

  // 获取设备列表
  const fetchDevices = async () => {
    try {
      const data = await deviceAPI.getDevices();
      setDevices(data);
    } catch (error) {
      message.error('获取设备列表失败');
    }
  };

  // 获取备份记录
  const fetchBackups = async () => {
    setLoading(true);
    try {
      const data = await backupAPI.getBackups();
      setBackups(data);
    } catch (error) {
      message.error('获取备份记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    fetchBackups();
  }, []);

  // 筛选备份记录
  const getFilteredBackups = () => {
    let filtered = backups;
    
    if (filterDevice) {
      filtered = filtered.filter(backup => backup.device?.id === filterDevice);
    }
    
    if (filterStatus) {
      filtered = filtered.filter(backup => backup.status === filterStatus);
    }
    
    if (filterType) {
      filtered = filtered.filter(backup => backup.backup_type === filterType);
    }
    
    return filtered;
  };

  // 清除所有筛选
  const clearFilters = () => {
    setFilterDevice(null);
    setFilterStatus(null);
    setFilterType(null);
  };

  // 获取筛选后的备份记录
  const filteredBackups = getFilteredBackups();

  // 执行备份
  const executeBackup = async () => {
    if (!selectedDevice) {
      message.warning('请先选择设备');
      return;
    }

    setBackupLoading(true);
    try {
      const result = await backupAPI.executeBackup(selectedDevice, backupType);
      
      if (result && typeof result === 'object') {
        if (result.success === true) {
          message.success('备份执行成功');
          fetchBackups();
        } else {
          message.error(`备份执行失败: ${result.message || '未知错误'}`);
        }
      } else {
        message.error('备份执行失败: 响应格式错误');
      }
    } catch (error) {
      message.error(`备份执行失败: ${error.message || '网络错误'}`);
    } finally {
      setBackupLoading(false);
    }
  };

  // 删除备份
  const handleDeleteBackup = async (backupId) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条备份记录吗？',
      onOk: async () => {
        try {
          await backupAPI.deleteBackup(backupId);
          message.success('备份记录删除成功');
          fetchBackups();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 批量删除备份
  const batchDeleteBackups = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的备份记录');
      return;
    }

    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 条备份记录吗？`,
      onOk: async () => {
        try {
          const result = await backupAPI.batchDeleteBackups(selectedRowKeys);
          if (result.success) {
            message.success(result.message);
            setSelectedRowKeys([]);
            fetchBackups();
          } else {
            message.error('批量删除失败');
          }
        } catch (error) {
          message.error('批量删除失败');
        }
      }
    });
  };

  // 查看备份内容
  const viewBackup = async (backup) => {
    setSelectedBackup(backup);
    setViewModalVisible(true);
    setContentLoading(true);
    setBackupContent('');
    
    try {
      const result = await backupAPI.getBackupContent(backup.id);
      if (result.success) {
        setBackupContent(result.content);
      } else {
        message.error('获取备份内容失败');
      }
    } catch (error) {
      message.error('获取备份内容失败');
    } finally {
      setContentLoading(false);
    }
  };

  // 下载备份文件
  const downloadBackup = async (backup) => {
    if (backup.status !== 'success' && backup.status !== 'completed') {
      message.warning('只能下载成功的备份文件');
      return;
    }
    
    if (!backup.file_path) {
      message.warning('备份文件不存在');
      return;
    }
    
    try {
      setContentLoading(true);
      
      const response = await backupAPI.downloadBackup(backup.id);
      
      const blob = new Blob([response], { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const fileName = backup.file_path ? backup.file_path.split('/').pop() : `backup_${backup.id}.txt`;
      link.download = fileName;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(url);
      
      message.success(`文件 ${fileName} 下载成功`);
    } catch (error) {
      if (error.response?.status === 404) {
        message.error('备份文件不存在或已被删除');
      } else if (error.response?.status === 500) {
        message.error('服务器错误，请稍后重试');
      } else {
        message.error('文件下载失败，请检查网络连接');
      }
    } finally {
      setContentLoading(false);
    }
  };

  // 复制配置内容到剪贴板
  const copyBackupContent = async (backup) => {
    if (backup.status !== 'success' && backup.status !== 'completed') {
      message.warning('只能复制成功的备份内容');
      return;
    }
    
    try {
      setContentLoading(true);
      
      const result = await backupAPI.getBackupContent(backup.id);
      if (result.success) {
        await navigator.clipboard.writeText(result.content);
        message.success('配置内容已复制到剪贴板');
      } else {
        message.error('获取备份内容失败');
      }
    } catch (error) {
      message.error('复制失败，请手动复制');
    } finally {
      setContentLoading(false);
    }
  };

  // 打开AI分析弹窗
  const openAnalysisModal = (backup) => {
    setSelectedAnalysisBackup(backup);
    setAnalysisModalVisible(true);
  };

  // AI分析完成回调
  const handleAnalysisComplete = (result) => {
    // 可以在这里处理分析完成后的逻辑
    // 分析完成处理逻辑
  };

  // 表格列定义
  const columns = [
    {
      title: '设备',
      dataIndex: 'device',
      key: 'device',
      width: 120,
      render: (device) => device?.name || '-',
    },
    {
      title: '备份类型',
      dataIndex: 'backup_type',
      key: 'backup_type',
      width: 120,
      render: (type) => {
        const displayName = backupTypeMap[type] || type;
        const commandInfo = backupCommandMap[type];
        
        return (
          <div>
            <div style={{ fontWeight: 'bold' }}>{displayName}</div>
            {commandInfo && (
              <Tooltip title={
                <div>
                  <div><strong>命令说明：</strong>{commandInfo.description}</div>
                  <Divider style={{ margin: '4px 0' }} />
                  <div><strong>H3C命令：</strong>{commandInfo.h3c}</div>
                  <div><strong>Cisco命令：</strong>{commandInfo.cisco}</div>
                  <div><strong>华为命令：</strong>{commandInfo.huawei}</div>
                </div>
              }>
                <Text type="secondary" style={{ fontSize: '12px', cursor: 'help' }}>
                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                  查看命令
                </Text>
              </Tooltip>
            )}
          </div>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const statusMap = {
          pending: { color: 'processing', text: '进行中' },
          success: { color: 'success', text: '成功' },
          completed: { color: 'success', text: '成功' },
          failed: { color: 'error', text: '失败' },
        };
        const config = statusMap[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size) => {
        if (!size) return '-';
        const kb = size / 1024;
        return kb > 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${kb.toFixed(2)} KB`;
      },
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
      width: 250,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewBackup(record)}
            disabled={record.status !== 'success' && record.status !== 'completed'}
          >
            查看
          </Button>
          <Button
            size="small"
            icon={<CopyOutlined />}
            onClick={() => copyBackupContent(record)}
            disabled={record.status !== 'success' && record.status !== 'completed'}
          >
            复制
          </Button>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => downloadBackup(record)}
            disabled={record.status !== 'success' && record.status !== 'completed'}
          >
            下载
          </Button>
          <Button
            size="small"
            icon={<RobotOutlined />}
            onClick={() => openAnalysisModal(record)}
            disabled={record.status !== 'success' && record.status !== 'completed'}
          >
            AI分析
          </Button>
          <Popconfirm
            title="确定要删除这个备份记录吗？"
            onConfirm={() => handleDeleteBackup(record.id)}
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
        <Title level={2}>备份管理</Title>
        <Text type="secondary">执行设备配置备份和查看备份记录</Text>
      </div>

      {/* 备份操作区域 */}
      <Card title="执行备份" style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col span={6}>
            <Text>选择设备：</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              placeholder="请选择设备"
              value={selectedDevice}
              onChange={(value) => {
                setSelectedDevice(value);
              }}
            >
              {devices.map(device => (
                <Option key={device.id} value={device.id}>
                  {device.name} ({device.ip_address})
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={6}>
            <Text>备份类型：</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              value={backupType}
              onChange={(value) => {
                setBackupType(value);
              }}
            >
              {Object.entries(backupTypeMap).map(([key, value]) => (
                <Option key={key} value={key}>
                  {value}
                </Option>
              ))}
            </Select>
            {backupCommandMap[backupType] && (
              <div style={{ marginTop: 4, fontSize: '12px', color: '#8c8c8c' }}>
                {backupCommandMap[backupType].description}
              </div>
            )}
          </Col>
          <Col span={6}>
            <Button
              type="primary"
              icon={<CloudUploadOutlined />}
              loading={backupLoading}
              onClick={() => {
                executeBackup();
              }}
              disabled={!selectedDevice}
              style={{ marginTop: 32 }}
            >
              执行备份
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 备份记录表格 */}
      <Card title="备份记录">
        {/* 筛选区域 */}
        <div style={{ marginBottom: 16, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
          <Row gutter={16} align="middle">
            <Col span={6}>
              <Text strong>设备筛选：</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="选择设备"
                value={filterDevice}
                onChange={setFilterDevice}
                allowClear
              >
                {devices.map(device => (
                  <Option key={device.id} value={device.id}>
                    {device.name} ({device.ip_address})
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Text strong>状态筛选：</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="选择状态"
                value={filterStatus}
                onChange={setFilterStatus}
                allowClear
              >
                <Option value="success">成功</Option>
                <Option value="failed">失败</Option>
                <Option value="pending">进行中</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Text strong>类型筛选：</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="选择备份类型"
                value={filterType}
                onChange={setFilterType}
                allowClear
              >
                {Object.entries(backupTypeMap).map(([key, value]) => (
                  <Option key={key} value={key}>
                    {value}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Space style={{ marginTop: 32 }}>
                <Button
                  onClick={() => fetchBackups()}
                  disabled={loading}
                >
                  刷新
                </Button>
                <Button
                  onClick={clearFilters}
                  disabled={!filterDevice && !filterStatus && !filterType}
                >
                  清除筛选
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {/* 操作区域 */}
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Text type="secondary">
              提示：勾选左侧复选框可选择多条记录进行批量删除
            </Text>
            {(filterDevice || filterStatus || filterType) && (
              <Text type="secondary">
                已筛选：{filteredBackups.length} 条记录
              </Text>
            )}
          </Space>
          {selectedRowKeys.length > 0 && (
            <Space>
              <Text strong style={{ color: '#ff4d4f' }}>
                已选择 {selectedRowKeys.length} 条记录
              </Text>
              <Button 
                danger 
                icon={<DeleteOutlined />}
                onClick={batchDeleteBackups}
              >
                批量删除
              </Button>
            </Space>
          )}
        </div>
        
        <Table
          className="backup-table"
          columns={columns}
          dataSource={filteredBackups}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            selections: [
              {
                key: 'all',
                text: '全选',
                onSelect: () => setSelectedRowKeys(filteredBackups.map(item => item.id))
              },
              {
                key: 'none',
                text: '取消全选',
                onSelect: () => setSelectedRowKeys([])
              }
            ]
          }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 查看备份内容模态框 */}
      <Modal
        title={
          <div>
            <div>备份内容</div>
            {selectedBackup && (
              <div style={{ fontSize: '14px', fontWeight: 'normal', color: '#8c8c8c', marginTop: 4 }}>
                {selectedBackup.device?.name} - {backupTypeMap[selectedBackup.backup_type]}
              </div>
            )}
          </div>
        }
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={() => {
            if (backupContent) {
              navigator.clipboard.writeText(backupContent);
              message.success('配置内容已复制到剪贴板');
            }
          }}>
            复制内容
          </Button>,
          <Button key="download" icon={<DownloadOutlined />} onClick={() => {
            if (selectedBackup) {
              downloadBackup(selectedBackup);
            }
          }}>
            下载文件
          </Button>,
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
        style={{ top: 20 }}
      >
        {selectedBackup && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Text strong>设备：</Text> {selectedBackup.device?.name}
                </Col>
                <Col span={8}>
                  <Text strong>备份类型：</Text> {backupTypeMap[selectedBackup.backup_type]}
                </Col>
                <Col span={8}>
                  <Text strong>备份时间：</Text> {dayjs(selectedBackup.created_at).format('YYYY-MM-DD HH:mm:ss')}
                </Col>
              </Row>
              
              {backupCommandMap[selectedBackup.backup_type] && (
                <div style={{ marginTop: 12, padding: '8px 12px', background: '#f6ffed', borderRadius: 4, border: '1px solid #b7eb8f' }}>
                  <Text strong>使用的命令：</Text>
                  <div style={{ marginTop: 4, fontSize: '12px' }}>
                    <div>H3C: {backupCommandMap[selectedBackup.backup_type].h3c}</div>
                    <div>Cisco: {backupCommandMap[selectedBackup.backup_type].cisco}</div>
                    <div>华为: {backupCommandMap[selectedBackup.backup_type].huawei}</div>
                  </div>
                </div>
              )}
            </div>
            
            {/* 备份信息 */}
            <div style={{ 
              marginBottom: 16, 
              padding: '8px 12px', 
              background: '#f0f0f0', 
              borderRadius: 4,
              fontSize: 12
            }}>
              <Text>总行数: {backupContent ? backupContent.split('\n').length : 0} 行 | 文件大小: {selectedBackup?.file_size || 0} 字节</Text>
            </div>
            
            {contentLoading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Text>正在加载备份内容...</Text>
              </div>
            ) : backupContent ? (
              <div 
                style={{ 
                  background: '#f5f5f5', 
                  padding: 16, 
                  borderRadius: 4,
                  maxHeight: 600,
                  overflow: 'auto',
                  border: '1px solid #d9d9d9'
                }}
              >
                <pre style={{ 
                  margin: 0, 
                  fontSize: 12, 
                  lineHeight: '1.5',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all'
                }}>
                  {backupContent}
                </pre>
              </div>
            ) : (
              <div style={{ color: '#8c8c8c', textAlign: 'center', padding: 40 }}>
                备份内容不存在或无法读取
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* AI分析弹窗 */}
      <QuickAnalysisModal
        visible={analysisModalVisible}
        onCancel={() => {
          setAnalysisModalVisible(false);
          setSelectedAnalysisBackup(null);
        }}
        device={selectedAnalysisBackup?.device}
        backup={selectedAnalysisBackup}
        onAnalysisComplete={handleAnalysisComplete}
      />
    </div>
  );
};

export default BackupManagement;
