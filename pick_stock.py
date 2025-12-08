import pandas as pd
from stock_data_fetcher import StockDataFetcher
from stock_db import StockDB
from stock_tools import StockTools
from datetime import datetime, timedelta
import time
import requests

fetcher = StockDataFetcher()
db = StockDB()
def prepare_stock(stock_code, start_date, end_date):
    #获取日K线
    fetcher.get_daily_kline(stock_code, start_date, end_date)
    #获取5分钟K线
    fetcher.get_min_kline(stock_code, '5', start_date, end_date)
    #获取15分钟K线
    fetcher.get_min_kline(stock_code, '15', start_date, end_date)

def predict_stock(stock_code, datetime):
    # 计算 end_date 保持为 datetime 对象
    end_date_obj = datetime - timedelta(days=1)
    # 计算 start_date 保持为 datetime 对象
    start_date_obj = end_date_obj - timedelta(days=365)
    
    # 转换为字符串格式
    end_date = end_date_obj.strftime("%Y-%m-%d")
    start_date = start_date_obj.strftime("%Y-%m-%d")

    pd_data = fetcher.get_daily_kline(stock_code, start_date, end_date)

    history_data_for_chart = []
    for _, row in pd_data.iterrows():
        timestamp = row.get('timestamp', row.get('date', ''))
        if hasattr(timestamp, 'strftime'):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(timestamp)
        
        history_data_for_chart.append({
            "timestamps": timestamp_str,
            "open": float(row.get('open', 0)),
            "high": float(row.get('high', 0)),
            "low": float(row.get('low', 0)),
            "close": float(row.get('close', 0)),
            "volume": float(row.get('volume', 0))
        })

    predict_request = {
        "predict_len": 1,
        "data": history_data_for_chart
    }

    # 目标服务地址
    target_url = "http://127.0.0.1:6030/predict"

    # 发送请求
    response = requests.post(
        target_url,
        json=predict_request,
        timeout=60
    )

    response_data = response.json()
    prediction_data=response_data['prediction']

    return prediction_data

if __name__ == '__main__':
    pd_data = fetcher.get_all_stock_info()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

    for _, row in pd_data.iterrows():
        stock_code = row.get('stock_code')
        stock_name = row.get('stock_name')
        if stock_code:
            print(f"开始处理 {stock_name}({stock_code})")
            prepare_stock(stock_code, start_date=start_date, end_date=end_date)

            for i in range(1, 100):
                p_date = datetime.now() - timedelta(days=i)
                p_data = db.get_predict_daily_data(stock_code, p_date.strftime("%Y-%m-%d"))
                if not p_data.empty:
                    continue
                predict_data = predict_stock(stock_code, datetime.now() - timedelta(days=i))
                db.save_predict_daily_data(stock_code, p_date.strftime("%Y-%m-%d"), predict_data[0])
                



