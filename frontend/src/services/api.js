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
    console.log('API响应:', response.data);
    return response.data;
  },
  (error) => {
    console.error('API请求错误:', error.response?.data || error.message);
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

export default api;
