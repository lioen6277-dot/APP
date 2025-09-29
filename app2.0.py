import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import warnings
import time
import re 
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

st.set_page_config(
    page_title="AI趨勢分析", 
    page_icon="📈", 
    layout="wide"
)

# 週期映射：(YFinance Period, YFinance Interval)
PERIOD_MAP = { 
    "30 分 (短期)": ("60d", "30m"), 
    "4 小時 (波段)": ("1y", "60m"), 
    "1 日 (中長線)": ("5y", "1d"), 
    "1 週 (長期)": ("max", "1wk")
}

# 🚀 您的【所有資產清單】(FULL_SYMBOLS_MAP) - 維持不變
FULL_SYMBOLS_MAP = {
    # ----------------------------------------------------
    # A. 美股核心 (US Stocks) - 個股
    # ----------------------------------------------------
    "TSLA": {"name": "特斯拉", "keywords": ["特斯拉", "電動車", "TSLA", "Tesla"]},
    "NVDA": {"name": "輝達", "keywords": ["輝達", "英偉達", "AI", "NVDA", "Nvidia"]},
    "AAPL": {"name": "蘋果", "keywords": ["蘋果", "Apple", "AAPL"]},
    "GOOGL": {"name": "谷歌/Alphabet", "keywords": ["谷歌", "Alphabet", "GOOGL", "GOOG"]},
    "MSFT": {"name": "微軟", "keywords": ["微軟", "Microsoft", "MSFT"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["亞馬遜", "Amazon", "AMZN"]},
    "META": {"name": "Meta/臉書", "keywords": ["臉書", "Meta", "FB", "META"]},
    "NFLX": {"name": "網飛", "keywords": ["網飛", "Netflix", "NFLX"]},
    "ADBE": {"name": "Adobe", "keywords": ["Adobe", "ADBE"]},
    "CRM": {"name": "Salesforce", "keywords": ["Salesforce", "CRM"]},
    "ORCL": {"name": "甲骨文", "keywords": ["甲骨文", "Oracle", "ORCL"]},
    "COST": {"name": "好市多", "keywords": ["好市多", "Costco", "COST"]},
    "JPM": {"name": "摩根大通", "keywords": ["摩根大通", "JPMorgan", "JPM"]},
    "V": {"name": "Visa", "keywords": ["Visa", "V"]},
    "WMT": {"name": "沃爾瑪", "keywords": ["沃爾瑪", "Walmart", "WMT"]},
    "PG": {"name": "寶潔", "keywords": ["寶潔", "P&G", "PG"]},
    "KO": {"name": "可口可樂", "keywords": ["可口可樂", "CocaCola", "KO"]},
    "PEP": {"name": "百事", "keywords": ["百事", "Pepsi", "PEP"]},
    "MCD": {"name": "麥當勞", "keywords": ["麥當勞", "McDonalds", "MCD"]},
    "QCOM": {"name": "高通", "keywords": ["高通", "Qualcomm", "QCOM"]},
    "INTC": {"name": "英特爾", "keywords": ["英特爾", "Intel", "INTC"]},
    "AMD": {"name": "超微", "keywords": ["超微", "AMD"]},
    "LLY": {"name": "禮來", "keywords": ["禮來", "EliLilly", "LLY"]},
    "UNH": {"name": "聯合健康", "keywords": ["聯合健康", "UNH"]},
    "HD": {"name": "家得寶", "keywords": ["家得寶", "HomeDepot", "HD"]},
    "CAT": {"name": "開拓重工", "keywords": ["開拓重工", "Caterpillar", "CAT"]},
    # B. 美股指數/ETF (US Indices/ETFs)
    "^GSPC": {"name": "S&P 500 指數", "keywords": ["標普", "S&P500", "^GSPC", "SPX"]},
    "^IXIC": {"name": "NASDAQ 綜合指數", "keywords": ["納斯達克", "NASDAQ", "^IXIC"]},
    "^DJI": {"name": "道瓊工業指數", "keywords": ["道瓊", "DowJones", "^DJI"]},
    "SPY": {"name": "SPDR 標普500 ETF", "keywords": ["SPY", "標普ETF"]},
    "QQQ": {"name": "Invesco QQQ Trust", "keywords": ["QQQ", "納斯達克ETF"]},
    "VOO": {"name": "Vanguard 標普500 ETF", "keywords": ["VOO", "Vanguard"]},
    # ----------------------------------------------------
    # C. 台灣市場 (TW Stocks/ETFs/Indices)
    # ----------------------------------------------------
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "2330", "TSMC"]},
    "2317.TW": {"name": "鴻海", "keywords": ["鴻海", "2317", "Foxconn"]},
    "2454.TW": {"name": "聯發科", "keywords": ["聯發科", "2454", "MediaTek"]},
    "2308.TW": {"name": "台達電", "keywords": ["台達電", "2308", "Delta"]},
    "3017.TW": {"name": "奇鋐", "keywords": ["奇鋐", "3017", "散熱"]},
    "3231.TW": {"name": "緯創", "keywords": ["緯創", "3231"]},
    "2382.TW": {"name": "廣達", "keywords": ["廣達", "2382"]},
    "2379.TW": {"name": "瑞昱", "keywords": ["瑞昱", "2379"]},
    "2881.TW": {"name": "富邦金", "keywords": ["富邦金", "2881"]},
    "2882.TW": {"name": "國泰金", "keywords": ["國泰金", "2882"]},
    "2603.TW": {"name": "長榮", "keywords": ["長榮", "2603", "航運"]},
    "2609.TW": {"name": "陽明", "keywords": ["陽明", "2609", "航運"]},
    "2615.TW": {"name": "萬海", "keywords": ["萬海", "2615", "航運"]},
    "2891.TW": {"name": "中信金", "keywords": ["中信金", "2891"]},
    "1101.TW": {"name": "台泥", "keywords": ["台泥", "1101"]},
    "1301.TW": {"name": "台塑", "keywords": ["台塑", "1301"]},
    "2357.TW": {"name": "華碩", "keywords": ["華碩", "2357"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["台灣50", "0050", "台灣五十"]},
    "0056.TW": {"name": "元大高股息", "keywords": ["高股息", "0056"]},
    "00878.TW": {"name": "國泰永續高股息", "keywords": ["00878", "國泰永續"]},
    "^TWII": {"name": "台股指數", "keywords": ["台股指數", "加權指數", "^TWII"]},
    # ----------------------------------------------------
    # D. 加密貨幣 (Crypto)
    # ----------------------------------------------------
    "BTC-USD": {"name": "比特幣", "keywords": ["比特幣", "BTC", "bitcoin", "BTC-USDT"]},
    "ETH-USD": {"name": "以太坊", "keywords": ["以太坊", "ETH", "ethereum", "ETH-USDT"]},
    "SOL-USD": {"name": "Solana", "keywords": ["Solana", "SOL", "SOL-USDT"]},
    "BNB-USD": {"name": "幣安幣", "keywords": ["幣安幣", "BNB", "BNB-USDT"]},
    "DOGE-USD": {"name": "狗狗幣", "keywords": ["狗狗幣", "DOGE", "DOGE-USDT"]},
    "XRP-USD": {"name": "瑞波幣", "keywords": ["瑞波幣", "XRP", "XRP-USDT"]},
    "ADA-USD": {"name": "Cardano", "keywords": ["Cardano", "ADA", "ADA-USDT"]},
    "AVAX-USD": {"name": "Avalanche", "keywords": ["Avalanche", "AVAX", "AVAX-USDT"]},
    "DOT-USD": {"name": "Polkadot", "keywords": ["Polkadot", "DOT", "DOT-USDT"]},
    "LINK-USD": {"name": "Chainlink", "keywords": ["Chainlink", "LINK", "LINK-USDT"]},
}

