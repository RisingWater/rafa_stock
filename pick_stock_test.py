import pandas as pd
from stock_data_fetcher import StockDataFetcher
from stock_db import StockDB
from stock_tools import StockTools
from datetime import datetime, timedelta
import time
import requests

import logging

logger = logging.getLogger(__name__)

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

def predict_all_stock_price():
    pd_data = fetcher.get_all_stock_info()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

    for _, row in pd_data.iterrows():
        stock_code = row.get('stock_code')
        stock_name = row.get('stock_name')
        if stock_code:
            logger.info(f"开始处理 {stock_name}({stock_code})")
            prepare_stock(stock_code, start_date=start_date, end_date=end_date)

            for i in range(0, 100):
                p_date = datetime.now() - timedelta(days=i)
                if StockTools().is_trading_day(p_date):
                    p_data = db.get_predict_daily_data(stock_code, p_date.strftime("%Y-%m-%d"))
                    if not p_data.empty:
                        continue
                    predict_data = predict_stock(stock_code, p_date)
                    db.save_predict_daily_data(stock_code, p_date.strftime("%Y-%m-%d"), predict_data[0])

def get_stock_daily_infos(stock_code, date : str):
    """
    获取指定日期及前一天的股票数据
    返回: (预测数据, 当日数据, 前一日数据)
    如果任何数据为空，返回(None, None, None)
    """
    # 获取预测数据
    predict_data = db.get_predict_daily_data(stock_code, date)
    if predict_data.empty:
        return None, None, None
    
    # 获取当日数据
    actual_data = db.get_daily_data(stock_code, date, date)
    if actual_data.empty:
        return None, None, None
    
    # 获取前一日数据
    prev_date = StockTools().get_trading_day(date, -1)
    
    prev_actual_data = db.get_daily_data(stock_code, prev_date, prev_date)
    if prev_actual_data.empty:
        return None, None, None
    
    return predict_data, actual_data, prev_actual_data

def is_right_predict(date):
    p_data, data, prev_data = get_stock_daily_infos(stock_code, date)

    if p_data is None or data is None or prev_data is None:  # 获取数据失败
        return False

    prev_close = prev_data['close'].iloc[0]
    p_close = p_data['close'].iloc[0]
    data_close = data['close'].iloc[0]

    increase = data_close - prev_close
    p_increase = p_close - prev_close

    if increase > 0.09:
        #涨幅过大
        return False

    if increase * p_increase > 0 :
        rate = abs(increase - p_increase) / abs(data_close)
        if rate < 0.01 :
            return True

    return False



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    success = 0
    total = 0
    total_money = 100000
    pd_data = fetcher.get_all_stock_info()
    now = datetime.now()
    for _, row in pd_data.iterrows():  
        stock_code = row.get('stock_code')
        stock_name = row.get('stock_name')
        
        right_days = 0
        if stock_code:   
            for i in range(0, 300): 
                p_date = StockTools().get_trading_day(now, delta=-i)

                if right_days >= 2:
                    p_data, data, prev_data = get_stock_daily_infos(stock_code, p_date)

                    if p_data is None or data is None or prev_data is None:  # 获取数据失败
                        continue

                    actual_high = data['high'].iloc[0]    # 当日最高价
                    actual_close = data['close'].iloc[0]    # 当日最高价
                    predict_close = p_data['close'].iloc[0]  # 预测收盘价
                        
                    prev_close = prev_data['close'].iloc[0]

                    #如果以昨天收盘价买入
                    hand_price = prev_close * 100 #一手的价格
                    hands = int(total_money / hand_price) #一共可以买几手
                    volume = hands * 100 #一共可以买几股
                    cash = total_money - (volume * prev_close) #剩余的现金

                    increase_rate = (actual_high - prev_close) / prev_close
                    p_increase_rate = (predict_close - prev_close) / prev_close

                    if p_increase_rate > 0.02:
                        total = total + 1
                        if increase_rate > 0.02:
                            #以上涨2%的价格卖出
                            total_money = prev_close * 1.02 * volume + cash
                            logger.info(f"股票: {stock_code} {stock_name} {p_date}上涨预测ok, 前一日尾盘{prev_close}买入，以2%涨幅{prev_close * 1.02}卖出")
                            success = success + 1
                        else:
                            #以收盘价卖出
                            total_money = actual_close * volume + cash
                            logger.info(f"股票: {stock_code} {stock_name} {p_date}上涨预测failed, 前一日尾盘{prev_close}买入，以{actual_close}卖出，实际{increase_rate:.2f}%")

                        logger.info(f"账户余额: {total_money:.2f}")

                    right_days = 0

                right = is_right_predict(p_date)
                    
                if right:
                    right_days += 1
                else:
                    right_days = 0

    logger.info(f"预测完成，共{total}个交易日，其中{success}个交易日预测正确, 胜率为{success/total:.2%}")
    logger.info(f"本金100000，尾盘选股后，余额{total_money:.2f},利润率{total_money/100000:.2%}")
                
                



