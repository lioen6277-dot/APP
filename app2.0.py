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

# 🚀 您的【所有資產清單】(FULL_SYMBOLS_MAP) - 維持不變，用於快速選擇和代碼解析
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
    total_return = ((initial_capital - 100000) / 100000) * 100
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
        
        roe = info.get('returnOnEquity', 0)
        trailingPE = info.get('trailingPE', 99)
        freeCashFlow = info.get('freeCashflow', 0)
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0)

        # 1. 成長與效率評分 (ROE) (總分 3)
        roe_score = 0
        if roe > 0.15: roe_score = 3 # ROE > 15% (頂級標準)
        elif roe > 0.10: roe_score = 2
        elif roe > 0: roe_score = 1
        
        # 2. 估值評分 (PE) (總分 3)
        pe_score = 0
        if trailingPE < 15 and trailingPE > 0: pe_score = 3 # P/E < 15 (格雷厄姆標準)
        elif trailingPE < 25 and trailingPE > 0: pe_score = 2 # P/E < 25 (考慮成長股/行業平均)
        elif trailingPE < 35 and trailingPE > 0: pe_score = 1
        
        # 3. 現金流與償債能力 (總分 3)
        cf_score = 0
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt and totalDebt != 0 else 100
        
        # FCF > 0, 負債比率 < 50% (現金 > 債務)
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

