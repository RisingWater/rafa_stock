import React, { useEffect, useRef, useState } from 'react';
import { Card, Spin, Empty, Tag, Alert } from 'antd';
import { WifiOutlined, DisconnectOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

const MinuteChart = ({ stockCode, data: initialData, loading }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const [realTimeData, setRealTimeData] = useState(initialData);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const wsRef = useRef(null);

  useEffect(() => {
    console.log('chartRef.current:', chartRef.current);
    
    if (chartRef.current && !chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
      
      // 添加resize监听
      const handleResize = () => {
        chartInstance.current?.resize();
      };
      window.addEventListener('resize', handleResize);
      
      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartInstance.current) {
          chartInstance.current.dispose();
          chartInstance.current = null;
        }
      };
    }
  }, []);

  // WebSocket连接
  useEffect(() => {
    if (!stockCode) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${stockCode}`;
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setWsStatus('connected');
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'initial' || message.type === 'update') {
        setRealTimeData(message.data);
      }
    };

    wsRef.current.onclose = () => {
      setWsStatus('disconnected');
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsStatus('error');
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [stockCode]);

  // 更新图表
  useEffect(() => {
    console.log('更新图表效果:', {
      loading,
      hasInstance: !!chartInstance.current,
      hasRealTimeData: !!realTimeData,
      hasInitialData: !!initialData
    });

    if (!chartInstance.current) {
      console.log('图表实例不存在，跳过更新');
      return;
    }

    if (loading) {
      console.log('加载中，显示加载状态');
      chartInstance.current.showLoading();
      return;
    } else {
      chartInstance.current.hideLoading();
    }

    const data = realTimeData || initialData;
    
    // 检查数据有效性
    if (!data || !data.data || !data.data.data || !Array.isArray(data.data.data) || data.data.data.length === 0) {
      console.log('无数据，清除图表');
      chartInstance.current.clear();
      return;
    }

    const chartData = data.data.data;
    console.log('渲染图表数据:', chartData.length, '条');

    const times = chartData.map(item => {
      const datetime = item.datetime;
      return datetime.includes(' ') ? datetime.split(' ')[1] : datetime;
    });
    
    const values = chartData.map(item => [
      Number(item.open),
      Number(item.close), 
      Number(item.low),
      Number(item.high)
    ]);

    const option = {
      animation: false,
      title: {
        text: `${data.data.stock_name} (${data.data.stock_code}) - 5分钟K线`,
        subtext: data.data.trade_date ? `交易日: ${data.data.trade_date}` : '',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: function (params) {
          let result = `${params[0].axisValue}<br/>`;
          params.forEach(item => {
            if (item.seriesType === 'candlestick') {
              const data = item.data;
              result += `开: ${data[0].toFixed(2)}<br/>`;
              result += `收: ${data[1].toFixed(2)}<br/>`;
              result += `低: ${data[2].toFixed(2)}<br/>`;
              result += `高: ${data[3].toFixed(2)}<br/>`;
            }
          });
          return result;
        }
      },
      xAxis: {
        type: 'category',
        data: times,
        axisLabel: {
          show: false,
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitLine: {
          show: true
        },
        axisLabel: {
          formatter: (value) => value.toFixed(2)
        }
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          type: 'slider',
          show: true,
          start: 0,
          end: 100,
          bottom: 10
        }
      ],
      series: [
        {
          type: 'candlestick',
          data: values,
          itemStyle: {
            color: '#ef232a',
            color0: '#14b143',
            borderColor: '#ef232a',
            borderColor0: '#14b143'
          }
        }
      ]
    };

    chartInstance.current.setOption(option, true);
    
    // 确保图表正确显示
    setTimeout(() => {
      chartInstance.current?.resize();
    }, 100);
    
  }, [realTimeData, initialData, loading]);

  const getStatusColor = () => {
    switch (wsStatus) {
      case 'connected': return 'green';
      case 'disconnected': return 'red';
      case 'error': return 'orange';
      default: return 'default';
    }
  };

  const getStatusIcon = () => {
    switch (wsStatus) {
      case 'connected': return <WifiOutlined />;
      default: return <DisconnectOutlined />;
    }
  };

  const getStatusText = () => {
    switch (wsStatus) {
      case 'connected': return '实时模式';
      case 'disconnected': return '连接断开';
      case 'error': return '连接错误';
      default: return '未知状态';
    }
  };

  return (
    <Card>
      {/* 状态标签栏 */}
      <div style={{ marginBottom: 16 }}>
        <Tag 
          icon={getStatusIcon()} 
          color={getStatusColor()}
          style={{ fontSize: '14px', padding: '4px 8px' }}
        >
          {getStatusText()}
        </Tag>
        {realTimeData?.update_time && (
          <Tag color="blue">
            最后更新: {realTimeData.update_time}
          </Tag>
        )}
      </div>

      {/* 关键：始终渲染图表容器 */}
      <div 
        ref={chartRef} 
        style={{ 
          width: '100%', 
          height: '500px'
        }} 
      />
      
      {/* 叠加显示状态信息 */}
      {loading && (
        <div 
          style={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)',
            zIndex: 1000
          }}
        >
          <Spin size="large" />
        </div>
      )}
      
      {!loading && (!initialData && !realTimeData) && (
        <div 
          style={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)',
            zIndex: 1000
          }}
        >
          <Empty description="请查询股票数据" />
        </div>
      )}
    </Card>
  );
};

export default MinuteChart;