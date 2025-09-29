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

# 🚀 您的【所有資產清單】(FULL_SYMBOLS_MAP)
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

# 建立第二層選擇器映射
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

def get_symbol_from_query(query: str) -> str:
    """ 🎯 代碼解析函數：同時檢查 FULL_SYMBOLS_MAP """
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

# 核心技術指標計算
def calculate_technical_indicators(df):
    
    # 進階移動平均線 (MA)
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10) # 短線趨勢
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50) # 長線趨勢
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200) # 濾鏡
    
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
    
    # ATR (進階設定: 週期 9) - 風險控制的基石
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=9)
    
    # ADX (進階設定: 週期 9) - 趨勢強度的濾鏡
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=9)
    
    # 增加 SMA 20 (用於回測基準)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20) 
    
    return df

# get_technical_data_df (技術指標表格與判讀)
def get_technical_data_df(df):
    """獲取最新的技術指標數據和AI結論，並根據您的進階原則進行判讀。"""
    
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

# run_backtest (回測功能)
@st.cache_data(ttl=3600)
def run_backtest(df, initial_capital=100000, commission_rate=0.001):
    """
    執行基於 SMA 20 / EMA 50 交叉的簡單回測。
    策略: 黃金交叉買入 (做多)，死亡交叉清倉 (賣出)。
    """
    
    if df.empty or len(df) < 51:
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "數據不足 (少於 51 週期) 或計算錯誤。", "capital_curve": pd.Series([initial_capital], index=[datetime.now()])}

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
    if data.empty: return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "指標計算後數據不足。", "capital_curve": pd.Series([initial_capital], index=[datetime.now()])}

    # --- 模擬交易邏輯 ---
    capital = [initial_capital]
    position = 0 
    buy_price = 0
    trades = []
    
    current_capital = initial_capital
    
    for i in range(1, len(data)):
        current_close = data['Close'].iloc[i]
        
        # 1. Buy Signal
        if data['Signal'].iloc[i] == 1 and position == 0:
            position = 1
            buy_price = current_close
            current_capital -= current_capital * commission_rate 
            
        # 2. Sell Signal
        elif data['Signal'].iloc[i] == -1 and position == 1:
            sell_price = current_close
            profit = (sell_price - buy_price) / buy_price 
            
            trades.append({ 'entry_date': data.index[i], 'exit_date': data.index[i], 'profit_pct': profit, 'is_win': profit > 0 })
            
            current_capital *= (1 + profit)
            current_capital -= current_capital * commission_rate
            position = 0
            
        current_value = current_capital
        if position == 1:
            current_value = current_capital * (current_close / buy_price)
        
        capital.append(current_value)

    # 3. Handle open position
    if position == 1:
        sell_price = data['Close'].iloc[-1]
        profit = (sell_price - buy_price) / buy_price
        
        trades.append({ 'entry_date': data.index[-1], 'exit_date': data.index[-1], 'profit_pct': profit, 'is_win': profit > 0 })
        
        current_capital *= (1 + profit)
        current_capital -= current_capital * commission_rate
        if capital: capital[-1] = current_capital 

    # --- 計算回測結果 ---
    total_return = ((current_capital - initial_capital) / initial_capital) * 100
    total_trades = len(trades)
    win_rate = (sum(1 for t in trades if t['is_win']) / total_trades) * 100 if total_trades > 0 else 0
    
    capital_series = pd.Series(capital, index=data.index[:len(capital)])
    
    if capital_series.empty: capital_series = pd.Series([initial_capital], index=[datetime.now()])

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