def generate_expert_fusion_signal(df, fa_rating, is_long_term=True, currency_symbol="$"):
    """
    融合了精確的技術分析標準 (MA 排列、RSI 50 中軸、MACD 動能、ADX 濾鏡) 並納入了 ATR 風險控制 (TP/SL) 和 R:R 2:1 的原則。
    """
    df_clean = df.dropna().copy()
    
    if df_clean.empty or len(df_clean) < 2:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'expert_opinions': {}, 'atr': 0}
    
    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    adx_value = last_row['ADX']
    
    expert_opinions = {}
    
    # 1. 均線交叉與排列專家 (MA Cross & Alignment)
    ma_score = 0
    ema_10 = last_row['EMA_10']
    ema_50 = last_row['EMA_50']
    ema_200 = last_row['EMA_200']

    prev_10_above_50 = prev_row['EMA_10'] > prev_row['EMA_50']
    curr_10_above_50 = ema_10 > ema_50
    
    if not prev_10_above_50 and curr_10_above_50:
        ma_score = 3.5 # 黃金交叉
        expert_opinions['趨勢分析 (MA 交叉)'] = "**🚀 黃金交叉**：短線動能轉強，確認多頭信號。"
    elif prev_10_above_50 and not curr_10_above_50:
        ma_score = -3.5 # 死亡交叉
        expert_opinions['趨勢分析 (MA 交叉)'] = "**🚨 死亡交叉**：短線動能轉弱，確認空頭信號。"
    elif ema_10 > ema_50 and ema_50 > ema_200:
        ma_score = 2.0 # 多頭排列
        expert_opinions['趨勢分析 (MA 排列)'] = "✅ **多頭排列**：10/50/200 均線向上，趨勢結構強勁。"
    elif ema_10 < ema_50 and ema_50 < ema_200:
        ma_score = -2.0 # 空頭排列
        expert_opinions['趨勢分析 (MA 排列)'] = "❌ **空頭排列**：10/50/200 均線向下，趨勢結構疲弱。"
    elif current_price > ema_50:
        ma_score = 0.5
        expert_opinions['趨勢分析 (MA 排列)'] = "⚖️ **中長線偏多**：價格位於 EMA 50 上方。"
    else:
        ma_score = -0.5
        expert_opinions['趨勢分析 (MA 排列)'] = "⚖️ **中長線偏空**：價格位於 EMA 50 下方。"
        
    # 2. 動能專家 (RSI / MACD)
    momentum_score = 0
    rsi_value = last_row['RSI']
    macd_bar = last_row['MACD']
    prev_macd_bar = prev_row['MACD']
    
    if rsi_value > 70:
        momentum_score -= 1.0
        expert_opinions['動能分析 (RSI)'] = "🔻 **超買警示**：RSI > 70，動能過熱，可能回調。"
    elif rsi_value < 30:
        momentum_score += 1.0
        expert_opinions['動能分析 (RSI)'] = "🔺 **超賣信號**：RSI < 30，動能過冷，可能反彈。"
    elif rsi_value > 50:
        momentum_score += 0.5
        expert_opinions['動能分析 (RSI)'] = "📈 **強勢區間**：RSI > 50，多頭動能佔優。"
    else:
        momentum_score -= 0.5
        expert_opinions['動能分析 (RSI)'] = "📉 **弱勢區間**：RSI < 50，空頭動能佔優。"

    if macd_bar > 0 and macd_bar > prev_macd_bar:
        momentum_score += 1.5
        expert_opinions['動能分析 (MACD)'] = "➕ **動能放大**：MACD 紅柱放大，上漲動能正在增強。"
    elif macd_bar < 0 and macd_bar < prev_macd_bar:
        momentum_score -= 1.5
        expert_opinions['動能分析 (MACD)'] = "➖ **動能放大**：MACD 綠柱放大，下跌動能正在增強。"
    else:
        expert_opinions['動能分析 (MACD)'] = "⏸️ **動能盤整**：MACD 柱狀收縮，動能進入盤整。"
        
    # 3. 趨勢強度專家 (ADX)
    adx_score = 0
    if adx_value >= 40:
        adx_score = 1.0
        expert_opinions['強度分析 (ADX)'] = "🔥 **趨勢極強**：ADX > 40，無論多空，趨勢方向極為清晰。"
    elif adx_value >= 25:
        adx_score = 0.5
        expert_opinions['強度分析 (ADX)'] = "✅ **趨勢確認**：ADX > 25，趨勢方向已被確認。"
    else:
        adx_score = 0.0
        expert_opinions['強度分析 (ADX)'] = "⚠️ **盤整區間**：ADX < 25，市場可能處於橫盤整理。"

    # 4. 基本面專家 (融入 FA Rating)
    fa_score = 0
    if fa_rating >= 7:
        fa_score = 3.0
        expert_opinions['基本面評級'] = "🏆 **頂級優異 (7-9分)**：基本面極健康，適合長期持有。"
    elif fa_rating >= 5:
        fa_score = 1.0
        expert_opinions['基本面評級'] = "👍 **良好穩健 (5-6分)**：財務結構穩固。"
    else:
        fa_score = 0.0
        expert_opinions['基本面評級'] = "🛑 **中性警示 (<5分)**：基本面較弱或不適用，需警惕風險。"

    # 5. 總分計算與行動判斷
    total_score = ma_score + momentum_score + adx_score + fa_score
    
    # 標準化分數 (將分數映射到 -10.0 到 10.0)
    score_min, score_max = -7.0, 7.0 # 根據經驗調整最大/最小可能得分
    final_score = 0
    if total_score > 0:
        final_score = min(total_score, score_max)
    else:
        final_score = max(total_score, score_min)

    # 最終決策 (基於趨勢、動能、基本面)
    if final_score >= 3.0:
        action = f"🟢 **強烈買入** ({currency_symbol} {current_price:,.2f})"
        final_strategy = "融合指標顯示強勁的多頭趨勢和動能，建議追蹤並建立多頭部位。"
        final_confidence = min(9.5, 6.0 + abs(final_score) * 0.5)
    elif final_score >= 1.0:
        action = f"🟡 **考慮買入** ({currency_symbol} {current_price:,.2f})"
        final_strategy = "指標偏多，建議小額或分批建倉，注意入場時機。"
        final_confidence = min(8.0, 5.0 + abs(final_score) * 0.5)
    elif final_score <= -3.0:
        action = f"🔴 **強烈賣出/清倉** ({currency_symbol} {current_price:,.2f})"
        final_strategy = "融合指標顯示明確的空頭趨勢和動能，建議清倉或建立空頭部位。"
        final_confidence = min(9.5, 6.0 + abs(final_score) * 0.5)
    elif final_score <= -1.0:
        action = f"🟠 **考慮賣出/觀望** ({currency_symbol} {current_price:,.2f})"
        final_strategy = "指標偏空，建議觀望或減少持倉，避免進場。"
        final_confidence = min(8.0, 5.0 + abs(final_score) * 0.5)
    else:
        action = f"⚪ **中性觀望** ({currency_symbol} {current_price:,.2f})"
        final_strategy = "市場趨勢不明或指標互相矛盾，建議等待趨勢明朗。"
        final_confidence = min(7.0, 4.0 + abs(final_score) * 0.5)

    # 6. 風險管理 (R:R 2:1 基於 ATR)
    
    # ATR 乘數：風險 1x ATR, 報酬 2x ATR
    # 入場價設定為當前收盤價
    entry_price = current_price 
    
    if '買入' in action:
        # 多頭策略：止損在 1x ATR 之下，目標在 2x ATR 之上
        stop_loss = entry_price - atr_value * 1.0
        take_profit = entry_price + atr_value * 2.0
    elif '賣出' in action:
        # 空頭策略：止損在 1x ATR 之上，目標在 2x ATR 之下
        stop_loss = entry_price + atr_value * 1.0
        take_profit = entry_price - atr_value * 2.0
    else: # 中性/觀望
        stop_loss = 0
        take_profit = 0

    return {'action': action, 'score': final_score, 'confidence': round(final_confidence, 1), 'strategy': final_strategy, 
            'entry_price': round(entry_price, 2), 'take_profit': round(take_profit, 2), 'stop_loss': round(stop_loss, 2), 
            'current_price': round(current_price, 2), 'expert_opinions': expert_opinions, 'atr': round(atr_value, 2)}

