import sys
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from io import BytesIO
import numpy as np

def setup_environment():
    """
    设置跨平台环境，包括字体和后端
    """
    # 设置后端为非交互式（避免GUI问题）
    matplotlib.use('Agg')  # 使用Agg后端，不依赖GUI
    
    # 根据操作系统设置字体
    if sys.platform.startswith('win'):
        # Windows系统
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong', 'KaiTi']
        print("已设置Windows中文字体")
    elif sys.platform.startswith('linux'):
        # Linux系统
        matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
        print("已设置Linux中文字体")
    else:
        # macOS或其他系统
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
        print("已设置默认字体")
    
    # 解决负号显示问题
    matplotlib.rcParams['axes.unicode_minus'] = False
    
    # 设置其他默认参数（可选）
    matplotlib.rcParams['figure.dpi'] = 100
    matplotlib.rcParams['savefig.dpi'] = 150

def generate_prediction_chart(history_data, prediction_data, stock_code, predict_type):
    """
    生成预测图表 - 紧凑型布局
    """
    
    # 合并历史数据和预测数据
    history_df = pd.DataFrame(history_data)
    prediction_df = pd.DataFrame(prediction_data)
    
    if len(history_df) == 0 and len(prediction_df) == 0:
        raise ValueError("历史数据和预测数据都为空")
    
    # 确保时间戳为 datetime 类型
    history_df['timestamps'] = pd.to_datetime(history_df['timestamps'])
    prediction_df['timestamps'] = pd.to_datetime(prediction_df['timestamps'])
    
    # 获取历史数据的最后一个点，用于连接预测线
    last_history_point = history_df.iloc[-1] if len(history_df) > 0 else None
    
    # 创建图形 - 使用更紧凑的尺寸
    fig, ax = plt.subplots(figsize=(14, 7), facecolor='#f5f5f5')
    ax.set_facecolor('#ffffff')
    
    # 创建颜色配置
    COLOR_CONFIG = {
        'history_line': '#1f77b4',
        'prediction_line': '#d62728',
        'prediction_kline_up': '#ff4d4d',
        'prediction_kline_down': '#2ecc71',
        'connection_line': '#d62728',
        'grid': '#e0e0e0',
        'annotation_bg': '#ffffff'
    }
    
    # 设置网格
    ax.grid(True, color=COLOR_CONFIG['grid'], linestyle='--', alpha=0.7)
    
    # 1. 绘制历史数据的折线
    if len(history_df) > 0:
        ax.plot(history_df['timestamps'], history_df['close'], 
                color=COLOR_CONFIG['history_line'], linewidth=3.0, 
                label='历史收盘价', zorder=1, alpha=0.9)
    
    # 2. 绘制预测数据的折线
    if len(prediction_df) > 0:
        if last_history_point is not None:
            # 创建连接点
            connection_times = [last_history_point['timestamps'], prediction_df['timestamps'].iloc[0]]
            connection_prices = [last_history_point['close'], prediction_df['close'].iloc[0]]
            
            # 绘制连接线
            ax.plot(connection_times, connection_prices, 
                    color=COLOR_CONFIG['connection_line'], linewidth=2.5, 
                    linestyle='--', zorder=2, alpha=0.8)
        
        # 绘制预测折线
        ax.plot(prediction_df['timestamps'], prediction_df['close'], 
                color=COLOR_CONFIG['prediction_line'], linewidth=3.0, 
                label='预测收盘价', zorder=3, alpha=0.9)
    
    # 3. 绘制预测部分的K线图并标注价格
    if len(prediction_df) > 0:
        # 计算K线宽度
        num_points = len(prediction_df)
        if num_points <= 5:
            kline_width = 0.5
        elif num_points <= 10:
            kline_width = 0.35
        else:
            kline_width = 0.25
        
        x_positions = mdates.date2num(prediction_df['timestamps'])
        
        for idx, (timestamp, x_pos) in enumerate(zip(prediction_df['timestamps'], x_positions)):
            row = prediction_df.iloc[idx]
            
            # 确定颜色
            if row['close'] >= row['open']:
                color = COLOR_CONFIG['prediction_kline_up']
                fill_color = color
                edge_color = '#c0392b'
                annotation_color = '#c0392b'
            else:
                color = COLOR_CONFIG['prediction_kline_down']
                fill_color = color
                edge_color = '#27ae60'
                annotation_color = '#27ae60'
            
            # 绘制K线实体
            body_top = max(row['open'], row['close'])
            body_bottom = min(row['open'], row['close'])
            body_height = body_top - body_bottom
            
            if body_height > 0:
                rect = Rectangle(
                    (x_pos - kline_width/2, body_bottom),
                    kline_width, body_height,
                    facecolor=fill_color, edgecolor=edge_color, 
                    linewidth=2.0, alpha=0.85, zorder=4
                )
                ax.add_patch(rect)
            else:
                ax.plot([x_pos - kline_width/2, x_pos + kline_width/2], 
                       [body_top, body_top], color=edge_color, 
                       linewidth=2.0, zorder=4)
            
            # 绘制上下影线
            if row['high'] > body_top:
                ax.plot([x_pos, x_pos], [body_top, row['high']], 
                        color=color, linewidth=2.0, zorder=4, alpha=0.9)
            
            if row['low'] < body_bottom:
                ax.plot([x_pos, x_pos], [row['low'], body_bottom], 
                        color=color, linewidth=2.0, zorder=4, alpha=0.9)
            
            # 标注价格 - 使用更大字体
            vertical_offset = 0.5
            horizontal_offset = kline_width * 40
            
            # 开盘价标注（左）
            ax.annotate(f'开盘价:{row["open"]:.2f}', 
                       xy=(x_pos, row['open']), 
                       xytext=(-horizontal_offset, 0), 
                       textcoords='offset points',
                       fontsize=15, color=annotation_color, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor=COLOR_CONFIG['annotation_bg'], 
                                alpha=0.95, edgecolor='gray', linewidth=1),
                       zorder=6,
                       ha='right', va='center')
            
            # 收盘价标注（右）
            ax.annotate(f'收盘价:{row["close"]:.2f}', 
                       xy=(x_pos, row['close']), 
                       xytext=(horizontal_offset, 0), 
                       textcoords='offset points',
                       fontsize=15, color=annotation_color, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor=COLOR_CONFIG['annotation_bg'], 
                                alpha=0.95, edgecolor='gray', linewidth=1),
                       zorder=6,
                       ha='left', va='center')
            
            # 最高价标注（上）
            if row['high'] > max(row['open'], row['close']):
                ax.annotate(f'最高价:{row["high"]:.2f}', 
                           xy=(x_pos, row['high']), 
                           xytext=(0, vertical_offset * 8), 
                           textcoords='offset points',
                           fontsize=15, color=annotation_color, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor=COLOR_CONFIG['annotation_bg'], 
                                    alpha=0.9, edgecolor='lightgray'),
                           zorder=6,
                           ha='center', va='bottom')
            
            # 最低价标注（下）
            if row['low'] < min(row['open'], row['close']):
                ax.annotate(f'最低价:{row["low"]:.2f}', 
                           xy=(x_pos, row['low']), 
                           xytext=(0, -vertical_offset * 8), 
                           textcoords='offset points',
                           fontsize=15, color=annotation_color, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor=COLOR_CONFIG['annotation_bg'], 
                                    alpha=0.9, edgecolor='lightgray'),
                           zorder=6,
                           ha='center', va='top')
    
    # 4. 添加历史最后点标记
    if last_history_point is not None:
        ax.scatter(last_history_point['timestamps'], last_history_point['close'], 
                  color='blue', s=120, edgecolor='white', linewidth=2.5, 
                  zorder=6, label='历史收盘价')
        ax.annotate(f'历史收盘价\n{last_history_point["close"]:.2f}', 
                   xy=(last_history_point['timestamps'], last_history_point['close']), 
                   xytext=(-15, -30), textcoords='offset points',
                   fontsize=15, color='blue', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                            alpha=0.97, edgecolor='blue', linewidth=1.5),
                   zorder=7,
                   ha='right', va='top')
    
    # 5. 设置标题和标签 - 增大字体
    predict_type_map = {
        'daily': '日线',
        'min5': '5分钟线',
        'min15': '15分钟线'
    }
    title = f'{stock_code} {predict_type_map.get(predict_type, predict_type)}价格预测'
    ax.set_title(title, fontsize=22, fontweight='bold', pad=15, color='#2c3e50')
    ax.set_xlabel('时间', fontsize=16, fontweight='bold', color='#2c3e50', labelpad=10)
    ax.set_ylabel('价格 (元)', fontsize=16, fontweight='bold', color='#2c3e50', labelpad=10)
    
    # 6. 设置图例 - 增大字体
    handles, labels = ax.get_legend_handles_labels()
    unique_labels = []
    unique_handles = []
    for handle, label in zip(handles, labels):
        if label not in unique_labels:
            unique_labels.append(label)
            unique_handles.append(handle)
    
    if unique_handles:  # 只有当有图例项时才添加图例
        ax.legend(unique_handles, unique_labels, loc='upper left', fontsize=14,
                  framealpha=0.95, shadow=True, fancybox=True, borderpad=0.8)
    
    # 7. 设置x轴时间格式 - 增大字体
    if predict_type == "daily":
        date_format = '%m-%d'
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    elif predict_type == "min5":
        date_format = '%m-%d %H:%M'
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    elif predict_type == "min15":
        date_format = '%m-%d %H:%M'
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    else:
        date_format = '%m-%d'
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    
    
    
    ax.tick_params(axis='x', labelsize=13, rotation=45)
    ax.tick_params(axis='y', labelsize=13)
    
    # 8. 设置y轴格式
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    
    # 9. 设置图表边框
    for spine in ax.spines.values():
        spine.set_edgecolor('#95a5a6')
        spine.set_linewidth(2.0)
    
    # 10. 紧凑布局，减少空白
    plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.15)
    
    # 保存图片到内存
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                pad_inches=0.1, facecolor=fig.get_facecolor())
    plt.close(fig)
    
    buffer.seek(0)
    return buffer

