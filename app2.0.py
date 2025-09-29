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

# 🎯 新增兩層選擇的類別與熱門選項映射 (基於 FULL_SYMBOLS_MAP)
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
    """
    🎯 進化後的代碼解析函數：
    同時檢查 FULL_SYMBOLS_MAP
    """
    query = query.strip()
    # 1. 優先精確代碼/英文關鍵字匹配 (轉大寫)
    query_upper = query.upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        # 檢查 YFinance 代碼 (2330.TW, BNB-USD)
        if query_upper == code: # code 本身就是 yfinance_code
            return code
        # 檢查英文關鍵詞 (TSMC, BNB, BTC-USDT)
        if any(query_upper == kw.upper() for kw in data["keywords"]):
            return code # 返回 FULL_SYMBOLS_MAP 中的標準代碼
    # 2. 中文名稱精確匹配 (不轉大寫)
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == data["name"]:
            return code
    # 3. 台灣股票代碼自動補齊 (例如: 2317 -> 2317.TW)
    if re.fullmatch(r'\d{4,6}', query) and not any(ext in query_upper for ext in ['.TW', '.HK', '.SS', '-USD']):
        # 如果純數字代碼在 FULL_SYMBOLS_MAP 中有對應，則補齊
        tw_code = f"{query}.TW"
        if tw_code in FULL_SYMBOLS_MAP:
             return tw_code
        # 如果不在清單，仍嘗試補齊 (交給 yfinance 驗證)
        return tw_code
    # 4. 沒匹配到任何預設代碼，直接返回用戶輸入 (交給 yfinance 處理)
    return query

@st.cache_data(ttl=3600, show_spinner="正在從 Yahoo Finance 獲取數據...")
def get_stock_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return pd.DataFrame()
        
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
        # 從 FULL_SYMBOLS_MAP 中推導出 category 和 currency
        if symbol.endswith(".TW") or symbol.startswith("^TWII"):
            category = "台股 (TW)"
            currency = "TWD"
        elif symbol.endswith("-USD"):
            category = "加密貨幣 (Crypto)"
            currency = "USD"
        else:
            category = "美股 (US)"
            currency = "USD" # 預設美股為 USD
            
        return {"name": info['name'], "category": category, "currency": currency}
    
    try:
        ticker = yf.Ticker(symbol)
        yf_info = ticker.info
        name = yf_info.get('longName') or yf_info.get('shortName') or symbol
        currency = yf_info.get('currency') or "USD"
        category = "未分類"
        
        # 嘗試從代碼判斷類別
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
    if currency_code == 'TWD':
        return 'NT$'
    elif currency_code == 'USD':
        return '$'
    elif currency_code == 'HKD':
        return 'HK$'
    else:
        return currency_code + ' '

def calculate_technical_indicators(df):
    """
    優化後的技術指標計算：採用進階設定 (10, 50, 200 EMA & 9期 RSI/MACD/ATR)。
    """
    
    # 進階移動平均線 (MA)
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10) # 短線趨勢 (進階設定)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50) # 長線趨勢 (進階設定)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200) # 濾鏡 (長期趨勢)
    
    # MACD (進階設定: 快線 8, 慢線 17, 信號線 9)
    macd_instance = ta.trend.MACD(df['Close'], window_fast=8, window_slow=17, window_sign=9)
    df['MACD_Line'] = macd_instance.macd()
    df['MACD_Signal'] = macd_instance.macd_signal()
    df['MACD'] = macd_instance.macd_diff() # MACD 柱狀圖 (Histogram)
    
    # RSI (進階設定: 週期 9)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=9)
    
    # 經典布林通道 (20, 2)
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'], window=20, window_dev=2)
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'], window=20, window_dev=2)
    
    # ATR (進階設定: 週期 9)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=9)
    
    # ADX (進階設定: 週期 9)
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=9)
    
    # 增加 SMA 20 (作為回測基準)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20) 
    
    return df

