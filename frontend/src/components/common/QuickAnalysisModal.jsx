import React, { useState, useEffect } from 'react';
import { Modal, Button, Checkbox, Space, Typography, Alert, Spin, message, Collapse } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const { Text } = Typography;

const QuickAnalysisModal = ({ visible, onCancel, device, backup, onAnalysisComplete }) => {
  const [selectedDimensions, setSelectedDimensions] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  // 分析维度选项 - 修复维度映射
  const dimensionOptions = [
    { label: '🔒 安全加固', value: 'security' },
    { label: '🔄 冗余高可用', value: 'redundancy' },
    { label: '⚡ 性能优化', value: 'performance' },
    { label: '✅ 配置健全性', value: 'integrity' },
    { label: '📋 最佳实践', value: 'best_practices' }, // 修复：使用复数形式
  ];

  // 维度信息映射
  const dimensionInfoMap = {
    'security': { icon: '🔒', name: '安全加固' },
    'redundancy': { icon: '🔄', name: '冗余高可用' },
    'performance': { icon: '⚡', name: '性能优化' },
    'integrity': { icon: '✅', name: '配置健全性' },
    'best_practices': { icon: '📋', name: '最佳实践' }
  };

  // 默认不选择任何维度
  useEffect(() => {
    if (visible) {
      setSelectedDimensions([]);
      setAnalysisResult(null);
      setShowResult(false);
    }
  }, [visible]);

  // 开始分析
  const startAnalysis = async () => {
    if (selectedDimensions.length === 0) {
      message.warning('请至少选择一个分析维度');
      return;
    }

    setAnalyzing(true);
    try {
      // 调用后端API - 修复API路径
      const response = await fetch('http://localhost:8000/api/analysis/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_id: device.id,
          backup_id: backup.id,
          dimensions: selectedDimensions
        }),
      });

      const result = await response.json();

      if (result.success) {
        message.success('分析完成');
        setAnalysisResult(result.data);
        setShowResult(true);
        if (onAnalysisComplete) {
          onAnalysisComplete(result.data);
        }
      } else {
        // 修复undefined问题，提供默认错误信息
        const errorMessage = result.message || '未知错误';
        message.error(`分析失败: ${errorMessage}`);
      }
    } catch (error) {
      console.error('AI分析错误:', error);
      message.error('分析失败，请检查AI配置');
    } finally {
      setAnalyzing(false);
    }
  };

  // 全选/取消全选 - 修复逻辑
  const handleSelectAll = (checked) => {
    if (checked) {
      // 如果当前不是全选状态，则全选
      setSelectedDimensions(dimensionOptions.map(option => option.value));
    } else {
      // 如果当前是全选状态，则全部取消
      setSelectedDimensions([]);
    }
  };

  const allSelected = selectedDimensions.length === dimensionOptions.length;
  const indeterminate = selectedDimensions.length > 0 && selectedDimensions.length < dimensionOptions.length;

  return (
    <>
      {/* 分析选择弹窗 */}
      <Modal
        title={
          <Space>
            <RobotOutlined />
            快速AI分析
          </Space>
        }
        open={visible && !showResult}
        onCancel={onCancel}
        footer={[
          <Button key="cancel" onClick={onCancel}>
            取消
          </Button>,
          <Button
            key="analyze"
            type="primary"
            icon={<RobotOutlined />}
            loading={analyzing}
            onClick={startAnalysis}
            disabled={selectedDimensions.length === 0}
          >
            开始分析
          </Button>
        ]}
        width={500}
      >
        <div>
          <Alert
            message="分析目标"
            description={`${device?.name} - ${backup?.backup_type}`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <div style={{ marginBottom: 16 }}>
            <Text strong>选择分析维度：</Text>
            <div style={{ marginTop: 8 }}>
              <Checkbox
                indeterminate={indeterminate}
                onChange={handleSelectAll}
                checked={allSelected}
              >
                全选
              </Checkbox>
            </div>
            <div style={{ marginTop: 8 }}>
              <Checkbox.Group
                options={dimensionOptions}
                value={selectedDimensions}
                onChange={setSelectedDimensions}
              />
            </div>
          </div>

          <Alert
            message="分析说明"
            description="AI将根据选择的维度分析配置，生成详细的分析报告和改进建议。分析结果将保存到历史记录中。"
            type="info"
            showIcon
          />

          {analyzing && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Spin size="large" />
              <div style={{ marginTop: 8 }}>
                <Text>正在分析配置，请稍候...</Text>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* 分析结果弹窗 - 与AI分析历史查看结果保持一致 */}
      <Modal
        title="AI分析结果"
        open={showResult}
        onCancel={() => {
          setShowResult(false);
          onCancel();
        }}
        width={800}
        footer={[
          <Button key="close" onClick={() => {
            setShowResult(false);
            onCancel();
          }}>
            关闭
          </Button>,
          <Button 
            key="new" 
            type="primary"
            onClick={() => {
              setShowResult(false);
              setAnalysisResult(null);
            }}
          >
            新的分析
          </Button>
        ]}
      >
        {analysisResult && (
          <div>
            <Alert
              message="分析完成"
              description={`${device?.name} - ${backup?.backup_type} 配置分析已完成，已分析 ${selectedDimensions.length} 个维度`}
              type="success"
              showIcon
              style={{ marginBottom: '16px' }}
            />
            
            <Collapse defaultActiveKey={selectedDimensions}>
              {selectedDimensions.map(dimension => {
                const dimensionInfo = dimensionInfoMap[dimension];
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
    </>
  );
};

export default QuickAnalysisModal;
