import json
from datetime import datetime

class TradeDecision:
    def __init__(self, datetime, action, stock_code, price, quantity, 
                 reason, stop_loss=None, take_profit=None):
        self.datetime = datetime
        self.action = action  # 'buy'/'sell'/'
        self.stock_code = stock_code
        self.price = price
        self.quantity = quantity
        self.reason = reason  # AI决策逻辑说明
        self.stop_loss = stop_loss  # 止损价位
        self.take_profit = take_profit  # 止盈价位

    @classmethod
    def from_json(cls, json_str):
        """从JSON字符串创建TradeDecision对象"""
        # 找到第一个{和最后一个}的位置
        start_index = json_str.find('{')
        end_index = json_str.rfind('}')
        
        if start_index == -1 or end_index == -1:
            raise ValueError("未找到有效的JSON对象")
        
        # 提取JSON内容
        json_content = json_str[start_index:end_index+1]
        data = json.loads(json_content)
        
        # 将字符串时间转换为datetime对象
        dt = datetime.strptime(data['datetime'], '%Y-%m-%d %H:%M:%S')
        
        return cls(
            datetime=dt,
            action=data['action'],
            stock_code=data['stock_code'],
            price=data['price'],
            quantity=data['quantity'],
            reason=data['reason'],
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit')
        )

