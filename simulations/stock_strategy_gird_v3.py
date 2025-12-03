from simulations.stock_account_tplus1 import TPlusOneStockAccount, TradeDecision
from datetime import datetime
from stock_data_fetcher import StockDataFetcher
from stock_tools import GridBaseLine

class StockStrategyGridV3:
    def __init__(self):
        self._grid_size_buy_index = 0
        self._grid_size_sell_index = 0
        self._fetcher = StockDataFetcher()
        self._base_line = None

        self._grid_size = [
            0.02,
            0.03,
            0.05,
            0.10
        ]

        self._sell_cache = 0
        self._buy_cache = 0

    def name(self) -> str:
        return "Grid Strategy v3"
    
    def get_grid_buy_size(self):
        index = self._grid_size_buy_index
        if index >= len(self._grid_size):
            index = len(self._grid_size) - 1
        elif index < 0:
            index = 0

        return self._grid_size[index]

    def get_grid_sell_size(self):
        index = self._grid_size_sell_index
        if index >= len(self._grid_size):
            index = len(self._grid_size) - 1
        elif index < 0:
            index = 0
            
        return self._grid_size[index]

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
        kVolume = 0.0
        down_edge = self._base_line.price
        down_edge -= self._base_line.price * self.get_grid_buy_size()

        while True:
            self._grid_size_buy_index += 1
            self._grid_size_sell_index -= 1

            kVolume += 1.0
                
            #计算出新的网格下限
            down_edge -= self._base_line.price * self.get_grid_buy_size()
            #如果当前价格小于网格下限，则继续循环，否则就退出循环
            #如果连续穿过多个网格，则买入N份
            if price > down_edge:
                break
        
        if self._sell_cache == kVolume:
            #如果买入的份数和缓存中未卖出的份数一致，则不进行买入
            self._base_line.price = price + self._get_fee_price(price)
            #清空缓存
            self._sell_cache = 0
            msg += f", 新买入网格间隔为{self.get_grid_buy_size()}, 新卖出网格间隔为{self.get_grid_sell_size()}, 由于有缓存，不进行买入，清空缓存"
            return self._create_none_decision(stock_code, cur_datetime, msg)
        elif self._sell_cache > kVolume:
            #如果买入的份数小于缓存中未卖出的份数，则卖出全部缓存减去kVolume份
            volume = self._base_line.volume * (self._sell_cache - kVolume)
            self._base_line.price = price + self._get_fee_price(price)
            #清空缓存
            self._sell_cache = 0
            msg += f", 新买入网格间隔为{self.get_grid_buy_size()}, 新卖出网格间隔为{self.get_grid_sell_size()}, 由于有缓存，不进行买入，反而进行卖出{volume}份股票，清空缓存"
            return TradeDecision(cur_datetime, "sell", stock_code, price, volume, msg)
        else:
            #如果需要买入的分数大于缓存中未卖出的分数，则买入kVolumue减去缓存的分数
            kVolume = kVolume - self._sell_cache
            self._sell_cache = 0
        
            #如果kVolume还大于1，则建立买入缓存
            if kVolume > 1.0:
                self._buy_cache += kVolume

            msg += f", 新买入网格间隔为{self.get_grid_buy_size()}, 新卖出网格间隔为{self.get_grid_sell_size()}, 卖出1份股票，缓存{self._buy_cache}份"
            self._base_line.price = price + self._get_fee_price(price)

            volume = self._base_line.volume * kVolume
            volume = int(volume / 100) * 100
            return TradeDecision(cur_datetime, "buy", stock_code, price, self._base_line.volume, msg)
    
    def _create_sell_decision(self, stock_code, cur_datetime, price, msg) -> TradeDecision:
        kVolume = 0.0
        up_edge = self._base_line.price
        up_edge += self._base_line.price * self.get_grid_sell_size()

        while True:
            self._grid_size_sell_index += 1
            self._grid_size_buy_index -= 1

            kVolume += 1.0
                
            #计算出新的网格上限
            up_edge += self._base_line.price * self.get_grid_sell_size()
            #如果当前价格高于网格上限，则继续循环，否则就退出循环
            #如果连续穿过多个网格，则卖出N份

            if price < up_edge:
                break

        if self._buy_cache == kVolume:
            #如果卖出的份数和缓存中未买入的份数一致，则不进行卖出
            self._base_line.price = price
            #清空缓存
            self._buy_cache = 0
            msg += f", 新买入网格间隔为{self.get_grid_buy_size()}, 新卖出网格间隔为{self.get_grid_sell_size()}, 由于有缓存，不进行卖出，清空缓存"
            return self._create_none_decision(stock_code, cur_datetime, msg)
        elif self._buy_cache > kVolume:
            #如果卖出的份数小于缓存中未买入的份数，则卖出全部缓存减去kVolume份
            volume = self._base_line.volume * (self._buy_cache - kVolume)
            self._base_line.price = price
            #清空缓存
            self._buy_cache = 0
            msg += f", 新买入网格间隔为{self.get_grid_buy_size()}, 新卖出网格间隔为{self.get_grid_sell_size()}, 由于有缓存，不进行卖出，反而进行买入{volume}份股票，清空缓存"
            return TradeDecision(cur_datetime, "buy", stock_code, price, volume, msg)
        else:
            #如果需要卖出的分数大于缓存中未买入的分数，则买入kVolumue减去缓存的分数
            kVolume = kVolume - self._buy_cache
            self._buy_cache = 0

            #如果kVolume还大于1，则建立买入缓存
            if kVolume > 1.0:
                self._sell_cache += kVolume

            msg += f", 新买入网格间隔为{self.get_grid_buy_size()}, 新卖出网格间隔为{self.get_grid_sell_size()}, 卖出1份股票，缓存{self._sell_cache}份"

            self._base_line.price = price
            volume = self._base_line.volume
            volume = int(volume / 100) * 100
            return TradeDecision(cur_datetime, "sell", stock_code, price, volume, msg)

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
        
        grid_up_edge = self._base_line.price * (1 + self.get_grid_sell_size())
        grid_down_edge = self._base_line.price * (1 - self.get_grid_buy_size())

        price_change = (current_price - self._base_line.price) / self._base_line.price

        price_msg = f"当前价格{current_price}，基线价格{self._base_line.price}，涨跌幅{price_change:.2%}，买入网格下限{grid_down_edge}，卖出网格上限{grid_up_edge}"

        if current_price < grid_down_edge:
            if self._can_buy_a_base_line(stock_code, current_price, account):
                msg = f"{price_msg}\n买入{self._base_line.volume}股，新价格基线为{current_price}"
                return self._create_buy_decision(stock_code, cur_datetime, current_price, msg)
            else:
                return self._create_none_decision(stock_code, cur_datetime, f"{price_msg}\n满足买入网格要求，但资金不足，无法买入")
            
        if current_price > grid_up_edge:
            if self._can_sell_a_base_line(stock_code, current_price, account):
                msg = f"{price_msg}\n卖出{self._base_line.volume}股，新价格基线为{current_price}"
                return self._create_sell_decision(stock_code, cur_datetime, current_price, msg)
            else:
                return self._create_none_decision(stock_code, cur_datetime, f"{price_msg}\n满足卖出网格要求，但股票不足，无法卖出")
            
        return self._create_none_decision(stock_code, cur_datetime, f"{price_msg}\n不满足网格条件，不需要操作")