import pandas as pd
from datetime import datetime, timedelta
import akshare as ak
import time
import logging

logger = logging.getLogger(__name__)

class StockAKShare:
    def __init__(self):
        pass

    def get_daily_kline_from_api_easymoney(self, stock_code, start_date, end_date, adjust='qfq', sleep_time=0):
        """
        从东方财经API获取日K线数据
        
        参数:
            stock_code (str): 股票代码，格式如 "000001"
            start_date (str): 开始时间 "YYYYMMDD"
            end_date (str): 结束时间 "YYYYMMDD"
            adjust (str): 复权类型 '', 'qfq', 'hfq'
            
        返回:
            pandas.DataFrame: 包含日K线数据的DataFrame
        """
        try:
            # 获取日线数据
            stock_data = ak.stock_zh_a_daily(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            # sleep防止调用过于频繁
            if sleep_time > 0:
                time.sleep(sleep_time)

            if not stock_data.empty:
                # 新浪接口返回的列名已经是英文，但需要确保格式一致
                stock_data = stock_data.rename(columns={
                    '日期': 'date',
                    '开盘': 'open', 
                    '最高': 'high',
                    '最低': 'low',
                    '收盘': 'close',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })
                
                # 确保日期列为datetime类型
                stock_data['date'] = pd.to_datetime(stock_data['date'])
                
                # 按时间排序
                stock_data = stock_data.sort_values('date')
                            
            return stock_data
                    
        except Exception as e:
            logger.error(f"❌ 从东方财经API获取日线数据失败: {e}")
            return pd.DataFrame()

    
    def get_daily_kline_from_api_sina(self, stock_code, start_date, end_date, adjust='qfq', sleep_time=0):
        """
        从新浪财经API获取日K线数据
        
        参数:
            stock_code (str): 股票代码，格式如 "000001"
            start_date (str): 开始时间 "YYYYMMDD"
            end_date (str): 结束时间 "YYYYMMDD"
            adjust (str): 复权类型 '', 'qfq', 'hfq'
            
        返回:
            pandas.DataFrame: 包含日K线数据的DataFrame
        """
        try:
            # 清理股票代码，添加市场前缀
            if '.' in stock_code:
                stock_code = stock_code.split('.')[0]
            
            # 判断市场并添加前缀
            if stock_code.startswith('6'):
                symbol = f"sh{stock_code}"  # 上海
            elif stock_code.startswith('8') or stock_code.startswith('4'):
                symbol = f"bj{stock_code}"  # 北京交易所
            else:
                symbol = f"sz{stock_code}"  # 深圳
            
            # 获取日线数据
            stock_data = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            # sleep防止调用过于频繁
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            if not stock_data.empty:
                # 新浪接口返回的列名已经是英文，但需要确保格式一致
                stock_data = stock_data.rename(columns={
                    'date': 'date',
                    'open': 'open', 
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume',
                    'amount': 'amount'
                })
                
                # 确保日期列为datetime类型
                stock_data['date'] = pd.to_datetime(stock_data['date'])
                
                # 按时间排序
                stock_data = stock_data.sort_values('date')
                            
            return stock_data
            
        except Exception as e:
            logger.error(f"❌ 从新浪API获取日线数据失败: {e}")
            return pd.DataFrame()
                
    def get_all_min_kline_from_api(self, stock_code, period='5', adjust='qfq'):
        """
        从新浪财经API获取5分钟K线数据
        
        参数:
            stock_code (str): 股票代码，格式如 "000001"
            period (str): 时间周期 '1', '5', '15', '30', '60' 分钟
            adjust (str): 复权类型 '', 'qfq', 'hfq'
            
        返回:
            pandas.DataFrame: 包含5分钟K线数据的DataFrame
        """
        try:
            # 清理股票代码，添加市场前缀
            if '.' in stock_code:
                stock_code = stock_code.split('.')[0]
            
            # 判断市场并添加前缀
            if stock_code.startswith('6'):
                symbol = f"sh{stock_code}"  # 上海
            else:
                symbol = f"sz{stock_code}"  # 深圳
            
            # 获取分钟数据
            stock_data = ak.stock_zh_a_minute(
                symbol=symbol,
                period=period,
                adjust=adjust
            )
            
            if not stock_data.empty:
                # 重命名列名为英文
                stock_data = stock_data.rename(columns={
                    'day': 'datetime',
                    'open': 'open',
                    'high': 'high', 
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                
                # 确保时间列为datetime类型
                stock_data['datetime'] = pd.to_datetime(stock_data['datetime'])
                
                # 按时间排序
                stock_data = stock_data.sort_values('datetime')
                
            return stock_data
            
        except Exception as e:
            logger.error(f"❌ 从新浪API获取分钟线数据失败: {e}")
            return pd.DataFrame()
        
    def _get_index_info_from_api(self, symbol, symbol_name):
        try:
            index_stock_cons_csindex_df = ak.index_stock_cons_csindex(symbol=symbol)
            if not index_stock_cons_csindex_df.empty:
                stock_info = index_stock_cons_csindex_df.rename(columns={
                    '日期': 'date',
                    '指数代码': 'index_code',
                    '指数名称': 'index_name',
                    '指数英文名称': 'index_name_en',
                    '成分券代码': 'stock_code',
                    '成分券名称': 'stock_name',
                    '成分券英文名称': 'stock_name_en',
                    '交易所': 'exchange_name',
                    '交易所英文名称': 'exchange_name_en'
                })

                return stock_info
        
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ 从中证指数网站获取{symbol_name}({symbol})成分股数据失败: {e}")
            return pd.DataFrame()

    def get_zz1000_stockinfo_from_api(self):
        symbol = '000852'
        return self._get_index_info_from_api(symbol, '中证1000')
        

    def get_hs300_stockinfo_from_api(self):
        symbol = '000300'
        return self._get_index_info_from_api(symbol, '沪深300')

    def get_csi500_stockinfo_from_api(self):
        symbol = '000905'
        return self._get_index_info_from_api(symbol, '中证500')

    def get_today_data_realtime(self, date):
        stock_data = ak.stock_zh_a_spot()
        if not stock_data.empty:
            required_columns = ['代码', '名称', '最新价', '今开', '最高', '最低', '成交量', '名称', '成交额']
            stock_data = stock_data[required_columns]
            # 重命名列名为英文
            stock_data = stock_data.rename(columns={
                '代码': 'stock_code',
                '名称': 'stock_name',
                '最新价': 'close', 
                '今开': 'open',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '名称': 'stock_name'
            })

            # 为所有行添加相同的date值
            stock_data['date'] = date

            return stock_data

        return pd.DataFrame()