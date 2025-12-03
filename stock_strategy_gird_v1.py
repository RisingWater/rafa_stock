from stock_account_tplus1 import TPlusOneStockAccount, TradeDecision
from datetime import datetime
from stock_data_fetcher import StockDataFetcher
from stock_tools import GridBaseLine

class StockStrategyGridV1:
    def __init__(self):
        self._grid_size_buy_index = 0
        self._grid_size_sell_index = 0
        self._fetcher = StockDataFetcher()
        self._base_line = None

        self._grid_size = [
            0.02
        ]

    def name(self) -> str:
        return "Grid Strategy v1"
    
    def _can_buy_a_base_line(self, stock_code, cur_price, account) -> bool:
        if account.cash >= cur_price * self._base_line.volume:
            return True
        else:
            return False
        
    def _can_sell_a_base_line(self, stock_code, cur_price, account) -> bool:
        if account.holdings[stock_code][1] >= self._base_line.volume:
            return True
        else:
            return False

    def _get_fee_price(self, price):
        return (self._base_line.volume * price * 0.0005 + 10) / self._base_line.volume

    def _create_buy_decision(self, stock_code, cur_datetime, price, msg) -> TradeDecision:
        if self._grid_size_buy_index < len(self._grid_size) - 1:
            self._grid_size_buy_index += 1
        if self._grid_size_sell_index > 0:
            self._grid_size_sell_index -= 1

        msg += f", 新买入网格间隔为{self._grid_size[self._grid_size_buy_index]}, 新卖出网格间隔为{self._grid_size[self._grid_size_sell_index]}"
        self._base_line.price = price + self._get_fee_price(price)
        return TradeDecision(cur_datetime, "buy", stock_code, price, self._base_line.volume, msg)

    def _create_sell_decision(self, stock_code, cur_datetime, price, msg) -> TradeDecision:
        if self._grid_size_sell_index < len(self._grid_size) - 1:
            self._grid_size_sell_index += 1
        if self._grid_size_buy_index > 0:
            self._grid_size_buy_index -= 1

        msg += f", 新买入网格间隔为{self._grid_size[self._grid_size_buy_index]}, 新卖出网格间隔为{self._grid_size[self._grid_size_sell_index]}"

        self._base_line.price = price
        return TradeDecision(cur_datetime, "sell", stock_code, price, self._base_line.volume, msg)
    def _create_none_decision(self, stock_code, cur_datetime, msg) -> TradeDecision:
        return TradeDecision(cur_datetime, "none", stock_code, 0, 0, msg)

    def _create_base_line(self, stock_code, cur_price, cur_datetime, account) -> TradeDecision:
        if stock_code in account.holdings:
            total_quantity = account.holdings[stock_code][0] #获取当前持仓
        else:
            total_quantity = 0

        can_buy = int(account.cash / (cur_price * 100)) * 100 # 可用资金可以买的股票数
        grid_volume = int((total_quantity + can_buy) / 1000) * 100
        self._base_line = GridBaseLine(cur_price, grid_volume)
        if (can_buy > total_quantity):
            #补仓
            volume = (can_buy - total_quantity) / 2
            volume  = int(volume / 100) * 100
            if (volume > 0):
                return TradeDecision(cur_datetime, "buy", stock_code, cur_price, volume, f"买入{volume}股，创建基础半仓，价格基线为{cur_price}，单次操作{volume}股")
            else:
                return self._create_none_decision(stock_code, cur_datetime, f"正好半仓，不需要调仓，价格基线为{cur_price}，单次操作{volume}股")
        else:
            #清仓
            volume = (total_quantity - can_buy) / 2
            volume  = int(volume / 100) * 100
            if (volume > 0):
                return TradeDecision(cur_datetime, "sell", stock_code, cur_price, volume, f"卖出{volume}股，创建基础半仓，价格基线为{cur_price}，单次操作{volume}股")
            else:
                return self._create_none_decision(stock_code, cur_datetime, f"正好半仓，不需要调仓，价格基线为{cur_price}，单次操作{volume}股")
    def make_decision(self, stock_name: str, stock_code: str, account: TPlusOneStockAccount, cur_datetime: datetime) -> TradeDecision:        
        current_price = self._fetcher.get_price(stock_code, '15', cur_datetime)

        if self._base_line is None:
            return self._create_base_line(stock_code, current_price, cur_datetime, account)
        
        if current_price < self._base_line.price * (1 - self._grid_size[self._grid_size_buy_index]):
            if self._can_buy_a_base_line(stock_code, current_price, account):
                msg = f"买入{self._base_line.volume}股，原价格基线为{self._base_line.price}，单次操作{self._base_line.volume}股，新价格基线为{current_price}"
                return self._create_buy_decision(stock_code, cur_datetime, current_price, msg)
            else:
                return self._create_none_decision(stock_code, cur_datetime, f"满足买入网格要求，但资金不足，无法买入")
            
        if current_price > self._base_line.price * (1 + self._grid_size[self._grid_size_sell_index]):
            if self._can_sell_a_base_line(stock_code, current_price, account):
                msg = f"卖出{self._base_line.volume}股，原价格基线为{self._base_line.price}，单次操作{self._base_line.volume}股，新价格基线为{current_price}"
                return self._create_sell_decision(stock_code, cur_datetime, current_price, msg)
            else:
                return self._create_none_decision(stock_code, cur_datetime, f"满足卖出网格要求，但股票不足，无法卖出")
            
        return self._create_none_decision(stock_code, cur_datetime, f"不满足网格条件，不需要操作")