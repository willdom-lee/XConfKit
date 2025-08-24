import React from 'react';
import { Alert, Button } from 'antd';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    
    console.error('React错误边界捕获到错误:', error);
    console.error('错误信息:', errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '24px' }}>
          <Alert
            message="组件错误"
            description={
              <div>
                <p>系统配置组件发生了错误，请刷新页面重试。</p>
                <p>错误详情: {this.state.error?.message}</p>
                <Button 
                  type="primary" 
                  onClick={() => window.location.reload()}
                  style={{ marginTop: '16px' }}
                >
                  刷新页面
                </Button>
              </div>
            }
            type="error"
            showIcon
          />
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
