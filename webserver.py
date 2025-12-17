import os
import asyncio
import matplotlib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from stock_data_fetcher import StockDataFetcher
from datetime import datetime, timedelta
import pandas as pd
import requests
import sys
import time
import threading
import concurrent.futures
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 导入你的模块
from pick_stock import StockPicker
from chart_generate import generate_prediction_chart, setup_environment

# 初始化
picker = StockPicker()
select_stocks = []
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)  # 用于执行同步阻塞任务

app = FastAPI(title='Kronos', version='1.0')

# 全局状态
is_prepare_task_running = False
is_pick_task_running = False
prepare_task_future = None
pick_task_future = None

@app.get("/")
async def get_root():
    """根路径"""
    return FileResponse("index.html")

@app.get("/pick")
async def get_pick():
    """获取pick任务状态"""
    return {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_running": picker.is_running,
        "process": picker.process_count,
        "total": picker.total_count,
        "select_stocks": select_stocks,
    }

@app.get("/prepare")
async def get_prepare():
    """获取prepare任务状态"""
    return {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_running": picker.prepare_running,
        "process": picker.prepare_count, 
        "total": picker.prepare_total_count,
    }

@app.post("/start_prepare")
async def start_prepare():
    """异步启动prepare任务"""
    global is_prepare_task_running, prepare_task_future
    
    # 检查是否已经在运行
    if is_prepare_task_running:
        return JSONResponse(
            status_code=400,
            content={
                "message": "准备任务已在运行中",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
        )
    
    # 标记为运行中
    is_prepare_task_running = True
    
    # 定义异步任务包装器
    async def run_prepare():
        global is_prepare_task_running
        try:
            # 如果picker.prepare_stock()是同步方法，使用线程池执行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(executor, picker.prepare_stock)
            return True
        except Exception as e:
            logger.error(f"准备任务执行出错: {e}")
            return False
        finally:
            is_prepare_task_running = False
    
    # 启动异步任务（不等待）
    prepare_task_future = asyncio.create_task(run_prepare())
    
    return {
        "message": "股票数据准备任务已启动",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "is_running": True
    }

@app.post("/stop_prepare")
async def stop_prepare():
    """停止prepare任务"""
    global is_prepare_task_running, prepare_task_future
    
    if not is_prepare_task_running:
        return JSONResponse(
            status_code=400,
            content={
                "message": "没有运行中的准备任务",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
        )
    
    # 尝试停止任务
    if picker:
        picker.interrupt_prepare = True
    
    # 尝试取消异步任务
    if prepare_task_future and not prepare_task_future.done():
        prepare_task_future.cancel()
        try:
            await prepare_task_future
        except asyncio.CancelledError:
            pass
    
    is_prepare_task_running = False
    
    return {
        "message": "准备任务已停止",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "is_running": False
    }

@app.post("/start_pick")
async def start_pick(request: Request):
    """异步启动pick任务，支持日期参数"""
    global is_pick_task_running, select_stocks, pick_task_future
    
    # 检查是否已经在运行
    if is_pick_task_running:
        return JSONResponse(
            status_code=400,
            content={
                "message": "选股任务已在运行中",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
        )
    
    # 获取请求体中的参数
    try:
        body = await request.json()
        pick_date = body.get("date")  # 可选参数
    except json.JSONDecodeError:
        pick_date = None
    
    # 标记为运行中
    is_pick_task_running = True
    
    # 定义异步任务包装器
    async def run_pick():
        global is_pick_task_running, select_stocks
        try:
            # 如果picker.pick_up_stock()是同步方法，使用线程池执行
            loop = asyncio.get_event_loop()
            # 传递pick_date参数给pick_up_stock方法
            stocks = await loop.run_in_executor(
                executor, 
                lambda: picker.pick_up_stock(pick_date=pick_date)
            )
            select_stocks = stocks if stocks else []
            return True
        except Exception as e:
            logger.error(f"选股任务执行出错: {e}")
            select_stocks = []
            return False
        finally:
            is_pick_task_running = False
    
    # 启动异步任务（不等待）
    pick_task_future = asyncio.create_task(run_pick())
    
    # 构建返回消息
    if pick_date:
        message = f"选股任务已启动（预测日期：{pick_date}）"
    else:
        message = "选股任务已启动（使用最新数据）"
    
    return {
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "is_running": True,
        "pick_date": pick_date
    }

@app.post("/stop_pick")
async def stop_pick():
    """停止pick任务"""
    global is_pick_task_running, pick_task_future
    
    if not is_pick_task_running:
        return JSONResponse(
            status_code=400,
            content={
                "message": "没有运行中的选股任务",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
        )
    
    # 尝试停止任务
    if picker:
        picker.interrupt_pick = True
    
    # 尝试取消异步任务
    if pick_task_future and not pick_task_future.done():
        pick_task_future.cancel()
        try:
            await pick_task_future
        except asyncio.CancelledError:
            pass
    
    is_pick_task_running = False
    
    return {
        "message": "选股任务已停止",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "is_running": False
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
        else:
            return {"message": "Invalid predict_type"}

        # 检查是否获取到数据
        if pd_data is None or len(pd_data) == 0:
            return {"message": "No data available for prediction"}
                
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


def predict_timer():
    """定时任务执行器"""
    while True:
        try:
            current_time = datetime.now()
            
            # 00:10:00 执行准备任务
            if current_time.hour == 0 and current_time.minute == 10 and current_time.second == 0:
                logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始执行准备任务")
                try:
                    picker.prepare_stock()
                except Exception as e:
                    logger.error(f"定时准备任务执行出错: {e}")
            
            # 14:45:00 执行选股任务
            if current_time.hour == 14 and current_time.minute == 45 and current_time.second == 0:
                logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始执行选股任务")
                try:
                    global select_stocks
                    stocks = picker.pick_up_stock()
                    select_stocks = stocks if stocks else []
                    logger.info(f"选股完成，选出 {len(select_stocks)} 只股票")
                except Exception as e:
                    logger.error(f"定时选股任务执行出错: {e}")
                    select_stocks = []
        
        except Exception as e:
            logger.error(f"定时任务调度出错: {e}")
        
        time.sleep(1)  # 每秒检查一次，提高精度

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    timer_thread = threading.Thread(target=predict_timer, daemon=True)
    timer_thread.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6029, access_log=False)