# 建立第二層選擇器映射 (無須修改)
CATEGORY_MAP = {
    "美股 (US) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if not (c.endswith(".TW") or c.endswith("-USD") or c.startswith("^TWII"))],
    "台股 (TW) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith(".TW") or c.startswith("^TWII")],
    "加密貨幣 (Crypto)": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith("-USD")],
}

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

# get_symbol_from_query, get_stock_data, get_company_info, get_currency_symbol 
# (數據獲取與基礎資訊 - 維持不變)

def get_symbol_from_query(query: str) -> str:
    """ 🎯 進化後的代碼解析函數：同時檢查 FULL_SYMBOLS_MAP """
    query = query.strip()
    query_upper = query.upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query_upper == code: return code
        if any(query_upper == kw.upper() for kw in data["keywords"]): return code 
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == data["name"]: return code
    if re.fullmatch(r'\d{4,6}', query) and not any(ext in query_upper for ext in ['.TW', '.HK', '.SS', '-USD']):
        tw_code = f"{query}.TW"
        if tw_code in FULL_SYMBOLS_MAP: return tw_code
        return tw_code
    return query

@st.cache_data(ttl=3600, show_spinner="正在從 Yahoo Finance 獲取數據...")
def get_stock_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty: return pd.DataFrame()
        df.columns = [col.capitalize() for col in df.columns] 
        df.index.name = 'Date'
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        return df.iloc[:-1]
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    info = FULL_SYMBOLS_MAP.get(symbol, {})
    if info:
        if symbol.endswith(".TW") or symbol.startswith("^TWII"): category, currency = "台股 (TW)", "TWD"
        elif symbol.endswith("-USD"): category, currency = "加密貨幣 (Crypto)", "USD"
        else: category, currency = "美股 (US)", "USD"
        return {"name": info['name'], "category": category, "currency": currency}
    
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
    
@st.cache_data
def get_currency_symbol(symbol):
    currency_code = get_company_info(symbol).get('currency', 'USD')
    if currency_code == 'TWD': return 'NT$'
    elif currency_code == 'USD': return '$'
    elif currency_code == 'HKD': return 'HK$'
    else: return currency_code + ' '

# 核心修正：技術指標計算 - 採用進階設定 (10, 50, 200 EMA & 9期 RSI/MACD/ATR/ADX)
def calculate_technical_indicators(df):
    
    # 策略固定參數 (MA/RSI/MACD 週期) - 雖然被指出有 Overfitting 風險，但作為用戶定義策略保留
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10) # 短線趨勢
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50) # 長線趨勢
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200) # 趨勢濾鏡 (MTA 長期錨點)
    
    # MACD (進階設定: 快線 8, 慢線 17, 信號線 9)
    macd_instance = ta.trend.MACD(df['Close'], window_fast=8, window_slow=17, window_sign=9)
    df['MACD_Line'] = macd_instance.macd()
    df['MACD_Signal'] = macd_instance.macd_signal()
    df['MACD'] = macd_instance.macd_diff() # MACD 柱狀圖
    
    # RSI (進階設定: 週期 9)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=9)
    
    # 經典布林通道 (20, 2)
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'], window=20, window_dev=2)
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'], window=20, window_dev=2)
    
    # ATR (進階設定: 週期 9) - 風險控制的基石 (Dynamic Risk Management)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=9)
    
    # ADX (進階設定: 週期 9) - 趨勢強度的濾鏡
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=9)
    
    # 增加 SMA 20 (用於回測基準)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20) 
    
    return df

