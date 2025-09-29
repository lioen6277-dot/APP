import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta # Technical Analysis Library
import warnings
import time
import re 
from datetime import datetime, timedelta

# 警告處理：隱藏 Pandas 或 TA-Lib 可能發出的未來警告
warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

st.set_page_config(
    page_title="🤖 AI趨勢分析儀表板 📈", 
    page_icon="📈", 
    layout="wide"
)

# YFinance 參數對應表
PERIOD_MAP = { 
    "30 分 (短期)": ("60d", "30m"), 
    "4 小時 (波段)": ("1y", "60m"), 
    "1 日 (中長線)": ("5y", "1d"), 
    "1 週 (長期)": ("max", "1wk")
}

# 🚀 您的【所有資產清單】(FULL_SYMBOLS_MAP) - 已包含多種資產
FULL_SYMBOLS_MAP = {
    # ----------------------------------------------------
    # A. 美股核心 (US Stocks) - 個股
    # ----------------------------------------------------
    "TSLA": {"name": "特斯拉", "keywords": ["特斯拉", "電動車", "TSLA", "Tesla"]},
    "NVDA": {"name": "輝達", "keywords": ["輝達", "英偉達", "AI", "NVDA", "Nvidia"]},
    "AAPL": {"name": "蘋果", "keywords": ["蘋果", "手機", "AAPL", "Apple"]},
    "MSFT": {"name": "微軟", "keywords": ["微軟", "雲端", "MSFT", "Microsoft"]},
    "GOOGL": {"name": "Alphabet (Google)", "keywords": ["谷歌", "Google", "GOOGL"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["亞馬遜", "電商", "AMZN", "Amazon"]},
    "META": {"name": "Meta/臉書", "keywords": ["臉書", "Meta", "FB", "META"]},
    "NFLX": {"name": "網飛", "keywords": ["網飛", "Netflix", "NFLX"]},
    "LLY": {"name": "禮來", "keywords": ["禮來", "EliLilly", "LLY"]},
    # B. 美股指數/ETF (US Indices/ETFs)
    "^GSPC": {"name": "S&P 500 指數", "keywords": ["標普", "S&P500", "^GSPC", "SPX"]},
    "^IXIC": {"name": "NASDAQ 綜合指數", "keywords": ["納斯達克", "NASDAQ", "^IXIC"]},
    "SPY": {"name": "SPDR 標普500 ETF", "keywords": ["SPY", "標普ETF"]},
    "QQQ": {"name": "Invesco QQQ Trust", "keywords": ["QQQ", "納斯達克ETF"]},
    # ----------------------------------------------------
    # C. 台股核心 (TW Stocks) - AI/科技/權值
    # ----------------------------------------------------
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "晶圓", "2330", "TSMC"]},
    "2454.TW": {"name": "聯發科", "keywords": ["聯發科", "晶片", "2454"]},
    "2317.TW": {"name": "鴻海", "keywords": ["鴻海", "富士康", "2317"]},
    "3017.TW": {"name": "奇鋐", "keywords": ["奇鋐", "散熱", "AI", "3017"]},
    "6669.TW": {"name": "緯穎", "keywords": ["緯穎", "伺服器", "6669"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["0050", "台灣50"]},
    "^TWII": {"name": "台灣加權指數", "keywords": ["加權", "台股大盤"]},
    # ----------------------------------------------------
    # D. 加密貨幣 (Crypto)
    # ----------------------------------------------------
    "BTC-USD": {"name": "比特幣", "keywords": ["比特幣", "BTC"]},
    "ETH-USD": {"name": "以太幣", "keywords": ["以太幣", "ETH"]},
    "SOL-USD": {"name": "Solana", "keywords": ["Solana", "SOL"]},
}

# 🎯 側邊欄資產分類
CATEGORY_MAP = {
    "美股 (US) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if not (c.endswith(".TW") or c.endswith("-USD") or c.startswith("^TWII"))],
    "台股 (TW) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith(".TW") or c.startswith("^TWII")],
    "加密貨幣 (Crypto)": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith("-USD")],
}

