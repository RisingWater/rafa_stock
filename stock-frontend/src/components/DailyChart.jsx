import React, { useEffect, useRef } from 'react';
import { Card, Spin, Empty } from 'antd';
import * as echarts from 'echarts';

const DailyChart = ({ data, loading }) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        console.log('chartRef.current:', chartRef.current);
        
        if (chartRef.current && !chartInstance.current) {
            console.log('初始化ECharts实例');
            chartInstance.current = echarts.init(chartRef.current);
            
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

    useEffect(() => {
        console.log('数据更新:', {
            loading,
            hasData: !!(data?.data?.data?.length),
            hasInstance: !!chartInstance.current
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

        if (!data || !data.data || !data.data.data || data.data.data.length === 0) {
            console.log('无数据，清除图表');
            chartInstance.current.clear();
            return;
        }

        const chartData = data.data.data;
        console.log('渲染图表数据:', chartData.length, '条');

        const dates = chartData.map(item => item.date);
        const values = chartData.map(item => [
            Number(item.open),
            Number(item.close), 
            Number(item.low),
            Number(item.high)
        ]);
        const volumes = chartData.map(item => Number(item.volume));

        const option = {
            animation: false,
            title: {
                text: `${data.data.stock_name} (${data.data.stock_code}) - 日K线`,
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
                        } else if (item.seriesType === 'bar') {
                            result += `成交量: ${item.data.toLocaleString()}`;
                        }
                    });
                    return result;
                }
            },
            grid: [
                {
                    left: '50px',
                    right: '50px',
                    top: '60px',
                    height: '60%'
                },
                {
                    left: '50px',
                    right: '50px',
                    top: '75%',
                    height: '15%'
                }
            ],
            xAxis: [
                {
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap: false,
                    axisLine: { onZero: false },
                    splitLine: { show: false },
                    axisLabel: { show: false }
                },
                {
                    type: 'category',
                    gridIndex: 1,
                    data: dates,
                    boundaryGap: false,
                    axisLine: { onZero: false },
                    axisTick: { show: false },
                    splitLine: { show: false },
                    axisLabel: { show: false }
                }
            ],
            yAxis: [
                {
                    scale: true,
                    splitArea: { show: true }
                },
                {
                    scale: true,
                    gridIndex: 1,
                    splitNumber: 2,
                    axisLabel: { show: false },
                    axisLine: { show: false },
                    axisTick: { show: false },
                    splitLine: { show: false }
                }
            ],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0, 1],
                    start: 0,
                    end: 100
                }
            ],
            series: [
                {
                    name: 'K线',
                    type: 'candlestick',
                    data: values,
                    itemStyle: {
                        color: '#ef232a',
                        color0: '#14b143',
                        borderColor: '#ef232a',
                        borderColor0: '#14b143'
                    }
                },
                {
                    name: '成交量',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    data: volumes,
                    itemStyle: {
                        color: (params) => {
                            const dataIndex = params.dataIndex;
                            const open = values[dataIndex][0];
                            const close = values[dataIndex][1];
                            return close >= open ? '#ef232a' : '#14b143';
                        }
                    }
                }
            ]
        };

        chartInstance.current.setOption(option, true);
        
        setTimeout(() => {
            chartInstance.current?.resize();
        }, 100);
        
    }, [data, loading]);

    return (
        <Card>
            {/* 关键：始终渲染图表容器，确保ref被创建 */}
            <div 
                ref={chartRef} 
                style={{ 
                    width: '100%', 
                    height: '600px',
                    minHeight: '600px'
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
            
            {!loading && (!data || !data.data || !data.data.data || data.data.data.length === 0) && (
                <div 
                    style={{ 
                        position: 'absolute', 
                        top: '50%', 
                        left: '50%', 
                        transform: 'translate(-50%, -50%)',
                        zIndex: 1000
                    }}
                >
                    <Empty description="暂无数据" />
                </div>
            )}
        </Card>
    );
};

export default DailyChart;