# get_technical_data_df (維持不變 - 技術指標表格與判讀)
def get_technical_data_df(df):
    """獲取最新的技術指標數據和AI結論，並根據您的進階原則進行判讀。"""
    # 保持判讀函數不變，讓它作為對單一指標的解釋
    
    if df.empty or len(df) < 200: return pd.DataFrame()

    df_clean = df.dropna().copy()
    if df_clean.empty: return pd.DataFrame()

    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2] if len(df_clean) >= 2 else last_row 

    indicators = {}
    
    indicators['價格 vs. EMA 10/50/200'] = last_row['Close']
    indicators['RSI (9) 動能'] = last_row['RSI']
    indicators['MACD (8/17/9) 柱狀圖'] = last_row['MACD']
    indicators['ADX (9) 趨勢強度'] = last_row['ADX']
    indicators['ATR (9) 波動性'] = last_row['ATR']
    indicators['布林通道 (BB: 20/2)'] = last_row['Close']
    
    data = []
    
    for name, value in indicators.items():
        conclusion, color = "", "grey"
        
        if 'EMA 10/50/200' in name:
            ema_10 = last_row['EMA_10']
            ema_50 = last_row['EMA_50']
            ema_200 = last_row['EMA_200']

            # 採用進階的多頭排列判斷 (10 > 50 > 200)
            if ema_10 > ema_50 and ema_50 > ema_200:
                conclusion, color = f"**強多頭：MA 多頭排列** (10>50>200)", "red"
            elif ema_10 < ema_50 and ema_50 < ema_200:
                conclusion, color = f"**強空頭：MA 空頭排列** (10<50<200)", "green"
            elif last_row['Close'] > ema_50 and last_row['Close'] > ema_200:
                conclusion, color = f"中長線偏多：價格站上 EMA 50/200", "orange"
            else:
                conclusion, color = "中性：MA 糾結或趨勢發展中", "blue"
        
        elif 'RSI' in name:
            # 進階判斷: RSI > 50 多頭, < 50 空頭。70/30 為超買超賣
            if value > 70:
                conclusion, color = "警告：超買區域 (70)，潛在回調", "green" 
            elif value < 30:
                conclusion, color = "強化：超賣區域 (30)，潛在反彈", "red"
            elif value > 50:
                conclusion, color = "多頭：RSI > 50，位於強勢區間", "red"
            else:
                conclusion, color = "空頭：RSI < 50，位於弱勢區間", "green"


        elif 'MACD' in name:
            # 判斷 MACD 柱狀圖是否放大
            if value > 0 and value > prev_row['MACD']:
                conclusion, color = "強化：多頭動能增強 (紅柱放大)", "red"
            elif value < 0 and value < prev_row['MACD']:
                conclusion, color = "削弱：空頭動能增強 (綠柱放大)", "green"
            else:
                conclusion, color = "中性：動能盤整 (柱狀收縮)", "orange"
        
        elif 'ADX' in name:
             # ADX > 25 確認強趨勢
            if value >= 40:
                conclusion, color = "強趨勢：極強勢趨勢 (多或空)", "red"
            elif value >= 25:
                conclusion, color = "強趨勢：確認強勢趨勢 (ADX > 25)", "orange"
            else:
                conclusion, color = "盤整：弱勢或橫盤整理 (ADX < 25)", "blue"

        elif 'ATR' in name:
            avg_atr = df_clean['ATR'].iloc[-30:].mean() if len(df_clean) >= 30 else df_clean['ATR'].mean()
            if value > avg_atr * 1.5:
                conclusion, color = "警告：極高波動性 (1.5x 平均)", "green"
            elif value < avg_atr * 0.7:
                conclusion, color = "中性：低波動性 (醞釀突破)", "orange"
            else:
                conclusion, color = "中性：正常波動性", "blue"

        elif '布林通道' in name:
            high = last_row['BB_High']
            low = last_row['BB_Low']
            range_pct = (high - low) / last_row['Close'] * 100
            
            if value > high:
                conclusion, color = f"警告：價格位於上軌外側 (>{high:,.2f})", "red"
            elif value < low:
                conclusion, color = f"強化：價格位於下軌外側 (<{low:,.2f})", "green"
            else:
                conclusion, color = f"中性：在上下軌間 ({range_pct:.2f}% 寬度)", "blue"
        
        data.append([name, value, conclusion, color])

    technical_df = pd.DataFrame(data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    technical_df = technical_df.set_index('指標名稱')
    return technical_df

# run_backtest (保留並確認其為量化分析的重要組成部分)
def run_backtest(df, initial_capital=100000, commission_rate=0.001):
    """
    執行基於 SMA 20 / EMA 50 交叉的簡單回測。
    策略: 黃金交叉買入 (做多)，死亡交叉清倉 (賣出)。
    """
    
    if df.empty or len(df) < 51:
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "數據不足 (少於 51 週期) 或計算錯誤。"}

    data = df.copy()
    
    # 黃金/死亡交叉信號
    data['Prev_MA_State'] = (data['SMA_20'].shift(1) > data['EMA_50'].shift(1))
    data['Current_MA_State'] = (data['SMA_20'] > data['EMA_50'])
    data['Signal'] = np.where(
        (data['Current_MA_State'] == True) & (data['Prev_MA_State'] == False), 1, 0 # Buy
    )
    data['Signal'] = np.where(
        (data['Current_MA_State'] == False) & (data['Prev_MA_State'] == True), -1, data['Signal'] # Sell
    )
    
    data = data.dropna()
    if data.empty: return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "指標計算後數據不足。"}

    # --- 模擬交易邏輯 ---
    capital = [initial_capital]
    position = 0 
    buy_price = 0
    trades = []
    
    for i in range(1, len(data)):
        current_close = data['Close'].iloc[i]
        
        # 1. Buy Signal
        if data['Signal'].iloc[i] == 1 and position == 0:
            position = 1
            buy_price = current_close
            initial_capital -= initial_capital * commission_rate 
            
        # 2. Sell Signal
        elif data['Signal'].iloc[i] == -1 and position == 1:
            sell_price = current_close
            profit = (sell_price - buy_price) / buy_price 
            
            trades.append({ 'entry_date': data.index[i], 'exit_date': data.index[i], 'profit_pct': profit, 'is_win': profit > 0 })
            
            initial_capital *= (1 + profit)
            initial_capital -= initial_capital * commission_rate
            position = 0
            
        current_value = initial_capital
        if position == 1:
            current_value = initial_capital * (current_close / buy_price)
        
        capital.append(current_value)

    # 3. Handle open position
    if position == 1:
        sell_price = data['Close'].iloc[-1]
        profit = (sell_price - buy_price) / buy_price
        
        trades.append({ 'entry_date': data.index[-1], 'exit_date': data.index[-1], 'profit_pct': profit, 'is_win': profit > 0 })
        
        initial_capital *= (1 + profit)
        initial_capital -= initial_capital * commission_rate
        if capital: capital[-1] = initial_capital 

    # --- 計算回測結果 ---
    final_value = initial_capital
    total_return = ((final_value - 100000) / 100000) * 100
    total_trades = len(trades)
    win_rate = (sum(1 for t in trades if t['is_win']) / total_trades) * 100 if total_trades > 0 else 0
    
    capital_series = pd.Series(capital)
    max_value = capital_series.expanding(min_periods=1).max()
    drawdown = (capital_series - max_value) / max_value
    max_drawdown = abs(drawdown.min()) * 100
    
    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 2),
        "max_drawdown": round(max_drawdown, 2),
        "total_trades": total_trades,
        "message": f"回測區間 {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}。",
        "capital_curve": capital_series
    }