class TPlusOneStockAccount:
    """T+1交易股票账户"""
    
    def __init__(self, initial_cash=0):
        """
        初始化股票账户
        
        Args:
            initial_cash (float): 初始现金
        """
        self.cash = initial_cash
        # 持股信息 {股票代码: [总数量, 可售数量, 成本价]}
        self.holdings = {}
        self.total_assets = initial_cash
        self.transaction_fee = 5  # 买入/卖出固定手续费(元)
        self.stamp_duty_rate = 0.0005  # 印花税率(万分之五)

        self.trade_history = []  # 交易记录列表

    def _add_trade_record(self, decision: TradeDecision):
        self.trade_history.append(decision)        

    def get_recent_decisions(self, stock_code=None, count=10):
        """
        获取近期决策记录
        
        Args:
            stock_code (str, optional): 筛选特定股票代码，None表示所有股票
            count (int): 获取最近多少条记录，默认10条
            
        Returns:
            list: 符合条件的TradeDecision对象列表，按时间倒序排列
        """
        # 筛选符合条件的记录
        filtered_decisions = []
        for decision in reversed(self.trade_history):  # 从最新开始遍历
            # 股票代码筛选
            if stock_code is not None and decision.stock_code != stock_code:
                continue
                
            filtered_decisions.append(decision)
            
            # 达到指定数量就停止
            if len(filtered_decisions) >= count:
                break
        
        return filtered_decisions
    
    def get_recent_decisions_summary(self, stock_code=None, count=10):
        """
        获取近期决策记录的字符串版本
        
        Args:
            stock_code (str, optional): 筛选特定股票代码
            count (int): 获取最近多少条记录
            
        Returns:
            str: 格式化的决策记录字符串
        """
        recent_decisions = self.get_recent_decisions(stock_code, count)
        
        if not recent_decisions:
            return "暂无历史操作记录"
        
        lines = ["近期操作历史:"]
        for i, decision in enumerate(recent_decisions, 1):
            lines.append(f"{i}. 时间: {decision.datetime.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"   操作: {decision.action} {decision.quantity}股 {decision.stock_code}")
            lines.append(f"   价格: {decision.price:.2f}元")
            lines.append(f"   理由: {decision.reason}")
            if decision.stop_loss:
                lines.append(f"   止损: {decision.stop_loss:.2f}元")
            if decision.take_profit:
                lines.append(f"   止盈: {decision.take_profit:.2f}元")
            lines.append("")  # 空行分隔
        
        return "\n".join(lines)
    
    def _is_valid_quantity(self, quantity):
        """
        检查数量是否是100的倍数
        
        Args:
            quantity (int): 数量
            
        Returns:
            bool: 是否有效
        """
        if quantity <= 0:
            print("交易数量必须大于0")
            return False
        if quantity % 100 != 0:
            print("交易数量必须是100的整数倍")
            return False
        return True
    
    def _calculate_buy_cost(self, price, quantity):
        """
        计算买入总成本（含买入手续费和预扣卖出手续费）
        
        Args:
            price (float): 价格
            quantity (int): 数量
            
        Returns:
            float: 总成本（含所有费用）
        """
        total_cost = price * quantity
        # 买入手续费
        buy_fee = self.transaction_fee
        # 预扣卖出手续费（在买入时就算入成本）
        sell_fee = self.transaction_fee + total_cost * self.stamp_duty_rate
        return total_cost + buy_fee + sell_fee

    def buy(self, code, price, quantity, decision: TradeDecision):
        """
        买入股票
        
        Args:
            code (str): 股票代码
            price (float): 买入价格
            quantity (int): 买入数量
        """
        if not self._is_valid_quantity(quantity):
            return False
        
        # 计算买入总成本（含所有费用）
        total_expense = self._calculate_buy_cost(price, quantity)
        
        # 检查现金是否足够
        if self.cash < total_expense:
            print(f"现金不足！需要{total_expense:.2f}元，当前现金{self.cash:.2f}元")
            return False
        
        # 更新现金
        self.cash -= total_expense
        
        # 更新持股信息
        if code in self.holdings:
            total_quantity, available_quantity, old_cost = self.holdings[code]
            new_total_quantity = total_quantity + quantity
            
            # 计算新的平均成本（包含所有交易费用）
            total_old_cost = total_quantity * old_cost
            total_new_cost = total_old_cost + total_expense
            new_cost = total_new_cost / new_total_quantity
            
            # 新买入的不可出售
            new_available_quantity = available_quantity
            
            self.holdings[code] = [new_total_quantity, new_available_quantity, new_cost]
        else:
            # 第一次买入该股票
            actual_cost_per_share = total_expense / quantity
            # 新买入的不可出售
            self.holdings[code] = [quantity, 0, actual_cost_per_share]
        
        actual_cost = total_expense / quantity
        print(f"成功买入 {quantity}股{code}，价格{price:.2f}元")
        print(f"实际成本: {actual_cost:.4f}元/股（已含买卖手续费）")
        print(f"总支出: {total_expense:.2f}元")
        
        self._update_total_assets()
        self._add_trade_record(decision)
        return True
    
    def sell(self, code, price, quantity, decision: TradeDecision):
        """
        卖出股票
        
        Args:
            code (str): 股票代码
            price (float): 卖出价格
            quantity (int): 卖出数量
        """
        if not self._is_valid_quantity(quantity):
            return False
        
        # 检查是否持有该股票
        if code not in self.holdings:
            print(f"未持有股票{code}")
            return False
        
        total_quantity, available_quantity, cost_price = self.holdings[code]
        
        # 检查可售数量是否足够
        if available_quantity < quantity:
            print(f"可售数量不足！可售{available_quantity}股，持有{total_quantity}股，尝试卖出{quantity}股")
            return False
        
        # 计算卖出收入（不再扣除费用，因为费用已在买入时计入成本）
        income = price * quantity
        
        # 更新现金
        self.cash += income
        
        # 更新持股信息（不清除零持股，保留记录）
        new_total_quantity = total_quantity - quantity
        new_available_quantity = available_quantity - quantity
        
        # 成本价保持不变，便于后续重新买入时计算
        self.holdings[code] = [new_total_quantity, new_available_quantity, cost_price]
        
        # 计算盈亏（由于费用已计入成本，这里直接比较）
        total_cost = cost_price * quantity
        profit_loss = income - total_cost
        profit_loss_rate = (profit_loss / total_cost) * 100 if total_cost > 0 else 0
        
        print(f"成功卖出 {quantity}股{code}，价格{price:.2f}元")
        print(f"收入: {income:.2f}元，成本: {total_cost:.2f}元")
        print(f"盈亏: {profit_loss:.2f}元 ({profit_loss_rate:+.2f}%)")
        
        self._update_total_assets()
        self._add_trade_record(decision)
        return True
    
    def next_trading_day(self):
        """进入下一个交易日"""
        print("进入下一个交易日...")
        stocks_to_remove = []
        
        for code, (total_quantity, available_quantity, cost_price) in self.holdings.items():
            if total_quantity == 0:
                # 标记零持股的股票
                stocks_to_remove.append(code)
                print(f"清除零持股: {code}")
            else:
                # 将所有不可售股票转为可售
                self.holdings[code] = [total_quantity, total_quantity, cost_price]
                newly_available = total_quantity - available_quantity
                if newly_available > 0:
                    print(f"{code}: {newly_available}股变为可售")
        
        # 清除零持股记录
        for code in stocks_to_remove:
            del self.holdings[code]
        
        print("交易日切换完成")
    
    def _update_total_assets(self):
        """更新总资产"""
        total_stock_value = 0
        for total_quantity, _, cost_price in self.holdings.values():
            total_stock_value += total_quantity * cost_price
        self.total_assets = self.cash + total_stock_value
    
    def get_break_even_price(self, code):
        """
        获取股票的保本价
        
        Args:
            code (str): 股票代码
            
        Returns:
            float: 保本价
        """
        if code not in self.holdings:
            return 0
        _, _, cost_price = self.holdings[code]
        return cost_price
    
    def get_total_value(self, current_prices):
        """获取投资组合的总价值"""
        total_value = 0
        for code, (total_quantity, available_quantity, cost_price) in self.holdings.items():
            cost_value = total_quantity * cost_price
            current_price = current_prices.get(code, cost_price) if current_prices else cost_prices
            current_value = total_quantity * current_price
            total_value += current_value

        total_value += self.cash
        return total_value

    def display_portfolio(self, current_prices):
        """显示投资组合信息"""
        msg = ""
        msg += ("\n" + "="*70 + "\n")
        msg += ("T+1 投资组合概览\n")
        msg += ("="*70 + "\n")
        msg += (f"现金: {self.cash:.2f}元\n")
        
        if self.holdings:
            msg += ("\n持股详情:\n")
            msg += ("-"*50 + "\n")
            total_stock_value = 0
            
            for code, (total_quantity, available_quantity, cost_price) in self.holdings.items():
                cost_value = total_quantity * cost_price
                current_price = current_prices.get(code, cost_price) if current_prices else cost_price
                current_value = total_quantity * current_price
                profit_loss = current_value - cost_value
                profit_loss_rate = (profit_loss / cost_value) * 100 if cost_value > 0 else 0
                
                total_stock_value += current_value
                
                status = "可售" if available_quantity > 0 else "持仓"
                msg += (f"{code}: {total_quantity}股 ({status}: {available_quantity}股)\n")
                msg += (f"     成本价: {cost_price:.4f}元 | 保本价: {cost_price:.4f}元\n")
                msg += (f"     当前价: {current_price:.2f}元 | 当前市值: {current_value:.2f}元\n")
                msg += (f"     盈亏: {profit_loss:.2f}元 ({profit_loss_rate:+.2f}%)\n")
                
                msg += ("-"*25 + "\n")
            
            msg += (f"\n股票总市值: {total_stock_value:.2f}元\n")
        else:
            msg += ("\n当前未持有任何股票\n")
            total_stock_value = 0
        
        msg += (f"总资产: {self.total_assets:.2f}元\n")
        msg += ("="*70 + "\n")

        return msg

    def availiable_quantity(self, stock_code):
        holding = self.holdings.get(stock_code)
        if holding:
            return holding[1]
        else:
            return 0

    def get_portfolio_summary(self, current_prices):
        """获取投资组合的紧凑字符串摘要，用于生成提示词"""
        lines = []
        lines.append(f"现金: {self.cash:.2f}元")
        
        if self.holdings:
            total_stock_value = 0
            holdings_info = []
            
            for code, (total_quantity, available_quantity, cost_price) in self.holdings.items():
                current_price = current_prices.get(code, cost_price) if current_prices else cost_price
                current_value = total_quantity * current_price
                cost_value = total_quantity * cost_price
                profit_loss = current_value - cost_value
                profit_loss_rate = (profit_loss / cost_value) * 100 if cost_value > 0 else 0
                
                total_stock_value += current_value
                
                stock_info = (
                    f"{code}: {total_quantity}股(可售{available_quantity}股), "
                    f"成本{cost_price:.4f}, 现价{current_price:.2f}, "
                    f"盈亏{profit_loss:+.2f}元({profit_loss_rate:+.1f}%)"
                )
                holdings_info.append(stock_info)
            
            lines.append(f"持股数: {len(self.holdings)}只")
            lines.extend(holdings_info)
            lines.append(f"股票总市值: {total_stock_value:.2f}元")
        else:
            lines.append("当前未持有股票")
        
        lines.append(f"总资产: {self.total_assets:.2f}元")
        
        return "\n".join(lines)

