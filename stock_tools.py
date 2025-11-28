# stock_tools.py
import chinese_calendar as calendar
from datetime import datetime, timedelta

class StockTools:
    def __init__(self):
        pass
    
    def get_previous_trading_day(self, date):
        """
        获取上一个交易日
        """
        try:
            if isinstance(date, str):
                date_obj = datetime.strptime(date, '%Y-%m-%d')
            else:
                date_obj = date
            
            current = date_obj
            
            # 最多找30天，避免无限循环
            for _ in range(30):
                if calendar.is_workday(current) and current.weekday() < 5:
                    return current.strftime('%Y-%m-%d')
                current -= timedelta(days=1)
            
            return None
            
        except Exception as e:
            print(f"获取上一个交易日失败: {e}")
            return None
    
    def is_trading_day(self, date):
        """
        判断是否为交易日
        """
        try:
            if isinstance(date, str):
                date_obj = datetime.strptime(date, '%Y-%m-%d')
            else:
                date_obj = date
            
            return calendar.is_workday(date_obj) and date_obj.weekday() < 5
            
        except Exception as e:
            print(f"判断交易日失败: {e}")
            return False