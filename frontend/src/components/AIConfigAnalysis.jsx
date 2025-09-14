import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Select,
  message,
  Space,
  Typography,
  Row,
  Col,
  Alert,
  Tag,
  Modal,
  Collapse,
  Checkbox,
  List,
  Popconfirm,
} from 'antd';
import {
  PlayCircleOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import { deviceAPI, backupAPI, analysisAPI, configAPI } from '../services/api';
import dayjs from 'dayjs';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const { Text } = Typography;

const AIConfigAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [showResultModal, setShowResultModal] = useState(false);
  const [devices, setDevices] = useState([]);
  const [backups, setBackups] = useState([]);
  
  // 分析维度选择
  const [selectedDimensions, setSelectedDimensions] = useState([
    'security', 'redundancy', 'performance', 'integrity', 'best_practices'
  ]);

  // 分析维度配置
  const analysisDimensions = [
    {
      key: 'security',
      name: '安全加固',
      description: '检查配置中的安全漏洞和加固建议',
      icon: '🔒'
    },
    {
      key: 'redundancy',
      name: '冗余与高可用',
      description: '分析冗余配置和高可用性设置',
      icon: '🔄'
    },
    {
      key: 'performance',
      name: '性能优化',
      description: '识别性能瓶颈和优化建议',
      icon: '⚡'
    },
    {
      key: 'integrity',
      name: '配置健全性',
      description: '检查配置的完整性和一致性',
      icon: '✅'
    },
    {
      key: 'best_practices',
      name: '最佳实践',
      description: '园区网配置最佳实践建议',
      icon: '📋'
    }
  ];

  // 备份类型映射（与系统保持一致）
  const backupTypeMap = {
    'running-config': '运行配置',
    'startup-config': '启动配置', 
    'ip-route': '路由表',
    'arp-table': 'ARP表',
    'mac-table': 'MAC表',
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

  // 获取备份列表
  const fetchBackups = async (deviceId) => {
    if (!deviceId) {
      setBackups([]);
      return;
    }
    
    try {
      const data = await backupAPI.getBackups(deviceId);
      setBackups(data);
    } catch (error) {
      message.error('获取备份列表失败');
    }
  };

  // 获取分析历史
  const fetchAnalysisHistory = async () => {
    setLoading(true);
    try {
      const data = await analysisAPI.getAnalysisHistory();
      setAnalysisHistory(data);
    } catch (error) {
      message.error('获取分析历史失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取当前AI配置
  const getCurrentAIConfig = async () => {
    try {
      const config = await configAPI.getAIConfig();
      return config;
    } catch (error) {
      // 获取AI配置失败
      return null;
    }
  };

  // 查看分析结果
  const viewAnalysisResult = async (recordId) => {
    try {
      const response = await analysisAPI.getAnalysisResult(recordId);
      // 后端直接返回数据对象，不是 {success: true, data: {...}} 格式
      if (response && response.result) {
        setAnalysisResult(response.result);
        setShowResultModal(true);
      } else {
        message.error('获取分析结果失败');
      }
    } catch (error) {
      message.error('获取分析结果失败');
    }
  };

  // 删除单个分析记录
  const handleDeleteRecord = async (recordId) => {
    try {
      const result = await analysisAPI.deleteAnalysisRecord(recordId);
      if (result.success) {
        message.success('删除成功');
        fetchAnalysisHistory(); // 刷新历史列表
      } else {
        message.error(result.message || '删除失败');
      }
    } catch (error) {
      // 删除分析记录失败
      message.error('删除失败，请稍后重试');
    }
  };

  // 清空所有分析记录
  const handleClearAllRecords = async () => {
    try {
      const result = await analysisAPI.deleteAllAnalysisRecords();
      if (result.success) {
        message.success(result.message || '清空成功');
        fetchAnalysisHistory(); // 刷新历史列表
      } else {
        message.error(result.message || '清空失败');
      }
    } catch (error) {
      // 清空分析记录失败
      message.error('清空失败，请稍后重试');
    }
  };

  useEffect(() => {
    fetchDevices();
    fetchAnalysisHistory();
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      fetchBackups(selectedDevice);
    } else {
      setBackups([]);
      setSelectedBackup(null);
    }
  }, [selectedDevice]);

  // 开始分析
  const handleAnalyze = async () => {
    if (!selectedDevice || !selectedBackup) {
      message.error('请选择设备和备份文件');
      return;
    }

    if (selectedDimensions.length === 0) {
      message.error('请至少选择一个分析维度');
      return;
    }

    setLoading(true);
    try {
      // 获取当前AI配置
      const aiConfig = await getCurrentAIConfig();
      
      const response = await analysisAPI.analyzeConfig({
        device_id: selectedDevice,
        backup_id: selectedBackup,
        dimensions: selectedDimensions,
        ai_config: aiConfig  // 传递当前AI配置
      });

      if (response.success) {
        setAnalysisResult(response.data);
        setShowResultModal(true);
        message.success('分析完成');
        fetchAnalysisHistory();
      } else {
        message.error(response.message || '分析失败');
      }
    } catch (error) {
      message.error('分析失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理维度选择变化
  const handleDimensionChange = (checkedValues) => {
    setSelectedDimensions(checkedValues);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="AI配置分析" extra={
        <Space>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchAnalysisHistory}
          >
            刷新历史
          </Button>
          <Popconfirm
            title="确定要清空所有分析记录吗？"
            description="此操作将删除所有分析历史，无法恢复。"
            onConfirm={handleClearAllRecords}
            okText="确定"
            cancelText="取消"
            okType="danger"
          >
            <Button 
              danger
              icon={<ClearOutlined />} 
            >
              清空全部分析
            </Button>
          </Popconfirm>
        </Space>
      }>
        <Row gutter={[24, 24]}>
          {/* AI分析区域 */}
          <Col span={12}>
            <Card title="AI分析" size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>选择设备:</div>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="选择要分析的设备"
                    value={selectedDevice}
                    onChange={setSelectedDevice}
                    onFocus={fetchDevices}
                  >
                    {devices.map(device => (
                      <Select.Option key={device.id} value={device.id}>
                        {device.name} ({device.ip_address})
                      </Select.Option>
                    ))}
                  </Select>
                </div>

                <div>
                  <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>选择备份:</div>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="选择要分析的备份文件"
                    value={selectedBackup}
                    onChange={setSelectedBackup}
                    onFocus={() => selectedDevice && fetchBackups(selectedDevice)}
                    disabled={!selectedDevice}
                  >
                    {backups.map(backup => (
                      <Select.Option key={backup.id} value={backup.id}>
                        {backupTypeMap[backup.backup_type] || backup.backup_type} - {dayjs(backup.created_at).format('YYYY-MM-DD HH:mm')}
                      </Select.Option>
                    ))}
                  </Select>
                </div>

                {/* 分析维度选择 */}
                <div>
                  <div style={{ marginBottom: '12px', fontWeight: 'bold' }}>分析维度:</div>
                  <div style={{ 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px', 
                    padding: '16px',
                    backgroundColor: '#fafafa'
                  }}>
                    <Checkbox.Group 
                      value={selectedDimensions}
                      onChange={handleDimensionChange}
                      style={{ width: '100%' }}
                    >
                      <Row gutter={[16, 12]}>
                        {analysisDimensions.map(dimension => (
                          <Col span={24} key={dimension.key}>
                            <Checkbox value={dimension.key} style={{ width: '100%' }}>
                              <div style={{ 
                                display: 'flex', 
                                alignItems: 'flex-start',
                                padding: '8px',
                                borderRadius: '4px',
                                backgroundColor: 'white',
                                border: '1px solid #e8e8e8'
                              }}>
                                <span style={{ 
                                  fontSize: '20px', 
                                  marginRight: '12px',
                                  marginTop: '2px'
                                }}>
                                  {dimension.icon}
                                </span>
                                <div style={{ flex: 1 }}>
                                  <div style={{ 
                                    fontWeight: 'bold', 
                                    fontSize: '14px',
                                    marginBottom: '4px',
                                    color: '#262626'
                                  }}>
                                    {dimension.name}
                                  </div>
                                  <div style={{ 
                                    fontSize: '12px', 
                                    color: '#8c8c8c',
                                    lineHeight: '1.4'
                                  }}>
                                    {dimension.description}
                                  </div>
                                </div>
                              </div>
                            </Checkbox>
                          </Col>
                        ))}
                      </Row>
                    </Checkbox.Group>
                    
                    <div style={{ marginTop: '12px', textAlign: 'center' }}>
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setSelectedDimensions(analysisDimensions.map(d => d.key))}
                      >
                        全选
                      </Button>
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setSelectedDimensions([])}
                      >
                        清空
                      </Button>
                    </div>
                  </div>
                </div>

                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  loading={loading}
                  onClick={handleAnalyze}
                  disabled={!selectedDevice || !selectedBackup || selectedDimensions.length === 0}
                  style={{ width: '100%', height: '40px' }}
                >
                  开始分析 ({selectedDimensions.length} 个维度)
                </Button>
              </Space>
            </Card>
          </Col>

          {/* 分析历史区域 */}
          <Col span={12}>
            <Card title="分析历史" size="small">
              <List
                dataSource={analysisHistory}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        size="small"
                        onClick={() => viewAnalysisResult(item.id)}
                      >
                        查看结果
                      </Button>,
                      <Popconfirm
                        title="确定要删除这条分析记录吗？"
                        description="此操作无法恢复。"
                        onConfirm={() => handleDeleteRecord(item.id)}
                        okText="确定"
                        cancelText="取消"
                        okType="danger"
                      >
                        <Button
                          type="link"
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                        >
                          删除
                        </Button>
                      </Popconfirm>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                      title={
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                            {item.device_name || `设备 ${item.device_id}`} ({item.device_ip || '未知IP'})
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            {backupTypeMap[item.backup_type] || item.backup_type || '未知类型'} - {item.backup_created_at ? dayjs(item.backup_created_at).format('YYYY-MM-DD HH:mm') : '未知时间'}
                          </div>
                        </div>
                      }
                      description={
                        <div>
                          <div style={{ marginBottom: '4px' }}>
                            <div style={{ 
                              display: 'flex', 
                              flexWrap: 'wrap', 
                              gap: '4px',
                              maxWidth: '200px' // 限制最大宽度，避免与按钮重叠
                            }}>
                              {item.dimensions && item.dimensions.length > 0 ? (
                                item.dimensions.map(dim => {
                                  const dimInfo = analysisDimensions.find(d => d.key === dim);
                                  return (
                                    <Tag key={dim} color="blue" size="small">
                                      {dimInfo?.icon} {dimInfo?.name}
                                    </Tag>
                                  );
                                })
                              ) : (
                                <Tag color="blue" size="small">全部维度</Tag>
                              )}
                            </div>
                          </div>
                          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                            {dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 分析结果模态框 */}
      <Modal
        title="AI分析结果"
        open={showResultModal}
        onCancel={() => setShowResultModal(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setShowResultModal(false)}>
            关闭
          </Button>
        ]}
      >
        {analysisResult && (
          <div>
            <Alert
              message="分析完成"
              description={`已分析 ${selectedDimensions.length} 个维度`}
              type="success"
              showIcon
              style={{ marginBottom: '16px' }}
            />
            
            <Collapse defaultActiveKey={selectedDimensions}>
              {selectedDimensions.map(dimension => {
                const dimensionInfo = analysisDimensions.find(d => d.key === dimension);
                const result = analysisResult[dimension];
                
                return (
                  <Collapse.Panel 
                    key={dimension} 
                    header={
                      <Space>
                        <span>{dimensionInfo?.icon}</span>
                        <span>{dimensionInfo?.name}</span>
                      </Space>
                    }
                  >
                    {result ? (
                      <div>
                        <div style={{ 
                          lineHeight: '1.6',
                          fontSize: '14px'
                        }}>
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h1: ({node, ...props}) => <h1 style={{fontSize: '20px', marginTop: '16px', marginBottom: '12px'}} {...props} />,
                              h2: ({node, ...props}) => <h2 style={{fontSize: '18px', marginTop: '14px', marginBottom: '10px'}} {...props} />,
                              h3: ({node, ...props}) => <h3 style={{fontSize: '16px', marginTop: '12px', marginBottom: '8px'}} {...props} />,
                              p: ({node, ...props}) => <p style={{marginBottom: '8px'}} {...props} />,
                              ul: ({node, ...props}) => <ul style={{marginBottom: '8px', paddingLeft: '20px'}} {...props} />,
                              ol: ({node, ...props}) => <ol style={{marginBottom: '8px', paddingLeft: '20px'}} {...props} />,
                              li: ({node, ...props}) => <li style={{marginBottom: '4px'}} {...props} />,
                              code: ({node, inline, ...props}) => 
                                inline ? 
                                  <code style={{backgroundColor: '#f5f5f5', padding: '2px 4px', borderRadius: '3px', fontSize: '13px'}} {...props} /> :
                                  <code style={{backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px', display: 'block', fontSize: '13px', marginBottom: '8px'}} {...props} />,
                              pre: ({node, ...props}) => <pre style={{backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px', overflow: 'auto', marginBottom: '8px'}} {...props} />,
                              blockquote: ({node, ...props}) => <blockquote style={{borderLeft: '4px solid #d9d9d9', paddingLeft: '12px', margin: '8px 0', color: '#666'}} {...props} />,
                              table: ({node, ...props}) => <table style={{borderCollapse: 'collapse', width: '100%', marginBottom: '8px'}} {...props} />,
                              th: ({node, ...props}) => <th style={{border: '1px solid #d9d9d9', padding: '8px', backgroundColor: '#fafafa', textAlign: 'left'}} {...props} />,
                              td: ({node, ...props}) => <td style={{border: '1px solid #d9d9d9', padding: '8px'}} {...props} />,
                            }}
                          >
                            {result}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <div style={{ color: '#8c8c8c', fontStyle: 'italic' }}>
                        该维度暂无分析结果
                      </div>
                    )}
                  </Collapse.Panel>
                );
              })}
            </Collapse>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AIConfigAnalysis;