# calculate_fundamental_rating (修正：轉為計分模型，模擬相對對標)
def calculate_fundamental_rating(symbol):
    """
    修正：將基本面判斷標準轉為計分模型，模擬 Meta-Learner 的輸入，
    並將 ROE>15%、PE<15、現金流/負債健康度作為得分標準，而非絕對過濾器。
    """
    MAX_FA_SCORE = 10.0
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if symbol.startswith('^') or symbol.endswith('-USD'):
            return {
                "Combined_Rating": 0.0, 
                "Message": "不適用：指數或加密貨幣無標準基本面數據。",
                "Details": None
            }

        roe = info.get('returnOnEquity', 0) 
        trailingPE = info.get('trailingPE', 999) 
        freeCashFlow = info.get('freeCashflow', 0) 
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0) 
        
        fa_score = 0
        details = {}
        
        # 1. 成長與效率評分 (ROE - 權重 4/10)
        # ROE > 15% 為優秀標準
        if roe >= 0.15: 
            roe_score = 4.0
            details["ROE_Score"] = "優異 (ROE ≥ 15%)"
        elif roe >= 0.10: 
            roe_score = 3.0
            details["ROE_Score"] = "良好 (10% ≤ ROE < 15%)"
        else:
            roe_score = max(0, roe * 10) # 0.0 ~ 1.0 
            details["ROE_Score"] = "偏弱"
        fa_score += roe_score
        
        # 2. 估值評分 (PE - 權重 3/10)
        # PE < 15 為低估，但考慮行業失真，25 以下為合理區間
        if trailingPE > 0 and trailingPE <= 15: 
            pe_score = 3.0
            details["PE_Score"] = "低估 (P/E ≤ 15)"
        elif trailingPE > 15 and trailingPE <= 25: 
            pe_score = 2.0
            details["PE_Score"] = "合理 (15 < P/E ≤ 25)"
        elif trailingPE > 25 and trailingPE <= 40: 
            pe_score = 1.0
            details["PE_Score"] = "略高 (25 < P/E ≤ 40)"
        else:
            pe_score = 0.0
            details["PE_Score"] = "高估或無效"
        fa_score += pe_score
        
        # 3. 現金流與償債能力 (CF/Debt - 權重 3/10)
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt and totalDebt != 0 else 100 
        
        # FCF > 0 且 現金/債務 > 2 視為健康
        if freeCashFlow > 0 and cash_debt_ratio >= 2: 
            cf_score = 3.0
            details["CF_Score"] = "極健康 (FCF > 0, Cash/Debt ≥ 2)"
        elif freeCashFlow > 0 and cash_debt_ratio >= 1: 
            cf_score = 2.0
            details["CF_Score"] = "穩健 (FCF > 0, Cash/Debt ≥ 1)"
        else: 
            cf_score = 0.0
            details["CF_Score"] = "警示 (FCF 負或高負債)"
        fa_score += cf_score

        # 綜合評級 (總分 MAX_FA_SCORE)
        combined_rating = min(fa_score, MAX_FA_SCORE)
        
        # 評級解讀
        if combined_rating >= 8.0:
            message = "頂級優異 (強護城河)：基本面極健康，**ROE/估值/現金流**表現卓越，適合長期持有。"
        elif combined_rating >= 5.0:
            message = "良好穩健：財務結構穩固，但可能在估值或 ROE 方面有待加強。"
        else:
            message = "基本面較弱/警示：指標不佳或估值過高，需警惕風險。"
            
        return { 
            "Combined_Rating": combined_rating, 
            "Message": message, 
            "Details": details,
            "Max_Score": MAX_FA_SCORE 
        }

    except Exception as e:
        return { 
            "Combined_Rating": 0.0, 
            "Message": f"基本面數據獲取失敗或不適用。", 
            "Details": None,
            "Max_Score": MAX_FA_SCORE 
        }