# 建立第二層 Selectbox 的選項 {顯示名稱: 代碼}
CATEGORY_HOT_OPTIONS = {}
for category, codes in CATEGORY_MAP.items():
    options = {}
    sorted_codes = sorted(codes) 
    for code in sorted_codes:
        info = FULL_SYMBOLS_MAP.get(code)
        if info:
            options[f"{code} - {info['name']}"] = code
    CATEGORY_HOT_OPTIONS[category] = options
    
# ==============================================================================
# 2. 輔助函式定義
# ==============================================================================

def get_symbol_from_query(query: str) -> str:
    """解析用戶輸入，嘗試匹配並補齊 YFinance 代碼 (例如: 2330 -> 2330.TW)。"""
    query = query.strip()
    # 1. 優先精確代碼/英文關鍵字匹配 (轉大寫)
    query_upper = query.upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query_upper == code:
            return code
        if any(query_upper == kw.upper() for kw in data["keywords"]):
            return code
    # 2. 中文名稱精確匹配
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == data["name"]:
            return code
    # 3. 台灣股票代碼自動補齊
    if re.fullmatch(r'\d{4,6}', query) and not any(ext in query_upper for ext in ['.TW', '.HK', '.SS', '-USD']):
        tw_code = f"{query}.TW"
        if tw_code in FULL_SYMBOLS_MAP:
             return tw_code
        return tw_code # 即使不在清單，仍嘗試補齊
    # 4. 沒匹配到任何預設代碼，直接返回用戶輸入
    return query

@st.cache_data(ttl=3600, show_spinner="正在從 Yahoo Finance 獲取數據...")
def get_stock_data(symbol, period, interval):
    """
    獲取股票數據。核心修正：返回最新的「已完成 K 線」數據。
    """
    try:
        ticker = yf.Ticker(symbol)
        # 為了應對 yfinance 間歇性故障，嘗試兩次
        for _ in range(2):
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                break
            time.sleep(1)
        
        if df.empty:
            return pd.DataFrame()
        
        df.columns = [col.capitalize() for col in df.columns] 
        df.index.name = 'Date'
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # 🚩 核心修正：移除最後一筆（通常是未結束的當前K線，以確保指標計算的準確性）
        return df.iloc[:-1]
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    """獲取公司名稱、類別和貨幣資訊"""
    info = FULL_SYMBOLS_MAP.get(symbol, {})
    if info:
        if symbol.endswith(".TW") or symbol.startswith("^TWII"):
            category = "台股 (TW)"
            currency = "TWD"
        elif symbol.endswith("-USD"):
            category = "加密貨幣 (Crypto)"
            currency = "USD"
        else:
            category = "美股 (US)"
            currency = "USD"
        return {"name": info['name'], "category": category, "currency": currency}
    
    # 嘗試從 YFinance 獲取更詳細資訊 (用於自訂標的)
    try:
        ticker = yf.Ticker(symbol)
        yf_info = ticker.info
        name = yf_info.get('longName') or yf_info.get('shortName') or symbol
        currency = yf_info.get('currency') or "USD"
        category = "未分類"
        if symbol.endswith(".TW"): category = "台股 (TW)"
        elif symbol.endswith("-USD"): category = "加密貨幣 (Crypto)"
        elif symbol.startswith("^"): category = "指數"
        elif currency == "USD": category = "美股 (US)"
        return {"name": name, "category": category, "currency": currency}
    except:
        return {"name": symbol, "category": "未分類", "currency": "USD"}

def get_currency_symbol(symbol):
    """根據貨幣代碼返回符號"""
    currency_code = get_company_info(symbol).get('currency', 'USD')
    if currency_code == 'TWD':
        return 'NT$'
    elif currency_code == 'USD':
        return '$'
    elif currency_code == 'HKD':
        return 'HK$'
    else:
        return currency_code + ' '

