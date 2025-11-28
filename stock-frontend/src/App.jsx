import React, { useState } from 'react';
import { Layout, Tabs, message, Spin, Tag } from 'antd';
import { StockOutlined, BarChartOutlined, CalendarOutlined } from '@ant-design/icons';
import StockSearch from './components/StockSearch';
import DailyChart from './components/DailyChart';
import MinuteChart from './components/MinuteChart';
import { stockAPI } from './services/api';
import './App.css';

const { Header, Content } = Layout;
const { TabPane } = Tabs;

function App() {
  const [currentStock, setCurrentStock] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [dailyData, setDailyData] = useState(null);
  const [min5Data, setMin5Data] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('daily');

  const handleStockSelect = async (stockCode, endDate = null) => {
    setLoading(true);
    setCurrentStock(stockCode);
    setSelectedDate(endDate);
    
    try {
      // 并行加载日线和5分钟数据
      const [dailyResponse, min5Response] = await Promise.all([
        stockAPI.getDailyData(stockCode, endDate),
        stockAPI.getMin5Data(stockCode, endDate)
      ]);

      if (dailyResponse.error) {
        message.error(`日线数据加载失败: ${dailyResponse.error}`);
      } else {
        setDailyData(dailyResponse);
      }

      if (min5Response.error) {
        message.error(`5分钟数据加载失败: ${min5Response.error}`);
      } else {
        setMin5Data(min5Response);
      }

      const dateText = endDate ? ` (${endDate})` : ' (最新数据)';
      message.success(`股票 ${stockCode}${dateText} 数据加载成功`);
    } catch (error) {
      message.error('数据加载失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (key) => {
    setActiveTab(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#001529', 
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px'
      }}>
        <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
          📈 股票数据查看器
        </div>
        {selectedDate && (
          <Tag color="blue" icon={<CalendarOutlined />}>
            查询日期: {selectedDate}
          </Tag>
        )}
      </Header>
      
      <Content style={{ padding: '24px', background: '#f0f2f5' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <StockSearch 
            onStockSelect={handleStockSelect}
            loading={loading}
          />
          {currentStock && (
            <Tabs
              activeKey={activeTab}
              onChange={handleTabChange}
              items={[
                {
                  key: 'daily',
                  label: (
                    <span>
                      <StockOutlined />
                      日K线
                      {dailyData?.end_date && (
                        <Tag color="green" style={{ marginLeft: 8, fontSize: '12px' }}>
                          至 {dailyData.end_date}
                        </Tag>
                      )}
                    </span>
                  ),
                  children: (
                    <DailyChart 
                      data={dailyData}
                      loading={loading && activeTab === 'daily'}
                    />
                  )
                },
                {
                  key: 'min5',
                  label: (
                    <span>
                      <BarChartOutlined />
                      5分钟K线
                      {min5Data?.trade_date && (
                        <Tag color="orange" style={{ marginLeft: 8, fontSize: '12px' }}>
                          {min5Data.trade_date}
                        </Tag>
                      )}
                    </span>
                  ),
                  children: (
                    <MinuteChart 
                      stockCode={currentStock}
                      data={min5Data}
                      loading={loading && activeTab === 'min5'}
                    />
                  )
                }
              ]}
            />
          )}
        </div>
      </Content>
    </Layout>
  );
}

export default App;