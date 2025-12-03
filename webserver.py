import os
import matplotlib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from stock_data_fetcher import StockDataFetcher
from datetime import datetime, timedelta
import pandas as pd
import requests
import sys

matplotlib.use('Agg')  # 设置后端
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

app = FastAPI(title='Kronos', version='1.0')
fetcher = StockDataFetcher()
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "stock API",
        "version": "1.0", 
    }

class PredictRequest(BaseModel):
    stock_code: str
    stock_name: str
    predict_type: str # daily or min5 or min15
    predict_date: str
    predict_len: int #'daily is valid' 'minute always 1'

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from io import BytesIO
import base64
from datetime import datetime, timedelta

def generate_prediction_chart(history_data, prediction_data, stock_code, predict_type):
    """
    生成预测图表
    
    参数:
    - history_data: 历史数据 DataFrame，包含 ['timestamps', 'open', 'high', 'low', 'close', 'volume']
    - prediction_data: 预测数据 DataFrame，包含 ['timestamps', 'open', 'high', 'low', 'close', 'volume']
    - stock_code: 股票代码
    - predict_type: 预测类型 ('daily', 'min5', 'min15')
    """
    
    # 合并历史数据和预测数据
    history_df = pd.DataFrame(history_data)
    prediction_df = pd.DataFrame(prediction_data)
    
    # 确保时间戳为 datetime 类型
    history_df['timestamps'] = pd.to_datetime(history_df['timestamps'])
    prediction_df['timestamps'] = pd.to_datetime(prediction_df['timestamps'])
    
    # 获取历史数据的最后一个点，用于连接预测线
    last_history_point = history_df.iloc[-1] if len(history_df) > 0 else None
    
    # 创建图形 - 只用一个子图
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # 1. 绘制历史数据的折线（蓝色）
    if len(history_df) > 0:
        ax.plot(history_df['timestamps'], history_df['close'], 
                color='blue', linewidth=2, label='历史收盘价', zorder=1)
    
    # 2. 绘制预测数据的折线（红色）
    # 如果需要连接历史最后一个点，先创建一个连接线
    if last_history_point is not None and len(prediction_df) > 0:
        # 创建连接点（历史最后一个点和预测第一个点）
        connection_times = [last_history_point['timestamps'], prediction_df['timestamps'].iloc[0]]
        connection_prices = [last_history_point['close'], prediction_df['close'].iloc[0]]
        
        # 绘制连接线（红色虚线）
        ax.plot(connection_times, connection_prices, 
                color='red', linewidth=2, linestyle='--', zorder=2)
        
        # 绘制预测折线（从第一个预测点开始）
        ax.plot(prediction_df['timestamps'], prediction_df['close'], 
                color='red', linewidth=2, label='预测收盘价', zorder=3)
    elif len(prediction_df) > 0:
        # 如果没有历史数据，直接绘制预测线
        ax.plot(prediction_df['timestamps'], prediction_df['close'], 
                color='red', linewidth=2, label='预测收盘价', zorder=3)
    
    # 3. 在同一个图上绘制K线图（预测部分的K线）
    if len(prediction_df) > 0:
        # 设置K线的宽度（根据数据点数量调整）
        kline_width = 0.4
        spacing = 0.8  # K线之间的间距
        
        for i, (_, row) in enumerate(prediction_df.iterrows()):
            timestamp = row['timestamps']
            x_pos = mdates.date2num(timestamp)
            
            # 确定颜色：红色表示上涨（收盘>=开盘），绿色表示下跌
            if row['close'] >= row['open']:
                color = 'red'
            else:
                color = 'green'
            
            # 绘制实体（K线的主体部分）
            body_top = max(row['open'], row['close'])
            body_bottom = min(row['open'], row['close'])
            body_height = body_top - body_bottom
            
            if body_height > 0:  # 避免绘制高度为0的矩形
                rect = Rectangle(
                    (x_pos - kline_width/2, body_bottom),
                    kline_width, body_height,
                    facecolor=color, edgecolor=color, alpha=0.7, zorder=4
                )
                ax.add_patch(rect)
            
            # 绘制上下影线
            # 上影线：从最高价到实体顶部
            if row['high'] > body_top:
                ax.plot([x_pos, x_pos], [body_top, row['high']], 
                        color=color, linewidth=1, zorder=4)
            
            # 下影线：从实体底部到最低价
            if row['low'] < body_bottom:
                ax.plot([x_pos, x_pos], [row['low'], body_bottom], 
                        color=color, linewidth=1, zorder=4)
            
            # 标记开盘和收盘价
            if i == 0 or i == len(prediction_df)-1:
                ax.scatter(x_pos, row['open'], color=color, s=20, zorder=5)
                ax.scatter(x_pos, row['close'], color=color, s=20, zorder=5)
    
    # 设置标题和标签
    title = f'{stock_code} {predict_type} 价格预测'
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('价格', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')
    
    # 设置x轴时间格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # 自动调整布局
    plt.tight_layout()
    
    # 保存图片到内存
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    buffer.seek(0)
    return buffer

@app.post("/predict")  # ✅ 移除 response_model 参数
async def predict_endpoint(request: PredictRequest):
    """预测接口"""
    try:
        end_date = datetime.strptime(request.predict_date, "%Y-%m-%d")

        if request.predict_type == 'daily':
            end_date = end_date + timedelta(days=-1)
            start_date = end_date - timedelta(days=365)
            pd_data = fetcher.get_daily_kline(request.stock_code, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
            if request.predict_len > 7:
                return {"message": "Invalid predict_len"}
            predict_len = request.predict_len
        elif request.predict_type == 'min5':
            end_date = end_date + timedelta(days=-1)
            start_date = end_date - timedelta(days=10)
            pd_data = fetcher.get_min_kline(request.stock_code, period='5', start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
            predict_len = 48
        elif request.predict_type == 'min15':
            end_date = end_date + timedelta(days=-1)
            start_date = end_date - timedelta(days=20)
            pd_data = fetcher.get_min_kline(request.stock_code, period='15', start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
            predict_len = 16
        else:
            return {"message": "Invalid predict_type"}

        # 检查是否获取到数据
        if pd_data is None or len(pd_data) == 0:
            return {"message": "No data available for prediction"}
        
        print(f"{pd_data}")
        
        # 转换历史数据为图表需要的格式
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
        
        # 构建预测请求体
        predict_data_list = history_data_for_chart.copy()  # 与图表数据格式相同
        predict_request = {
            "predict_len": predict_len,
            "data": predict_data_list
        }

        # 目标服务地址
        target_url = "http://192.168.1.180:6030/predict"

        # 发送请求
        response = requests.post(
            target_url,
            json=predict_request,
            timeout=60
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if 'prediction' in response_data:
                # ✅ 使用转换后的历史数据
                chart_buffer = generate_prediction_chart(
                    history_data=history_data_for_chart[-5:],
                    prediction_data=response_data['prediction'],
                    stock_code=request.stock_code,
                    predict_type=request.predict_type
                )
                
                import base64
                chart_base64 = base64.b64encode(chart_buffer.getvalue()).decode('utf-8')

                # 返回包含图片数据的 JSON 响应
                return JSONResponse(
                    content={
                        "predictions": response_data['prediction'],
                        "chart_image": chart_base64,
                        "message": "预测成功",
                        "stock_code": request.stock_code,
                        "predict_type": request.predict_type
                    }
                )
            else:
                return {"message": "Invalid response format", "data": response_data}
        else:
            return {"message": f"Prediction service error: {response.status_code}", "error": response.text}
        
    except requests.exceptions.RequestException as e:
        return {"message": f"HTTP request failed: {str(e)}"}
    except Exception as e:
        return {"message": f"Prediction failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6029)