def get_technical_data_df(df):
    """
    獲取最新的技術指標數據和AI結論。
    """
    
    # 確保有足夠的數據計算指標，這裡 200 週期是個合理的閾值
    if df.empty or len(df) < 200: 
        return pd.DataFrame()

    df_clean = df.dropna().copy()
    if df_clean.empty:
        return pd.DataFrame()

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
        conclusion = ""
        color = "grey"
        
        if 'EMA 10/50/200' in name:
            ema_10 = last_row['EMA_10']
            ema_50 = last_row['EMA_50']
            ema_200 = last_row['EMA_200']

            # 採用進階的多頭排列判斷 (10 > 50 > 200)
            if ema_10 > ema_50 and ema_50 > ema_200:
                conclusion = f"**強多頭：MA 多頭排列** (10>50>200)"
                color = "red"
            elif ema_10 < ema_50 and ema_50 < ema_200:
                conclusion = f"**強空頭：MA 空頭排列** (10<50<200)"
                color = "green"
            elif last_row['Close'] > ema_50 and last_row['Close'] > ema_200:
                conclusion = f"中長線偏多：價格站上 EMA 50/200"
                color = "orange"
            else:
                conclusion = "中性：MA 糾結或趨勢發展中"
                color = "blue"
        
        elif 'RSI' in name:
            # 進階判斷: RSI > 50 多頭, < 50 空頭。70/30 為超買超賣
            if value > 70:
                conclusion = "警告：超買區域 (70)，潛在回調"
                color = "green" 
            elif value < 30:
                conclusion = "強化：超賣區域 (30)，潛在反彈"
                color = "red"
            elif value > 50:
                conclusion = "多頭：RSI > 50，位於強勢區間"
                color = "red"
            else:
                conclusion = "空頭：RSI < 50，位於弱勢區間"
                color = "green"


        elif 'MACD' in name:
            # 判斷 MACD 柱狀圖是否放大
            if value > 0 and value > prev_row['MACD']:
                conclusion = "強化：多頭動能增強 (紅柱放大)"
                color = "red"
            elif value < 0 and value < prev_row['MACD']:
                conclusion = "削弱：空頭動能增強 (綠柱放大)"
                color = "green"
            else:
                conclusion = "中性：動能盤整 (柱狀收縮)"
                color = "orange"
        
        elif 'ADX' in name:
             # ADX > 25 確認強趨勢
            if value >= 40:
                conclusion = "強趨勢：極強勢趨勢 (多或空)"
                color = "red"
            elif value >= 25:
                conclusion = "強趨勢：確認強勢趨勢 (ADX > 25)"
                color = "orange"
            else:
                conclusion = "盤整：弱勢或橫盤整理 (ADX < 25)"
                color = "blue"

        elif 'ATR' in name:
            # 使用過去 30 期的平均 ATR 作為比較基準
            avg_atr = df_clean['ATR'].iloc[-30:].mean() if len(df_clean) >= 30 else df_clean['ATR'].mean()
            
            if value > avg_atr * 1.5:
                conclusion = "警告：極高波動性 (1.5x 平均)"
                color = "green"
            elif value < avg_atr * 0.7:
                conclusion = "中性：低波動性 (醞釀突破)"
                color = "orange"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif '布林通道' in name:
            high = last_row['BB_High']
            low = last_row['BB_Low']
            range_pct = (high - low) / last_row['Close'] * 100
            
            if value > high:
                conclusion = f"警告：價格位於上軌外側 (>{high:,.2f})"
                color = "red"
            elif value < low:
                conclusion = f"強化：價格位於下軌外側 (<{low:,.2f})"
                color = "green"
            else:
                conclusion = f"中性：在上下軌間 ({range_pct:.2f}% 寬度)"
                color = "blue"
        
        data.append([name, value, conclusion, color])

    technical_df = pd.DataFrame(data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    technical_df = technical_df.set_index('指標名稱')
    return technical_df

def run_backtest(df, initial_capital=100000, commission_rate=0.001):
    """
    執行基於 SMA 20 / EMA 50 交叉的簡單回測。
    策略: 黃金交叉買入 (做多)，死亡交叉清倉 (賣出)。
    """
    
    # 確保有足夠的數據
    if df.empty or len(df) < 51:
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "數據不足 (少於 51 週期) 或計算錯誤。"}

    data = df.copy()
    
    # 計算信號：當前週期 MA 20 > MA 50 且前一週期不滿足，即為黃金交叉 (Buy/Long)
    data['Prev_MA_State'] = (data['SMA_20'].shift(1) > data['EMA_50'].shift(1))
    data['Current_MA_State'] = (data['SMA_20'] > data['EMA_50'])
    
    # Buy Signal (Golden Cross)
    data['Signal'] = np.where(
        (data['Current_MA_State'] == True) & (data['Prev_MA_State'] == False), 1, 0
    )
    
    # Sell Signal (Death Cross)
    data['Signal'] = np.where(
        (data['Current_MA_State'] == False) & (data['Prev_MA_State'] == True), -1, data['Signal']
    )
    
    # 移除 NaN，確保指標計算完整
    data = data.dropna()
    if data.empty:
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "指標計算後數據不足。"}

    # --- 模擬交易邏輯 ---
    capital = [initial_capital]
    position = 0 # 0: 沒有倉位, 1: 做多
    buy_price = 0
    trades = []
    
    for i in range(1, len(data)):
        current_close = data['Close'].iloc[i]
        
        # 1. 檢查是否發生黃金交叉 (Buy Signal) 且目前無倉位
        if data['Signal'].iloc[i] == 1 and position == 0:
            position = 1
            buy_price = current_close
            # 扣除手續費 (假設買入/賣出總共 0.2%)
            initial_capital -= initial_capital * commission_rate 
            
        # 2. 檢查是否發生死亡交叉 (Sell Signal) 且目前有倉位 (清倉)
        elif data['Signal'].iloc[i] == -1 and position == 1:
            sell_price = current_close
            profit = (sell_price - buy_price) / buy_price # 單次交易收益率
            
            # 記錄交易
            trades.append({
                'entry_date': data.index[i],
                'exit_date': data.index[i],
                'profit_pct': profit,
                'is_win': profit > 0
            })
            
            # 更新資金
            initial_capital *= (1 + profit)
            # 扣除手續費
            initial_capital -= initial_capital * commission_rate
            
            position = 0
            
        # 記錄每日資金變化 (即使沒有交易，也要記錄)
        current_value = initial_capital
        if position == 1:
            # 計算當前倉位的市值，並加回資金
            current_value = initial_capital * (current_close / buy_price)
        
        capital.append(current_value)

    # 3. 處理最後一天仍持有的倉位 (以最後一個收盤價平倉)
    if position == 1:
        sell_price = data['Close'].iloc[-1]
        profit = (sell_price - buy_price) / buy_price
        
        trades.append({
            'entry_date': data.index[-1],
            'exit_date': data.index[-1],
            'profit_pct': profit,
            'is_win': profit > 0
        })
        
        initial_capital *= (1 + profit)
        initial_capital -= initial_capital * commission_rate
        # 更新最後一天的資金
        if capital: 
             capital[-1] = initial_capital 

    # --- 計算回測結果 ---
    
    # 總回報率
    total_return = ((initial_capital - 100000) / 100000) * 100
    
    # 勝率
    total_trades = len(trades)
    win_rate = (sum(1 for t in trades if t['is_win']) / total_trades) * 100 if total_trades > 0 else 0
    
    # 最大回撤 (Max Drawdown, MDD)
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
    更新: 融合了 '基本面的判斷標準'，特別是 ROE > 15%、PE 估值、以及現金流/負債健康度。
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 排除指數和加密貨幣 (通常沒有完整的基本面數據)
        if symbol.startswith('^') or symbol.endswith('-USD'):
            return {
                "Combined_Rating": 0.0, 
                "Message": "不適用：指數或加密貨幣無標準基本面數據。",
                "Details": None
            }

        # 獲取關鍵基本面指標
        roe = info.get('returnOnEquity', 0) # 獲利能力: ROE > 15%
        trailingPE = info.get('trailingPE', 99) # 估值: P/E Ratio
        freeCashFlow = info.get('freeCashflow', 0) # 營運現金流健康
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0) # 財務健康: 負債比率 < 50%
        
        # 1. 成長與效率評分 (ROE) (總分 3)
        roe_score = 0
        if roe > 0.15: # ROE > 15% (高效資本利用)
            roe_score = 3 
        elif roe > 0.10: 
            roe_score = 2
        elif roe > 0: 
            roe_score = 1
        
        # 2. 估值評分 (PE) (總分 3)
        pe_score = 0
        if trailingPE < 15 and trailingPE > 0: # P/E < 15 (格雷厄姆標準)
            pe_score = 3
        elif trailingPE < 25 and trailingPE > 0: # P/E < 25 (考慮成長股/行業平均)
            pe_score = 2
        elif trailingPE < 35 and trailingPE > 0: 
            pe_score = 1
        
        # 3. 現金流與償債能力 (總分 3)
        cf_score = 0
        
        # 財務健康度: 現金 vs 負債 (避免除以零)
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt and totalDebt != 0 else 100 
        
        # 負債比率 < 50% / 現金流為正 / 現金 > 債務
        if freeCashFlow > 0 and cash_debt_ratio > 2: # FCF > 0, 現金是債務的 2 倍以上 (超低風險)
            cf_score = 3
        elif freeCashFlow > 0 and cash_debt_ratio > 1: # FCF > 0, 現金 > 債務 (低風險)
            cf_score = 2
        elif freeCashFlow > 0: # 至少 FCF 為正
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
    更新: 融合了更精確的技術分析標準，特別是 MA 排列、RSI 50 中軸判斷、MACD 動能。
    並納入了 ATR 風險控制。
    """
    
    # 確保有足夠的數據
    df_clean = df.dropna().copy()
    if df_clean.empty or len(df_clean) < 2:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'expert_opinions': {}}

    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    adx_value = last_row['ADX'] # 納入 ADX 趨勢強度
    
    expert_opinions = {}
    
    # 1. 均線交叉與排列專家 (MA Cross & Alignment) - 趨勢線與MA判斷
    ma_score = 0
    ema_10 = last_row['EMA_10']
    ema_50 = last_row['EMA_50']
    ema_200 = last_row['EMA_200']
    
    # 黃金/死亡交叉 (10 vs 50)
    prev_10_above_50 = prev_row['EMA_10'] > prev_row['EMA_50']
    curr_10_above_50 = ema_10 > ema_50
    
    if not prev_10_above_50 and curr_10_above_50:
        ma_score = 3.5 # 黃金交叉，強勁買入信號
        expert_opinions['趨勢分析 (MA 交叉)'] = "**🚀 黃金交叉 (GC)**：EMA 10 向上穿越 EMA 50，強勁看漲信號！"
    elif prev_10_above_50 and not curr_10_above_50:
        ma_score = -3.5 # 死亡交叉，強勁賣出信號
        expert_opinions['趨勢分析 (MA 交叉)'] = "**💀 死亡交叉 (DC)**：EMA 10 向下穿越 EMA 50，強勁看跌信號！"
    elif ema_10 > ema_50 and ema_50 > ema_200:
        ma_score = 2.0 # 保持多頭排列 (10 > 50 > 200)
        expert_opinions['趨勢分析 (MA 排列)'] = "強勢多頭排列：**10 > 50 > 200**，趨勢結構穩固。"
    elif ema_10 < ema_50 and ema_50 < ema_200:
        ma_score = -2.0 # 保持空頭排列
        expert_opinions['趨勢分析 (MA 排列)'] = "強勢空頭排列：**10 < 50 < 200**，趨勢結構崩潰。"
    elif curr_10_above_50:
        ma_score = 1.0
        expert_opinions['趨勢分析 (MA 排列)'] = "多頭：EMA 10 位於 EMA 50 之上。"
    else:
        ma_score = -1.0
        expert_opinions['趨勢分析 (MA 排列)'] = "空頭：EMA 10 位於 EMA 50 之下。"

    # 2. 動能專家 (RSI) - 相對強弱判斷
    momentum_score = 0
    rsi = last_row['RSI']
    
    if rsi > 60:
        momentum_score = -2.0 # 接近超買
        expert_opinions['動能分析 (RSI 9)'] = "警告：RSI > 60，動能過熱，潛在回調壓力大。"
    elif rsi < 40:
        momentum_score = 2.0 # 接近超賣
        expert_opinions['動能分析 (RSI 9)'] = "強化：RSI < 40，動能低位，潛在反彈空間大。"
    elif rsi > 50: # RSI > 50 為多頭
        momentum_score = 1.0 
        expert_opinions['動能分析 (RSI 9)'] = "多頭：RSI > 50 中軸，維持在強勢區域。"
    else:
        momentum_score = -1.0 # RSI < 50 為空頭
        expert_opinions['動能分析 (RSI 9)'] = "空頭：RSI < 50 中軸，維持在弱勢區域。"

    # 3. 趨勢強度專家 (MACD & ADX) - 趨勢強度判斷
    strength_score = 0
    macd_diff = last_row['MACD']
    prev_macd_diff = prev_row['MACD']

    # MACD 動能
    if macd_diff > 0 and macd_diff > prev_macd_diff:
        strength_score += 1.5
        expert_opinions['趨勢強度 (MACD)'] = "多頭：MACD 柱狀圖放大，多頭動能強勁。"
    elif macd_diff < 0 and macd_diff < prev_macd_diff:
        strength_score -= 1.5
        expert_opinions['趨勢強度 (MACD)'] = "空頭：MACD 柱狀圖放大，空頭動能強勁。"
    else:
        strength_score += 0
        expert_opinions['趨勢強度 (MACD)'] = "中性：MACD 柱狀圖收縮，動能盤整。"

    # ADX 確認 (ADX > 25 確認強趨勢)
    if adx_value > 25:
        strength_score *= 1.5 # 趨勢強度大於 25 時，強化信號
        expert_opinions['趨勢強度 (ADX 9)'] = f"**確認強趨勢**：ADX {adx_value:.2f} > 25，信號有效性高。"
    else:
        expert_opinions['趨勢強度 (ADX 9)'] = f"盤整：ADX {adx_value:.2f} < 25，信號有效性降低。"


    # 4. K線形態專家 (簡單判斷) - K線型態判斷
    kline_score = 0
    is_up_bar = last_row['Close'] > last_row['Open']
    is_strong_up = is_up_bar and (last_row['Close'] - last_row['Open']) > atr_value * 0.7 # 使用 0.7 ATR
    is_strong_down = not is_up_bar and (last_row['Open'] - last_row['Close']) > atr_value * 0.7

    if is_strong_up:
        kline_score = 1.0
        expert_opinions['K線形態分析'] = "強化：實體大陽線（> 0.7 ATR），買盤積極。"
    elif is_strong_down:
        kline_score = -1.0
        expert_opinions['K線形態分析'] = "削弱：實體大陰線（> 0.7 ATR），賣壓沉重。"
    else:
        kline_score = 0
        expert_opinions['K線形態分析'] = "中性：K線實體小，觀望。"

    # 5. 融合評分 (總分: MA 3.5 + RSI 2 + Strength 1.5*1.5 + Kline 1 + FA 3 = 13.75)
    # 將 FA 評分 (0-9) 正規化到 -3 到 +3 的範圍
    fa_normalized_score = ((fa_rating / 9) * 6) - 3 if fa_rating > 0 else 0
    fusion_score = ma_score + momentum_score + strength_score + kline_score + fa_normalized_score
    
    # 最終行動
    action = "觀望 (Neutral)"
    
    if fusion_score >= 4.0:
        action = "買進 (Buy)"
    elif fusion_score >= 1.0:
        action = "中性偏買 (Hold/Buy)"
    elif fusion_score <= -4.0:
        action = "賣出 (Sell/Short)"
    elif fusion_score <= -1.0:
        action = "中性偏賣 (Hold/Sell)"
        
    # 信心指數 (將評分正規化到 0-100)
    MAX_SCORE = 13.75 
    confidence = min(100, max(0, 50 + (fusion_score / MAX_SCORE) * 50))
    
    # 風險控制與交易策略 (R:R 達到 2:1) - 風險管理專家的原則
    risk_multiple = 2.0 if is_long_term else 1.5 # 長線用 2.0 ATR 止損
    reward_multiple = 2.0 # 追求 2:1 的回報風險比
    
    # 定義策略
    entry_buffer = atr_value * 0.3 # 允許 0.3 ATR 的緩衝
    
    if action in ["買進 (Buy)", "中性偏買 (Hold/Buy)"]:
        # 回調買入
        entry = current_price - entry_buffer
        stop_loss = entry - (atr_value * risk_multiple)
        take_profit = entry + (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議在 **{currency_symbol}{entry:.2f} (± {entry_buffer:,.4f})** 範圍內尋找支撐或等待回調進場。"
    elif action in ["賣出 (Sell/Short)", "中性偏賣 (Hold/Sell)"]:
        # 反彈賣出
        entry = current_price + entry_buffer
        stop_loss = entry + (atr_value * risk_multiple)
        take_profit = entry - (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議在 **{currency_symbol}{entry:.2f} (± {entry_buffer:,.4f})** 範圍內尋找阻力或等待反彈後進場。"
    else:
        entry = current_price
        stop_loss = current_price - atr_value
        take_profit = current_price + atr_value
        strategy_desc = "市場信號混亂，建議等待趨勢明朗或在區間內操作。"

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
    # 必須確保 df 已經計算了指標且移除了 NaN
    df_clean = df.dropna().copy()
    if df_clean.empty:
        # 返回一個空的圖表或錯誤提示
        return go.Figure().update_layout(title="數據不足，無法繪製圖表")

    # 1. 主圖：K線與均線 (展示 EMA 10, 50, 200)
    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.08,
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=(f"{symbol} 價格走勢 (週期: {period_key})", "MACD 指標", "RSI/ADX 指標"))

    fig.add_trace(go.Candlestick(x=df_clean.index,
                                 open=df_clean['Open'],
                                 high=df_clean['High'],
                                 low=df_clean['Low'],
                                 close=df_clean['Close'],
                                 name='K線',
                                 increasing_line_color='#cc0000', decreasing_line_color='#1e8449'), 
                  row=1, col=1)

    # 繪製 EMA 10 (短線)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['EMA_10'], line=dict(color='#ffab40', width=1), name='EMA 10'), row=1, col=1) 
    # 繪製 EMA 50 (中線)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['EMA_50'], line=dict(color='#0077b6', width=1.5), name='EMA 50'), row=1, col=1) 
    # 繪製 EMA 200 (濾鏡)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['EMA_200'], line=dict(color='#800080', width=1.5, dash='dash'), name='EMA 200'), row=1, col=1) 
    
    # 2. MACD 圖 (MACD Line 和 Signal Line)
    colors = np.where(df_clean['MACD'] > 0, '#cc0000', '#1e8449') 
    fig.add_trace(go.Bar(x=df_clean.index, y=df_clean['MACD'], name='MACD 柱狀圖', marker_color=colors, opacity=0.5), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['MACD_Line'], line=dict(color='#0077b6', width=1), name='DIF'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['MACD_Signal'], line=dict(color='#ffab40', width=1), name='DEA'), row=2, col=1)

    fig.update_yaxes(title_text="MACD", row=2, col=1)

    # 3. RSI 圖 (包含 ADX)
    # RSI
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1, annotation_text="超買 (70)", annotation_position="top right")
    fig.add_hline(y=50, line_dash="dash", line_color="grey", row=3, col=1, annotation_text="多/空分界 (50)", annotation_position="top left")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1, annotation_text="超賣 (30)", annotation_position="bottom right")
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    
    # ADX - 使用第二個 Y 軸 (右側)
    fig.add_trace(go.Scatter(x=df_clean.index, y=df_clean['ADX'], line=dict(color='#cc6600', width=1.5, dash='dot'), name='ADX', yaxis='y4'), row=3, col=1)
    fig.update_layout(yaxis4=dict(title="ADX", overlaying='y3', side='right', range=[0, 100], showgrid=False))
    fig.add_hline(y=25, line_dash="dot", line_color="#cc6600", row=3, col=1, annotation_text="強勢趨勢 (ADX 25)", annotation_position="bottom left", yref='y4')


    # 佈局設定
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

# Streamlit 側邊欄函數
def update_search_input():
    """
    當第二層快速選擇下拉選單改變時，自動更新搜尋欄位的代碼。
    """
    # 讀取第二層 Selectbox 的當前值 (顯示文字，e.g., "SOL-USD - Solana")
    selected_option_display = st.session_state.symbol_select_box
    # If the placeholder is selected, do nothing.
    if selected_option_display and selected_option_display != "請選擇標的...":
        # 解析出代碼 (e.g., "SOL-USD - Solana" -> "SOL-USD")
        code = selected_option_display.split(' - ')[0]
        # 1. 設置 Text Input 的值 (使用 Text Input 的 key: sidebar_search_input)
        st.session_state.sidebar_search_input = code
        # 2. 強制設置 analyze_trigger 為 True，確保代碼改變後分析被觸發
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
            /* 輕微的陰影和圓角，模擬玻璃感 */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); 
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        /* 2. 懸停 (Hover) 效果 - 增強淡橙色 */
        [data-testid="stSidebar"] .stButton button:hover {
            color: #cc6600 !important; /* 懸停時文字顏色變深橙 */
            background-color: rgba(255, 171, 64, 0.15) !important; /* 懸停時輕微背景色 */
            border-color: #cc6600 !important;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15); /* 輕微提升陰影 */
        }
        
        /* 3. 點擊 (Active/Focus) 效果 */
        [data-testid="stSidebar"] .stButton button:active,
        [data-testid="stSidebar"] .stButton button:focus {
            color: #ff9933 !important;
            background-color: rgba(255, 171, 64, 0.25) !important;
            border-color: #ff9933 !important;
            box-shadow: none !important; /* 點擊時移除陰影 */
        }
        
        /* 4. 修正主標題顏色 (未分析時的首頁標題) */
        h1 { color: #cc6600; } 
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
    
    # 根據第一層選擇，準備第二層的選項 (顯示名稱)
    current_category_options_display = list(CATEGORY_HOT_OPTIONS.get(selected_category_key, {}).keys())
    
    # 找出當前 symbol 是否在列表中的預設值
    current_symbol_code = st.session_state.get('last_search_symbol', "2330.TW")
    default_symbol_index = 0
    
    # 嘗試匹配當前代碼到顯示名稱
    try:
        current_display_name = f"{current_symbol_code} - {FULL_SYMBOLS_MAP[current_symbol_code]['name']}"
        if current_display_name in current_category_options_display:
            default_symbol_index = current_category_options_display.index(current_display_name)
    except:
        # 如果當前代碼不在當前類別，預設選第一個
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

    is_long_term = selected_period_key in ["1 日 (中長線)", "1 週 (長期)"]

    st.sidebar.markdown("---")

    # --- 5. 開始分析 (Button) ---
    st.sidebar.markdown("5. **開始分析**")
    
    # 使用自定義 CSS 實現的玻璃按鍵 (淡橙色高亮)
    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", key="main_analyze_button") 

    # === 主要分析邏輯 (Main Analysis Logic) ===
    if analyze_button_clicked or st.session_state.get('analyze_trigger', False):
        
        st.session_state['data_ready'] = False
        st.session_state['analyze_trigger'] = False 
        
        try:
            with st.spinner(f"🔍 正在啟動AI模型，獲取並分析 **{final_symbol_to_analyze}** 的數據 ({selected_period_key})..."):
                
                df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval) 
                
                if df.empty or len(df) < 200: # 提高門檻到 200，以便計算 EMA 200
                    display_symbol = final_symbol_to_analyze
                    
                    st.error(f"❌ **數據不足或代碼無效。** 請確認代碼 **{display_symbol}** 是否正確。")
                    st.info(f"💡 **提醒：** 台灣股票需要以 **代碼.TW** 格式輸入 (例如：**2330.TW**)。")
                    st.session_state['data_ready'] = False 
                else:
                    company_info = get_company_info(final_symbol_to_analyze) 
                    currency_symbol = get_currency_symbol(final_symbol_to_analyze) 
                    
                    # 🚀 使用優化後的指標參數
                    df = calculate_technical_indicators(df) 
                    fa_result = calculate_fundamental_rating(final_symbol_to_analyze)
                    
                    # 🛠️ 將 currency_symbol 傳入函數
                    analysis = generate_expert_fusion_signal(
                        df, 
                        fa_rating=fa_result['Combined_Rating'], 
                        is_long_term=is_long_term,
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
        df = results['df'].dropna() # 確保所有指標都計算完整
        company_info = results['company_info']
        currency_symbol = results['currency_symbol']
        fa_result = results['fa_result']
        analysis = results['analysis']
        selected_period_key = results['selected_period_key']
        final_symbol_to_analyze = results['final_symbol_to_analyze']
        
        st.header(f"📈 **{company_info['name']}** ({final_symbol_to_analyze}) AI趨勢分析")
        
        current_price = analysis['current_price']
        prev_close = df['Close'].iloc[-2] if len(df) >= 2 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        price_delta_color = 'inverse' if change < 0 else 'normal'

        st.markdown(f"**分析週期:** **{selected_period_key}** | **FA 評級:** **{fa_result['Combined_Rating']:.2f}/9.0**")
        st.markdown(f"**基本面診斷:** {fa_result['Message']}")
        st.markdown("---")
        
        st.subheader("💡 核心行動與量化評分")
        
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
            action_class = "action-buy" if analysis['action'] == "買進 (Buy)" else ("action-sell" if analysis['action'] == "賣出 (Sell/Short)" else "action-neutral")
            st.markdown(f"<p class='{action_class}' style='font-size: 20px;'>{analysis['action']}</p>", unsafe_allow_html=True)
        
        with col_core_3: 
            st.metric("🔥 總量化評分", f"{analysis['score']}", help="FA/TA 融合策略總分 (正數看漲)")
        with col_core_4: 
            st.metric("🛡️ 信心指數", f"{analysis['confidence']:.0f}%", help="AI對此建議的信心度")
        
        st.markdown("---")

        st.subheader("🛡️ 精確交易策略與風險控制")
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
            
        st.info(f"**💡 策略總結:** **{analysis['strategy']}** | **⚖️ 風險/回報比 (R:R):** **{risk_reward:.2f}** | **波動單位 (ATR):** {analysis.get('atr', 0):.4f}")
        
        st.markdown("---")
        
        st.subheader("📊 關鍵技術指標數據與AI判讀 (交叉驗證細節)")
        
        ai_df = pd.DataFrame(analysis['expert_opinions'].items(), columns=['AI領域', '判斷結果']) 
        
        if isinstance(fa_result, dict) and 'Message' in fa_result:
            # 將基本面分析結果加入交叉驗證細節
            ai_df.loc[len(ai_df)] = ['基本面 FCF/ROE/PE 診斷', fa_result['Message']]
        
        def style_expert_opinion(s):
            is_positive = s.str.contains('牛市|買進|多頭|強化|利多|極健康|穩固|潛在反彈|強勢區間|多頭排列|黃金交叉|強勁|穩固', case=False)
            is_negative = s.str.contains('熊市|賣出|空頭|削弱|利空|下跌|疲弱|潛在回調|弱勢區間|空頭排列|死亡交叉|過熱|崩潰', case=False)
            is_warning = s.str.contains('盤整|警告|中性|觀望|趨勢發展中|不適用|收縮|低波動性|過高|壓力', case=False) 
            
            colors = np.select(
                [is_negative, is_positive, is_warning],
                ['color: #1e8449; font-weight: bold;', 'color: #cc0000; font-weight: bold;', 'color: #cc6600;'],
                default='color: #888888;'
            )
            return [f'{c}' for c in colors]

        styled_ai_df = ai_df.style.apply(style_expert_opinion, subset=['判斷結果'], axis=0)

        st.dataframe(
            styled_ai_df,
            use_container_width=True,
            key=f"ai_df_{final_symbol_to_analyze}_{selected_period_key}",
            column_config={
                "AI領域": st.column_config.Column("AI領域", help="FA/TA 分析範疇"),
                "判斷結果": st.column_config.Column("判斷結果", help="AI對該領域的量化判讀與結論"),
            }
        )
        
        st.caption("ℹ️ **設計師提示:** 判讀結果顏色：**紅色=多頭/強化信號** (類似低風險買入)，**綠色=空頭/削弱信號** (類似高風險賣出)，**橙色=中性/警告**。")

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
                # MDD 數字越大越不好，所以反向使用 delta_color
                st.metric("📉 最大回撤 (MDD)", f"{backtest_results['max_drawdown']}%", delta_color='inverse')

            with col_bt_4:
                st.metric("🤝 交易總次數", f"{backtest_results['total_trades']} 次")
                
            # 資金曲線圖
            if 'capital_curve' in backtest_results:
                fig_bt = go.Figure()
                fig_bt.add_trace(go.Scatter(x=df.index.to_list(), y=backtest_results['capital_curve'], name='策略資金曲線', line=dict(color='#cc6600', width=2)))
                fig_bt.add_hline(y=100000, line_dash="dash", line_color="#1e8449", annotation_text="起始資金 $100,000", annotation_position="bottom right")
                
                fig_bt.update_layout(
                    title='SMA 20/EMA 50 交叉策略資金曲線',
                    xaxis_title='交易週期',
                    yaxis_title='賬戶價值 ($)',
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300
                )
                st.plotly_chart(fig_bt, use_container_width=True)
                
            st.caption("ℹ️ **策略說明:** 此回測使用 **SMA 20/EMA 50** 交叉作為**開倉/清倉**信號 (初始資金 $100,000，單次交易手續費 0.1%)。 **總回報率**越高越好，**最大回撤 (MDD)**越低越好。")
        else:
            st.info(f"回測無法執行或無交易信號：{backtest_results.get('message', '數據不足或發生錯誤。')}")

        st.markdown("---")
        
        st.subheader("🛠️ 技術指標狀態表")
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
            st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化（**紅色=多頭/強化信號**（類似低風險買入），**綠色=空頭/削弱信號**（類似高風險賣出），**橙色=中性/警告**）。")

        else:
            st.info("無足夠數據生成關鍵技術指標表格。")
        
        st.markdown("---")
        
        st.subheader(f"📊 完整技術分析圖表")
        chart = create_comprehensive_chart(df, final_symbol_to_analyze, selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

    # === 修正部分：未分析時的預設首頁顯示 (將標題改為淡橙色 #cc6600) ===
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          # 使用 HTML 語法來控制顏色 (橙色調：#cc6600)
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
        st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'sidebar_search_input' not in st.session_state:
        st.session_state['sidebar_search_input'] = "2330.TW"
    if 'analyze_trigger' not in st.session_state:
        st.session_state['analyze_trigger'] = False
        
    main()
    
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")
