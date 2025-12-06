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
from chart_generate import generate_prediction_chart, setup_environment

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

setup_environment()

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
                    history_data=history_data_for_chart[-3:],
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