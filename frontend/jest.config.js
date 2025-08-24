module.exports = {
  // 测试环境
  testEnvironment: 'jsdom',
  
  // 测试文件匹配模式
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}',
    '<rootDir>/../tests/frontend/**/*.test.{js,jsx,ts,tsx}'
  ],
  
  // 忽略的文件
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/'
  ],
  
  // 模块文件扩展名
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json'],
  
  // 模块名称映射
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1'
  },
  
  // 转换器
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
    '^.+\\.(css|less|scss|sass)$': 'jest-transform-css',
    '^.+\\.(png|jpg|jpeg|gif|svg)$': 'jest-transform-file'
  },
  
  // 设置文件
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.js'
  ],
  
  // 收集覆盖率
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.js',
    '!src/main.jsx',
    '!src/setupTests.js'
  ],
  
  // 覆盖率报告
  coverageReporters: [
    'text',
    'html',
    'lcov',
    'json'
  ],
  
  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  
  // 测试超时时间
  testTimeout: 10000,
  
  // 最大并发数
  maxWorkers: '50%',
  
  // 详细输出
  verbose: true,
  
  // 颜色输出
  colors: true,
  
  // 错误报告
  errorOnDeprecated: true,
  
  // 清理模拟
  clearMocks: true,
  
  // 恢复模拟
  restoreMocks: true,
  
  // 重置模块
  resetModules: true,
  
  // 重置模拟
  resetMocks: true,
  
  // 快照序列化器
  snapshotSerializers: [
    'jest-serializer-vue',
    'jest-serializer-react'
  ],
  
  // 模块路径映射
  modulePaths: [
    '<rootDir>/src'
  ],
  
  // 测试环境设置
  testEnvironmentOptions: {
    url: 'http://localhost'
  },
  
  // 全局设置
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json'
    }
  }
};
