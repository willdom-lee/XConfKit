import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  message,
  Space,
  Typography,
  Alert,
  Tag,
  Tooltip,
  Collapse,
  Select,
  Modal,
  Row,
  Col,
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { configAPI } from '../services/api';

const { Title, Text } = Typography;
const { Panel } = Collapse;

const SystemConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [aiTesting, setAiTesting] = useState(false);

  const [aiConfig, setAiConfig] = useState({});
  const [prompts, setPrompts] = useState({});

  // AI服务商预设配置 (仅支持阿里云通义千问)
  const aiProviderConfigs = {
    alibaba: {
      name: '阿里云通义千问',
      icon: '☁️',
      description: '阿里云AI服务，中文理解能力强，稳定可靠',
      base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      models: [
        { value: 'qwen-turbo', label: '通义千问 Turbo (快速)' },
        { value: 'qwen-plus', label: '通义千问 Plus (平衡)' },
        { value: 'qwen-max', label: '通义千问 Max (最强)' },
        { value: 'qwen-max-longcontext', label: '通义千问 Max (长文本)' }
      ],
      default_model: 'qwen-turbo',
      api_key_placeholder: 'sk-...',
      api_key_description: '从阿里云控制台获取API密钥'
    }
  };

  // 加载配置
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const [aiConfigData, promptsData] = await Promise.all([
        configAPI.getAIConfig(),
        configAPI.getAnalysisPrompts()
      ]);
      
      setAiConfig(aiConfigData);
      setPrompts(promptsData);
      
      // 使用setTimeout确保状态更新完成后再设置表单值
      setTimeout(() => {
        // 设置表单初始值
        const formData = {};
        
        // 添加AI配置到表单数据
        if (aiConfigData) {
          formData.ai_provider = aiConfigData.provider || 'alibaba';
          formData.ai_model = aiConfigData.model || 'qwen-turbo';
          formData.ai_api_key = aiConfigData.api_key || '';
          formData.ai_base_url = aiConfigData.base_url || 'https://dashscope.aliyuncs.com/compatible-mode/v1';
          formData.ai_timeout = aiConfigData.timeout || 30;
          formData.ai_enable_cache = aiConfigData.enable_cache !== false;
        }
        
        console.log('最终表单数据:', formData);
        form.setFieldsValue(formData);
        console.log('表单值设置完成');
      }, 100);
      
    } catch (error) {
      message.error('加载配置失败');
      console.error('加载配置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    try {
      setLoading(true);
      
      // 获取表单数据
      const formData = form.getFieldsValue();
      console.log('保存配置 - 表单数据:', formData);
      
      // 分离AI配置
      const aiConfigData = {
        provider: formData.ai_provider,
        model: formData.ai_model,
        api_key: formData.ai_api_key,
        base_url: formData.ai_base_url,
        timeout: formData.ai_timeout,
        enable_cache: formData.ai_enable_cache,
        enable_history: formData.ai_enable_history,
        auto_retry: formData.ai_auto_retry
      };
      
      // 保存AI配置
      await configAPI.updateAIConfig(aiConfigData);
      
      message.success('AI配置保存成功');
      console.log('配置保存完成，准备重新加载配置');
      // 延迟重新加载，确保后端保存完成
      setTimeout(() => {
        console.log('开始重新加载配置');
        loadConfigs();
      }, 500);
    } catch (error) {
      console.error('保存配置失败:', error);
      console.error('错误详情:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      
      let errorMessage = '保存配置失败';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 处理AI服务商切换
  const handleProviderChange = (provider) => {
    const config = aiProviderConfigs[provider];
    if (config) {
      form.setFieldsValue({
        ai_base_url: config.base_url,
        ai_model: config.default_model,
        ai_api_key: config.api_key_placeholder
      });
    }
  };

  // 获取当前选中的AI服务商配置
  const getCurrentProviderConfig = () => {
    const currentProvider = form.getFieldValue('ai_provider') || 'alibaba';
    return aiProviderConfigs[currentProvider];
  };

  // 测试AI配置
  const testAIConfig = async () => {
    try {
      const values = await form.validateFields();
      
      // 检查必要字段
      if (!values.ai_provider) {
        message.error('请先选择AI服务提供商');
        return;
      }
      
      if (!values.ai_api_key || values.ai_api_key === getCurrentProviderConfig()?.api_key_placeholder) {
        message.error('请输入有效的API密钥');
        return;
      }
      
      if (!values.ai_model) {
        message.error('请先选择AI模型');
        return;
      }
      
      // 显示确认对话框
      const providerConfig = getCurrentProviderConfig();
      const confirmResult = await new Promise((resolve) => {
        Modal.confirm({
          title: '测试AI配置',
          content: (
            <div>
              <p>即将测试以下配置：</p>
              <ul>
                <li><strong>服务商：</strong>{providerConfig?.name}</li>
                <li><strong>模型：</strong>{values.ai_model}</li>
                <li><strong>API地址：</strong>{values.ai_base_url}</li>
                <li><strong>超时时间：</strong>{values.ai_timeout}秒</li>
              </ul>
              <p style={{ color: '#ff4d4f', marginTop: '8px' }}>
                ⚠️ 注意：测试将消耗少量API调用额度
              </p>
            </div>
          ),
          okText: '开始测试',
          cancelText: '取消',
          onOk: () => resolve(true),
          onCancel: () => resolve(false),
        });
      });
      
      if (!confirmResult) return;
      
      setAiTesting(true);
      
      const testConfig = {
        provider: values.ai_provider,
        api_key: values.ai_api_key,
        model: values.ai_model,
        base_url: values.ai_base_url,
        timeout: values.ai_timeout,
        enable_cache: values.ai_enable_cache
      };

      const result = await configAPI.testAIConnection(testConfig);
      
      if (result.success) {
        message.success('AI配置测试成功！连接正常');
      } else {
        // 提供更详细的错误信息
        let errorMessage = result.message || '未知错误';
        
        // 处理"连接失败:"前缀的情况
        if (errorMessage.startsWith('连接失败: ')) {
          const actualError = errorMessage.substring(6); // 移除"连接失败: "前缀
          try {
            // 尝试解析JSON错误信息
            const errorObj = JSON.parse(actualError);
            if (errorObj.error) {
              const errorCode = errorObj.error.code;
              const errorMsg = errorObj.error.message;
              
              // 根据错误代码提供具体建议
              if (errorCode === 'invalid_api_key' || errorMsg.includes('API key')) {
                errorMessage = 'API密钥无效，请检查密钥是否正确';
              } else if (errorCode === 'model_not_found') {
                errorMessage = '指定的模型不存在，请检查模型名称';
              } else if (errorCode === 'rate_limit') {
                errorMessage = 'API调用频率超限，请稍后重试';
              } else if (errorCode === 'quota_exceeded') {
                errorMessage = 'API配额已用完，请检查账户余额';
              } else {
                errorMessage = `API错误: ${errorMsg}`;
              }
            } else {
              errorMessage = `连接失败: ${actualError}`;
            }
          } catch (e) {
            // 如果不是JSON格式，直接使用错误信息
            errorMessage = `连接失败: ${actualError}`;
          }
        } else {
          // 处理其他错误类型
          if (errorMessage.includes('InvalidApiKey')) {
            errorMessage = 'API密钥无效，请检查密钥是否正确';
          } else if (errorMessage.includes('rate_limit')) {
            errorMessage = 'API调用频率超限，请稍后重试';
          } else if (errorMessage.includes('quota_exceeded')) {
            errorMessage = 'API配额已用完，请检查账户余额';
          } else if (errorMessage.includes('model_not_found')) {
            errorMessage = '指定的模型不存在，请检查模型名称';
          } else if (errorMessage.includes('network') || errorMessage.includes('timeout')) {
            errorMessage = '网络连接超时，请检查网络连接和API地址';
          }
        }
        
        message.error(`AI配置测试失败: ${errorMessage}`);
      }
    } catch (error) {
      console.error('AI配置测试失败:', error);
      
      // 提供更具体的错误信息
      let errorMessage = 'AI配置测试失败，请检查配置参数';
      if (error.message) {
        if (error.message.includes('fetch')) {
          errorMessage = '网络连接失败，请检查后端服务是否正常运行';
        } else if (error.message.includes('timeout')) {
          errorMessage = '请求超时，请检查网络连接';
        }
      }
      
      message.error(errorMessage);
    } finally {
      setAiTesting(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Form form={form} layout="vertical">
        <Card
          title={
            <Space>
              <SettingOutlined />
              <span>系统配置</span>
            </Space>
          }
          extra={
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadConfigs}
                loading={loading}
              >
                刷新
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={loading}
              >
                保存配置
              </Button>
            </Space>
          }
        >
          <div style={{ marginBottom: 16 }}>
            <Alert
              message="AI配置"
              description="配置AI分析服务、提示词等智能功能，其他系统配置由后台自动管理"
              type="info"
              showIcon
            />
          </div>
          
          <Card 
            title="AI服务配置" 
            size="small" 
            style={{ marginBottom: 16 }}
            extra={
              <Space>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  填写完整配置后可测试连接
                </Text>
                <Button
                  type="primary"
                  size="small"
                  onClick={testAIConfig}
                  loading={aiTesting}
                  icon={<RobotOutlined />}
                >
                  测试连接
                </Button>
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Form.Item
                  name="ai_provider"
                  label={
                    <Space>
                      <span>AI服务提供商</span>
                      <Tooltip title="选择您要使用的AI服务提供商">
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <Select
                    placeholder="选择AI服务提供商"
                    onChange={(value) => handleProviderChange(value)}
                    style={{ width: '100%' }}
                  >
                    {Object.entries(aiProviderConfigs).map(([key, config]) => (
                      <Select.Option key={key} value={key}>
                        <Space>
                          <span>{config.icon}</span>
                          <span>{config.name}</span>
                        </Space>
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>
                
                {/* 显示当前服务商描述 */}
                {getCurrentProviderConfig() && (
                  <div style={{ 
                    marginBottom: 16, 
                    padding: 12, 
                    backgroundColor: '#f6f8fa', 
                    borderRadius: 6,
                    border: '1px solid #e1e4e8'
                  }}>
                    <Text type="secondary">{getCurrentProviderConfig().description}</Text>
                  </div>
                )}
              </Col>
              
              <Col span={12}>
                <Form.Item
                  name="ai_model"
                  label={
                    <Space>
                      <span>AI模型</span>
                      <Tooltip title="选择具体的AI模型">
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <Select 
                    placeholder="选择AI模型"
                    style={{ width: '100%' }}
                  >
                    {getCurrentProviderConfig()?.models.map(model => (
                      <Select.Option key={model.value} value={model.value}>
                        {model.label}
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              
              <Col span={12}>
                <Form.Item
                  name="ai_timeout"
                  label={
                    <Space>
                      <span>请求超时时间</span>
                      <Tooltip title="API请求的超时时间">
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <InputNumber
                    min={10}
                    max={300}
                    placeholder="30"
                    addonAfter="秒"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              
              <Col span={24}>
                <Form.Item
                  name="ai_api_key"
                  label={
                    <Space>
                      <span>API密钥</span>
                      <Tooltip title={getCurrentProviderConfig()?.api_key_description}>
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <Input.Password 
                    placeholder={getCurrentProviderConfig()?.api_key_placeholder || "请输入您的API密钥"}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              
              <Col span={24}>
                <Form.Item
                  name="ai_base_url"
                  label={
                    <Space>
                      <span>API地址</span>
                      <Tooltip title="AI服务的API基础地址">
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <Input 
                    placeholder="请输入API基础地址"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              
              <Col span={12}>
                <Form.Item
                  name="ai_enable_cache"
                  label={
                    <Space>
                      <span>启用结果缓存</span>
                      <Tooltip title="缓存AI分析结果以提高响应速度">
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </Space>
                  }
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Card title="分析提示词" size="small">
            <Collapse>
              {Object.entries(prompts).map(([dimension, prompt]) => (
                <Panel
                  header={
                    <Space>
                      <span>{prompt.name}</span>
                      <Tag color="blue">{dimension}</Tag>
                    </Space>
                  }
                  key={dimension}
                >
                  <div style={{ marginBottom: 8 }}>
                    <Text type="secondary">{prompt.description}</Text>
                  </div>
                  <Form.Item
                    name={`prompt_${dimension}`}
                    label="提示词内容"
                    initialValue={prompt.content}
                  >
                    <Input.TextArea rows={6} />
                  </Form.Item>
                </Panel>
              ))}
            </Collapse>
          </Card>
        </Card>
      </Form>
    </div>
  );
};

export default SystemConfig;
