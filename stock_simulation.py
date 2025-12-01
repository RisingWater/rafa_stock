
from datetime import datetime, timedelta
from stock_account_tplus1 import TPlusOneStockAccount, TradeDecision
from stock_data_fetcher import StockDataFetcher
from deepseek import DeepSeekAPI
from stock_tools import StockTools
import os
import uuid
import json

class StockSimulation:
    def __init__(self, stock_code, stock_name, start_date, end_date, strategy, initial_cash=100000):
        self.simluation_name = f"{stock_name}({stock_code})-{start_date.strftime('%Y-%m%d')}-{end_date.strftime('%m%d')}-{strategy.name()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.uuid = str(uuid.uuid4())

        os.makedirs('./log', exist_ok=True)

        self.log_file = f"./log/{self.simluation_name}.log"
        self.decision_file = f"./log/{self.simluation_name}.json"

        self.account = None

        self._fetcher = StockDataFetcher()
        # 初始化日志文件
        self._setup_logging()
        self._setup_decision_file()
        self._data_preparation()
        self._initial_cash = initial_cash

    def set_initial_state(self, initial_cash: float):
        self.account = TPlusOneStockAccount(initial_cash)

    def _setup_logging(self):
        """设置日志文件"""
        try:
            # 清空或创建日志文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== 股票模拟交易日志 ===\n")
                f.write(f"模拟名称: {self.simluation_name}\n")
                f.write(f"uuid: {self.uuid}\n")
                f.write(f"股票: {self.stock_name}({self.stock_code})\n")
                f.write(f"期间: {self.start_date} 至 {self.end_date}\n")
                f.write(f"策略: {self.strategy.name()}\n")
                f.write("=" * 50 + "\n\n")
            print(f"日志文件已创建: {self.log_file}")
        except Exception as e:
            print(f"创建日志文件失败: {e}")

    def _log_message(self, message, to_console : bool = False):
        """将消息同时输出到控制台和日志文件"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        # 输出到控制台
        if to_console:
            print(log_entry)
        
        # 输出到文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"写入日志失败: {e}")

    def _setup_decision_file(self):
            """初始化决策记录文件"""
            try:
                with open(self.decision_file, 'w', encoding='utf-8') as f:
                    initial_data = {
                        "simulation_info": {
                            "name": self.simluation_name,
                            "uuid": self.uuid,
                            "stock_code": self.stock_code,
                            "stock_name": self.stock_name,
                            "start_date": self.start_date.strftime('%Y-%m-%d'),
                            "end_date": self.end_date.strftime('%Y-%m-%d'),
                            "strategy": self.strategy.name(),
                            "created_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        "decisions": []
                    }
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                self._log_message(f"决策文件已创建: {self.decision_file}")
            except Exception as e:
                self._log_message(f"创建决策文件失败: {e}")

    def _log_decision(self, decision: TradeDecision, decision_time: datetime):
        """记录交易决策到JSON文件"""
        try:
            # 读取现有的决策数据
            with open(self.decision_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 构建决策记录
            decision_record = {
                "decision_time": decision_time.strftime('%Y-%m-%d %H:%M:%S'),
                "action": decision.action,
                "stock_code": decision.stock_code,
                "price": decision.price,
                "quantity": decision.quantity,
                "reason": decision.reason,
                "stop_loss": getattr(decision, 'stop_loss', None),
                "take_profit": getattr(decision, 'take_profit', None)
            }
            
            # 添加决策记录
            data["decisions"].append(decision_record)
            
            # 写回文件
            with open(self.decision_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self._log_message(f"决策已记录到: {self.decision_file}")
            
        except Exception as e:
            self._log_message(f"记录决策失败: {e}")

    def _data_preparation(self):
        #获取日K线
        self._fetcher.get_daily_kline(self.stock_code, self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))
        #获取5分钟K线
        self._fetcher.get_min_kline(self.stock_code, '5', self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))
        #获取15分钟K线
        self._fetcher.get_min_kline(self.stock_code, '15', self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))

    def run(self):
        if not hasattr(self.strategy, "make_decision"):
            return

        if not self.account:
            self.account = TPlusOneStockAccount(self._initial_cash)

        fetcher = StockDataFetcher()

        cur_date = self.start_date

        while cur_date <= self.end_date:
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
                
                current_price = fetcher.get_price(self.stock_code, '15', cur_datetime)
                self._log_message(f"\n=== 决策时间: {cur_datetime} 当前价格: {current_price} ===")

                if current_price is None:
                    self._log_message(f"无法获取当前价格，跳过此决策")
                    continue
                
                current_prices = {self.stock_code : current_price}
                self._log_message(f"\n=== 仓位情况: {self.account.get_portfolio_summary(current_prices)}")

                availiable_quantity = self.account.availiable_quantity(self.stock_code)
                if availiable_quantity == 0 and self.account.cash < 100 * current_price:
                    self._log_message(f"=== 账户可售股票为0，且资金不足, 无法买入股票，跳过此决策===")
                    continue
           
                decision = self.strategy.make_decision(self.stock_name, self.stock_code, self.account, cur_datetime)
                
                if decision.action == "buy":
                    if fetcher.is_trade_success(decision.stock_code, '15', decision.price, decision.quantity, 'buy', cur_datetime + timedelta(minutes=15)):
                        success = self.account.buy(decision.stock_code, decision.price, decision.quantity, decision)
                        if success:
                            self._log_decision(decision, cur_datetime)
                            self._log_message(f"成功买入 {decision.stock_code} {decision.quantity}股 @ {decision.price}")
                            self._log_message(f"操作说明: {decision.reason}")
                            if decision.stop_loss:
                                self._log_message(f"止损点: {decision.stop_loss:.2f}")
                            if decision.take_profit:
                                self._log_message(f"止盈点: {decision.take_profit:.2f}")
                elif decision.action == "sell":
                    if fetcher.is_trade_success(decision.stock_code, '15', decision.price, decision.quantity, 'buy', cur_datetime + timedelta(minutes=15)):
                        success = self.account.sell(decision.stock_code, decision.price, decision.quantity, decision)
                        if success:
                            self._log_decision(decision, cur_datetime)
                            self._log_message(f"{cur_datetime} 成功卖出 {decision.stock_code} {decision.quantity}股")
                            self._log_message(f"操作说明: {decision.reason}")
                else:
                    self._log_message(f"操作说明: {decision.reason}")

            end_price = self._fetcher.get_daily_end_price(self.stock_code, cur_date)
            end_prices = {self.stock_code : end_price}

            # 进入下一个交易日
            cur_date += timedelta(days=1)
            self.account.next_trading_day()
            
            # 显示每日总结
            
            self._log_message(f"\n=== {cur_date.strftime('%Y-%m-%d')} 交易日结束 ===")
            self._log_message(self.account.display_portfolio(end_prices))

        start_price = self._fetcher.get_daily_start_price(self.stock_code, self.start_date)
        end_price = self._fetcher.get_daily_end_price(self.stock_code, self.end_date)

        change_rate = (end_price - start_price) / start_price
        origin_value = self._initial_cash * (1 + change_rate)

        new_value = self.account.get_total_value(end_prices)
        new_change_rate = (new_value - self._initial_cash) / self._initial_cash

        self._log_message(f"\n=== 模拟交易结束 ===", True)
        self._log_message(f"股票：{self.stock_name}({self.stock_code})", True)
        self._log_message(f"初始资金：{self._initial_cash}", True)
        self._log_message(f"模拟期间：{self.start_date.strftime('%Y-%m-%d')} 至 {self.end_date.strftime('%Y-%m-%d')}", True)
        self._log_message(f"初始股票价格：{start_price:.2f} 元， 结束股票价格：{end_price:.2f} 元，涨跌幅：{change_rate*100:.2f}%", True)
        self._log_message(f"理论总资产（不交易情况下）：{origin_value:.2f} 元, 利润率：{change_rate*100:.2f}%", True)
        self._log_message(f"实际总资产（交易后）：{new_value:.2f} 元, 利润率：{new_change_rate*100:.2f}%", True)
        performance_diff = (new_change_rate - change_rate) * 100  # 转换为百分比

        if performance_diff > 0:
            self._log_message(f"跑赢了{performance_diff:.2f}%", True)
        else:
            self._log_message(f"跑输了{abs(performance_diff):.2f}%", True)
        
        self._log_message(f"模拟交易决策已保存到: \n    {self.decision_file}")
        self._log_message(f"模拟交易日志已保存到: \n    {self.log_file}")
