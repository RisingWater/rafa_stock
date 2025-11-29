import logging
import os
from datetime import datetime, timedelta
from stock_data_fetcher import StockDataFetcher
from deepseek import DeepSeekAPI
from stock_tools import StockTools
from dotenv import load_dotenv

load_dotenv()

class PromptGenerator:
    def __init__(self):
        self.daily_kline_days = int(os.environ.get("DAYLI_KLINE_DAYS"))
        self.min15_kline_days = int(os.environ.get("MIN15_KLINE_DAYS"))

    def generate_prompt(self, stock_name: str, stock_code: str, account: TPlusOneStockAccount, current_datetime: datetime):
        prompt_header = f"你是一个专业的短线股票操盘手，擅长日内盘，做T或反T，现在你在操盘股票{stock_name},代码{stock_code}，当前时间是{current_datetime}。\n"
        prompt_header += f"你操作的是中国大陆A股市场，是T+1的市场，今日买入明日才能卖出，手续费买入卖出为5元，印花税万分之5\n"
        fetcher = StockDataFetcher()

        daily_start_time = (current_datetime - timedelta(days=self.daily_kline_days)).strftime("%Y-%m-%d")
        daily_end_time = current_datetime.strftime("%Y-%m-%d")

        daily_data = fetcher.get_daily_kline(stock_code, daily_start_time, daily_end_time)

        min15_start_time = (current_datetime - timedelta(days=self.min15_kline_days)).strftime("%Y-%m-%d")
        min15_end_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        min15_data = fetcher.get_min_kline(stock_code, "15", min15_start_time, min15_end_time, realtime=True)
        
        daily_data_str = "这只股票近期的日K线数据:\n" + daily_data.to_string() + "\n"
        min15_data_str = "这只股票近期的15分钟K线数据:\n" + min15_data.to_string() + "\n"

        current_price = min15_data['close'].iloc[-1]
        current_prices = {stock_code: current_price}
        account_prompt = "你的账户情况:\n" + account.get_portfolio_summary(current_prices)
        history_prompt = "你的历史操作与说明:\n" + account.get_recent_decisions_summary()

        prompt_end = " 请根据以上信息，给出你的操作建议。输出格式为json，包含以下字段：\n"
        prompt_end += "datetime 操作时间格式%Y-%m-%d %H:%M:%S\n"
        prompt_end += "action, 操作buy/sell/none\n"
        prompt_end += "stock_code 股票代码\n"
        prompt_end += "price 买入或者卖出价格,如果操作为none为0\n"
        prompt_end += "quantity 买入卖出手数，必须为100的倍数\n"
        prompt_end += "reason 操作的原因，50字以内\n"
        prompt_end += "stop_loss 止损价格, take_profit 止盈价格，买入必须给，如果是反T操作则按照做空给出止损和止盈价格\n"
        prompt_end += "交易可能有1-2分钟延迟，请买入或者卖出价格时候请注意留余量\n"
        prompt_end += "只需要给出json，不要输出任何其它内容\n"

        return prompt_header + daily_data_str + min15_data_str + account_prompt + history_prompt + prompt_end

if __name__ == "__main__":
    my_account = TPlusOneStockAccount(initial_cash=100000)
    fetcher = StockDataFetcher()

    #stock_code = '002396'
    #stock_name = '星网锐捷'
    stock_code = '002170'
    stock_name = '芭田股份'

    start_date = datetime(2025, 9, 1)  # 使用datetime构造函数
    end_date = datetime(2025, 11, 28)
    cur_date = start_date

    while cur_date <= end_date:
        # 检查是否为交易日
        if not StockTools().is_trading_day(cur_date):
            cur_date += timedelta(days=1)
            continue
        
        decision_times = [
            "09:30:00",
            "09:45:00", 
            "10:00:00",
            "10:15:00",
            "10:30:00",
            "10:45:00",
            "11:00:00",
            "11:15:00",
            "13:00:00",
            "13:15:00",
            "13:30:00",
            "13:45:00",
            "14:00:00",
            "14:15:00",
            "14:30:00",
            "14:45:00"
        ]
        
        for decision_time in decision_times:
            # 构建完整的datetime对象
            cur_datetime = datetime.combine(cur_date.date(), 
                                          datetime.strptime(decision_time, "%H:%M:%S").time())
            
            current_price = fetcher.get_price(stock_code, '15', cur_datetime)
            print(f"\n=== 决策时间: {cur_datetime} 当前价格: {current_price} ===")
            
            current_prices = {stock_code : current_price}
            print(f"\n=== 仓位情况: {my_account.get_portfolio_summary(current_prices)}")

            availiable_quantity = my_account.availiable_quantity(stock_code)
            if availiable_quantity == 0 and my_account.cash < 100 * current_price:
                print(f"=== 账户可售股票为0，且资金不足, 无法买入股票，跳过此决策===")
                continue
            
            try:
                prompt = PromptGenerator().generate_prompt(stock_name, stock_code, my_account, cur_datetime)
            
                deepseek_api = DeepSeekAPI()
                response = deepseek_api.ask_question(prompt)
            
                decision = TradeDecision.from_json(response)
                
                if decision.action == "buy":
                    if fetcher.is_trade_success(decision.stock_code, '15', decision.price, decision.quantity, 'buy', cur_datetime + timedelta(minutes=15)):
                        success = my_account.buy(decision.stock_code, decision.price, decision.quantity, decision)
                        if success:
                            print(f"成功买入 {decision.stock_code} {decision.quantity}股 @ {decision.price}")
                            print(f"操作说明: {decision.reason}")
                            print(f"止损点: {decision.stop_loss:.2f}")
                            print(f"止盈点: {decision.take_profit:.2f}")
                elif decision.action == "sell":
                    if fetcher.is_trade_success(decision.stock_code, '15', decision.price, decision.quantity, 'buy', cur_datetime + timedelta(minutes=15)):
                        success = my_account.sell(decision.stock_code, decision.price, decision.quantity, decision)
                        if success:
                            print(f"{cur_datetime} 成功卖出 {decision.stock_code} {decision.quantity}股")
                            print(f"操作说明: {decision.reason}")
                else:
                    print(f"操作说明: {decision.reason}")
                                    
            except Exception as e:
                print(f"决策解析失败: {e}")
                continue

        # 进入下一个交易日
        cur_date += timedelta(days=1)
        my_account.next_trading_day()
        
        # 显示每日总结
        print(f"\n=== {cur_date.strftime('%Y-%m-%d')} 交易日结束 ===")
        my_account.display_portfolio()