# ==============================================================================
# 3. Streamlit 介面主邏輯與圖表
# ==============================================================================

def create_comprehensive_chart(df, symbol, period_key):
    """
    建立包含 K 線、交易量、RSI、MACD 和 ADX 的綜合圖表。
    """
    
    # 檢查數據是否足夠
    if df.empty or len(df) < 20: return go.Figure().set_annotation_text("數據不足無法繪圖")

    # 1. 建立子圖：K線, 交易量, RSI, MACD, ADX (5個子圖)
    fig = make_subplots(
        rows=5, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.5, 0.1, 0.15, 0.15, 0.1]
    )

    # --- 區塊 1: K 線圖 + MA + BB ---
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線',
        showlegend=False
    ), row=1, col=1)

    # 均線 (EMA 50, EMA 200)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#ff9933', width=1), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#008080', width=1), name='EMA 200'), row=1, col=1)
    
    # 布林通道
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='rgba(100, 100, 255, 0.5)', width=0.5, dash='dash'), name='BB 上軌'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='rgba(100, 100, 255, 0.5)', width=0.5, dash='dash'), name='BB 下軌', fill='tonexty', fillcolor='rgba(100, 100, 255, 0.1)'), row=1, col=1)
    
    # --- 區塊 2: 交易量 ---
    colors = ['#ff4d4d' if df['Open'].iloc[i] > df['Close'].iloc[i] else '#1db954' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='交易量', marker_color=colors, showlegend=False), row=2, col=1)

    # --- 區塊 3: RSI ---
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#ff5733', width=1.5), name='RSI (9)'), row=3, col=1)
    fig.add_hline(y=70, line_width=1, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_width=1, line_dash="dash", line_color="green", row=3, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)

    # --- 區塊 4: MACD ---
    # MACD 柱狀圖
    macd_colors = ['#ff4d4d' if val >= 0 else '#1db954' for val in df['MACD']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD'], name='MACD 柱狀圖', marker_color=macd_colors, showlegend=False), row=4, col=1)
    # MACD Line & Signal Line
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='#0000ff', width=1), name='MACD Line'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#ff00ff', width=1), name='Signal Line'), row=4, col=1)

    # --- 區塊 5: ADX ---
    fig.add_trace(go.Scatter(x=df.index, y=df['ADX'], line=dict(color='#7C4DFF', width=1.5), name='ADX (9)'), row=5, col=1)
    fig.add_hline(y=25, line_width=1, line_dash="dash", line_color="orange", row=5, col=1)
    fig.update_yaxes(range=[0, 70], row=5, col=1)

    # --- 全局佈局優化 ---
    fig.update_layout(
        title=f'{symbol} - 綜合技術分析 ({period_key})',
        title_x=0.5,
        xaxis_rangeslider_visible=False,
        height=900,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # 隱藏除底部外的 X 軸標籤
    for i in range(1, 5):
        fig.update_xaxes(showticklabels=False, row=i, col=1)
        
    # Y 軸標題
    fig.update_yaxes(title_text=f'{symbol} 價格 ({df.iloc[-1]["Close"]:.2f})', row=1, col=1)
    fig.update_yaxes(title_text='成交量', row=2, col=1)
    fig.update_yaxes(title_text='RSI', row=3, col=1)
    fig.update_yaxes(title_text='MACD', row=4, col=1)
    fig.update_yaxes(title_text='ADX', row=5, col=1)

    return fig


def main():
    
    # -------------------
    # A. 側邊欄輸入控制
    # -------------------
    with st.sidebar:
        # st.image("LOGO.jpg") # 這裡您需要上傳您的 LOGO 圖片
        st.markdown(
            """
            <h1 style='color: #ff9933; font-size: 32px; font-weight: bold;'>AI 趨勢分析 V4.0</h1>
            <p style='color: #a0a0a0; font-size: 14px;'>融合技術面、基本面、量化回測的一站式決策儀表板。</p>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("---")
        
        # 1. 資產類別選擇
        category_options = list(CATEGORY_HOT_OPTIONS.keys())
        selected_category = st.selectbox("1️⃣ 選擇資產類別:", category_options, index=1)
        
        # 2. 熱門標的選擇 (用於快速切換)
        hot_options = CATEGORY_HOT_OPTIONS.get(selected_category, {})
        hot_option_names = list(hot_options.keys())
        default_index = 0
        if "2330.TW - 台積電" in hot_option_names:
             default_index = hot_option_names.index("2330.TW - 台積電")
        
        selected_hot_option_name = st.selectbox(
            "2️⃣ 快速選擇熱門標的:", 
            hot_option_names,
            index=default_index,
            key='select_hot_option'
        )
        selected_symbol_from_hot = hot_options.get(selected_hot_option_name)
        
        # 3. 手動輸入 (優先級最高)
        search_input = st.text_input(
            "3️⃣ 或手動輸入代碼 (例如: NVDA, 2330.TW):", 
            value=st.session_state.get('last_search_symbol', selected_symbol_from_hot),
            key='sidebar_search_input'
        )
        
        # 4. 週期選擇
        period_keys = list(PERIOD_MAP.keys())
        selected_period_key = st.selectbox("4️⃣ 選擇分析週期:", period_keys, index=2)
        
        st.markdown("---")
        
        # 5. 執行按鈕
        analyze_button_clicked = st.button("📊 執行AI分析", use_container_width=True, type="primary")

    # -------------------
    # B. 主頁面內容顯示
    # -------------------
    
    # 決定最終分析代碼
    final_symbol_input = get_symbol_from_query(search_input)
    final_symbol_to_analyze = final_symbol_input or selected_symbol_from_hot
    
    st.session_state['last_search_symbol'] = final_symbol_to_analyze

    if analyze_button_clicked or st.session_state.get('data_ready', False):
        st.session_state['data_ready'] = True
        
        # 獲取參數
        period, interval = PERIOD_MAP[selected_period_key]
        
        # 數據獲取 (使用緩存)
        df = get_stock_data(final_symbol_to_analyze, period, interval)
        company_info = get_company_info(final_symbol_to_analyze)
        currency_symbol = get_currency_symbol(final_symbol_to_analyze)

        st.markdown(f"## 💎 AI 趨勢分析：{company_info['name']} ({final_symbol_to_analyze})")
        st.caption(f"數據週期: **{selected_period_key}** (載入 {period} 的 {interval} 數據)")
        st.markdown("---")
        
        if df.empty or len(df) < 200:
            st.error(f"❌ 無法獲取 **{final_symbol_to_analyze}** 的足夠數據。請檢查代碼或選擇更長的週期 (至少需要 200 個數據點)。")
            st.session_state['data_ready'] = False
            return
        
        # 1. 執行技術指標計算與策略信號生成
        df = calculate_technical_indicators(df)
        fa_rating = calculate_fundamental_rating(final_symbol_to_analyze)
        fusion_signal = generate_expert_fusion_signal(
            df, 
            fa_rating['Combined_Rating'], 
            is_long_term=("1 週" in selected_period_key),
            currency_symbol=currency_symbol
        )
        
        # 2. 顯示AI融合決策信號
        col_signal, col_fa, col_price = st.columns([1, 1, 1])
        
        with col_signal:
            action = fusion_signal['action']
            color = "#ff9933" if '買入' in action else ("#e34848" if '賣出' in action else "#1e90ff")
            
            st.markdown(f"### 🤖 AI 決策信號")
            st.markdown(
                f"<div style='background-color:{color}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-weight: bold; font-size: 24px;'>{action}</div>",
                unsafe_allow_html=True
            )
            st.metric(
                label="信心分數", 
                value=f"{fusion_signal['confidence']:.1f} / 10.0", 
                delta=f"{fusion_signal['score']:.1f}", 
                delta_color="off" # 這裡的 delta 顯示總得分
            )
            st.markdown(f"**策略建議:** {fusion_signal['strategy']}")
            
        with col_fa:
            st.markdown("### 🏛️ 基本面評級 (總分 9)")
            
            rating = fa_rating['Combined_Rating']
            color_fa = "#ff9933" if rating >= 7 else ("#1e90ff" if rating >= 5 else "#e34848")

            st.markdown(
                f"<div style='background-color:{color_fa}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-weight: bold; font-size: 24px;'>{rating:.1f} 分</div>",
                unsafe_allow_html=True
            )
            st.caption(fa_rating['Message'])
            
            # 詳細意見
            with st.expander("AI基本面詳細意見"):
                for k, v in fusion_signal['expert_opinions'].items():
                    if '基本面' in k:
                        st.markdown(f"**{k.split(': ')[0]}**：{v.split(': ')[1]}")
                        
        with col_price:
            st.markdown("### 🎯 ATR 風控 (R:R 2:1)")
            
            atr = fusion_signal['atr']
            current_close = df['Close'].iloc[-1]
            
            st.metric(label=f"當前收盤價 ({currency_symbol})", value=f"{current_close:,.2f}")
            
            if atr > 0:
                st.metric(label="入場價格", value=f"{fusion_signal['entry_price']:,.2f}", delta="基於策略")
                st.metric(label="目標價 (TP)", value=f"{fusion_signal['take_profit']:,.2f}", delta="2x ATR")
                st.metric(label="止損價 (SL)", value=f"{fusion_signal['stop_loss']:,.2f}", delta="-1x ATR")
            else:
                 st.metric(label="ATR (波動性) 無法計算", value="--")

        st.markdown("---")

        # 3. 技術指標狀態表
        st.subheader("🛠️ 技術指標狀態表")
        technical_df = get_technical_data_df(df)

        # *** 修正 IndentationError 的地方：確保此 if 區塊的縮排與其上層一致 ***
        if not technical_df.empty: 
            def style_dataframe(df):
                df_styler = df.style
                
                # 應用結論欄位的背景色
                def color_conclusion(series):
                    return [
                        'background-color: #ffe0e0' if '多頭' in v or '強化' in v or '上軌' in v else 
                        ('background-color: #e0fff0' if '空頭' in v or '削弱' in v or '下軌' in v else 
                         'background-color: #fff0d0' if '中性' in v or '警告' in v else '')
                        for v in series
                    ]
                
                df_styler = df_styler.apply(color_conclusion, subset=['分析結論'], axis=0)
                
                return df_styler

            styled_df = technical_df[['最新值', '分析結論', '顏色']].drop(columns=['顏色'])
            styled_df = style_dataframe(styled_df)
            
            st.dataframe(
                styled_df, 
                use_container_width=True,
                key=f"technical_df_{final_symbol_to_analyze}_{selected_period_key}",
                column_config={
                    "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值", format="%.2f"),
                    "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的專業解讀"),
                }
            )
            st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化（**粉色=多頭/強化信號**，**淺綠=空頭/削弱信號**，**淺黃=中性/警告**）。")

        else:
            st.info("無足夠數據生成關鍵技術指標表格。")
        
        st.markdown("---")
        
        # 4. 完整技術分析圖表
        st.subheader(f"📊 完整技術分析圖表")
        chart = create_comprehensive_chart(df, final_symbol_to_analyze, selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")
        
        st.markdown("---")
        
        # 5. 量化回測結果
        st.subheader("🤖 策略回測報告 (SMA 20 / EMA 50 交叉)")
        
        backtest_results = run_backtest(df)
        
        if backtest_results['total_trades'] > 0:
            
            col_bt1, col_bt2, col_bt3, col_bt4 = st.columns(4)
            
            with col_bt1:
                st.metric(label="總報酬率", value=f"{backtest_results['total_return']:.2f} %", delta="基於回測策略")
            with col_bt2:
                st.metric(label="勝率", value=f"{backtest_results['win_rate']:.2f} %")
            with col_bt3:
                st.metric(label="最大回撤 (MDD)", value=f"{backtest_results['max_drawdown']:.2f} %", delta_color="inverse")
            with col_bt4:
                st.metric(label="總交易次數", value=backtest_results['total_trades'])
            
            st.caption(f"ℹ️ **回測區間:** {backtest_results['message']}")
            
            # 繪製資金曲線
            fig_capital = go.Figure()
            fig_capital.add_trace(go.Scatter(
                y=backtest_results['capital_curve'], 
                x=df.index[len(df)-len(backtest_results['capital_curve']):], # 確保 x 軸日期對齊
                mode='lines', 
                name='策略資金曲線'
            ))
            fig_capital.update_layout(
                title='回測資金曲線',
                height=350,
                showlegend=False,
                xaxis_title='日期',
                yaxis_title='資金 (USD/TWD)',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_capital, use_container_width=True)
            
        else:
            st.info(f"無法執行回測：{backtest_results['message']}")
            
        st.markdown("---")
        
        # 6. AI 綜合結論 (詳細意見)
        st.subheader("💡 AI 綜合決策與建議 (專家意見融合)")
        
        for k, v in fusion_signal['expert_opinions'].items():
             st.markdown(f"* **{k}**: {v}")
             
        st.markdown(f"**最終行動:** {fusion_signal['action']} ({fusion_signal['confidence']:.1f} 信心)")
        st.markdown(f"**風險管理:** 入場價 {fusion_signal['entry_price']:,.2f} | 止損 {fusion_signal['stop_loss']:,.2f} | 目標 {fusion_signal['take_profit']:,.2f} (R:R 2:1)")

    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          # 使用 HTML 語法來控制顏色 (橙色調：#ff9933)
          st.markdown(
              """
              <h1 style='color: #ff9933; font-size: 32px; font-weight: bold;'>🚀 歡迎使用 AI 趨勢分析</h1>
              """, 
              unsafe_allow_html=True
          )
          
          st.info("請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 **『📊 執行AI分析』** 按鈕開始。")
          
          st.markdown("---")
          
          st.subheader("📝 使用步驟：")
          st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
          st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
          st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分 (短期)`、`1 日 (中長線)`）。")
          # 🔥 修正：將顏色改為 #ff9933
          st.markdown(f"4. **執行分析**：點擊 <span style='color: #ff9933; font-weight: bold;'>『📊 執行AI分析』**</span>，AI將融合基本面與技術面指標提供交易策略。", unsafe_allow_html=True)
          
          st.markdown("---")


if __name__ == '__main__':
    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'sidebar_search_input' not in st.session_state:
        st.session_state['sidebar_search_input'] = "2330.TW" # 確保初始值與 last_search_symbol 一致

    # 呼叫主函式
    main()
    
    # 🚨 綜合免責聲明區塊
    st.markdown("---")
    st.markdown("⚠️ **綜合風險與免責聲明 (Risk & Disclaimer)**", unsafe_allow_html=True)
    st.markdown("本AI趨勢分析模型，是基於**量化集成學習 (Ensemble)** 和 **ATR 動態風險控制** 的專業架構。其分析結果**僅供教育與參考用途**，且性能受限於固定參數的**過度擬合風險**和市場的固有不穩定性。")
    st.markdown("投資涉及風險，所有交易決策應基於您個人的**獨立研究和財務狀況**，並強烈建議諮詢**專業金融顧問**。", unsafe_allow_html=True)
    st.markdown("📊 **數據來源:** Yahoo Finance | 🛠️ **技術指標:** TA 庫 | 💻 **APP優化:** 專業程式碼專家")

