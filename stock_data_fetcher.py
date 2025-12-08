import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from stock_tools import StockTools
from stock_akshare import StockAKShare
from stock_db import StockDB

class StockDataFetcher:
    """
    股票数据获取类
    使用akshare获取股票日K线数据
    """
    
    def __init__(self):
        pass
    def get_daily_kline(self, stock_code, start_date=None, end_date=None):
        """
        获取股票日K线数据 - 简化缓存版本
        """
        # 设置默认时间范围
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # 修正结束日期为交易日
        tools = StockTools()
        end_date = tools.get_trading_day(end_date, 0)
        
        try:
            db = StockDB()

            # 先检查最新日期
            latest_db_date = db.get_latest_daily_date(stock_code)

            # 如果数据库中已经有数据且覆盖了请求范围，直接返回
            if latest_db_date and latest_db_date >= end_date:
                db_data = db.get_daily_data(stock_code, start_date, end_date)
                return db_data
            else:
                # 否则从API获取数据并更新数据库
                # 直接获取1000天的数据，确保数据完整
                one_year_ago = (datetime.now() - timedelta(days=1000)).strftime("%Y%m%d")
                full_data = StockAKShare().get_daily_kline_from_api(stock_code, one_year_ago, end_date.replace('-', ''))

                if not full_data.empty:
                    db.save_daily_data(stock_code, full_data)
                    print(f"✅ 更新一年数据成功: {len(full_data)} 条")
                    
                    # 从完整数据中提取请求的时间范围
                    update_data = full_data[
                        (full_data['date'] >= pd.to_datetime(start_date)) & 
                        (full_data['date'] <= pd.to_datetime(end_date))
                    ]
                    return update_data
                else:
                    print("⚠️ 未获取到API数据")
                    return pd.DataFrame()
                    
        except Exception as e:
            print(f"❌ 获取daily数据失败: {e}")
            return pd.DataFrame()
            
    def get_min_kline(self, stock_code, period='5', start_date=None, end_date=None, realtime=False, adjust=''):
        """
        获取股票分钟K线数据 - 支持缓存
        
        参数:
            stock_code (str): 股票代码
            period (str): 时间周期 '1', '5', '15', '30', '60'
            start_date (str): 开始日期 "YYYY-MM-DD"，默认今天
            end_date (str): 结束日期 "YYYY-MM-DD"，默认今天
            adjust (str): 复权类型
            
        返回:
            pandas.DataFrame: 分钟K线数据
        """
        # 设置默认日期范围（今天）
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # 修正结束日期为交易日
        tools = StockTools()
        # 提取纯日期部分（去掉时间）
        end_date_only = end_date.split(' ')[0] if ' ' in end_date else end_date
        start_date_only = start_date.split(' ')[0] if ' ' in start_date else start_date

        # 修正结束日期为交易日
        corrected_end_date = tools.get_trading_day(end_date_only, 0) or end_date_only
        
        # 转换为完整的时间范围（9:30-15:00）
        start_datetime = f"{start_date_only} 09:30:00"
        if not realtime:
            end_datetime = f"{corrected_end_date} 15:00:00"
        else:
            end_datetime = end_date
        
        try:
            db = StockDB()
            
            # 获取数据库中最新的分钟数据时间
            latest_min_datetime = db.get_latest_min_datetime(stock_code, period)
            
            # 如果数据库中有数据且覆盖了请求范围，直接返回
            if latest_min_datetime and latest_min_datetime >= end_datetime:
                db_data = db.get_min_data(stock_code, period, start_datetime, end_datetime)
                return db_data
            else:
                # 数据库数据不够新，从API获取最新数据
                print(f"🔄 数据库数据不够新，从API获取最新{period}分钟数据")
                api_data = StockAKShare().get_all_min_kline_from_api(stock_code, period=period, adjust=adjust)
                
                if not api_data.empty:
                    # 保存到数据库
                    db.save_min_data(stock_code, period, api_data)
                    print(f"💾 已保存{period}分钟数据到数据库: {len(api_data)} 条")
                    
                    # 从完整数据中提取请求的时间范围
                    filtered_data = api_data[
                        (api_data['datetime'] >= pd.to_datetime(start_datetime)) & 
                        (api_data['datetime'] <= pd.to_datetime(end_datetime))
                    ]
                    return filtered_data
                
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ 获取{period}分钟K线数据失败: {e}")
            return pd.DataFrame()

    def get_daily_end_price(self, stock_code: str, current_datetime: datetime) -> float:
        try:
            db = StockDB()

            db_data = db.get_daily_data(stock_code, current_datetime.strftime("%Y-%m-%d"), current_datetime.strftime("%Y-%m-%d"))

            if db_data.empty:
                print(f"没有数据")
                return None
            
            return float(db_data['close'].iloc[0])
        
        except Exception as e:
            print(f"❌ 获取价格失败: {e}")
            return None

    def get_daily_start_price(self, stock_code: str, current_datetime: datetime) -> float:
        try:
            db = StockDB()

            db_data = db.get_daily_data(stock_code, current_datetime.strftime("%Y-%m-%d"), current_datetime.strftime("%Y-%m-%d"))

            if db_data.empty:
                print(f"没有数据")
                return None
            
            return float(db_data['open'].iloc[0])
        
        except Exception as e:
            print(f"❌ 获取价格失败: {e}")
            return False
            
    def get_price(self, stock_code: str, period: str, current_datetime: datetime) -> float:
        try:
            db = StockDB()

            current_datetime += timedelta(minutes=15)
            
            # 统一转换为datetime对象
            if isinstance(current_datetime, str):
                current_dt = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
            else:
                current_dt = current_datetime
            
            # 获取数据库中最新的分钟数据时间
            latest_min_datetime = db.get_latest_min_datetime(stock_code, period)
            
            if latest_min_datetime is None:
                print(f"{stock_code} 没有数据")
                return None
            
            # 如果latest_min_datetime是字符串，也转换为datetime
            if isinstance(latest_min_datetime, str):
                latest_dt = datetime.strptime(latest_min_datetime, '%Y-%m-%d %H:%M:%S')
            else:
                latest_dt = latest_min_datetime
            
            # 现在用datetime对象比较
            if latest_dt < current_dt:
                print(f"{stock_code} 的最新5分钟数据已经更新，请勿重复获取")
                return None
            
            # 获取数据时使用字符串格式
            current_datetime_str = current_dt.strftime('%Y-%m-%d %H:%M:%S')
            db_data = db.get_min_data(stock_code, period, current_datetime_str, current_datetime_str)

            if db_data.empty:
                print(f"{current_datetime_str}没有数据")
                return None
            
            return float(db_data['open'].iloc[0])
        
        except Exception as e:
            print(f"❌ 获取价格失败: {e}")
            return False

    def is_trade_success(self, stock_code: str, period: str, price: float, quantity: int, action: str, current_datetime: str) -> bool:
        """判断交易是否成功"""
        try:
            db = StockDB()
            
            # 统一转换为datetime对象
            if isinstance(current_datetime, str):
                current_dt = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
            else:
                current_dt = current_datetime
            
            # 获取数据库中最新的分钟数据时间
            latest_min_datetime = db.get_latest_min_datetime(stock_code, period)
            
            if latest_min_datetime is None:
                return False
                
            # 如果latest_min_datetime是字符串，也转换为datetime
            if isinstance(latest_min_datetime, str):
                latest_dt = datetime.strptime(latest_min_datetime, '%Y-%m-%d %H:%M:%S')
            else:
                latest_dt = latest_min_datetime
            
            # 现在用datetime对象比较
            if latest_dt < current_dt:
                return False
            
            # 获取数据时使用字符串格式
            current_datetime_str = current_dt.strftime('%Y-%m-%d %H:%M:%S')
            db_data = db.get_min_data(stock_code, period, current_datetime_str, current_datetime_str)

            if db_data.empty:
                return False

            low = float(db_data['low'].iloc[0])
            high = float(db_data['high'].iloc[0])

            return low <= price <= high
            
        except Exception as e:
            print(f"❌ 获取判断交易成功与否失败: {e}")
            return False
    
    def get_all_stock_info(self):
        db = StockDB()

        pd = db.get_stock_info()

        if pd.empty:
            zz1000 = StockAKShare().get_zz1000_stockinfo_from_api()
            db.save_stock_info(zz1000)

            hs300 = StockAKShare().get_hs300_stockinfo_from_api()
            db.save_stock_info(hs300)

            pd = db.get_stock_info()

            if pd.empty:
                print("❌ 获取股票信息失败")
        
        return pd

