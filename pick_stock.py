import pandas as pd
from stock_data_fetcher import StockDataFetcher
from stock_db import StockDB
from stock_tools import StockTools
from datetime import datetime, timedelta
from stock_akshare import StockAKShare
import time
import requests

class StockPicker:
    def __init__(self):
        self._fetcher = StockDataFetcher()
        self._db = StockDB()
        self._tools = StockTools()
        self._akshare = StockAKShare()
        self.process_count = 0
        self.is_running = False
        self.total_count = 0
        self.prepare_running = False
        self.prepare_count = 0
        self.prepare_total_count = 0
        self.interrupt_prepare = False
        self.interrupt_pick = False

    def prepare_stock(self, console_print=False):
        """
            准备股票数据
            每日0点之后执行，提前准备日k线数据
            从api获取之后sleep两秒，防止api调用过于频繁
            1800只股票准备一次数据大约1-2小时
        """ 
        self.prepare_running = True
        self.interrupt_prepare = False
        pd_data = self._fetcher.get_all_stock_info()
        last_date, current_date, predict_date = self._get_trade_date()
    
        self.prepare_count = 0
        self.prepare_total_count = len(pd_data)

        for _, row in pd_data.iterrows():  
            stock_code = row.get('stock_code')
            stock_name = row.get('stock_name')
            self._fetcher.get_daily_kline(stock_code, last_date, last_date, sleep_time=2)

            self.prepare_count = self.prepare_count + 1

            if self.interrupt_prepare:
                self.interrupt_prepare = False
                break

            # 计算百分比
            percent = (self.prepare_count / self.prepare_total_count) * 100
            # 可视化进度条（长度为20）
            bar_length = 40
            filled_length = int(bar_length * self.prepare_count / self.prepare_total_count)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            if console_print:
                # 输出进度条（\r 覆盖，end='' 不换行）
                print(f"\r进度: [{bar}] {percent:.1f}% {self.prepare_count}/{self.prepare_total_count} {stock_name}({stock_code})          ", end='', flush=True)
            else:
                print(f"进度: [{bar}] {percent:.1f}% {self.prepare_count}/{self.prepare_total_count} {stock_name}({stock_code})")

        self.prepare_running = False

    def _predict_stock(self, stock_code, datetime, current_data = pd.DataFrame()):
        end_date = self._tools.get_trading_day(datetime, delta=-1)
        start_date = self._tools.get_trading_day(datetime, delta=-200)
        
        pd_data = self._fetcher.get_daily_kline(stock_code, start_date, end_date)

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

        # 如果存在今日数据，就加入，然后预测明天的
        if not current_data.empty:
            history_data_for_chart.append({
                "timestamps": datetime + " 00:00:00",
                "open": float(current_data['open'].iloc[0]),
                "high": float(current_data['high'].iloc[0]),
                "low": float(current_data['low'].iloc[0]),
                "close": float(current_data['close'].iloc[0]),
                "volume": float(current_data['volume'].iloc[0])
            })

        predict_request = {
            "predict_len": 1,
            "data": history_data_for_chart
        }

        # 目标服务地址
        target_url = "http://192.168.1.180:6030/predict"

        # 发送请求
        response = requests.post(
            target_url,
            json=predict_request,
            timeout=60
        )

        try:
            response_data = response.json()
            prediction_data=response_data['prediction']
        except Exception as e:
            print(f"请求失败: {response}")
            print(f"请求失败: {len(history_data_for_chart)}")
            print(f"请求失败: {e}")
        
        return prediction_data

    def _get_trade_date(self):
        """
        获取交易日，返回前一个交易日，当前交易日，预测交易日（下一个）
        """
        now = datetime.now()

        predict_date = self._tools.get_trading_day(now, delta=1)

        if self._tools.is_trading_day(now):
            current_date = self._tools.get_trading_day(now, 0)
        else:
            current_date = self._tools.get_trading_day(now, -1)

        last_date = self._tools.get_trading_day(current_date, -1)

        return last_date, current_date, predict_date

    def _is_right_predict(self, stock_code, p_data, data, datetime):
        prev_date = self._tools.get_trading_day(datetime, -1)
        prev_data = self._fetcher.get_daily_kline(stock_code, prev_date, prev_date)

        try:
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
        except Exception as e:
            return False

    def pick_up_stock(self, console_print=False):
        self.is_running = True
        self.interrupt_pick = False

        pick_up_stocks = []

        pd_data = self._fetcher.get_all_stock_info()

        self._fetcher.fetch_current_date()

        self.process_count = 0
        self.total_count = len(pd_data)

        last_date, current_date, predict_date = self._get_trade_date()

        #计算好交易日
        print(f"上个交易日{last_date}")
        print(f"当前交易日{current_date}")
        print(f"预测交易日{predict_date}")

        for _, row in pd_data.iterrows():  
            stock_code = row.get('stock_code')
            stock_name = row.get('stock_name')

            self.process_count = self.process_count + 1

            if self.interrupt_pick:
                self.interrupt_pick = False
                break

            # 计算百分比
            percent = (self.process_count / self.total_count) * 100
            # 可视化进度条（长度为20）
            bar_length = 40
            filled_length = int(bar_length * self.process_count / self.total_count)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)

            if console_print:
                # 输出进度条（\r 覆盖，end='' 不换行）
                print(f"\r进度: [{bar}] {percent:.1f}% {self.process_count}/{self.total_count} {stock_name}({stock_code})          ", end='', flush=True)
            else:
                print(f"进度: [{bar}] {percent:.1f}% {self.process_count}/{self.total_count} {stock_name}({stock_code})\r\n")

            #获取上一个交易日的股票数据与预测数据
            try:
                lastdate_data = self._fetcher.get_daily_kline(stock_code, last_date, last_date)
                lastdate_p_data = self._db.get_predict_daily_data(stock_code, last_date)
                if lastdate_p_data.empty:
                    tmp = self._predict_stock(stock_code, last_date)
                    self._db.save_predict_daily_data(stock_code, last_date, tmp[0])
                    lastdate_p_data = self._db.get_predict_daily_data(stock_code, last_date)

                if not self._is_right_predict(stock_code, lastdate_p_data, lastdate_data, last_date):
                    continue
            except Exception as e:
                print(f"获取上一个交易日的股票数据失败: {stock_code} {e}")
                continue
            
            #获取当前交易日的股票数据与预测数据
            try:
                current_data = self._db.get_realtime_daily_data(stock_code, current_date)
                if current_data.empty:
                    self._fetcher.fetch_current_date(current_date)
                    current_data = self._db.get_realtime_daily_data(stock_code, current_date)
                    if current_data.empty:
                        continue

                curdate_p_data = self._db.get_predict_daily_data(stock_code, current_date)
                if curdate_p_data.empty:
                    tmp = self._predict_stock(stock_code, current_date)
                    self._db.save_predict_daily_data(stock_code, current_date, tmp[0])
                    curdate_p_data = self._db.get_predict_daily_data(stock_code, current_date)

                if not self._is_right_predict(stock_code, curdate_p_data, current_data, current_date):
                    continue
            except Exception as e:
                print(f"获取当前交易日的股票数据失败: {stock_code} {e}")
                continue

            #预测下一个交易日数据，并存储
            try:
                predict_data = self._predict_stock(stock_code, current_date, current_data)
                increase = (predict_data[0]['close'] - current_data['close'].iloc[0]) / current_data['close'].iloc[0]

                pick_up_stocks.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "date": predict_date,
                    "open": predict_data[0]['open'],
                    "close": predict_data[0]['close'],
                    "high": predict_data[0]['high'],
                    "low": predict_data[0]['low'],
                    "increase": increase
                })
            except Exception as e:
                print(f"预测股票数据失败: {stock_code}")
                continue

        #按increase从大到小排序
        sorted_stocks = sorted(pick_up_stocks, key=lambda x: x['increase'], reverse=True)

        #筛选出increase大于0.02的股票
        filtered_stocks = [stock for stock in sorted_stocks if stock['increase'] > 0.02]

        #处理数量：至少选3个，不够则取最大的3个
        if len(filtered_stocks) >= 5:
            selected_stocks = filtered_stocks  # 筛选后足够，直接取筛选结果
        else:
            # 筛选后不足3个，取排序后的前3个
            selected_stocks = sorted_stocks[:5]

        self.is_running = False

        return selected_stocks

if __name__ == '__main__':
    selected_stocks = StockPicker().pick_up_stock(console_print=True)
    for stock in selected_stocks:
        print(f"股票代码：{stock['stock_code']}，股票名称：{stock['stock_name']}，涨幅：{stock['increase']}")

        

        