# 可选：添加一个辅助函数来生成示例数据用于测试
def create_sample_data():
    """创建示例数据用于测试 - 历史3天，预测1天"""
    import numpy as np
    from datetime import datetime, timedelta
    
    # 设置基础价格，让数据看起来更真实
    base_price = 100.0
    volatility = 2.0  # 波动性
    
    # 生成历史数据（3天）
    base_date = datetime.now() - timedelta(days=3)
    history_dates = [base_date + timedelta(days=i) for i in range(3)]
    
    # 生成更真实的股价数据
    history_close = [base_price]
    for i in range(2):  # 生成后两天的收盘价
        change = np.random.uniform(-volatility, volatility)
        history_close.append(history_close[-1] + change)
    
    # 为每一天生成OHLC数据
    history_opens = []
    history_highs = []
    history_lows = []
    history_closes = []
    
    for i in range(3):
        close_price = history_close[i]
        open_price = close_price + np.random.uniform(-volatility/2, volatility/2)
        high_price = max(open_price, close_price) + np.random.uniform(0, volatility)
        low_price = min(open_price, close_price) - np.random.uniform(0, volatility)
        
        # 确保高>低，并且包含开盘和收盘价
        high_price = max(high_price, max(open_price, close_price) + 0.5)
        low_price = min(low_price, min(open_price, close_price) - 0.5)
        
        history_opens.append(open_price)
        history_highs.append(high_price)
        history_lows.append(low_price)
        history_closes.append(close_price)
    
    history_data = {
        'timestamps': history_dates,
        'open': history_opens,
        'high': history_highs,
        'low': history_lows,
        'close': history_closes,
        'volume': np.random.randint(100000, 500000, 3)
    }
    
    # 生成预测数据（1天）
    # 基于历史最后一天的价格进行预测
    last_close = history_closes[-1]
    pred_date = history_dates[-1] + timedelta(days=1)
    
    # 生成预测的OHLC数据
    pred_open = last_close + np.random.uniform(-volatility/2, volatility/2)
    # 预测通常有一定上涨趋势
    pred_close = last_close + np.random.uniform(0, volatility*1.5)
    pred_high = max(pred_open, pred_close) + np.random.uniform(0.5, volatility*2)
    pred_low = min(pred_open, pred_close) - np.random.uniform(0.5, volatility*1.5)
    
    # 确保价格合理性
    if pred_high <= max(pred_open, pred_close):
        pred_high = max(pred_open, pred_close) + 0.8
    if pred_low >= min(pred_open, pred_close):
        pred_low = min(pred_open, pred_close) - 0.8
    
    prediction_data = {
        'timestamps': [pred_date],
        'open': [pred_open],
        'high': [pred_high],
        'low': [pred_low],
        'close': [pred_close],
        'volume': [np.random.randint(80000, 300000)]
    }
    
    return pd.DataFrame(history_data), pd.DataFrame(prediction_data)


# 使用示例
if __name__ == "__main__":
    # 生成示例数据（历史3天，预测1天）
    history_df, prediction_df = create_sample_data()
    
    print("历史数据（3天）：")
    print(history_df)
    print("\n预测数据（1天）：")
    print(prediction_df)
    
    # 生成图表
    chart_buffer = generate_prediction_chart(
        history_data=history_df,
        prediction_data=prediction_df,
        stock_code='AAPL',
        predict_type='daily'
    )
    
    # 保存到文件查看
    with open('prediction_chart_3d1p.png', 'wb') as f:
        f.write(chart_buffer.getvalue())
    
    print("\n图表已保存为 prediction_chart_3d1p.png")
    
    # 输出价格信息
    print(f"\n历史最后收盘价: {history_df['close'].iloc[-1]:.2f}")
    print(f"预测开盘价: {prediction_df['open'].iloc[0]:.2f}")
    print(f"预测收盘价: {prediction_df['close'].iloc[0]:.2f}")
    print(f"预测涨跌幅: {((prediction_df['close'].iloc[0] - history_df['close'].iloc[-1]) / history_df['close'].iloc[-1] * 100):.2f}%")