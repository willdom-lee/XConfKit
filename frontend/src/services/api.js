import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 对于下载请求，直接返回response对象
    if (response.config.responseType === 'blob') {
      return response.data;
    }

    return response.data;
  },
  (error) => {

    return Promise.reject(error);
  }
);

// 设备管理API
export const deviceAPI = {
  // 获取设备列表
  getDevices: () => api.get('/devices'),
  
  // 获取单个设备
  getDevice: (id) => api.get(`/devices/${id}`),
  
  // 创建设备
  createDevice: (device) => api.post('/devices', device),
  
  // 更新设备
  updateDevice: (id, device) => api.put(`/devices/${id}`, device),
  
  // 删除设备
  deleteDevice: (id) => api.delete(`/devices/${id}`),
  
  // 测试设备连接
  testConnection: (id) => api.post(`/devices/${id}/test`),
  
  // 快速备份设备
  quickBackup: (id) => api.post(`/devices/${id}/quick-backup`),
};

// 备份管理API
export const backupAPI = {
  // 获取备份列表
  getBackups: (deviceId) => api.get('/backups', { params: { device_id: deviceId } }),
  
  // 获取单个备份
  getBackup: (id) => api.get(`/backups/${id}`),
  
  // 获取备份内容
  getBackupContent: (id) => api.get(`/backups/${id}/content`),
  
  // 下载备份文件
  downloadBackup: (id) => api.get(`/backups/${id}/download`, { responseType: 'blob' }),
  
  // 执行备份
  executeBackup: (deviceId, backupType = 'running-config') => 
    api.post(`/backups/execute?device_id=${deviceId}&backup_type=${backupType}`),
  
  // 删除备份
  deleteBackup: (id) => api.delete(`/backups/${id}`),
  
  // 批量删除备份
  batchDeleteBackups: (ids) => api.post('/backups/batch-delete', ids),
};

// 备份策略API
export const strategyAPI = {
  // 获取策略列表
  getStrategies: () => api.get('/strategies'),
  
  // 获取单个策略
  getStrategy: (id) => api.get(`/strategies/${id}`),
  
  // 创建策略
  createStrategy: (strategy) => api.post('/strategies', strategy),
  
  // 更新策略
  updateStrategy: (id, strategy) => api.put(`/strategies/${id}`, strategy),
  
  // 删除策略
  deleteStrategy: (id) => api.delete(`/strategies/${id}`),
  
  // 切换策略状态
  toggleStrategyStatus: (id) => api.post(`/strategies/${id}/toggle`),
  
  // 获取到期策略
  getDueStrategies: () => api.get('/strategies/due/list'),
  
  // 执行策略
  executeStrategy: (id) => api.post(`/strategies/${id}/execute`),
  
  // 立即执行策略（不影响调度）
  executeStrategyNow: (id) => api.post(`/strategies/${id}/execute-now`),
};

// 系统配置API
export const configAPI = {
  // 获取所有配置
  getAllConfigs: () => api.get('/configs/'),
  
  // 获取按分类分组的配置
  getConfigsByCategories: () => api.get('/configs/categories'),
  
  // 获取配置（兼容方法）
  getConfigs: async () => {
    try {
      const categories = await api.get('/configs/categories');
      
      // 转换为对象格式，确保与前端期望的结构一致
      const configs = {};
      categories.forEach(category => {
        configs[category.category] = category.configs; // 保持原始数组格式
      });
      
      return configs;
    } catch (error) {
      // 获取配置失败
      throw error;
    }
  },
  
  // 获取指定分类的配置
  getConfigsByCategory: (category) => api.get(`/configs/category/${category}`),
  
  // 获取单个配置
  getConfig: (category, key) => api.get(`/configs/${category}/${key}`),
  
  // 创建配置
  createConfig: (config) => api.post('/configs/', config),
  
  // 更新配置
  updateConfig: (category, key, config) => api.put(`/configs/${category}/${key}`, config),
  
  // 批量更新配置
  batchUpdateConfigs: (batchUpdate) => api.post('/configs/batch-update', batchUpdate),
  
  // 更新配置（兼容方法）
  updateConfigs: async (category, configs) => {
    try {
      const batchUpdate = {
        configs: Object.keys(configs).map(key => ({
          category,
          key,
          value: configs[key]
        }))
      };
      
      const result = await api.post('/configs/batch-update', batchUpdate);
      return result;
    } catch (error) {
      throw error;
    }
  },
  
  // 获取默认值
  getDefaultValues: () => api.get('/configs/defaults'),
  
  // 获取指定分类的默认值
  getDefaultValuesByCategory: (category) => api.get(`/configs/defaults/${category}`),
  
  // 重置单个配置为默认值
  resetConfigToDefault: (category, key) => api.post(`/configs/${category}/${key}/reset`),
  
  // 重置指定分类的所有配置为默认值
  resetCategoryToDefault: (category) => api.post(`/configs/${category}/reset`),
  
  // 重置所有配置为默认值（不包括AI配置）
  resetAllConfigsToDefault: () => api.post('/configs/reset-all'),
  
  // 初始化默认配置
  initDefaultConfigs: () => api.post('/configs/init-defaults'),
  
  // 删除配置
  deleteConfig: (category, key) => api.delete(`/configs/${category}/${key}`),
  

  
  // AI配置相关API
  getAIConfig: () => api.get('/analysis/config/ai'),
  updateAIConfig: (config) => api.post('/analysis/config/ai', config),
  testAIConnection: (config) => api.post('/analysis/config/ai/test', config),
  
  // 分析提示词相关API
  getAnalysisPrompts: () => api.get('/analysis/config/prompts'),
  updateAnalysisPrompts: (prompts) => api.post('/analysis/config/prompts', prompts)
};

// AI分析相关API
export const analysisAPI = {
  // 分析配置
  analyzeConfig: async (params) => {
    try {
      const response = await fetch('/api/analysis/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_id: params.device_id,
          backup_id: params.backup_id,
          dimensions: params.dimensions || null  // 支持维度选择
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      throw error;
    }
  },

  // 获取分析历史
  getAnalysisHistory: async () => {
    try {
      const response = await fetch('/api/analysis/history');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      throw error;
    }
  },

  // 获取分析结果
  getAnalysisResult: async (analysisId) => {
    try {
      const response = await fetch(`/api/analysis/record/${analysisId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      throw error;
    }
  },

  // 删除单个分析记录
  deleteAnalysisRecord: async (recordId) => {
    try {
      const response = await fetch(`/api/analysis/record/${recordId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      throw error;
    }
  },

  // 删除所有分析记录
  deleteAllAnalysisRecords: async () => {
    try {
      const response = await fetch('/api/analysis/records/all', {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      throw error;
    }
  },
};



export default api;
