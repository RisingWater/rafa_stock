from stock_simulation import StockSimulation

from datetime import datetime
from stock_strategy_deepseek import DeepSeekStrategy
from stock_strategy_gird_v1 import StockStrategyGridV1
from stock_strategy_gird_v2 import StockStrategyGridV2
from stock_strategy_gird_v3 import StockStrategyGridV3
import os

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

    initial_cash = 100000

    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 11, 28)

    stratepys_classes = [
        StockStrategyGridV1,
        StockStrategyGridV2,
        StockStrategyGridV3,
    ]

    os.makedirs('./log', exist_ok=True)

    log_file_dir_base = f'./log/{datetime.now().strftime("%Y%m%d%H%M%S")}'

    for strategy_class in stratepys_classes:
        tmp = strategy_class()
        log_file_dir = f'{log_file_dir_base}/{tmp.name()}'
        os.makedirs(log_file_dir, exist_ok=True)

        summary_file = f'{log_file_dir}/summary.log'
        total_performance = 0
        win_count = 0
        total_old = 0
        total_new = 0
        with open(summary_file, 'w', encoding='utf-8') as f:
            for stock in stocks:
                stock_code = stock['stock_code']
                stock_name = stock['stock_name']
                strategy = strategy_class()
                simulation = StockSimulation(stock_code, stock_name, start_date, end_date, strategy, initial_cash=initial_cash, log_dir_path=log_file_dir, summary_file=f)
                old, new = simulation.run()

                performance_diff = new - old

                total_old += old * initial_cash
                total_new += new * initial_cash

                if performance_diff > 0:
                    win_count += 1
                total_performance += performance_diff

            f.write(f"合计             \t理论利润  ：{total_old:8.2f}% \t实际利润  ：{total_new:8.2f}%\n")
            f.write(f"                 \t差额 {(total_new - total_old):8.2f}% \t百分比  ：{((total_new - total_old)/total_new):8.2f}%\n")

            if total_performance > 0:
                f.write(f"平均跑赢: {total_performance / len(stocks):.2f}%\n")
            else:
                f.write(f"平均跑输: {total_performance / len(stocks):.2f}%\n")

            f.write(f"胜率    : {(win_count / len(stocks)):.2f}%\n")