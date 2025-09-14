import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button, Space, Typography, Alert, Spin, Divider } from 'antd';
import { CodeOutlined, SendOutlined, ClearOutlined, DisconnectOutlined } from '@ant-design/icons';

const { Text } = Typography;

const CLIConnection = ({ visible, onClose, device }) => {
  const [terminalContent, setTerminalContent] = useState('');
  const [currentLine, setCurrentLine] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isConnected, setIsConnected] = useState(false);
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [cursorPosition, setCursorPosition] = useState(0);
  const terminalRef = useRef(null);
  const inputRef = useRef(null);

  // 自动滚动到底部
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalContent]);

  // 初始化连接
  useEffect(() => {
    if (visible && device) {
      initializeConnection();
    }
  }, [visible, device]);

  // 初始化连接
  const initializeConnection = async () => {
    setLoading(true);
    setTerminalContent('');
    setCurrentLine('');
    
    try {
      // 模拟连接过程
      let connectionOutput = `正在连接到设备 ${device.name} (${device.ip_address})...\n`;
      setTerminalContent(connectionOutput);
      
      // 模拟SSH连接建立过程
      setTimeout(() => {
        connectionOutput += `SSH连接已建立\n`;
        connectionOutput += `\n`;
        connectionOutput += `******************************************************************************\n`;
        connectionOutput += `*  Copyright (c) 2004-2025 New H3C Technologies Co., Ltd. All rights reserved.*\n`;
        connectionOutput += `*  Without the owner's prior written consent,                           *\n`;
        connectionOutput += `*  no decompiling or reverse-engineering shall be allowed.              *\n`;
        connectionOutput += `******************************************************************************\n`;
        connectionOutput += `\n`;
        connectionOutput += `H3C Comware Software, Version 5.20.99, Release 1234P01\n`;
        connectionOutput += `Copyright (c) 2004-2025 New H3C Technologies Co., Ltd. All rights reserved.\n`;
        connectionOutput += `H3C ${device.name} uptime is 0 weeks, 0 days, 0 hours, 0 minutes\n`;
        connectionOutput += `\n`;
        connectionOutput += `Last login: ${new Date().toLocaleString()} from 127.0.0.1\n`;
        connectionOutput += `\n`;
        connectionOutput += `${getPrompt()}`;
        
        setIsConnected(true);
        setCurrentPrompt(getPrompt());
        setDeviceInfo(device);
        setTerminalContent(connectionOutput);
        setLoading(false);
        
        // 聚焦到终端
        if (terminalRef.current) {
          terminalRef.current.focus();
        }
      }, 1500); // 模拟1.5秒的连接过程
      
    } catch (error) {
      const errorOutput = `连接失败: ${error.message}\n请检查网络连接。\n`;
      setTerminalContent(errorOutput);
      setLoading(false);
    }
  };

  // 从输出中提取真实的设备主机名
  const extractRealHostname = (output) => {
    if (!output) return null;
    
    // 查找H3C设备的真实提示符
    const h3cPromptMatch = output.match(/<(\w+)>/);
    if (h3cPromptMatch) {
      return h3cPromptMatch[1];
    }
    
    // 查找其他设备的提示符
    const ciscoPromptMatch = output.match(/(\w+)@([^#]+)#/);
    if (ciscoPromptMatch) {
      return ciscoPromptMatch[2];
    }
    
    const huaweiPromptMatch = output.match(/\[(\w+)-([^\]]+)\]/);
    if (huaweiPromptMatch) {
      return huaweiPromptMatch[2];
    }
    
    return null;
  };

  // 从输出中提取视图状态
  const extractViewState = (output) => {
    if (!output) return null;
    
    // 检查是否在系统视图中
    if (output.includes('System View:') || output.includes('[1F_jieru]')) {
      return 'system';
    }
    
    // 检查是否在用户视图中
    if (output.includes('<1F_jieru>') || output.includes('<admin>')) {
      return 'user';
    }
    
    return null;
  };

  // 获取命令提示符
  const getPrompt = () => {
    if (!device) return '$ ';
    
    // 根据设备类型生成不同的提示符
    const deviceType = device.device_type?.toLowerCase() || 'unknown';
    const username = device.username || 'admin';
    
    // 检查当前视图状态
    const viewState = deviceInfo?.viewState;
    const realHostname = deviceInfo?.realHostname || 'admin';
    
    // 如果有真实的设备主机名，使用它
    if (deviceType === 'h3c' || deviceType === 'hp') {
      if (viewState === 'system') {
        // 系统视图提示符
        return `[${realHostname}]`;
      } else {
        // 用户视图提示符
        return `<${realHostname}>`;
      }
    } else if (deviceType === 'cisco') {
      if (viewState === 'system') {
        return `${username}@${realHostname}#`;
      } else {
        return `${username}@${realHostname}>`;
      }
    } else if (deviceType === 'huawei') {
      if (viewState === 'system') {
        return `[${username}-${realHostname}]`;
      } else {
        return `<${username}-${realHostname}>`;
      }
    } else {
      return `${username}@${realHostname}:~$ `;
    }
  };

  // 处理终端键盘事件
  const handleTerminalKeyDown = (e) => {
    // 如果正在执行命令，只允许Ctrl+C中断
    if (loading) {
      if (e.ctrlKey && e.key === 'c') {
        e.preventDefault();
        // 中断命令执行
        setLoading(false);
        setTerminalContent(prev => prev + '\n命令执行被中断\n' + getPrompt());
        setCurrentLine('');
        setCursorPosition(0);
      }
      return; // 其他按键在加载时被忽略
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      executeCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndex < history.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        const command = history[history.length - 1 - newIndex];
        setCurrentLine(command);
        setCursorPosition(command.length);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        const command = history[history.length - 1 - newIndex];
        setCurrentLine(command);
        setCursorPosition(command.length);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setCurrentLine('');
        setCursorPosition(0);
      }
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      if (cursorPosition > 0) {
        setCursorPosition(cursorPosition - 1);
      }
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      if (cursorPosition < currentLine.length) {
        setCursorPosition(cursorPosition + 1);
      }
    } else if (e.key === 'Home') {
      e.preventDefault();
      setCursorPosition(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setCursorPosition(currentLine.length);
    } else if (e.key === 'Backspace') {
      e.preventDefault();
      if (cursorPosition > 0) {
        const newLine = currentLine.slice(0, cursorPosition - 1) + currentLine.slice(cursorPosition);
        setCurrentLine(newLine);
        setCursorPosition(cursorPosition - 1);
      }
    } else if (e.key === 'Delete') {
      e.preventDefault();
      if (cursorPosition < currentLine.length) {
        const newLine = currentLine.slice(0, cursorPosition) + currentLine.slice(cursorPosition + 1);
        setCurrentLine(newLine);
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      // 简单的命令补全
      const suggestions = getCommandSuggestions(currentLine);
      if (suggestions.length === 1) {
        setCurrentLine(suggestions[0]);
        setCursorPosition(suggestions[0].length);
      }
    } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      const newLine = currentLine.slice(0, cursorPosition) + e.key + currentLine.slice(cursorPosition);
      setCurrentLine(newLine);
      setCursorPosition(cursorPosition + 1);
    }
  };

  // 获取命令建议
  const getCommandSuggestions = (partial) => {
    const commonCommands = [
      'display', 'show', 'ping', 'traceroute', 'telnet', 'ssh',
      'interface', 'ip', 'route', 'vlan', 'user', 'system',
      'quit', 'exit', 'help', 'clear', 'save', 'reset'
    ];
    
    return commonCommands.filter(cmd => 
      cmd.toLowerCase().startsWith(partial.toLowerCase())
    );
  };

  // 清理输出中的控制字符和格式问题
  const cleanOutput = (output) => {
    if (!output) return output;
    
    return output
      // 清理ANSI控制字符
      .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')
      // 清理分页控制字符
      .replace(/\[16D\s*\[16D/g, '')
      .replace(/\[16D/g, '')
      .replace(/\s+\[16D\s+/g, ' ')
      // 移除分页提示
      .replace(/---- More ----/g, '')
      // 清理多余的空行
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      // 修复分页后的缩进问题 - 移除行首的多余空格
      .split('\n')
      .map(line => {
        // 如果行以多个空格开头，可能是分页后的格式问题
        if (line.match(/^\s{8,}/)) {
          // 移除行首的8个或更多空格
          return line.replace(/^\s{8,}/, '');
        }
        return line;
      })
      .join('\n')
      // 清理行首的孤立空格
      .replace(/\n\s+\n/g, '\n\n')
      // 确保没有多余的空格
      .trim();
  };

  // 处理命令执行
  const executeCommand = async () => {
    if (!currentLine.trim() || !isConnected || loading) return;

    setLoading(true);
    const currentCommand = currentLine.trim();
    
    // 添加到历史记录
    setHistory(prev => [...prev, currentCommand]);
    setHistoryIndex(-1);

    // 显示命令和提示符
    const commandLine = `${currentPrompt}${currentCommand}\n`;
    setTerminalContent(prev => prev + commandLine);

    try {
      const response = await fetch(`/api/devices/${device.id}/cli`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: currentCommand }),
      });

      const result = await response.json();
      
      // 构建输出内容
      let newOutput = '';
      
      if (result.success) {
        if (result.data.output) {
          // 清理输出中的控制字符
          newOutput += cleanOutput(result.data.output);
          
          // 尝试从输出中提取真实的设备主机名和视图状态
          const realHostname = extractRealHostname(result.data.output);
          const viewState = extractViewState(result.data.output);
          
          if (realHostname) {
            // 更新设备信息中的真实主机名
            setDeviceInfo(prev => ({
              ...prev,
              realHostname: realHostname
            }));
          }
          
          if (viewState) {
            // 更新视图状态
            setDeviceInfo(prev => ({
              ...prev,
              viewState: viewState
            }));
          }
        }
        if (result.data.error) {
          newOutput += `\n错误: ${result.data.error}`;
        }
      } else {
        newOutput += `错误: ${result.message}`;
      }
      
      // 检查输出中是否已经包含提示符，避免重复
      const hasPrompt = newOutput.includes('<') || newOutput.includes('[') || newOutput.includes('#') || newOutput.includes('$');
      
      // 只有在输出中没有提示符时才添加新的提示符
      if (!hasPrompt) {
        if (!newOutput.endsWith('\n')) {
          newOutput += '\n';
        }
        newOutput += `${getPrompt()}`;
      }
      
      setTerminalContent(prev => prev + newOutput);
      setCurrentLine('');
      setCursorPosition(0);
    } catch (error) {
      const errorOutput = `错误: 网络请求失败 - ${error.message}\n${getPrompt()}`;
      setTerminalContent(prev => prev + errorOutput);
      setCurrentLine('');
      setCursorPosition(0);
    } finally {
      setLoading(false);
    }
  };

  // 清空终端
  const clearTerminal = () => {
    setTerminalContent('');
    if (isConnected) {
      setTerminalContent(`${getPrompt()}`);
    }
  };

  // 断开连接
  const disconnect = async () => {
    try {
      // 调用后端API关闭SSH会话
      await fetch(`/api/devices/${device.id}/cli`, {
        method: 'DELETE',
      });
    } catch (error) {
      // 关闭SSH会话失败
    }
    
    setIsConnected(false);
    setTerminalContent(prev => prev + '\n连接已断开。\n');
  };

  // 模态框关闭时清理状态
  const handleClose = async () => {
    // 如果还连接着，先断开连接
    if (isConnected) {
      await disconnect();
    }
    
    setTerminalContent('');
    setCurrentLine('');
    setHistory([]);
    setHistoryIndex(-1);
    setIsConnected(false);
    setCurrentPrompt('');
    setDeviceInfo(null);
    setCursorPosition(0);
    onClose();
  };

  // 常用命令快捷按钮
  const commonCommands = [
    { label: '显示版本', command: 'display version' },
    { label: '显示接口', command: 'display interface brief' },
    { label: '显示配置', command: 'display current-configuration' },
    { label: '显示路由', command: 'display ip routing-table' },
    { label: 'Ping测试', command: 'ping 8.8.8.8' },
    { label: '帮助', command: 'help' },
  ];

  // 渲染当前行（包含光标）
  const renderCurrentLine = () => {
    const beforeCursor = currentLine.slice(0, cursorPosition);
    const afterCursor = currentLine.slice(cursorPosition);
    const cursorChar = '█'; // 光标字符
    
    return (
      <span>
        {beforeCursor}
        <span style={{ 
          backgroundColor: '#ffffff', 
          color: '#000000',
          animation: 'blink 1s infinite'
        }}>
          {cursorChar}
        </span>
        {afterCursor}
      </span>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <CodeOutlined />
          <span>SSH终端 - {device?.name || '设备'}</span>
          {isConnected && (
            <Text type="success" style={{ fontSize: 12 }}>
              ● 已连接
            </Text>
          )}
        </Space>
      }
      open={visible}
      onCancel={handleClose}
      width={1000}
      footer={null}
      destroyOnClose
    >
      <div style={{ marginBottom: 16 }}>
        {/* 设备信息 */}
        <div style={{ 
          backgroundColor: '#f5f5f5', 
          padding: 12, 
          borderRadius: 6, 
          marginBottom: 16,
          fontSize: 12 
        }}>
          <Text strong>设备信息:</Text> {device?.name} ({device?.ip_address}:{device?.port || 22})
          <br />
          <Text strong>设备类型:</Text> {device?.device_type || '未知'}
          <br />
          <Text strong>用户名:</Text> {device?.username}
        </div>

        {/* 常用命令快捷按钮 */}
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ marginRight: 8 }}>常用命令:</Text>
          <Space wrap>
            {commonCommands.map((cmd, index) => (
              <Button
                key={index}
                size="small"
                onClick={() => {
                  setCurrentLine(cmd.command);
                  setCursorPosition(cmd.command.length);
                  if (terminalRef.current) {
                    terminalRef.current.focus();
                  }
                }}
                disabled={!isConnected}
              >
                {cmd.label}
              </Button>
            ))}
          </Space>
        </div>

        <Divider style={{ margin: '8px 0' }} />
        
        {/* 集成终端区域 */}
        <div
          ref={terminalRef}
          tabIndex={0}
          onKeyDown={handleTerminalKeyDown}
          style={{
            height: 500,
            backgroundColor: '#1e1e1e',
            color: '#ffffff',
            padding: 12,
            fontFamily: 'Consolas, Monaco, monospace',
            fontSize: 13,
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            marginBottom: 16,
            position: 'relative',
            outline: 'none',
            cursor: 'text'
          }}
        >
          <style>
            {`
              @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
              }
            `}
          </style>
          
          {terminalContent || '正在连接...\n'}
          {isConnected && (
            <span style={{ color: '#52c41a' }}>
              {currentPrompt}
            </span>
          )}
          {!loading && renderCurrentLine()}
          
          {loading && (
            <div style={{ 
              position: 'absolute', 
              bottom: 8, 
              right: 8,
              color: '#52c41a',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <Spin size="small" />
              <span style={{ fontSize: 12 }}>执行中...</span>
            </div>
          )}
          
          {/* 命令执行期间的覆盖层 */}
          {loading && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none'
            }}>
              <div style={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                color: '#ffffff',
                padding: '8px 16px',
                borderRadius: 4,
                fontSize: 12
              }}>
                命令执行中，请稍候... (Ctrl+C 中断)
              </div>
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div style={{ marginTop: 16, textAlign: 'right' }}>
          <Space>
            <Button
              icon={<ClearOutlined />}
              onClick={clearTerminal}
              disabled={!terminalContent}
              size="small"
            >
              清空
            </Button>
            <Button
              icon={<DisconnectOutlined />}
              onClick={disconnect}
              disabled={!isConnected}
              size="small"
            >
              断开
            </Button>
            <Button onClick={handleClose} size="small">
              关闭
            </Button>
          </Space>
        </div>

        {/* 提示信息 */}
        <div style={{ marginTop: 12 }}>
          <Text type="secondary" style={{ fontSize: 11 }}>
            快捷键: Enter执行 | ↑↓历史 | ←→移动光标 | Tab补全 | Ctrl+C中断命令
          </Text>
        </div>
      </div>
    </Modal>
  );
};

export default CLIConnection;
