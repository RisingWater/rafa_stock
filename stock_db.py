# stock_db.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

class StockDB:
    def __init__(self, db_path='stock_data.db'):
        self.db_path = db_path
        self._init_daily_database()
        self._init_min_database()  # 只需要初始化统一分钟表
    
    def _init_daily_database(self):
        """初始化日线数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_kline (
                stock_code TEXT,
                date DATE,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER, amount REAL, 
                PRIMARY KEY (stock_code, date)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stock_date ON daily_kline(stock_code, date)')
        conn.commit()
        conn.close()
    
    def _init_min_database(self):
        """初始化统一分钟数据表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建统一分钟K线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS minute_kline (
                stock_code TEXT,
                period TEXT,
                datetime DATETIME,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER,
                PRIMARY KEY (stock_code, period, datetime)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_minute_stock_period_datetime ON minute_kline(stock_code, period, datetime)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_minute_datetime ON minute_kline(datetime)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_minute_period ON minute_kline(period)')
        
        conn.commit()
        conn.close()
    
    def save_daily_data(self, stock_code, kline_data):
        """保存日K线数据"""
        if kline_data.empty:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for _, row in kline_data.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_kline 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_code, row['date'].strftime('%Y-%m-%d'),
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume'], row.get('amount', 0)
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False
    
    def save_min_data(self, stock_code, period, kline_data):
        """
        保存分钟K线数据到统一分钟表
        """
        if kline_data.empty:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for _, row in kline_data.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO minute_kline 
                    (stock_code, period, datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_code, period,
                    row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume']
                ))
                saved_count += 1
            
            conn.commit()
            conn.close()
            print(f"✅ 保存{period}分钟K线数据: {stock_code} - {saved_count} 条")
            return True
        except Exception as e:
            print(f"❌ 保存{period}分钟K线数据失败: {e}")
            return False

    def get_daily_data(self, stock_code, start_date, end_date):
        """获取日K线数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT * FROM daily_kline 
                WHERE stock_code = ? AND date BETWEEN ? AND ?
                ORDER BY date
            '''
            df = pd.read_sql_query(query, conn, params=[stock_code, start_date, end_date])
            conn.close()
            
            print(f"从数据库中获取{stock_code}的日K线数据成功")
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except:
            return pd.DataFrame()
  
    def get_min_data(self, stock_code, period, start_datetime, end_datetime):
        """
        从统一分钟表获取分钟K线数据
        """
        valid_periods = ['1', '5', '15', '30', '60']
        if period not in valid_periods:
            print(f"❌ 不支持的周期: {period}")
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT stock_code, datetime, open, high, low, close, volume
                FROM minute_kline 
                WHERE stock_code = ? AND period = ? AND datetime BETWEEN ? AND ?
                ORDER BY datetime
            '''
            df = pd.read_sql_query(query, conn, params=[stock_code, period, start_datetime, end_datetime])
            conn.close()
            
            if not df.empty:
                df['datetime'] = pd.to_datetime(df['datetime'])
                print(f"✅ 获取{period}分钟数据: {stock_code} - {len(df)} 条")
            
            return df
            
        except Exception as e:
            print(f"❌ 获取{period}分钟K线数据失败: {e}")
            return pd.DataFrame()
        
    def get_latest_daily_date(self, stock_code):
        """获取日线最新数据日期"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(date) FROM daily_kline WHERE stock_code = ?
            ''', (stock_code,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] else None
        except:
            return None        

    def get_latest_min_datetime(self, stock_code, period):
        """获取分钟线的最新数据时间"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(datetime) FROM minute_kline 
                WHERE stock_code = ? AND period = ?
            ''', (stock_code, period))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] else None
        except:
            return None