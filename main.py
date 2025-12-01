from stock_simulation import StockSimulation

from datetime import datetime
from stock_strategy_deepseek import DeepSeekStrategy
from stock_strategy_gird_v1 import StockStrategyGridV1
from stock_strategy_gird_v2 import StockStrategyGridV2

if __name__ == '__main__':
    stocks = [
        { 'stock_code' : '002396', 'stock_name' : '星网锐捷' },
        { 'stock_code' : '002170', 'stock_name' : '芭田股份' },
        { 'stock_code' : '000063', 'stock_name' : '中兴通讯' },
        { 'stock_code' : '600203', 'stock_name' : '福日电子' },
        { 'stock_code' : '600036', 'stock_name' : '招商银行' },
        { 'stock_code' : '301165', 'stock_name' : '锐捷网络' },
        { 'stock_code' : '603828', 'stock_name' : 'ST柯利达' },
        { 'stock_code' : '002352', 'stock_name' : '顺丰控股' },
        { 'stock_code' : '000901', 'stock_name' : '航天科技' },
        { 'stock_code' : '601377', 'stock_name' : '兴业证券' },
        { 'stock_code' : '002222', 'stock_name' : '福晶科技' },
        { 'stock_code' : '002487', 'stock_name' : '大金重工' },
        { 'stock_code' : '601619', 'stock_name' : '嘉泽新能' },
        { 'stock_code' : '002065', 'stock_name' : '东华软件' },
    ]



    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 11, 28)

    for stock in stocks:
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        simulation = StockSimulation(stock_code, stock_name, start_date, end_date, StockStrategyGridV2())
        simulation.run()