# generate_expert_fusion_signal (重構：實作 Meta-Learner 集成與 ATR 動態風險控制)
def generate_expert_fusion_signal(df, fa_result, currency_symbol="$"):
    """
    重構：模擬 Meta-Learner 決策層，通過量化和權重集成六大因子，
    並實施 EMA 200 趨勢濾鏡和 ATR 動態風險控制。
    """
    
    df_clean = df.dropna().copy()
    if df_clean.empty or len(df_clean) < 2:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'factor_scores': {}, 'atr': 0}

    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    adx_value = last_row['ADX'] 
    
    # 初始化因子得分 (範圍 -5.0 到 +5.0)
    factor_scores = {
        'MA_趨勢': 0.0,
        '動能_RSI': 0.0,
        '動能_MACD': 0.0,
        '強度_ADX': 0.0,
        '形態_K線': 0.0,
        '基本面_FA': 0.0,
    }
    
    # ----------------------------------------------------
    # 1. 技術因子評分 (基學習器 Base Learners)
    # ----------------------------------------------------
    ema_10 = last_row['EMA_10']
    ema_50 = last_row['EMA_50']
    ema_200 = last_row['EMA_200']
    
    # A. MA 趨勢得分 (權重高，Max ±4.0)
    if ema_10 > ema_50:
        factor_scores['MA_趨勢'] += 2.0
    else:
        factor_scores['MA_趨勢'] -= 2.0
    
    # 黃金/死亡交叉 (額外獎懲)
    prev_10_above_50 = prev_row['EMA_10'] > prev_row['EMA_50']
    curr_10_above_50 = ema_10 > ema_50
    if not prev_10_above_50 and curr_10_above_50:
        factor_scores['MA_趨勢'] += 2.0 # 黃金交叉
    elif prev_10_above_50 and not curr_10_above_50:
        factor_scores['MA_趨勢'] -= 2.0 # 死亡交叉

    # B. RSI 動能得分 (Max ±3.0)
    rsi = last_row['RSI']
    if rsi > 55:
        factor_scores['動能_RSI'] += 1.5
    elif rsi < 45:
        factor_scores['動能_RSI'] -= 1.5
    
    if rsi > 70: factor_scores['動能_RSI'] -= 1.5 # 超買懲罰
    if rsi < 30: factor_scores['動能_RSI'] += 1.5 # 超賣獎勵
        
    # C. MACD 動能得分 (Max ±2.0)
    macd_diff = last_row['MACD']
    prev_macd_diff = prev_row['MACD']
    
    if macd_diff > 0: factor_scores['動能_MACD'] += 1.0
    else: factor_scores['動能_MACD'] -= 1.0

    if macd_diff > prev_macd_diff: factor_scores['動能_MACD'] += 1.0 # 動能增強
    elif macd_diff < prev_macd_diff: factor_scores['動能_MACD'] -= 1.0 # 動能減弱

    # D. ADX 強度濾鏡 (Max ±1.0)
    if adx_value > 30: factor_scores['強度_ADX'] += 1.0
    elif adx_value > 25: factor_scores['強度_ADX'] += 0.5
    else: factor_scores['強度_ADX'] -= 1.0 # 盤整/趨勢弱
    
    # E. K線形態得分 (Max ±1.0)
    is_up_bar = last_row['Close'] > last_row['Open']
    is_strong_up = is_up_bar and (last_row['Close'] - last_row['Open']) > atr_value * 0.7 
    is_strong_down = not is_up_bar and (last_row['Open'] - last_row['Close']) > atr_value * 0.7

    if is_strong_up: factor_scores['形態_K線'] = 1.0
    elif is_strong_down: factor_scores['形態_K線'] = -1.0
    
    # ----------------------------------------------------
    # 2. 基本面因子評分 (FA - 權重調整，Max ±5.0)
    # ----------------------------------------------------
    fa_rating = fa_result.get('Combined_Rating', 0.0)
    fa_max_score = fa_result.get('Max_Score', 10.0)
    
    # 歸一化 FA Score 至 -5.0 ~ +5.0
    if fa_max_score > 0:
        # (Score / Max Score) * 10 - 5.0
        factor_scores['基本面_FA'] = (fa_rating / fa_max_score) * 10.0 - 5.0
        
    # ----------------------------------------------------
    # 3. Meta-Learner 決策層 - 融合與 EMA 200 趨勢濾鏡
    # ----------------------------------------------------
    
    # 總分 (簡單加權集成)
    fusion_score = sum(factor_scores.values()) 
    
    # **🔥 EMA 200 長期趨勢濾鏡 (MTA 錨點) **
    # 只有當長期趨勢支持時，才強化短線信號
    is_long_trend_up = current_price > ema_200 and ema_50 > ema_200
    is_long_trend_down = current_price < ema_200 and ema_50 < ema_200
    
    if is_long_trend_up:
        # 長期趨勢向上，強化所有多頭信號 (Meta-Learner 權重調整)
        if fusion_score > 0: fusion_score *= 1.5
        # 長期趨勢向上，弱化空頭信號 (防止在牛市中做空)
        elif fusion_score < 0: fusion_score *= 0.5 
    elif is_long_trend_down:
        # 長期趨勢向下，強化所有空頭信號 
        if fusion_score < 0: fusion_score *= 1.5
        # 長期趨勢向下，弱化多頭信號 (防止在熊市中抄底)
        elif fusion_score > 0: fusion_score *= 0.5
        
    # 最終行動
    action = "觀望 (Neutral)"
    if fusion_score >= 8.0: action = "強烈買進 (Strong Buy)"
    elif fusion_score >= 4.0: action = "買進 (Buy)"
    elif fusion_score <= -8.0: action = "強烈賣出/做空 (Strong Sell/Short)"
    elif fusion_score <= -4.0: action = "賣出/清倉 (Sell/Clear)"
        
    # 信心指數
    MAX_SCORE = 20.0 # 假設最大總分約 20 (經濾鏡放大後)
    confidence = min(100, max(0, 50 + (fusion_score / MAX_SCORE) * 50))
    
    # ----------------------------------------------------
    # 4. ATR 動態風險控制與交易策略 (R:R 2:1 的原則)
    # ----------------------------------------------------
    risk_multiple = 2.5 # 使用 2.5 ATR 作為風險單位 (專業量化標準)
    reward_multiple = 2.0 # 追求 2:1 的回報風險比
    
    entry_buffer = atr_value * 0.2 # 允許 0.2 ATR 的緩衝/滑點

    if action.startswith("買進") or action.startswith("強烈買進"):
        entry = current_price # 直接按當前價位進場，但策略建議會給出緩衝區間
        stop_loss = entry - (atr_value * risk_multiple) # ATR 動態止損
        take_profit = entry + (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議進場價格區間 {currency_symbol}{entry - entry_buffer:.2f} ~ {currency_symbol}{entry + entry_buffer:.2f}，止損嚴格按 ATR 單位執行。"
    elif action.startswith("賣出") or action.startswith("強烈賣出"):
        entry = current_price
        stop_loss = entry + (atr_value * risk_multiple)
        take_profit = entry - (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議進場價格區間 {currency_symbol}{entry - entry_buffer:.2f} ~ {currency_symbol}{entry + entry_buffer:.2f}，止損嚴格按 ATR 單位執行。"
    else:
        entry = current_price
        stop_loss = current_price - atr_value
        take_profit = current_price + atr_value
        strategy_desc = "市場信號混亂或趨勢不夠強勁，建議等待趨勢明朗或在 ATR 範圍內觀望。"

    return {
        'action': action,
        'score': round(fusion_score, 2),
        'confidence': round(confidence, 0),
        'strategy': strategy_desc,
        'entry_price': entry,
        'take_profit': take_profit,
        'stop_loss': stop_loss,
        'current_price': current_price,
        'factor_scores': factor_scores, # **新增 XAI 因子分數**
        'atr': atr_value
    }

# create_comprehensive_chart (維持不變 - 綜合圖表繪製)
def create_comprehensive_chart(df, symbol, period_key):
    df_clean = df.dropna().copy()
    if df_clean.empty: return go.Figure().update_layout(title="數據不足，無法繪製圖表")

    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.08,
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=(f"{symbol} 價格走勢 (週期: {period_key})", "MACD 指標", "RSI/ADX 指標"))

    # 1. 主圖：K線與均線 (EMA 10, 50, 200)
    fig.add_trace(go.Candlestick(x=df_clean.index, open=df_clean['Open'], high=df_clean['High'], low=df_clean['Low'], close=df_clean['Close'], name='K線', increasing_line_color='#cc0000', decreasing_line_color='#1e8449'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['EMA_10'], line=dict(color='#ffab40', width=1), name='EMA 10'), row=1, col=1) 
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['EMA_50'], line=dict(color='#0077b6', width=1.5), name='EMA 50'), row=1, col=1) 
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['EMA_200'], line=dict(color='#800080', width=1.5, dash='dash'), name='EMA 200'), row=1, col=1) 
    
    # 2. MACD 圖 (MACD Line 和 Signal Line)
    colors = np.where(df_clean['MACD'] > 0, '#cc0000', '#1e8449') 
    fig.add_trace(go.Bar(x=df_clean.index, y=df_clean['MACD'], name='MACD 柱狀圖', marker_color=colors, opacity=0.5), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['MACD_Line'], line=dict(color='#0077b6', width=1), name='DIF'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['MACD_Signal'], line=dict(color='#ffab40', width=1), name='DEA'), row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)

    # 3. RSI 圖 (包含 ADX)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1, annotation_text="超買 (70)", annotation_position="top right")
    fig.add_hline(y=50, line_dash="dash", line_color="grey", row=3, col=1, annotation_text="多/空分界 (50)", annotation_position="top left")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1, annotation_text="超賣 (30)", annotation_position="bottom right")
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    
    # ADX - 使用第二個 Y 軸 (右側)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['ADX'], line=dict(color='#cc6600', width=1.5, dash='dot'), name='ADX', yaxis='y4'), row=3, col=1)
    fig.update_layout(yaxis4=dict(title="ADX", overlaying='y3', side='right', range=[0, 100], showgrid=False))
    fig.add_hline(y=25, line_dash="dot", line_color="#cc6600", row=3, col=1, annotation_text="強勢趨勢 (ADX 25)", annotation_position="bottom left", yref='y4')

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