# calculate_fundamental_rating (基本面評級)
@st.cache_data(ttl=3600)
def calculate_fundamental_rating(symbol):
    """
    融合了 '基本面的判斷標準'，特別是 ROE > 15%、PE 估值、以及現金流/負債健康度。
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 排除指數和加密貨幣
        if symbol.startswith('^') or symbol.endswith('-USD'):
            return {
                "Combined_Rating": 0.0,
                "Message": "不適用：指數或加密貨幣無標準基本面數據。",
                "Details": None
            }
        
        # 使用 info.get 安全獲取數據
        roe = info.get('returnOnEquity', 0)
        trailingPE = info.get('trailingPE', 99)
        freeCashFlow = info.get('freeCashflow', 0)
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0)
        
        # 1. 成長與效率評分 (ROE) (總分 3)
        roe_score = 0
        if roe > 0.15: roe_score = 3 
        elif roe > 0.10: roe_score = 2
        elif roe > 0: roe_score = 1
        
        # 2. 估值評分 (PE) (總分 3)
        pe_score = 0
        if trailingPE < 15 and trailingPE > 0: pe_score = 3 
        elif trailingPE < 25 and trailingPE > 0: pe_score = 2 
        elif trailingPE < 35 and trailingPE > 0: pe_score = 1 
        
        # 3. 現金流與償債能力 (總分 3)
        cf_score = 0
        # 避免除以零
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt and totalDebt != 0 else 100 
        
        if freeCashFlow > 0 and cash_debt_ratio > 2:
            cf_score = 3
        elif freeCashFlow > 0 and cash_debt_ratio > 1:
            cf_score = 2
        elif freeCashFlow > 0:
            cf_score = 1
            
        # 綜合評級 (總分 9)
        combined_rating = roe_score + pe_score + cf_score
        
        # 評級解讀
        if combined_rating >= 7:
            message = "頂級優異 (強護城河)：基本面極健康，**ROE > 15%**，成長與估值俱佳，適合長期持有。"
        elif combined_rating >= 5:
            message = "良好穩健：財務結構穩固，但可能在估值或 ROE 方面有待加強。"
        elif combined_rating >= 3:
            message = "中性警示：存在財務壓力或估值過高，需警惕風險（如現金流為負）。"
        else:
            message = "基本面較弱：財務指標不佳或數據缺失，不建議盲目進場。"
            
        return {
            "Combined_Rating": combined_rating,
            "Message": message,
            "Details": info
        }
    except Exception as e:
        return {
            "Combined_Rating": 1.0,
            "Message": f"基本面數據獲取失敗或不適用 (代碼可能錯誤或數據缺失)。",
            "Details": None
        }

# ==============================================================================
# 3. 繪圖函式 (新加入)
# ==============================================================================

def plot_candlestick_and_indicators(df, symbol):
    """繪製K線圖、EMA均線和交易量。"""
    
    # 創建子圖：K線/均線 (row 1) + MACD (row 2) + Volume (row 3)
    fig = make_subplots(
        rows=3, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2]
    )

    # --- 1. K線圖與EMA ---
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線',
        showlegend=False,
        increasing_line_color='#FF5733', # 紅色
        decreasing_line_color='#00CC99'  # 綠色
    ), row=1, col=1)

    # 均線
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_10'], name='EMA 10', line=dict(color='yellow', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], name='EMA 50', line=dict(color='blue', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], name='EMA 200', line=dict(color='purple', width=1, dash='dash')), row=1, col=1)

    # 布林通道
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], name='BB High', line=dict(color='grey', width=1, dash='dot'), opacity=0.5), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], name='BB Low', line=dict(color='grey', width=1, dash='dot'), opacity=0.5, fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)'), row=1, col=1)


    # --- 2. MACD 柱狀圖 ---
    colors = ['#FF5733' if val >= 0 else '#00CC99' for val in df['MACD']]
    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['MACD'], 
        name='MACD Hist', 
        marker_color=colors, 
        showlegend=False
    ), row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], name='MACD Line', line=dict(color='red', width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='MACD Signal', line=dict(color='blue', width=1)), row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)


    # --- 3. 交易量 ---
    colors_vol = ['#FF5733' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#00CC99' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['Volume'], 
        name='成交量', 
        marker_color=colors_vol, 
        showlegend=False
    ), row=3, col=1)
    fig.update_yaxes(title_text="成交量", row=3, col=1)

    # --- 佈局設定 ---
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=700,
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified",
        title_text=f"{symbol} K線圖與技術指標",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, row=1, col=1)
    
    return fig


# ==============================================================================
# 4. 融合信號與策略函式 (已修正效率問題)
# ==============================================================================

def generate_expert_fusion_signal(df, fa_rating, fa_message, is_long_term=True, currency_symbol="$"):
    """
    融合了精確的技術分析標準 (MA 排列、RSI 50 中軸、MACD 動能、ADX 濾鏡) 
    並納入了 ATR 風險控制 (TP/SL) 和 R:R 2:1 的原則。
    """
    df_clean = df.dropna().copy()
    if df_clean.empty or len(df_clean) < 2:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'expert_opinions': {}, 'atr': 0, 'factor_df': pd.DataFrame(), 'backtest_curve': pd.Series()}

    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    adx_value = last_row['ADX']
    expert_opinions = {}
    
    # 🎯 效率修正：提前運行回測
    backtest_result = run_backtest(df)
    total_return = backtest_result['total_return']


    # 1. 均線交叉與排列專家 (MA Cross & Alignment)
    ma_score = 0
    ema_10 = last_row['EMA_10']
    ema_50 = last_row['EMA_50']
    ema_200 = last_row['EMA_200']
    
    prev_10_above_50 = prev_row['EMA_10'] > prev_row['EMA_50']
    curr_10_above_50 = ema_10 > ema_50
    
    # 強多頭排列 (10 > 50 > 200)
    if ema_10 > ema_50 and ema_50 > ema_200:
        ma_score = 4.0
        expert_opinions['趨勢分析 (MA 排列)'] = "**🚀 強多頭排列** (10>50>200)，長期趨勢強勁！"
    # 強空頭排列 (10 < 50 < 200)
    elif ema_10 < ema_50 and ema_50 < ema_200:
        ma_score = -4.0
        expert_opinions['趨勢分析 (MA 排列)'] = "**📉 強空頭排列** (10<50<200)，長期趨勢向下！"
    # 黃金交叉
    elif not prev_10_above_50 and curr_10_above_50:
        ma_score = 3.5
        expert_opinions['趨勢分析 (MA 交叉)'] = "**🚀 黃金交叉 (GC)**：EMA 10 向上穿越 EMA 50，強勁看漲信號！"
    # 死亡交叉
    elif prev_10_above_50 and not curr_10_above_50:
        ma_score = -3.5
        expert_opinions['趨勢分析 (MA 交叉)'] = "**📉 死亡交叉 (DC)**：EMA 10 向下穿越 EMA 50，強勁看跌信號！"
    elif curr_10_above_50 and last_row['Close'] > ema_200:
        ma_score = 2.0
        expert_opinions['趨勢分析 (MA)'] = "中長線偏多：短期均線向上，價格位於 EMA 200 之上。"
    else:
        ma_score = 0.5 if last_row['Close'] > ema_50 else -0.5
        expert_opinions['趨勢分析 (MA)'] = "中性：均線糾結或趨勢不明。"

    # 2. 動能專家 (RSI / MACD)
    momentum_score = 0
    rsi = last_row['RSI']
    macd_hist = last_row['MACD'] # MACD 柱狀圖

    # RSI 判斷
    if rsi > 70:
        momentum_score -= 1.0
        expert_opinions['動能分析 (RSI)'] = "警告：RSI 超買 (>70)，潛在回調壓力。"
    elif rsi < 30:
        momentum_score += 1.0
        expert_opinions['動能分析 (RSI)'] = "強化：RSI 超賣 (<30)，潛在反彈動能。"
    elif rsi > 50:
        momentum_score += 1.5
        expert_opinions['動能分析 (RSI)'] = "多頭動能：RSI 位於強勢區間 (>50)。"
    else:
        momentum_score -= 1.5
        expert_opinions['動能分析 (RSI)'] = "空頭動能：RSI 位於弱勢區間 (<50)。"

    # MACD 判斷
    if macd_hist > 0 and macd_hist > prev_row['MACD']:
        momentum_score += 2.0
        expert_opinions['動能分析 (MACD)'] = "強化：MACD 紅柱放大，多頭動能加速！"
    elif macd_hist < 0 and macd_hist < prev_row['MACD']:
        momentum_score -= 2.0
        expert_opinions['動能分析 (MACD)'] = "削弱：MACD 綠柱放大，空頭動能加速！"
    elif macd_hist * prev_row['MACD'] < 0:
        momentum_score += 0.5 if macd_hist > 0 else -0.5
        expert_opinions['動能分析 (MACD)'] = "中性：MACD 穿越零軸附近。"
    
    # 3. 趨勢強度專家 (ADX)
    adx_score = 0
    if adx_value >= 40:
        adx_score = 2.0 # 極強趨勢
        expert_opinions['趨勢強度 (ADX)'] = "**極強趨勢** (ADX > 40)，多空方向明確，趨勢延續性高。"
    elif adx_value >= 25:
        adx_score = 1.0 # 確認趨勢
        expert_opinions['趨勢強度 (ADX)'] = "強趨勢：趨勢已確認 (ADX > 25)。"
    else:
        adx_score = 0.0 # 盤整
        expert_opinions['趨勢強度 (ADX)'] = "盤整：趨勢強度不足 (ADX < 25)，橫盤整理中。"
        
    # 4. 基本面因子
    fa_score = fa_rating / 3.0 # 將 0-9 轉換為 0-3 分
    expert_opinions['基本面評級 (FA)'] = f"基本面分數：{fa_rating}/9.0。"

    # 5. 綜合量化評分 (權重: MA=40%, Momentum=30%, ADX=10%, FA=20%)
    raw_score = (ma_score * 0.4) + (momentum_score * 0.3) + (adx_score * 0.1) + (fa_score * 0.2)
    
    # 將原始分數正規化到 0-10
    normalized_score = max(0, min(10, (raw_score * 1.5) + 5.0))
    
    # 6. 最終行動建議與策略生成
    if normalized_score >= 8.0:
        action = "強烈買進 (Strong Buy)"
        confidence_base = 80
    elif normalized_score >= 6.0:
        action = "買進 (Buy)"
        confidence_base = 65
    elif normalized_score >= 4.0:
        action = "觀望 (Neutral)"
        confidence_base = 50
    elif normalized_score >= 2.0:
        action = "賣出 (Sell)"
        confidence_base = 65
    else:
        action = "強烈賣出 (Strong Sell)"
        confidence_base = 80
        
    # 信心指數調整
    confidence = confidence_base + (adx_score * 5)
    if abs(ma_score) == 4.0: confidence += 5 
    confidence = min(95, confidence)

    # 7. ATR 風險管理 (R:R 2:1 原則)
    stop_loss_level = 1.5 * atr_value # 止損線設為 1.5 倍 ATR
    take_profit_level = 3.0 * atr_value # 止盈線設為 3.0 倍 ATR (R:R 2:1)
    
    if "買進" in action:
        stop_loss = current_price - stop_loss_level
        take_profit = current_price + take_profit_level
        entry_price = current_price 
        strategy_desc = f"基於強多頭訊號，建議在 **{currency_symbol}{entry_price:,.2f}** 附近買入。嚴格止損點設在 **{currency_symbol}{stop_loss:,.2f}**，目標止盈點設在 **{currency_symbol}{take_profit:,.2f}**。R:R 風險回報比約為 2:1。"
    elif "賣出" in action:
        stop_loss = current_price + stop_loss_level
        take_profit = current_price - take_profit_level
        entry_price = current_price
        strategy_desc = f"基於強空頭訊號，建議在 **{currency_symbol}{entry_price:,.2f}** 附近賣出（或放空）。嚴格止損點設在 **{currency_symbol}{stop_loss:,.2f}**，目標止盈點設在 **{currency_symbol}{take_profit:,.2f}**。R:R 風險回報比約為 2:1。"
    else:
        stop_loss, take_profit, entry_price = 0, 0, 0
        strategy_desc = "市場處於盤整或趨勢不明，建議觀望，等待更明確的買賣信號。"

    # 8. XAI 多因子分解 DataFrame
    factor_df = pd.DataFrame({
        "因子/指標": ["技術趨勢 (MA/ADX)", "動能指標 (RSI/MACD)", "基本面評級 (FA)", "量化回測表現"],
        "得分/數據": [ma_score, momentum_score, fa_rating, total_return],
        "Score": [
            max(0, min(10, (ma_score / 4.0 * 5.0) + 5.0)), # MA Score 正規化到 0-10
            max(0, min(10, (momentum_score / 3.5 * 5.0) + 5.0)), # Momentum Score 正規化到 0-10
            max(0, min(10, (fa_rating / 9.0 * 10.0))), # FA Score 正規化到 0-10
            max(0, min(10, (total_return / 50.0 * 10.0 + 5.0))) # 回測回報正規化 (假設>50%回報為10分)
        ],
        # 🎯 修正：直接使用傳入的 fa_message
        "AI解讀": [
            expert_opinions.get('趨勢分析 (MA 排列)') or expert_opinions.get('趨勢分析 (MA 交叉)') or expert_opinions.get('趨勢分析 (MA)'),
            expert_opinions.get('動能分析 (RSI)') + " / " + expert_opinions.get('動能分析 (MACD)'),
            fa_message, 
            f"回測總回報率：{total_return} %"
        ]
    }).set_index("因子/指標")
    
    # 格式化百分比和數值
    factor_df['得分/數據'] = factor_df['得分/數據'].apply(lambda x: f"{x:,.2f}")
    factor_df['Score'] = factor_df['Score'].apply(lambda x: f"{x:,.2f}")

    return {
        'action': action,
        'score': round(normalized_score, 2),
        'confidence': min(100, confidence),
        'strategy': strategy_desc,
        'entry_price': round(entry_price, 2),
        'take_profit': round(take_profit, 2),
        'stop_loss': round(stop_loss, 2),
        'current_price': round(current_price, 2),
        'expert_opinions': expert_opinions,
        'atr': round(atr_value, 2),
        'factor_df': factor_df,
        'backtest_curve': backtest_result['capital_curve'] # 傳回資金曲線
    }

# ==============================================================================
# 5. DataFrame 樣式與格式化函式 (AttributeError 修正點)
# ==============================================================================

# 🎯 核心修正點：確保能處理 scalar (float/int) 輸入，解決 AttributeError
def style_factor_score(score):
    """為因子得分 (0-10) 著色，分數越高，顏色越綠。"""
    # 檢查並確保輸入是數值
    if isinstance(score, (int, float, np.number)):
        value = score
    # 這是處理 Streamlit/Pandas apply(axis=0/1) 時傳入 Series 的備用邏輯
    elif isinstance(score, pd.Series) and not score.empty:
        try:
            value = score.iloc[0]
        except:
            return ''
    else:
        return '' 

    value = max(0, min(10, value))
    
    if value < 5.0:
        # 0分 (30) 到 5分 (60)
        hue = 30 + (value / 5.0) * 30
    else:
        # 5分 (60) 到 10分 (120)
        hue = 60 + ((value - 5.0) / 5.0) * 60
        
    hue = max(30, min(120, hue))
    
    return f'background-color: hsl({hue}, 80%, 85%); color: #000000; font-weight: bold;'


def style_factor_rating(rating):
    """為整體評級 (如 6.00/10.0) 著色。"""
    if isinstance(rating, (int, float, np.number)):
        score = max(0, min(10, rating))
        if score < 5.0:
            hue = 30 + (score / 5.0) * 30
        else:
            hue = 60 + ((score - 5.0) / 5.0) * 60
        hue = max(30, min(120, hue))
        return f'background-color: hsl({hue}, 80%, 75%); color: #000000; font-weight: bolder;'
    return ''

def style_factor_score_wrapper(x):
    """用於 st.dataframe 的 styler.apply(axis=0) 時，僅對 **Score** 欄位應用著色。"""
    if x.name == 'Score':
        return x.apply(lambda val: style_factor_score(float(val)))
    else:
        return [''] * len(x)
        
def highlight_action_cell(val):
    """為 'Action' 欄位高亮顯示。"""
    buy_keywords = ["買進", "強多頭", "反彈"]
    sell_keywords = ["賣出", "強空頭", "回調"]
    
    val_str = str(val)
    if any(k in val_str for k in buy_keywords):
        return 'background-color: #e6ffe6; color: #008000; font-weight: bold;'
    elif any(k in val_str for k in sell_keywords):
        return 'background-color: #ffe6e6; color: #cc0000; font-weight: bold;'
    elif "觀望" in val_str or "中性" in val_str:
        return 'background-color: #ffffee; color: #ff9900; font-weight: bold;'
    return ''

# ==============================================================================
# 6. Streamlit 主函式 (已修正參數傳遞與補全繪圖邏輯)
# ==============================================================================

def main():
    
    # 側邊欄輸入
    with st.sidebar:
        st.header("1. 標的選擇")
        category = st.selectbox(
            "資產類別", 
            options=list(CATEGORY_MAP.keys()), 
            index=0
        )

        hot_options = CATEGORY_HOT_OPTIONS.get(category, {})
        # 設置 QCOM 為默認選項
        default_index = 0
        if "QCOM - 高通" in hot_options.keys():
            default_index = list(hot_options.keys()).index("QCOM - 高通")
            
        selected_key = st.selectbox(
            "熱門標的快速選擇", 
            options=list(hot_options.keys()), 
            index=default_index,
            key='select_hot_symbol'
        )
        
        symbol_default = hot_options.get(selected_key)
        
        symbol_input = st.text_input(
            "或直接輸入代碼/名稱 (例如: NVDA, 2330, BTC-USD)", 
            value=symbol_default, 
            key='input_symbol'
        )
        
        analysis_period = st.selectbox(
            "2. 分析週期",
            options=list(PERIOD_MAP.keys()),
            index=list(PERIOD_MAP.keys()).index("1 日 (中長線)"),
            key='select_period'
        )
        
        analyze_button_clicked = st.button("📊 執行AI分析", type="primary")

        # 根據輸入更新 symbol
        if analyze_button_clicked:
            final_symbol = get_symbol_from_query(symbol_input)
            st.session_state['last_search_symbol'] = final_symbol
            st.session_state['current_period'] = analysis_period
        
        # 確保初始運行時有預設值
        current_symbol = st.session_state.get('last_search_symbol', 'QCOM')
        current_period = st.session_state.get('current_period', "1 日 (中長線)")

    # 主頁面顯示邏輯
    st.title("📈 AI 趨勢分析儀表板")
    st.markdown("---")

    if st.session_state.get('last_search_symbol') and analyze_button_clicked:
        
        # 獲取數據與資訊
        period, interval = PERIOD_MAP[current_period]
        df = get_stock_data(current_symbol, period, interval)
        company_info = get_company_info(current_symbol)
        
        if df.empty:
            st.error(f"❌ 無法獲取 **{current_symbol} ({company_info['name']})** 在 {current_period} 週期內的數據。請檢查代碼或週期設定。")
            return
        
        currency_symbol = get_currency_symbol(current_symbol)
        
        # 1. 計算技術指標
        df = calculate_technical_indicators(df)
        
        # 2. 基本面診斷
        fa_result = calculate_fundamental_rating(current_symbol)
        fa_rating = fa_result['Combined_Rating']
        fa_message = fa_result['Message']
        
        # 3. 融合信號生成 (🎯 修正：傳遞 fa_message)
        ai_signal = generate_expert_fusion_signal(
            df.rename(columns={'Close': f'Close_{current_symbol}'}), 
            fa_rating, 
            fa_message, # NEW: 傳遞 fa_message
            is_long_term="日" in current_period or "週" in current_period,
            currency_symbol=currency_symbol
        )
        
        # ========================================================
        # 報告頭部
        # ========================================================
        
        st.subheader(f"📈 {company_info['name']} ({current_symbol}) AI集成趨勢分析")
        col_period, col_fa_rating = st.columns([1, 4])
        
        with col_period:
            st.markdown(f"**分析週期**: {current_period}")
        with col_fa_rating:
            # 應用顏色樣式到評級分數
            styled_fa_rating = f"<span style='{style_factor_rating(fa_rating)}'>**{fa_rating:.2f}/10.0**</span>"
            st.markdown(f"**FA 評級**: {styled_fa_rating}", unsafe_allow_html=True)
            
        st.markdown(f"**基本面診斷**: {fa_message}")
        st.markdown("---")

        # ========================================================
        # 核心行動與量化評分
        # ========================================================
        st.header("💡 核心行動與量化評分 (Meta-Learner 決策)")
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            st.metric(
                label="💰 當前價格", 
                value=f"{currency_symbol}{ai_signal['current_price']:,.2f}",
                delta=f"{df['Close'].iloc[-1] - df['Close'].iloc[-2]:,.2f} ({df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1.0:+.2%})"
            )
            
        with col2:
            action_html = f"<h3 style='{highlight_action_cell(ai_signal['action'])} padding: 5px; border-radius: 5px;'>{ai_signal['action']}</h3>"
            st.markdown(f"**🎯 最終行動建議**")
            st.markdown(action_html, unsafe_allow_html=True)
            
        with col3:
            score_html = f"<h3 style='{style_factor_rating(ai_signal['score'])} padding: 5px; border-radius: 5px;'>{ai_signal['score']:.2f}</h3>"
            st.markdown(f"**🔥 總量化評分**")
            st.markdown(score_html, unsafe_allow_html=True)

        with col4:
            st.markdown(f"**🛡️ 決策信心指數**")
            st.metric(
                label="", 
                value=f"{ai_signal['confidence']}%",
                delta_color="off"
            )
        
        st.markdown("---")

        # ========================================================
        # AI決策可解釋性：多因子得分分解 (XAI)
        # ========================================================
        st.header("🔎 AI決策可解釋性：多因子得分分解 (XAI)")
        
        factor_df = ai_signal['factor_df'].reset_index()
        
        # 應用修正後的樣式
        styled_factor_df = factor_df.style.apply(
            style_factor_score_wrapper,
            subset=['Score'], 
            axis=0 
        ).set_properties(
            **{'text-align': 'left'}, 
            subset=['因子/指標', 'AI解讀']
        )
        
        st.dataframe(
            styled_factor_df,
            column_config={
                "得分/數據": st.column_config.TextColumn(label="原始得分 (±)", width="small"),
                "Score": st.column_config.TextColumn(label="Score (0-10)", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")

        # ========================================================
        # 交易策略與風險管理
        # ========================================================
        st.header("🛡️ 交易策略與風險管理 (R:R 2:1)")
        st.info(ai_signal['strategy'])

        col_tp, col_sl, col_atr = st.columns(3)
        with col_tp:
            st.metric("🎯 止盈點 (Take Profit)", f"{currency_symbol}{ai_signal['take_profit']:,.2f}")
        with col_sl:
            st.metric("🛑 止損點 (Stop Loss)", f"{currency_symbol}{ai_signal['stop_loss']:,.2f}", delta_color="inverse")
        with col_atr:
            st.metric("🔥 當前波動 (ATR 9)", f"{currency_symbol}{ai_signal['atr']:,.2f}")
            
        st.markdown("---")
        
        # ========================================================
        # 技術圖表與回測 (補齊功能)
        # ========================================================
        st.header("📊 技術圖表與量化回測分析")

        tab1, tab2 = st.tabs(["K線圖與指標分析", "量化回測績效"])

        with tab1:
            st.subheader(f"{company_info['name']} ({current_symbol}) K線圖 ({current_period})")
            
            # 繪製 K 線圖
            fig = plot_candlestick_and_indicators(df, current_symbol)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.subheader("技術指標最新判讀")
            tech_df = get_technical_data_df(df)
            
            # 應用顏色樣式到分析結論
            def highlight_tech_conclusion(s):
                return [f'color: {c}; font-weight: bold' for c in s['顏色']]

            styled_tech_df = tech_df.drop(columns=['顏色']).style.apply(
                highlight_tech_conclusion, 
                axis=1, 
                subset=['分析結論']
            ).format(
                {'最新值': '{:,.2f}'}
            ).set_properties(
                **{'text-align': 'left'}, 
                subset=['分析結論']
            )
            st.dataframe(styled_tech_df, use_container_width=True)


        with tab2:
            st.subheader("量化回測績效 (SMA 20/EMA 50 交叉策略)")
            backtest_result = run_backtest(df) 
            
            # 繪製資金曲線
            if backtest_result['total_trades'] > 0 and 'capital_curve' in backtest_result and not backtest_result['capital_curve'].empty:
                fig_curve = go.Figure()
                
                # 確保 index 是時間序列
                x_data = backtest_result['capital_curve'].index
                if isinstance(x_data, pd.DatetimeIndex) or len(x_data) == len(df.index.to_list()):
                    fig_curve.add_trace(go.Scatter(
                        x=x_data, 
                        y=backtest_result['capital_curve'].values, 
                        mode='lines', 
                        name='資金曲線'
                    ))
                    fig_curve.update_layout(
                        title="策略資金曲線",
                        yaxis_title=f"資產 ({currency_symbol})",
                        xaxis_title="日期",
                        height=400,
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig_curve, use_container_width=True)
                else:
                    st.warning("無法繪製資金曲線：日期索引或數據長度不匹配。")
            else:
                st.warning("無足夠數據進行回測，或回測策略未觸發交易。")
                
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.metric("總回報率", f"{backtest_result['total_return']:,.2f}%")
            with col_r2:
                st.metric("勝率", f"{backtest_result['win_rate']:,.2f}%")
            with col_r3:
                st.metric("最大回撤", f"{backtest_result['max_drawdown']:,.2f}%", delta_color="inverse")
            with col_r4:
                st.metric("總交易次數", f"{backtest_result['total_trades']}", delta_color="off")
            
            st.caption(f"**回測備註**: {backtest_result['message']}")


    elif not st.session_state.get('last_search_symbol', False):
        # 初始歡迎頁面
        st.markdown(
            """
            <h1 style='color: #cc6600; font-size: 32px; font-weight: bold;'>🚀 歡迎使用 AI 趨勢分析</h1>
            """, 
            unsafe_allow_html=True
        )
        
        st.info("請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 **『📊 執行AI分析』** 按鈕開始。")
        
        st.markdown("---")
        
        st.subheader("📝 使用步驟：")
        st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
        st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
        st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分 (短期)`、`1 日 (中長線)`）。")
        st.markdown("4. **執行分析**：點擊 **『📊 執行AI分析』**，AI將融合基本面與技術面指標提供交易策略。")


if __name__ == '__main__':
    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = 'QCOM'
    if 'current_period' not in st.session_state:
        st.session_state['current_period'] = "1 日 (中長線)"
        
    main()

    # 🎯 補回的結尾資訊
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")
