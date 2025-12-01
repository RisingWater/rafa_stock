from stock_simulation import StockSimulation

from datetime import datetime
from stock_strategy_deepseek import DeepSeekStrategy
from stock_strategy_gird_v1 import StockStrategyGridV1

if __name__ == '__main__':
    stocks = [
         { 'stock_code' : '002396', 'stock_name' : '星网锐捷' },
         { 'stock_code' : '002170', 'stock_name' : '芭田股份' },
         { 'stock_code' : '000063', 'stock_name' : '中兴通讯' },
         { 'stock_code' : '600203', 'stock_name' : '福日电子' },
         { 'stock_code' : '600036', 'stock_name' : '招商银行' },
    ]



    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 11, 28)

    for stock in stocks:
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        simulation = StockSimulation(stock_code, stock_name, start_date, end_date, StockStrategyGridV1())
        simulation.run()