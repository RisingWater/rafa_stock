import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'api', // 替换为实际的API基础URL
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const stockAPI = {
    // 获取日K线数据
    getDailyData: async (stockCode, endDate = null) => {
      try {
        const params = {};
        if (endDate) {
          params.end_date = endDate;
        }
        return await apiClient.get(`/stock/${stockCode}/daily`, { params });
      } catch (error) {
        console.error('获取日线数据失败:', error);
        return { error: error.message };
      }
    },
  
    // 获取5分钟K线数据
    getMin5Data: async (stockCode, endDate = null) => {
      try {
        const params = {};
        if (endDate) {
          params.end_date = endDate;
        }
        return await apiClient.get(`/stock/${stockCode}/min5`, { params });
      } catch (error) {
        console.error('获取5分钟数据失败:', error);
        return { error: error.message };
      }
    }
  };