def calculate_technical_indicators(df):
    """計算並將技術指標加入 DataFrame"""
    if len(df) < 50: 
        return df # 數據不足跳過

    # 趨勢指標
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    
    # 動能指標
    df['MACD'] = ta.trend.macd_diff(df['Close'])
    df['RSI'] = ta.momentum.rsi(df['Close'])
    df['Stoch_K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    
    # 波動性指標
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'])
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'])
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    
    return df

def get_technical_data_df(df):
    """根據最新技術指標數據生成帶有判讀結論的 DataFrame"""
    if df.empty or len(df) < 50: 
        return pd.DataFrame()

    last_row = df.iloc[-1]
    
    # 收集需要顯示的指標及其基準值
    indicators_to_display = {
        '收盤價 vs SMA-20': last_row['Close'],
        '收盤價 vs EMA-50': last_row['Close'],
        'RSI (14)': last_row['RSI'],
        'Stochastics (%K)': last_row['Stoch_K'],
        'MACD 柱狀圖 (Signal)': last_row['MACD'],
        'ATR (14)': last_row['ATR'],
        '布林通道 (BB)': last_row['Close'],
    }
    
    data = []
    
    for name, value in indicators_to_display.items():
        conclusion = "中性：數據正常"
        color = "blue"
        
        # 趨勢判讀 (SMA/EMA)
        if 'SMA-20' in name:
            ma = last_row['SMA_20']
            if value > ma * 1.01:
                conclusion = "多頭：價格強勢站上均線"
                color = "red"
            elif value < ma * 0.99:
                conclusion = "空頭：價格跌破均線"
                color = "green"
            elif value > ma:
                conclusion = "中性偏多：價格位於均線之上"
                color = "orange"
            else:
                conclusion = "中性偏空：價格位於均線之下"
                color = "orange"
        
        elif 'EMA-50' in name:
            ma = last_row['EMA_50']
            if value > ma * 1.02:
                conclusion = "多頭：中長線趨勢強勁"
                color = "red"
            elif value < ma * 0.98:
                conclusion = "空頭：中長線趨勢疲軟"
                color = "green"
            elif value > ma:
                conclusion = "中性偏多：位於中長線均線之上"
                color = "orange"
            else:
                conclusion = "中性偏空：位於中長線均線之下"
                color = "orange"

        # 動能判讀 (RSI/Stoch)
        elif name == 'RSI (14)':
            if value > 70:
                conclusion = "警告：超買區域，潛在回調"
                color = "green"
            elif value < 30:
                conclusion = "強化：超賣區域，潛在反彈"
                color = "red"
        
        elif name == 'Stochastics (%K)':
            if value > 80:
                conclusion = "警告：接近超買區域"
                color = "green"
            elif value < 20:
                conclusion = "強化：接近超賣區域"
                color = "red"

        elif name == 'MACD 柱狀圖 (Signal)':
            if value > 0 and last_row['MACD'] > df.iloc[-2]['MACD']:
                conclusion = "強化：多頭動能增強 (金叉趨勢)"
                color = "red"
            elif value < 0 and last_row['MACD'] < df.iloc[-2]['MACD']:
                conclusion = "削弱：空頭動能增強 (死叉趨勢)"
                color = "green"
            else:
                conclusion = "中性：動能盤整/轉折中"
                color = "orange"
        
        # 波動性判讀 (ATR)
        elif name == 'ATR (14)':
            avg_atr = df['ATR'].mean()
            if value > avg_atr * 1.5:
                conclusion = "警告：極高波動性"
                color = "green" # 高波動視為高風險
            elif value < avg_atr * 0.5:
                conclusion = "中性：低波動性 (盤整待突破)"
                color = "orange"

        # 布林通道判讀
        elif name == '布林通道 (BB)':
            high = last_row['BB_High']
            low = last_row['BB_Low']
            range_pct = (high - low) / low
            
            if value > high:
                conclusion = "警告：價格位於上軌外側 (極度超強勢)"
                color = "red"
            elif value < low:
                conclusion = "強化：價格位於下軌外側 (極度超弱勢)"
                color = "green"
            else:
                conclusion = f"中性：在上下軌間 ({range_pct*100:.2f}% 寬度)"
                color = "blue"
        
        data.append([name, value, conclusion, color])

    technical_df = pd.DataFrame(data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    technical_df = technical_df.set_index('指標名稱')
    return technical_df

@st.cache_data(ttl=3600)
def calculate_fundamental_rating(symbol):
    """執行基本面分析，並返回 0-9 評分"""
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 獲取關鍵基本面指標
        roe = info.get('returnOnEquity', 0)
        freeCashFlow = info.get('freeCashflow', 0)
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0)
        marketCap = info.get('marketCap', 1) 
        pe = info.get('trailingPE', 99)
        
        # 1. 成長與效率評分 (ROE) - 滿分 3 分
        roe_score = 0
        if roe > 0.15: roe_score = 3 
        elif roe > 0.08: roe_score = 2
        elif roe > 0: roe_score = 1
        
        # 2. 估值評分 (PE) - 滿分 3 分
        pe_score = 0
        if pe < 15: pe_score = 3
        elif pe < 25: pe_score = 2
        elif pe < 35: pe_score = 1
        
        # 3. 現金流與償債能力 - 滿分 3 分
        cf_score = 0
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt else 100
        if freeCashFlow > 0.05 * marketCap and cash_debt_ratio > 1.5: cf_score = 3
        elif freeCashFlow > 0 and cash_debt_ratio > 1: cf_score = 2
        elif freeCashFlow > 0: cf_score = 1

        # 綜合評級 (總分 9)
        combined_rating = roe_score + pe_score + cf_score
        
        # 評級解讀
        if combined_rating >= 7:
            message = "頂級優異：基本面健康，成長與估值均強勁，適合長期持有。"
        elif combined_rating >= 5:
            message = "良好穩健：財務結構穩固，但可能在成長性或估值方面有所不足。"
        elif combined_rating >= 3:
            message = "中性警示：存在財務壓力或估值過高，需警惕風險。"
        else:
            message = "基本面較弱：財務指標不佳，不建議盲目進場。"
            
        return {
            "Combined_Rating": combined_rating,
            "Message": message,
            "Details": info
        }

    except Exception:
        # 指數、加密貨幣或數據庫無資料時
        return {
            "Combined_Rating": 1.0, 
            "Message": "基本面數據獲取失敗或不適用 (例如指數/加密貨幣)。",
            "Details": None
        }

def generate_expert_fusion_signal(df, fa_rating, is_long_term=True):
    """
    基於多指標融合和基本面評級，產生最終的交易策略。
    """
    
    if df.empty or len(df) < 50:
        # 返回預設的錯誤或空值
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'expert_opinions': {}, 'atr': 0}

    last_row = df.iloc[-1]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    
    expert_opinions = {}
    
    # 1. 趨勢專家 (均線) - 總分 +/- 3
    trend_score = 0
    if last_row['Close'] > last_row['SMA_20'] and last_row['SMA_20'] > last_row['EMA_50']:
        trend_score = 3
        expert_opinions['趨勢分析 (均線)'] = "多頭：短線(SMA)與中長線(EMA)均線均呈多頭排列。"
    elif last_row['Close'] < last_row['SMA_20'] and last_row['SMA_20'] < last_row['EMA_50']:
        trend_score = -3
        expert_opinions['趨勢分析 (均線)'] = "空頭：短線與中長線均線均呈空頭排列。"
    else:
        trend_score = 0
        expert_opinions['趨勢分析 (均線)'] = "中性：價格位於均線之間，趨勢不明。"
        
    # 2. 動能專家 (RSI & Stoch) - 總分 +/- 2
    momentum_score = 0
    rsi = last_row['RSI']
    stoch_k = last_row['Stoch_K']
    if rsi < 40 and stoch_k < 40:
        momentum_score = 2
        expert_opinions['動能分析 (RSI/Stoch)'] = "強化：動能指標低位，潛在反彈空間大。"
    elif rsi > 60 and stoch_k > 60:
        momentum_score = -2
        expert_opinions['動能分析 (RSI/Stoch)'] = "削弱：動能指標高位，潛在回調壓力大。"
    else:
        momentum_score = 0
        expert_opinions['動能分析 (RSI/Stoch)'] = "中性：指標位於中間區域。"
        
    # 3. 波動性專家 (MACD) - 總分 +/- 2
    volatility_score = 0
    macd_diff = last_row['MACD']
    if macd_diff > 0 and macd_diff > df.iloc[-2]['MACD']:
        volatility_score = 2
        expert_opinions['波動分析 (MACD)'] = "多頭：MACD柱狀圖擴大，多頭動能強勁。"
    elif macd_diff < 0 and macd_diff < df.iloc[-2]['MACD']:
        volatility_score = -2
        expert_opinions['波動分析 (MACD)'] = "空頭：MACD柱狀圖擴大，空頭動能強勁。"
    else:
        volatility_score = 0
        expert_opinions['波動分析 (MACD)'] = "中性：動能盤整。"
        
    # 4. K線形態專家 (簡單判斷) - 總分 +/- 1.5
    kline_score = 0
    is_up_bar = last_row['Close'] > last_row['Open']
    is_strong_up = is_up_bar and (last_row['Close'] - last_row['Open']) > atr_value * 0.5
    is_strong_down = not is_up_bar and (last_row['Open'] - last_row['Close']) > atr_value * 0.5
    
    if is_strong_up:
        kline_score = 1.5
        expert_opinions['K線形態分析'] = "強化：實體大陽線，買盤積極。"
    elif is_strong_down:
        kline_score = -1.5
        expert_opinions['K線形態分析'] = "削弱：實體大陰線，賣壓沉重。"
    else:
        kline_score = 0
        expert_opinions['K線形態分析'] = "中性：K線實體小，觀望。"
        
    # 融合評分 (總分 8.5 分 + FA 評分)
    # 將 FA 評分(0-9)正規化到 0-3 的權重
    fa_weight = (fa_rating / 9) * 3 
    fusion_score = trend_score + momentum_score + volatility_score + kline_score + fa_weight
    
    # 最終行動
    action = "觀望 (Neutral)"
    if fusion_score >= 4.5:
        action = "買進 (Buy)"
    elif fusion_score >= 1.5:
        action = "中性偏買 (Hold/Buy)"
    elif fusion_score <= -4.5:
        action = "賣出 (Sell/Short)"
    elif fusion_score <= -1.5:
        action = "中性偏賣 (Hold/Sell)"

    # 信心指數 (將評分正規化到 0-100)
    confidence = min(100, max(0, 50 + fusion_score * 5))
    
    # 風險控制與交易策略 (基於 ATR)
    risk_multiple = 2.0 if is_long_term else 1.5 
    reward_multiple = 2.0 
    
    # 定義策略
    if "買進" in action:
        entry = current_price * 0.99 
        stop_loss = entry - (atr_value * risk_multiple)
        take_profit = entry + (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於**{action}**信號，建議考慮在 {entry:,.4f} 附近尋找進場點，並以 ATR 衡量風險。"
    elif "賣出" in action:
        entry = current_price * 1.01
        stop_loss = entry + (atr_value * risk_multiple) 
        take_profit = entry - (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於**{action}**信號，建議考慮在 {entry:,.4f} 附近尋找放空點，並以 ATR 衡量風險。"
    else:
        entry = current_price
        stop_loss = current_price - atr_value
        take_profit = current_price + atr_value
        strategy_desc = "市場信號混亂或處於盤整，建議等待趨勢明朗。無明確進場建議。"

    return {
        'action': action,
        'score': round(fusion_score, 2),
        'confidence': round(confidence, 0),
        'strategy': strategy_desc,
        'entry_price': entry,
        'take_profit': take_profit,
        'stop_loss': stop_loss,
        'current_price': current_price,
        'expert_opinions': expert_opinions,
        'atr': atr_value
    }

def create_comprehensive_chart(df, symbol, period_key):
    """繪製綜合 K 線圖，包含均線、MACD、RSI、BBands。"""
    
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                        row_heights=[0.6, 0.2, 0.2], 
                        subplot_titles=(f"{symbol} 價格走勢 ({period_key})", "MACD 指標", "RSI 指標"))

    # K線圖
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='K線',
            increasing_line_color='red', 
            decreasing_line_color='green'
        ),
        row=1, col=1
    )

    # 均線與布林通道
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='gray', width=0.5, dash='dash'), name='BB High'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='gray', width=0.5, dash='dash'), name='BB Low'), row=1, col=1)

    # MACD 圖
    colors = ['red' if val >= 0 else 'green' for val in df['MACD']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD'], name='MACD 柱狀圖', marker_color=colors), row=2, col=1)
    
    # RSI 圖
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_width=1, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=30, line_width=1, line_dash="dash", line_color="red", row=3, col=1)
    
    # Layout 配置
    fig.update_layout(
        height=800, 
        xaxis_rangeslider_visible=False,
        showlegend=True,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    fig.update_xaxes(showgrid=True, row=1, col=1)
    fig.update_xaxes(showgrid=True, row=2, col=1)
    fig.update_xaxes(showgrid=True, row=3, col=1, title_text="日期")
    
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    
    return fig

# ==============================================================================
# 3. Streamlit 主程式 (Main App)
# ==============================================================================

def main():
    # Session State 初始化
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = 'TSLA'
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'data_df' not in st.session_state:
        st.session_state['data_df'] = pd.DataFrame()

    # 側邊欄 (Sidebar) 處理
    st.sidebar.title("🛠️ 分析參數設定")

    # --- 1. 標的選擇 ---
    st.sidebar.subheader("1. 選擇分析標的")

    category_selection = st.sidebar.selectbox(
        "選擇類別:",
        list(CATEGORY_MAP.keys()),
        key='category_select'
    )

    hot_options = CATEGORY_HOT_OPTIONS.get(category_selection, {})
    default_index = 0
    try:
        last_symbol = st.session_state.get('last_search_symbol', 'TSLA')
        last_display_name = next(k for k, v in hot_options.items() if v == last_symbol)
        default_index = list(hot_options.keys()).index(last_display_name)
    except StopIteration:
        default_index = 0
    
    selected_display_name = st.sidebar.selectbox(
        "選擇熱門標的:",
        list(hot_options.keys()),
        index=default_index,
        key='hot_symbol_select'
    )
    
    selected_symbol_from_hot = hot_options.get(selected_display_name, 'TSLA')

    manual_input = st.sidebar.text_input(
        "或手動輸入代碼/名稱 (e.g., NVDA, 2330, 台積電):", 
        value=st.session_state.get('last_search_symbol', 'TSLA'),
        key='manual_symbol_input'
    )
    
    # 判斷最終要分析的代碼
    raw_symbol = manual_input if manual_input and manual_input.strip() != st.session_state.get('last_search_symbol', 'TSLA') else selected_symbol_from_hot
    final_symbol_to_analyze = get_symbol_from_query(raw_symbol)
    
    # --- 2. 週期選擇 ---
    st.sidebar.subheader("2. 選擇分析週期")
    selected_period_key = st.sidebar.selectbox(
        "選擇 K 線週期:",
        list(PERIOD_MAP.keys()),
        key='period_select'
    )
    
    period, interval = PERIOD_MAP[selected_period_key]

    # --- 3. 執行按鈕 ---
    st.sidebar.markdown("---")
    analyze_button_clicked = st.sidebar.button("執行 AI 分析 🚀", use_container_width=True)

    # ==============================================================================
    # 4. 資料獲取與處理
    # ==============================================================================

    # 只有在點擊按鈕或標的改變時才重新運行分析
    if analyze_button_clicked or (st.session_state.get('last_search_symbol') != final_symbol_to_analyze and raw_symbol != st.session_state.get('last_search_symbol')):
        
        st.session_state['last_search_symbol'] = final_symbol_to_analyze
        st.session_state['data_ready'] = False 

        with st.spinner(f"正在分析 {final_symbol_to_analyze} 的數據..."):
            
            # 獲取股價數據 (已修正為只取完整 K 線)
            df = get_stock_data(final_symbol_to_analyze, period, interval)
            
            if df.empty or len(df) < 50:
                st.error(f"⚠️ **數據獲取失敗或不足!** 無法獲取 **{final_symbol_to_analyze}** 在此週期 ({selected_period_key}) 的數據，或數據不足 50 筆以計算指標。")
                st.session_state['data_ready'] = False
            else:
                company_info = get_company_info(final_symbol_to_analyze)
                st.session_state['company_info'] = company_info
                
                # 技術指標計算 (所有指標都在這裡計算好)
                df = calculate_technical_indicators(df)
                st.session_state['data_df'] = df
                
                fa_result = calculate_fundamental_rating(final_symbol_to_analyze)
                st.session_state['fa_result'] = fa_result
                
                is_long_term = "日" in selected_period_key or "週" in selected_period_key
                expert_signal = generate_expert_fusion_signal(
                    df, 
                    fa_result['Combined_Rating'], 
                    is_long_term
                )
                st.session_state['expert_signal'] = expert_signal

                st.session_state['data_ready'] = True
                st.success(f"✅ {company_info['name']} ({final_symbol_to_analyze}) 數據分析完成！")

    # ==============================================================================
    # 5. 主內容區 (Main Content) 顯示
    # ==============================================================================

    if st.session_state.get('data_ready', False):
        
        df = st.session_state['data_df']
        fa_result = st.session_state['fa_result']
        expert_signal = st.session_state['expert_signal']
        company_info = st.session_state['company_info']
        currency_symbol = get_currency_symbol(final_symbol_to_analyze)
        
        st.title(f"🤖 {company_info['name']} ({final_symbol_to_analyze}) AI 趨勢分析儀表板")
        st.caption(f"類別: **{company_info['category']}** | **基準價格時間**: **{df.index[-1].strftime('%Y-%m-%d %H:%M')}** ({selected_period_key} K線收盤價)")
        st.markdown("---")

        # --- A. 核心信號區 ---
        st.subheader(f"⚡ AI 專家融合信號")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        action = expert_signal['action']
        if "買進" in action or "強化" in action:
            signal_color = "red"
        elif "賣出" in action or "削弱" in action:
            signal_color = "green"
        else:
            signal_color = "orange"

        with col1:
            st.metric(
                label=f"💰 基準價格 ({company_info['currency']})", 
                value=f"{currency_symbol}{expert_signal['current_price']:,.4f}",
                # 計算漲跌幅基於倒數第二根K線(即前一根完整K線)
                delta=f"相較前K線: {((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100):.2f}%" if len(df) > 1 else "N/A"
            )

        with col2:
            st.markdown(f"**🎯 綜合行動建議**")
            st.markdown(f"<h3 style='color:{signal_color}; font-weight:bold;'>{action}</h3>", unsafe_allow_html=True)
            st.caption(f"信心指數: **{int(expert_signal['confidence'])}/100**")

        with col3:
            st.metric("波動區間 (ATR 14)", f"{expert_signal['atr']:,.4f}")
            st.caption(f"總量化評分: **{expert_signal['score']:.2f}**")

        st.info(expert_signal['strategy'])
        
        # 交易策略細節
        with st.expander("AI 交易建議與風險控制 (基於 ATR 波動)"):
            c1, c2, c3 = st.columns(3)
            c1.metric("建議進場點 (Entry)", f"{currency_symbol}{expert_signal['entry_price']:,.4f}")
            c2.metric("🚀 建議停利點 (Take Profit)", f"{currency_symbol}{expert_signal['take_profit']:,.4f}")
            c3.metric("🛑 建議停損點 (Stop Loss)", f"{currency_symbol}{expert_signal['stop_loss']:,.4f}")
            
            st.markdown("---")
            st.markdown("**專家意見分解:**")
            
            for expert, opinion in expert_signal['expert_opinions'].items():
                st.markdown(f"* **{expert}**: {opinion}")

        st.markdown("---")

        # --- B. 基本面分析區 ---
        st.subheader("🏦 基本面與估值分析")
        
        fa_rating = fa_result['Combined_Rating']
        if fa_rating >= 7:
            fa_color = "red" 
        elif fa_rating >= 5:
            fa_color = "orange"
        else:
            fa_color = "green" 
            
        st.markdown(f"**綜合評級:** <span style='color:{fa_color}; font-weight:bold; font-size:24px;'>{fa_rating:.1f}/9.0</span>", unsafe_allow_html=True)
        st.warning(fa_result['Message'])
        
        if fa_result['Details']:
             with st.expander("查看關鍵基本面指標"):
                details = fa_result['Details']
                st.json({
                    "市值 (Market Cap)": f"{currency_symbol}{details.get('marketCap', 'N/A'):,.0f}",
                    "本益比 (P/E)": f"{details.get('trailingPE', 'N/A'):.2f}",
                    "股東權益報酬率 (ROE)": f"{details.get('returnOnEquity', 'N/A') * 100:.2f}%" if isinstance(details.get('returnOnEquity'), (int, float)) else "N/A",
                    "自由現金流 (Free Cash Flow)": f"{currency_symbol}{details.get('freeCashflow', 'N/A'):,.0f}",
                    "總負債/總現金 (Debt/Cash Ratio)": f"{details.get('totalDebt', 0) / (details.get('totalCash', 1) if details.get('totalCash', 1) > 0 else 1):.2f}"
                })
        
        st.markdown("---")

        # --- C. 技術指標與圖表區 ---
        st.subheader("🎯 關鍵技術指標判讀 (交叉驗證細節)")

        technical_df = get_technical_data_df(df)
        
        if not technical_df.empty:
            def color_cells(row):
                styles = []
                color = row['顏色']
                if color == 'red':
                    styles.append('background-color: rgba(255, 0, 0, 0.1); color: red; font-weight: bold;')
                elif color == 'green':
                    styles.append('background-color: rgba(0, 128, 0, 0.1); color: green; font-weight: bold;')
                elif color == 'orange':
                    styles.append('background-color: rgba(255, 165, 0, 0.1); color: orange;')
                else: 
                    styles.append('color: blue;')
                
                return styles * 2 + [''] 

            st.dataframe(
                technical_df[['最新值', '分析結論']].style.apply(color_cells, axis=1),
                use_container_width=True,
                key=f"technical_df_{final_symbol_to_analyze}_{selected_period_key}",
                column_config={
                    "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                    "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的專業解讀"),
                }
            )
            st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化（**紅色=多頭/強化信號**，**綠色=空頭/削弱信號**，**橙色=中性/警告**）。")

        else:
            st.info("無足夠數據生成關鍵技術指標表格。")
        
        st.markdown("---")
        
        st.subheader(f"📊 完整技術分析圖表")
        chart = create_comprehensive_chart(df, final_symbol_to_analyze, selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")
    
    # 首次載入或數據未準備好時的提示
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
         st.info("請在左側選擇或輸入標的，然後點擊 **『執行 AI 分析 🚀』** 開始。")


if __name__ == '__main__':
    main()
    
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")
