# stock_tools.py
import chinese_calendar as calendar
from datetime import datetime, timedelta

class StockTools:
    def __init__(self):
        pass
    
    def get_trading_day(self, date, delta=1):
        """
        获取下第N个交易日（支持正负值）
        
        参数:
        - date: 起始日期 (str或datetime)
        - delta: 要获取的第N个交易日，可以为正数、负数或0
                >0: 获取未来的第N个交易日
                <0: 获取过去的第N个交易日
                =0: 获取最近的交易日（如果当前是交易日则返回当前，否则返回下一个）
        
        返回:
        - 目标交易日的日期字符串 (格式: 'YYYY-MM-DD') 或 None
        """
        try:
            # 转换日期格式
            if isinstance(date, str):
                date_obj = datetime.strptime(date, '%Y-%m-%d')
            else:
                date_obj = date
            
            # delta=0 的特殊处理
            if delta == 0:
                # 检查当前日期是否是交易日
                if self.is_trading_day(date_obj):
                    return date_obj.strftime('%Y-%m-%d')
                else:
                    # 不是交易日，则获取下一个交易日
                    delta = 1
            
            current = date_obj
            found_count = 0
            step = 1 if delta > 0 else -1
            target_count = abs(delta)
            
            # 设置最大搜索天数
            max_days = 365  # 最大搜索365天，避免无限循环
            
            for i in range(max_days):
                # 移动到下一天（或前一天）
                current += timedelta(days=step)
                
                # 检查是否是交易日
                if self.is_trading_day(current):
                    found_count += 1
                    
                    # 找到目标交易日
                    if found_count == target_count:
                        return current.strftime('%Y-%m-%d')
            
            # 如果循环结束还没找到
            direction = "未来" if delta > 0 else "过去"
            print(f"警告: 在{max_days}天内未找到{direction}的第{target_count}个交易日")
            return None
            
        except Exception as e:
            print(f"获取下第{delta}个交易日失败: {e}")
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
    

class GridBaseLine:
    def __init__(self, price: float, volume: int):
        self.price = price
        self.volume = volume