# Streamlit 側邊欄函數 (維持不變)
def update_search_input():
    if st.session_state.symbol_select_box and st.session_state.symbol_select_box != "請選擇標的...":
        code = st.session_state.symbol_select_box.split(' - ')[0]
        st.session_state.sidebar_search_input = code
        if st.session_state.get('last_search_symbol') != code:
            st.session_state.last_search_symbol = code
            st.session_state.analyze_trigger = True


# ==============================================================================
# 3. Streamlit 主邏輯 (Main Function)
# ==============================================================================

def main():
    
    # === 新增自定義 CSS 來實現透明按鍵和淡橙色文字 (玻璃按鍵效果) ===
    st.markdown("""
        <style>
        /* 1. 側邊欄的主要分析按鈕 - 核心玻璃化設置 (淡橙色：#ffab40) */
        [data-testid="stSidebar"] .stButton button {
            color: #ffab40 !important; /* 淡橙色文字 */
            background-color: rgba(255, 255, 255, 0.1) !important; /* 透明背景 */
            border-color: #ffab40 !important; /* 淡橙色邊框 */
            border-width: 1px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); 
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        /* 2. 懸停 (Hover) 效果 */
        [data-testid="stSidebar"] .stButton button:hover {
            color: #cc6600 !important; 
            background-color: rgba(255, 171, 64, 0.15) !important; 
            border-color: #cc6600 !important;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15); 
        }
        /* 3. 點擊 (Active/Focus) 效果 */
        [data-testid="stSidebar"] .stButton button:active,
        [data-testid="stSidebar"] .stButton button:focus {
            color: #ff9933 !important;
            background-color: rgba(255, 171, 64, 0.25) !important;
            border-color: #ff9933 !important;
            box-shadow: none !important; 
        }
        /* 4. 修正主標題顏色 */
        h1 { color: #cc6600; } 
        
        /* 5. 因子分解表格標題顏色 (XAI/Transparency) */
        .factor-score-table th { background-color: rgba(204, 102, 0, 0.3) !important; }
        .factor-score-positive { color: #cc0000; font-weight: bold; }
        .factor-score-negative { color: #1e8449; font-weight: bold; }
        .factor-score-neutral { color: #cc6600; }
        </style>
        """, unsafe_allow_html=True)


    # --- 0. 側邊欄選擇器 (Category Selectbox) ---
    category_keys = list(CATEGORY_MAP.keys())
    
    st.sidebar.markdown("1. 選擇資產類別")
    selected_category_key = st.sidebar.selectbox(
        "選擇資產類別", 
        category_keys, 
        index=category_keys.index("台股 (TW) - 個股/ETF/指數"), # 預設選中台股
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("2. 快速選擇標的")
    
    current_category_options_display = list(CATEGORY_HOT_OPTIONS.get(selected_category_key, {}).keys())
    
    current_symbol_code = st.session_state.get('last_search_symbol', "2330.TW")
    default_symbol_index = 0
    
    try:
        current_display_name = f"{current_symbol_code} - {FULL_SYMBOLS_MAP[current_symbol_code]['name']}"
        if current_display_name in current_category_options_display:
            default_symbol_index = current_category_options_display.index(current_display_name)
    except:
        pass

    st.sidebar.selectbox(
        f"選擇 {selected_category_key} 標的",
        current_category_options_display,
        index=default_symbol_index,
        key="symbol_select_box",
        on_change=update_search_input,
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    # --- 3. 輸入股票代碼或中文名稱 (Text Input) ---
    st.sidebar.markdown("3. 🔍 **輸入股票代碼或中文名稱**")

    text_input_current_value = st.session_state.get('sidebar_search_input', st.session_state.get('last_search_symbol', "2330.TW"))

    selected_query = st.sidebar.text_input(
        "🔍 輸入股票代碼或中文名稱", 
        placeholder="例如：AAPL, 台積電, 廣達, BTC-USD", 
        value=text_input_current_value,
        key="sidebar_search_input",
        label_visibility="collapsed"
    )

    final_symbol_to_analyze = get_symbol_from_query(selected_query)

    is_symbol_changed = final_symbol_to_analyze != st.session_state.get('last_search_symbol', "INIT")

    if is_symbol_changed:
        if final_symbol_to_analyze and final_symbol_to_analyze != "---": 
            st.session_state['analyze_trigger'] = True
            st.session_state['last_search_symbol'] = final_symbol_to_analyze
            st.session_state['data_ready'] = False


    st.sidebar.markdown("---")

    # --- 4. 選擇週期 (Period Selectbox) ---
    st.sidebar.markdown("4. **選擇週期**")

    period_keys = list(PERIOD_MAP.keys())
    selected_period_key = st.sidebar.selectbox("分析時間週期", period_keys, index=period_keys.index("1 日 (中長線)")) 

    selected_period_value = PERIOD_MAP[selected_period_key]

    yf_period, yf_interval = selected_period_value

    st.sidebar.markdown("---")

    # --- 5. 開始分析 (Button) ---
    st.sidebar.markdown("5. **開始分析**")
    
    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", key="main_analyze_button") 

    # === 主要分析邏輯 (Main Analysis Logic) ===
    if analyze_button_clicked or st.session_state.get('analyze_trigger', False):
        
        st.session_state['data_ready'] = False
        st.session_state['analyze_trigger'] = False 
        
        try:
            with st.spinner(f"🔍 正在啟動AI模型，獲取並分析 **{final_symbol_to_analyze}** 的數據 ({selected_period_key})..."):
                
                df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval) 
                
                if df.empty or len(df) < 200: 
                    display_symbol = final_symbol_to_analyze
                    
                    st.error(f"❌ **數據不足或代碼無效。** 請確認代碼 **{display_symbol}** 是否正確。")
                    st.info(f"💡 **提醒：** 台灣股票需要以 **代碼.TW** 格式輸入 (例如：**2330.TW**)。")
                    st.session_state['data_ready'] = False 
                else:
                    company_info = get_company_info(final_symbol_to_analyze) 
                    currency_symbol = get_currency_symbol(final_symbol_to_analyze) 
                    
                    df = calculate_technical_indicators(df) 
                    fa_result = calculate_fundamental_rating(final_symbol_to_analyze)
                    
                    # 使用新的 Meta-Learner 集成函數
                    analysis = generate_expert_fusion_signal(
                        df, 
                        fa_result=fa_result, 
                        currency_symbol=currency_symbol 
                    )
                    
                    st.session_state['analysis_results'] = {
                        'df': df,
                        'company_info': company_info,
                        'currency_symbol': currency_symbol,
                        'fa_result': fa_result,
                        'analysis': analysis,
                        'selected_period_key': selected_period_key,
                        'final_symbol_to_analyze': final_symbol_to_analyze
                    }
                    
                    st.session_state['data_ready'] = True

        except Exception as e:
            st.error(f"❌ 分析 {final_symbol_to_analyze} 時發生未預期的錯誤: {str(e)}")
            st.info("💡 請檢查代碼格式或嘗試其他分析週期。")
            st.session_state['data_ready'] = False 

    # === 結果呈現區塊 ===
    if st.session_state.get('data_ready', False):
        
        results = st.session_state['analysis_results']
        df = results['df'].dropna() 
        company_info = results['company_info']
        currency_symbol = results['currency_symbol']
        fa_result = results['fa_result']
        analysis = results['analysis']
        selected_period_key = results['selected_period_key']
        final_symbol_to_analyze = results['final_symbol_to_analyze']
        
        st.header(f"📈 **{company_info['name']}** ({final_symbol_to_analyze}) AI集成趨勢分析")
        
        current_price = analysis['current_price']
        prev_close = df['Close'].iloc[-2] if len(df) >= 2 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        price_delta_color = 'inverse' if change < 0 else 'normal'

        st.markdown(f"**分析週期:** **{selected_period_key}** | **FA 評級:** **{fa_result['Combined_Rating']:.2f}/{fa_result['Max_Score']:.1f}**")
        st.markdown(f"**基本面診斷:** {fa_result['Message']}")
        st.markdown("---")
        
        st.subheader("💡 核心行動與量化評分 (Meta-Learner 決策)")
        
        st.markdown(
            """
            <style>
            [data-testid="stMetricValue"] { font-size: 20px; }
            [data-testid="stMetricLabel"] { font-size: 13px; }
            [data-testid="stMetricDelta"] { font-size: 12px; }
            .action-buy { color: #cc0000; font-weight: bold; }
            .action-sell { color: #1e8449; font-weight: bold; }
            .action-neutral { color: #cc6600; font-weight: bold; }
            </style>
            """, unsafe_allow_html=True
        )
        
        col_core_1, col_core_2, col_core_3, col_core_4 = st.columns(4)
        
        with col_core_1: 
            st.metric("💰 當前價格", f"{currency_symbol}{current_price:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)", delta_color=price_delta_color)
        
        with col_core_2: 
            st.markdown("**🎯 最終行動建議**")
            action_class = "action-buy" if "買進" in analysis['action'] else ("action-sell" if "賣出" in analysis['action'] else "action-neutral")
            st.markdown(f"<p class='{action_class}' style='font-size: 20px;'>{analysis['action']}</p>", unsafe_allow_html=True)
        
        with col_core_3: 
            st.metric("🔥 總量化評分", f"{analysis['score']}", help="多因子集成後的總得分 (正數看漲)")
        with col_core_4: 
            st.metric("🛡️ 決策信心指數", f"{analysis['confidence']:.0f}%", help="AI對此集成決策的信心度")
        
        st.markdown("---")
        
        # 🔥 XAI - 因子得分分解 (Factor Decomposition)
        st.subheader("🔎 AI決策可解釋性：多因子得分分解 (XAI)")
        
        # 準備因子分解表格
        factor_df = pd.DataFrame(analysis['factor_scores'].items(), columns=['因子名稱', '得分 (-5.0 ~ +5.0)'])
        
        fa_details_str = ""
        if fa_result['Details']:
            fa_details_str = f"({fa_result['Details'].get('ROE_Score', '')}, {fa_result['Details'].get('PE_Score', '')}, {fa_result['Details'].get('CF_Score', '')})"

        factor_df.loc[factor_df['因子名稱'] == '基本面_FA', '說明'] = f"基本面健康度得分 {fa_details_str}"
        factor_df.loc[factor_df['因子名稱'] == 'MA_趨勢', '說明'] = "短期/長期均線交叉與排列 (包含 EMA 200 濾鏡影響)"
        factor_df.loc[factor_df['因子名稱'] == '動能_RSI', '說明'] = "相對強弱指數 (RSI 9) 動能"
        factor_df.loc[factor_df['因子名稱'] == '動能_MACD', '說明'] = "異同移動平均線 (MACD) 柱狀圖變化"
        factor_df.loc[factor_df['因子名稱'] == '強度_ADX', '說明'] = "趨勢強度指標 (ADX 9) 判斷盤整或強趨勢"
        factor_df.loc[factor_df['因子名稱'] == '形態_K線', '說明'] = "當前 K 線實體強度"
        
        def style_factor_score(s):
            is_positive = s['得分 (-5.0 ~ +5.0)'] > 1.0
            is_negative = s['得分 (-5.0 ~ +5.0)'] < -1.0
            is_neutral = (s['得分 (-5.0 ~ +5.0)'] >= -1.0) & (s['得分 (-5.0 ~ +5.0)'] <= 1.0)
            
            colors = np.select(
                [is_positive, is_negative, is_neutral],
                ['color: #cc0000; font-weight: bold;', 'color: #1e8449; font-weight: bold;', 'color: #cc6600;'],
                default='color: #888888;'
            )
            return [f'{c}' for c in colors]

        styled_factor_df = factor_df[['因子名稱', '得分 (-5.0 ~ +5.0)', '說明']].style.apply(
            lambda x: style_factor_score(x), axis=1, subset=['得分 (-5.0 ~ +5.0)']
        ).format({'得分 (-5.0 ~ +5.0)': '{:.2f}'})

        st.dataframe(
            styled_factor_df,
            use_container_width=True,
            column_config={
                "因子名稱": "決策因子",
                "得分 (-5.0 ~ +5.0)": "量化支持度",
                "說明": "因子解讀",
            }
        )
        st.caption("ℹ️ **因子分解說明:** 得分為 Meta-Learner 決策層對各因子的量化權衡結果。**正數**表示支持買入，**負數**表示支持賣出/觀望。最終行動由所有因子積分集成後決定。")

        st.markdown("---")

        st.subheader("🛡️ 動態風險控制與精確交易策略")
        col_strat_1, col_strat_2, col_strat_3, col_strat_4 = st.columns(4)

        risk = abs(analysis['entry_price'] - analysis['stop_loss'])
        reward = abs(analysis['take_profit'] - analysis['entry_price'])
        risk_reward = reward / risk if risk > 0 else float('inf')

        with col_strat_1:
            st.markdown(f"**建議操作:** <span class='{action_class}' style='font-size: 18px;'>**{analysis['action']}**</span>", unsafe_allow_html=True)
        with col_strat_2:
            st.markdown(f"**建議進場價:** <span style='color:#cc6600;'>**{currency_symbol}{analysis['entry_price']:.2f}**</span>", unsafe_allow_html=True)
        with col_strat_3:
            st.markdown(f"**🚀 止盈價 (TP):** <span style='color:red;'>**{currency_symbol}{analysis['take_profit']:.2f}**</span>", unsafe_allow_html=True)
        with col_strat_4:
            st.markdown(f"**🛑 止損價 (SL):** <span style='color:green;'>**{currency_symbol}{analysis['stop_loss']:.2f}**</span>", unsafe_allow_html=True)
            
        st.info(f"**💡 策略總結:** **{analysis['strategy']}** | **⚖️ 風險/回報比 (R:R):** **{risk_reward:.2f}** (目標 2:1) | **波動單位 (ATR):** {analysis.get('atr', 0):.4f}。**止損點為動態 ATR 止損。**")
        
        st.markdown("---")
        
        st.subheader("🧪 策略回測報告 (SMA 20/EMA 50 交叉)")
        
        # 執行回測
        backtest_results = run_backtest(df.copy())
        
        # 顯示回測結果
        if backtest_results.get("total_trades", 0) > 0:
            
            col_bt_1, col_bt_2, col_bt_3, col_bt_4 = st.columns(4)
            
            with col_bt_1: 
                st.metric("📊 總回報率", f"{backtest_results['total_return']}%", 
                          delta_color='inverse' if backtest_results['total_return'] < 0 else 'normal',
                          delta=backtest_results['message'])

            with col_bt_2: 
                st.metric("📈 勝率", f"{backtest_results['win_rate']}%")

            with col_bt_3: 
                st.metric("📉 最大回撤 (MDD)", f"{backtest_results['max_drawdown']}%", delta_color='inverse')

            with col_bt_4:
                st.metric("🤝 交易總次數", f"{backtest_results['total_trades']} 次")
                
            # 資金曲線圖
            if 'capital_curve' in backtest_results:
                fig_bt = go.Figure()
                fig_bt.add_trace(go.Scatter(x=df.index.to_list(), y=backtest_results['capital_curve'], name='策略資金曲線', line=dict(color='#cc6600', width=2)))
                fig_bt.add_hline(y=100000, line_dash="dash", line_color="#1e8449", annotation_text="起始資金 $100,000", annotation_position="bottom right")
                
                fig_bt.update_layout(
                    title='SMA 20/EMA 50 交叉策略資金曲線 (回測魯棒性指標)',
                    xaxis_title='交易週期',
                    yaxis_title='賬戶價值 ($)',
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300
                )
                st.plotly_chart(fig_bt, use_container_width=True)
                
            st.caption("ℹ️ **策略說明:** 此回測作為策略**魯棒性 (Robustness)** 的基礎驗證，顯示了**最大回撤 (MDD)** 和總回報率。實盤策略應追求高夏普比率和低 MDD。")
        else:
            st.info(f"回測無法執行或無交易信號：{backtest_results.get('message', '數據不足或發生錯誤。')}")

        st.markdown("---")
        
        st.subheader("🛠️ 單一技術指標狀態表 (基礎判讀)")
        
        technical_df = get_technical_data_df(df)
        
        if not technical_df.empty:
            def style_indicator(s):
                df_color = technical_df['顏色']
                color_map = {'red': 'color: #cc0000; font-weight: bold;', 
                             'green': 'color: #1e8449; font-weight: bold;', 
                             'orange': 'color: #cc6600;',
                             'blue': 'color: #004d99;',
                             'grey': 'color: #888888;'}
                
                return [color_map.get(df_color.loc[index], '') for index in s.index]
                
            styled_df = technical_df[['最新值', '分析結論']].style.apply(style_indicator, subset=['最新值', '分析結論'], axis=0)

            st.dataframe(
                styled_df, 
                use_container_width=True,
                key=f"technical_df_{final_symbol_to_analyze}_{selected_period_key}",
                column_config={
                    "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                    "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的專業解讀"),
                }
            )
            st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化。這些判讀是 **Meta-Learner** 決策層的基礎輸入。")

        else:
            st.info("無足夠數據生成關鍵技術指標表格。")
        
        st.markdown("---")
        
        st.subheader(f"📊 完整技術分析圖表")
        chart = create_comprehensive_chart(df, final_symbol_to_analyze, selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

    # === 修正部分：未分析時的預設首頁顯示 (依照您的需求進行了修改) ===
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          st.markdown(
              """
              <h1 style='color: #cc6600; font-size: 32px; font-weight: bold;'>🚀 歡迎使用 AI 趨勢分析</h1>
              """, 
              unsafe_allow_html=True
          )
          
          st.info(f"請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 <span style='color: #cc6600; font-weight: bold;'>『📊 執行AI分析』</span> 按鈕開始。", unsafe_allow_html=True)
          
          st.markdown("---")
          
          st.subheader("📝 使用步驟：")
          st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
          st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
          st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分 (短期)`、`1 日 (中長線)`）。")
          st.markdown(f"4. **執行分析**：點擊 <span style='color: #cc6600; font-weight: bold;'>『📊 執行AI分析』</span>，AI將融合基本面與技術面指標提供交易策略。", unsafe_allow_html=True)
          
          st.markdown("---")
          st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
          st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")


if __name__ == '__main__':
    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'sidebar_search_input' not in st.session_state:
        st.session_state['sidebar_search_input'] = "2330.TW"
    if 'analyze_trigger' not in st.session_state:
        st.session_state['analyze_trigger'] = False
        
    main()
    
    st.markdown("---")
    # 底部免責聲明保持簡潔，與上方保持一致
    st.markdown("⚠️ **免責聲明 (風險揭示強化):** 本分析模型是基於**量化集成學習 (Ensemble)** 和 **ATR 動態風險控制** 的專業架構。但其性能仍受限於固定參數的**過度擬合風險** 和市場的固有不穩定性。分析結果**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")
