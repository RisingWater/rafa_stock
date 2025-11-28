import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from stock_tools import StockTools
from stock_akshare import StockAKShare

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

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
        end_date = tools.get_previous_trading_day(end_date)
        
        try:
            from stock_db import StockDB
            db = StockDB()

            # 先检查最新日期
            latest_db_date = db.get_latest_daily_date(stock_code)

            # 如果数据库中已经有数据且覆盖了请求范围，直接返回
            if latest_db_date and latest_db_date >= end_date:
                db_data = db.get_daily_data(stock_code, start_date, end_date)
                print(f"✅ 从数据库读取 {stock_code} 数据: {len(db_data)} 条")
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
            
    def get_min_kline(self, stock_code, period='5', start_date=None, end_date=None, adjust=''):
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
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        # 修正结束日期为交易日
        tools = StockTools()
        # 提取纯日期部分（去掉时间）
        end_date_only = end_date.split(' ')[0] if ' ' in end_date else end_date
        start_date_only = start_date.split(' ')[0] if ' ' in start_date else start_date
        
        # 修正结束日期为交易日
        corrected_end_date = tools.get_previous_trading_day(end_date_only) or end_date_only
        
        # 转换为完整的时间范围（9:30-15:00）
        start_datetime = f"{start_date_only} 09:30:00"
        end_datetime = f"{corrected_end_date} 15:00:00"
        
        print(f"📊 请求分钟数据范围: {start_datetime} 到 {end_datetime}")
        
        try:
            from stock_db import StockDB
            db = StockDB()
            
            # 获取数据库中最新的分钟数据时间
            latest_min_datetime = db.get_latest_min_datetime(stock_code, period)
            
            # 如果数据库中有数据且覆盖了请求范围，直接返回
            if latest_min_datetime and latest_min_datetime >= end_datetime:
                db_data = db.get_min_data(stock_code, period, start_datetime, end_datetime)
                print(f"✅ 从数据库读取{period}分钟数据: {stock_code} - {len(db_data)} 条")
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
     
# 使用示例
if __name__ == "__main__":
    # 创建数据获取器实例
    fetcher = StockDataFetcher()
    
    # 获取最近100天的数据
    print("=== 获取最近180天数据 ===")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=50)).strftime("%Y-%m-%d")
    
    daily_data = fetcher.get_daily_kline("000063", start_date, end_date)

    min5_data = fetcher.get_min_kline("000063", '5', "2025-01-01 09:30:00", "2025-11-28 15:00:00")

    min15_data = fetcher.get_min_kline("000063", '15', "2025-01-01 09:30:00", "2025-11-28 15:00:00")
    

    
#    if not data.empty:
#        print(f"数据时间范围: {data['date'].min()} 到 {data['date'].max()}")
#        
#        # 画K线图
#        plt.figure(figsize=(12, 8))
#        
#        # 绘制K线图
#        plt.subplot(2, 1, 1)
#        
#        # 遍历每个交易日画K线
#        for i in range(len(data)):
#            date = data['date'].iloc[i]
#            open_price = data['open'].iloc[i]
#            close_price = data['close'].iloc[i]
#            high = data['high'].iloc[i]
#            low = data['low'].iloc[i]
#            
#            # 判断涨跌颜色
#            if close_price >= open_price:
#                color = 'red'  # 上涨为红色
#                body_bottom = open_price
#                body_height = close_price - open_price
#            else:
#                color = 'green'  # 下跌为绿色
#                body_bottom = close_price
#                body_height = open_price - close_price
#            
#            # 画影线（上下影线）
#            plt.plot([i, i], [low, high], color='black', linewidth=1)
#            
#            # 画实体
#            if body_height > 0:
#                plt.bar(i, body_height, bottom=body_bottom, width=0.6, 
#                       color=color, edgecolor='black')
#        
#        plt.title('K线图 - 002396')
#        plt.ylabel('价格 (元)')
#        plt.grid(True, alpha=0.3)
#        
#        # 设置X轴刻度（只显示有数据的交易日）
#        plt.xticks(range(len(data)), 
#                  [date.strftime('%m-%d') for date in data['date']], 
#                  rotation=45)
#        
#        # 绘制成交量
#        plt.subplot(2, 1, 2)
#        
#        # 成交量颜色根据涨跌
#        colors = ['red' if close >= open else 'green' 
#                 for close, open in zip(data['close'], data['open'])]
#        
#        plt.bar(range(len(data)), data['volume'], color=colors, alpha=0.7)
#        plt.xlabel('交易日')
#        plt.ylabel('成交量')
#        plt.grid(True, alpha=0.3)
#        
#        # 设置X轴刻度（与K线图对齐）
#        plt.xticks(range(len(data)), 
#                  [date.strftime('%m-%d') for date in data['date']], 
#                  rotation=45)
#        
#        plt.tight_layout()
#        plt.show()
#        
#    else:
#        print("未获取到数据")