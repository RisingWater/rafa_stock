from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime, timedelta
from stock_db import StockDB
from stock_tools import StockTools
import akshare as ak
import asyncio
import json
import os

app = FastAPI(title="股票数据查看器")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建模板和静态文件目录
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

manager = ConnectionManager()

def get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    return f"股票{stock_code}"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stock/{stock_code}/daily")
async def get_daily_data(stock_code: str, end_date: str = None):
    """获取日K线数据API - 支持指定结束日期"""
    try:
        db = StockDB()
        tools = StockTools()
        
        # 设置默认结束日期（今天）
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
                
        # 计算开始日期（50个交易日前的近似值）
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - timedelta(days=100)).strftime("%Y-%m-%d")
        
        print(f"获取日线数据: {stock_code} {start_date} 到 {end_date}")
        
        # 从数据库获取数据
        data = db.get_daily_data(stock_code, start_date, end_date)
        
        if data.empty:
            return {"error": "未找到日K线数据"}
        
        # 取最新的50条数据
        latest_data = data.sort_values('date', ascending=False).head(50).sort_values('date', ascending=True)
        
        # 转换为前端需要的格式
        result = {
            "stock_code": stock_code,
            "stock_name": get_stock_name(stock_code),
            "end_date": end_date,
            "data": latest_data[['date', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
        }
        
        return result
        
    except Exception as e:
        print(f"获取日线数据错误: {e}")
        return {"error": str(e)}

@app.get("/api/stock/{stock_code}/min15")
async def get_min5_data(stock_code: str, end_date: str = None):
    """获取5分钟K线数据API - 支持指定结束日期"""
    try:
        db = StockDB()
        tools = StockTools()
        
        # 设置默认结束日期（今天）
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取指定日期的上一个交易日
        trade_date = tools.get_previous_trading_day(end_date)
        
        if not trade_date:
            return {"error": "未找到交易日"}
        
        # 设置时间范围（交易日的9:30-15:00）
        start_datetime = f"{trade_date} 09:30:00"
        end_datetime = f"{trade_date} 15:00:00"
        
        print(f"获取5分钟数据: {stock_code} {start_datetime} 到 {end_datetime}")
        
        # 从数据库获取数据
        data = db.get_min_data(stock_code, '15', start_datetime, end_datetime)
        
        if data.empty:
            return {"error": "未找到5分钟K线数据"}
        
        # 转换为前端需要的格式
        result = {
            "stock_code": stock_code,
            "stock_name": get_stock_name(stock_code),
            "trade_date": trade_date,
            "data": data[['datetime', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
        }
        
        return result
        
    except Exception as e:
        print(f"获取5分钟数据错误: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # 方法1: 使用模块字符串形式（推荐）
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )