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

# 應用 Streamlit 的客製化 CSS
# 修正重點：確保按鈕背景色在不同狀態下保持一致，並使用 CSS 選擇器精準覆蓋目標
st.markdown("""
<style>
/* 隱藏 Streamlit 默認的漢堡菜單和 Streamlit 標記 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* 設置側邊欄背景色 (稍微淺一點的灰色) */
[data-testid="stSidebar"] {
    background-color: #f0f2f6; 
}

/* 確保 '執行AI分析' 按鈕的顏色 (橙色調: #cc6600) */
/* 覆蓋 primary button 的默認樣式 */
div.stButton > button {
    background-color: #cc6600; /* 橙色背景 */
    color: white; /* 白色文字 */
    border-radius: 8px; /* 圓角 */
    border: 1px solid #cc6600; /* 邊框 */
    font-weight: bold; /* 加粗 */
    transition: background-color 0.2s, border-color 0.2s;
}

/* 按鈕懸停狀態 (hover) */
div.stButton > button:hover {
    background-color: #e57373; /* 淺一點的紅色/橙色 */
    border-color: #e57373;
}

/* 按鈕點擊狀態 (active) */
div.stButton > button:active {
    background-color: #b71c1c; /* 深紅色 */
    border-color: #b71c1c;
}

/* 修正 DataFrame 樣式，確保文字居中 */
.dataframe-text {
    text-align: center !important;
}

/* 確保標題使用橙色 */
h1 {
    color: #cc6600;
}
</style>
""", unsafe_allow_html=True)


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
        # yfinance 0.2.x 版本對於部分 symbol (如 BTC-USD) history 可能出錯，
        # 加上 auto_adjust=True 嘗試修復部分錯誤
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        
        if df.empty:
            return pd.DataFrame()
        
        # 統一列名為首字母大寫
        df.columns = [col.capitalize() for col in df.columns] 
        df.index.name = 'Date'
        
        # 只保留需要的列
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # 排除最後一個可能不完整的 K 線數據
        return df.iloc[:-1] if len(df) > 1 else pd.DataFrame()

    except Exception as e:
        # print(f"Error fetching data for {symbol}: {e}")
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
    
    # 確保 Close 列存在且非空
    if df.empty or 'Close' not in df.columns:
        return df

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
    
    # 清理 NaN 值，僅保留有指標數據的行
    df = df.dropna(subset=['SMA_20', 'EMA_50', 'MACD', 'RSI', 'ATR'])
    
    return df

def get_technical_data_df(df):
    
    # 至少需要 50 個數據點來確保 EMA-50 和 SMA-20 有效
    if df.empty or len(df) < 50: 
        return pd.DataFrame()

    last_row = df.iloc[-1]
    
    indicators = {}
    
    indicators['收盤價 vs SMA-20'] = last_row['Close']
    indicators['收盤價 vs EMA-50'] = last_row['Close']
    
    indicators['RSI (14)'] = last_row['RSI']
    indicators['Stochastics (%K)'] = last_row['Stoch_K']
    indicators['MACD 柱狀圖 (Signal)'] = last_row['MACD']
    
    indicators['ATR (14)'] = last_row['ATR']
    indicators['布林通道 (BB)'] = last_row['Close']
    
    data = []
    
    for name, value in indicators.items():
        conclusion = ""
        color = "grey"
        
        if name == '收盤價 vs SMA-20':
            ma = last_row['SMA_20']
            if value > ma * 1.01:
                conclusion = "多頭：價格強勢站上均線"
                color = "red"
            elif value < ma * 0.99:
                conclusion = "空頭：價格跌破均線"
                color = "green"
            else:
                conclusion = "中性：盤整或趨勢發展中"
                color = "orange"
        
        elif name == '收盤價 vs EMA-50':
            ma = last_row['EMA_50']
            if value > ma * 1.02:
                conclusion = "多頭：中長線趨勢強勁"
                color = "red"
            elif value < ma * 0.98:
                conclusion = "空頭：中長線趨勢疲軟"
                color = "green"
            else:
                conclusion = "中性：中長線盤整"
                color = "orange"

        elif name == 'RSI (14)':
            if value > 70:
                conclusion = "警告：超買區域，潛在回調"
                color = "green" # 綠色代表潛在賣壓
            elif value < 30:
                conclusion = "強化：超賣區域，潛在反彈"
                color = "red" # 紅色代表潛在買入機會
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == 'Stochastics (%K)':
            if value > 80:
                conclusion = "警告：接近超買區域"
                color = "green" # 綠色代表潛在賣壓
            elif value < 20:
                conclusion = "強化：接近超賣區域"
                color = "red" # 紅色代表潛在買入機會
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == 'MACD 柱狀圖 (Signal)':
            # 需要至少兩天的數據來判斷柱狀圖變化
            if len(df) < 2:
                conclusion = "中性：動能盤整"
                color = "orange"
            else:
                if value > 0 and last_row['MACD'] > df.iloc[-2]['MACD']:
                    conclusion = "強化：多頭動能增強 (金叉趨勢)"
                    color = "red"
                elif value < 0 and last_row['MACD'] < df.iloc[-2]['MACD']:
                    conclusion = "削弱：空頭動能增強 (死叉趨勢)"
                    color = "green"
                else:
                    conclusion = "中性：動能盤整"
                    color = "orange"
        
        elif name == 'ATR (14)':
            # 判斷波動性是高是低
            avg_atr = df['ATR'].mean()
            if value > avg_atr * 1.5:
                conclusion = "警告：極高波動性"
                color = "green" # 高波動性視為風險，用綠色
            elif value < avg_atr * 0.5:
                conclusion = "中性：低波動性 (可能預示盤整)"
                color = "orange"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == '布林通道 (BB)':
            high = last_row['BB_High']
            low = last_row['BB_Low']
            # 計算通道寬度
            range_pct = (high - low) / high if high else 0
            
            if value > high:
                conclusion = "警告：價格位於上軌外側 (超強勢)"
                color = "red"
            elif value < low:
                conclusion = "強化：價格位於下軌外側 (超弱勢)"
                color = "green"
            else:
                conclusion = f"中性：在上下軌間 ({range_pct*100:.2f}% 寬度)"
                color = "blue"
        
        # 數值格式化 (保留 2 位小數，ATR/BB 等可能需要更多)
        formatted_value = f"{value:.4f}" if name == 'ATR (14)' else f"{value:.2f}"
        
        data.append([name, formatted_value, conclusion, color])

    technical_df = pd.DataFrame(data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    technical_df = technical_df.set_index('指標名稱')
    return technical_df

def calculate_fundamental_rating(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 獲取關鍵基本面指標
        roe = info.get('returnOnEquity', 0)
        payoutRatio = info.get('payoutRatio', 0) 
        freeCashFlow = info.get('freeCashflow', 0)
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0)
        marketCap = info.get('marketCap', 1) 
        pe = info.get('trailingPE', 99)
        
        # 財務健康度 (Cash vs Debt)
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt else 100
        
        # 成長與效率評分 (ROE)
        roe_score = 0
        if roe > 0.15: roe_score = 3 
        elif roe > 0.08: roe_score = 2
        elif roe > 0: roe_score = 1
        
        # 估值評分 (PE)
        pe_score = 0
        if pe < 15: pe_score = 3
        elif pe < 25: pe_score = 2
        elif pe < 35: pe_score = 1
        
        # 現金流與償債能力
        cf_score = 0
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
            message = "基本面較弱：財務指標不佳，或數據缺失，不建議盲目進場。"
            
        return {
            "Combined_Rating": combined_rating,
            "Message": message,
            "Details": info
        }

    except Exception as e:
        # 非股票類標的 (指數/加密貨幣) 數據獲取失敗，給予最低分但給予提示
        if symbol.startswith('^') or symbol.endswith('-USD'):
             msg = "基本面數據不適用於指數或加密貨幣，已提供預設最低評分。"
        else:
             msg = f"基本面數據獲取失敗。請檢查代碼或稍後重試。"
        return {
            "Combined_Rating": 1.0, 
            "Message": msg,
            "Details": None
        }

def generate_expert_fusion_signal(df, fa_rating, is_long_term=True):
    
    if df.empty or len(df) < 50: # 確保至少有 50 個數據點計算指標
        return {
            'action': '數據不足', 
            'score': 0, 
            'confidence': 0, 
            'strategy': '無法評估', 
            'entry_price': 0, 
            'take_profit': 0, 
            'stop_loss': 0, 
            'current_price': 0, 
            'expert_opinions': {},
            'atr': 0
        }

    last_row = df.iloc[-1]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    
    expert_opinions = {}
    
    # 1. 趨勢專家 (均線) - 權重 3
    trend_score = 0
    if last_row['Close'] > last_row['SMA_20'] and last_row['SMA_20'] > last_row['EMA_50']:
        trend_score = 3
        expert_opinions['趨勢分析 (均線)'] = "多頭：短線(SMA)與中長線(EMA)均線呈多頭排列。"
    elif last_row['Close'] < last_row['SMA_20'] and last_row['SMA_20'] < last_row['EMA_50']:
        trend_score = -3
        expert_opinions['趨勢分析 (均線)'] = "空頭：短線與中長線均線呈空頭排列。"
    elif last_row['Close'] > last_row['SMA_20'] or last_row['Close'] > last_row['EMA_50']:
        trend_score = 1
        expert_opinions['趨勢分析 (均線)'] = "中性偏多：價格位於部分均線之上，趨勢正在發展。"
    else:
        trend_score = -1
        expert_opinions['趨勢分析 (均線)'] = "中性偏空：價格位於部分均線之下，趨勢正在發展。"

    # 2. 動能專家 (RSI & Stoch) - 權重 2
    momentum_score = 0
    rsi = last_row['RSI']
    stoch_k = last_row['Stoch_K']
    
    if rsi < 40 and stoch_k < 40:
        momentum_score = 2
        expert_opinions['動能分析 (RSI/Stoch)'] = "強化：動能指標低位，超賣區潛在反彈空間大。"
    elif rsi > 60 and stoch_k > 60:
        momentum_score = -2
        expert_opinions['動能分析 (RSI/Stoch)'] = "削弱：動能指標高位，超買區潛在回調壓力大。"
    else:
        momentum_score = 0
        expert_opinions['動能分析 (RSI/Stoch)'] = "中性：指標位於中間區域，趨勢發展中。"

    # 3. 波動性專家 (MACD) - 權重 2
    volatility_score = 0
    macd_diff = last_row['MACD']
    
    if len(df) >= 2:
        prev_macd_diff = df.iloc[-2]['MACD']
        if macd_diff > 0 and macd_diff > prev_macd_diff:
            volatility_score = 2
            expert_opinions['波動分析 (MACD)'] = "多頭：MACD柱狀圖擴大，多頭動能強勁。"
        elif macd_diff < 0 and macd_diff < prev_macd_diff:
            volatility_score = -2
            expert_opinions['波動分析 (MACD)'] = "空頭：MACD柱狀圖擴大，空頭動能強勁。"
        else:
            volatility_score = 0
            expert_opinions['波動分析 (MACD)'] = "中性：MACD柱狀圖收縮，動能盤整。"
    else:
        expert_opinions['波動分析 (MACD)'] = "中性：數據不足以判斷 MACD 變化。"
        
    # 4. K線形態專家 (簡單判斷) - 權重 1.5
    kline_score = 0
    is_up_bar = last_row['Close'] > last_row['Open']
    
    # 判斷實體大小是否超過 ATR 的 50%
    body_size = abs(last_row['Close'] - last_row['Open'])
    
    if atr_value > 0:
        is_strong_bar = body_size > atr_value * 0.5
        
        if is_strong_bar and is_up_bar:
            kline_score = 1.5
            expert_opinions['K線形態分析'] = "強化：實體大陽線，買盤積極。"
        elif is_strong_bar and not is_up_bar:
            kline_score = -1.5
            expert_opinions['K線形態分析'] = "削弱：實體大陰線，賣壓沉重。"
        else:
            kline_score = 0
            expert_opinions['K線形態分析'] = "中性：K線實體小，觀望。"
    else:
        expert_opinions['K線形態分析'] = "中性：ATR 為零或數據異常。"

    # 5. 基本面專家 (FA Rating) - 權重 3 (正規化到 -5.0 ~ +5.0 評分體系)
    # FA Rating 總分 9，這裡將其轉換為 -3 到 +3 的評分，與技術面評分對齊
    fa_normalized_score = (fa_rating / 9) * 3 
    
    # 融合評分 (總分 12 分技術面 + 3 分基本面 = 15 分評分空間)
    fusion_score = trend_score + momentum_score + volatility_score + kline_score + fa_normalized_score
    
    # 最終行動
    # 總分範圍約為 -7.5 到 +7.5 (如果基本面不計，為 -7.5 到 +7.5)
    
    # 總分正規化到 -5.0 ~ +5.0 的範圍 (大致等比例縮放，確保分數有意義)
    # 簡單將 fusion_score 縮放，使其在 -5.0 ~ +5.0 之間
    max_possible_score = 10.5 # 3+2+2+1.5 + 3 = 11.5 (Correction: 3+2+2+1.5=8.5 max tech score. Max FA score is 3. Total 11.5)
    min_possible_score = -6.5 # -3-2-2-1.5 - 0 = -8.5
    
    # 使用一個簡單的線性轉換，將其對齊到 [-5, 5] 範圍，並保留原始 fusion_score 的相對位置
    # 為了簡化，我們直接使用 fusion_score 作為評分基礎，因為它已經帶有權重
    
    score_scaled = round(fusion_score, 2)
    
    # 交易行動決策
    action = "觀望 (Neutral)" 
    if score_scaled >= 4.5:
        action = "買進 (Buy)"
    elif score_scaled >= 1.5:
        action = "中性偏買 (Hold/Buy)"
    elif score_scaled <= -4.5:
        action = "賣出 (Sell/Short)"
    elif score_scaled <= -1.5:
        action = "中性偏賣 (Hold/Sell)"

    # 信心指數 (將評分正規化到 0-100)
    # 假設中性為 0，最大正/負評分為 7.5
    confidence = min(100, max(0, 50 + (score_scaled / 7.5) * 50)) 
    
    # 風險控制與交易策略 (使用 ATR 設定 TP/SL)
    risk_multiple = 2.0 if is_long_term else 1.5 # 長線用較大 ATR 範圍
    reward_multiple = 2.0 
    
    entry, stop_loss, take_profit, strategy_desc = current_price, 0, 0, "市場信號混亂，建議等待趨勢明朗。"

    if action in ["買進 (Buy)", "中性偏買 (Hold/Buy)"]:
        entry = current_price - atr_value * 0.2 # 尋找略低於現價的進場點
        stop_loss = current_price - (atr_value * risk_multiple)
        take_profit = current_price + (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議以 {entry:.4f} 附近為進場參考點。"
    elif action in ["賣出 (Sell/Short)", "中性偏賣 (Hold/Sell)"]:
        entry = current_price + atr_value * 0.2 # 尋找略高於現價的進場點
        stop_loss = current_price + (atr_value * risk_multiple)
        take_profit = current_price - (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議以 {entry:.4f} 附近為進場參考點。"
    else:
        stop_loss = current_price - atr_value
        take_profit = current_price + atr_value

    return {
        'action': action,
        'score': score_scaled, # 評分 (-5.0 ~ +5.0)
        'confidence': round(confidence, 0), # 信心指數 (0-100)
        'strategy': strategy_desc,
        'entry_price': round(entry, 4) if atr_value else 0, 
        'take_profit': round(take_profit, 4) if atr_value else 0,
        'stop_loss': round(stop_loss, 4) if atr_value else 0,
        'current_price': round(current_price, 4),
        'expert_opinions': expert_opinions,
        'atr': round(atr_value, 4) if atr_value else 0
    }

# ==============================================================================
# 3. 繪圖函式 (Plotly)
# ==============================================================================

def create_comprehensive_chart(df, symbol, period_key):
    # 創建一個帶有兩個子圖的圖表：主 K 線/均線圖和子圖 MACD/RSI
    # rows=2, shared_xaxes=True, vertical_spacing=0.02
    # 設置每個子圖的高度比例 (K線:RSI:MACD = 3:1:1)
    fig = make_subplots(
        rows=3, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=[f'{symbol} K線圖與趨勢指標 ({period_key})', '相對強弱指數 (RSI, 14)', '平滑異同移動平均線 (MACD)']
    )

    # 1. 主 K 線圖 (Row 1)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線',
        showlegend=False
    ), row=1, col=1)

    # 均線 (SMA_20 & EMA_50)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='SMA-20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='EMA-50'), row=1, col=1)
    
    # 布林通道 (BB)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='gray', width=1, dash='dot'), name='BB上軌'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='gray', width=1, dash='dot'), name='BB下軌'), row=1, col=1)


    # 2. RSI (Row 2)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1) # 超買線
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1) # 超賣線
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    # 3. MACD 柱狀圖 (Row 3)
    colors = ['red' if val >= 0 else 'green' for val in df['MACD']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD'], name='MACD柱', marker_color=colors), row=3, col=1)
    fig.add_hline(y=0, line_width=1, line_color='black', row=3, col=1) # 零軸線
    

    # 全局佈局設置
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=900,
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        template="plotly_white", # 使用白色背景模板
        title_font_size=18,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    # 軸設置
    fig.update_xaxes(
        tickangle=0, 
        showgrid=True, 
        row=1, col=1, 
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    fig.update_yaxes(showgrid=True, row=1, col=1)

    return fig

# ==============================================================================
# 4. Streamlit DataFrame 樣式函數
# ==============================================================================

# **【修正點：修復 AttributeError: 'Series' object has no attribute 'iloc'】**
# 這個函數將被應用於 factor_df 的 '得分 (-5.0 ~ +5.0)' 欄位 (axis=1, subset=[...])
def style_factor_score(s):
    """
    對 factor_df 的 '得分' 列進行樣式設置。
    當使用 style.apply(axis=1, subset=[...]) 且 subset 只有一列時，
    s 是一個包含單一元素的 Series。
    """
    
    # 修正: 使用 .values[0] 提取單一數值，替代可能在 Streamlit/Pandas 版本中失敗的 .iloc[0]
    try:
        score_value = s.values[0]
    except Exception:
        # 如果不是 Series 或 Series 為空，則視為 0
        score_value = 0.0

    color = 'color: #0077b6;' # 藍色/中性

    # 這是原始代碼中的邏輯判斷 (行 722 附近)
    if score_value > 1.0:
        color = 'color: #cc6600; font-weight: bold;' # 橙色 (多頭)
    elif score_value < -1.0:
        color = 'color: #1e8449; font-weight: bold;' # 綠色 (空頭)
    
    # Styler.apply 必須返回一個包含 style string 的列表
    return [color] 

# 為了兼容 Streamlit 的 DataFrame Column Configuration，我們需要這個 wrapper
# 它確保 style_factor_score 僅接收評分數據
def style_factor_score_wrapper(x):
    # x 是 apply(axis=1) 傳入的 Series (整行數據)
    # 我們只需要評分那一列的數據，但因為我們已經使用 subset 篩選，x 就是評分 Series
    return style_factor_score(x)


# ==============================================================================
# 5. 主程式入口
# ==============================================================================

def main():
    st.set_page_config(
        page_title="🤖 AI趨勢分析儀表板 📈", 
        page_icon="📈", 
        layout="wide"
    )

    # ==================== 側邊欄輸入區 ====================
    st.sidebar.title("🛠️ 參數設定與標的選擇")

    # 兩層選擇結構
    selected_category = st.sidebar.selectbox(
        "1. 選擇資產類別:",
        list(CATEGORY_MAP.keys())
    )
    
    # 根據類別顯示熱門選項
    hot_options_dict = CATEGORY_HOT_OPTIONS.get(selected_category, {})
    hot_options_list = list(hot_options_dict.keys())
    selected_option_key = st.sidebar.selectbox(
        "2. 快速選擇標的 (熱門):",
        [""] + hot_options_list,
        index=0,
        format_func=lambda x: "--- 或自行輸入 ---" if x == "" else x
    )

    # 獲取選中的代碼
    selected_symbol_from_list = hot_options_dict.get(selected_option_key, "")

    # 用戶輸入
    user_input = st.sidebar.text_input(
        "3. 或手動輸入標的代碼/名稱:",
        placeholder="例如: NVDA, 2330, BTC-USD"
    )

    # 決定最終分析的代碼
    final_input = user_input if user_input else selected_symbol_from_list
    final_symbol_to_analyze = get_symbol_from_query(final_input) if final_input else None

    # 時間週期選擇
    selected_period_key = st.sidebar.selectbox(
        "4. 選擇分析週期:",
        list(PERIOD_MAP.keys()),
        index=2 # 默認選擇 '1 日 (中長線)'
    )
    
    # 執行按鈕
    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", type="primary", use_key=f"analyze_{final_symbol_to_analyze}_{selected_period_key}")

    # ==================== 數據獲取與分析 ====================

    if analyze_button_clicked and final_symbol_to_analyze:
        
        # 1. 獲取數據
        period, interval = PERIOD_MAP[selected_period_key]
        with st.spinner(f"正在獲取 {final_symbol_to_analyze} 的 {selected_period_key} 數據..."):
            df = get_stock_data(final_symbol_to_analyze, period, interval)
            
        # 檢查數據是否有效
        if df.empty:
            st.error(f"⚠️ 數據獲取失敗。請確認代碼 **{final_symbol_to_analyze}** ({final_input}) 是否正確，或該週期數據是否存在。")
            st.session_state['data_ready'] = False
            return

        # 2. 計算技術指標
        df = calculate_technical_indicators(df)
        
        # 3. 獲取基本面評級 (非阻塞)
        company_info = get_company_info(final_symbol_to_analyze)
        currency_symbol = get_currency_symbol(final_symbol_to_analyze)
        fa_rating_result = calculate_fundamental_rating(final_symbol_to_analyze)
        fa_rating = fa_rating_result['Combined_Rating']
        
        # 4. 生成融合信號
        # 判斷是否為長線分析 (日線或週線)
        is_long_term = selected_period_key in ["1 日 (中長線)", "1 週 (長期)"]
        signal = generate_expert_fusion_signal(df, fa_rating, is_long_term)
        
        st.session_state['data_ready'] = True
        st.session_state['df'] = df
        st.session_state['signal'] = signal
        st.session_state['company_info'] = company_info
        st.session_state['fa_rating_result'] = fa_rating_result
        st.session_state['technical_df'] = get_technical_data_df(df)
        st.session_state['currency_symbol'] = currency_symbol

    # ==================== 結果顯示區 ====================

    if st.session_state.get('data_ready', False):
        df = st.session_state['df']
        signal = st.session_state['signal']
        company_info = st.session_state['company_info']
        fa_rating_result = st.session_state['fa_rating_result']
        technical_df = st.session_state['technical_df']
        currency_symbol = st.session_state['currency_symbol']

        st.markdown(f"<h1>🤖 AI 趨勢分析結果：{company_info['name']} ({final_symbol_to_analyze})</h1>", unsafe_allow_html=True)
        st.caption(f"**分析週期**: {selected_period_key} | **貨幣**: {company_info['currency']} | **數據更新至**: {df.index[-1].strftime('%Y-%m-%d %H:%M')}")
        st.markdown("---")

        # ----------------- 總體評分與交易策略 -----------------
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])

        # 總體評分 (score) 
        score = signal['score']
        # 根據分數給予顏色和圖標
        if score >= 4.5:
            score_icon = "🔥🔥"
        elif score >= 1.5:
            score_icon = "📈"
        elif score <= -4.5:
            score_icon = "🥶🥶"
        elif score <= -1.5:
            score_icon = "📉"
        else:
            score_icon = " neutrality_face"

        with col1:
            st.metric(
                label="✅ 融合評分 (-5.0 ~ +5.0)",
                value=f"{score_icon} {score:.2f}",
                delta=signal['action']
            )

        with col2:
            st.metric(
                label="💡 AI交易信心指數 (0-100)",
                value=f"🎯 {int(signal['confidence'])}%",
                delta=f"當前價: {currency_symbol}{signal['current_price']:.4f}"
            )

        with col3:
            st.metric(
                label="📉 止損點 (Stop Loss)",
                value=f"{currency_symbol}{signal['stop_loss']:.4f}",
                delta=f"ATR(14): {signal['atr']:.4f}"
            )

        with col4:
            st.metric(
                label="🚀 止盈點 (Take Profit)",
                value=f"{currency_symbol}{signal['take_profit']:.4f}",
                delta=f"建議進場點: {currency_symbol}{signal['entry_price']:.4f}"
            )
        
        st.markdown("---")
        
        # ----------------- 專家意見表格 -----------------
        st.subheader("👨‍🔬 專家融合意見 (AI邏輯拆解)")
        
        # 創建表格數據
        factor_data = []
        for name, opinion in signal['expert_opinions'].items():
            # 從 opinion 中提取出顏色代碼和分數，方便格式化
            score_dict = {
                '趨勢分析 (均線)': signal['score'] * (3/signal['score']) if signal['score'] != 0 else 0, # Placeholder
                '動能分析 (RSI/Stoch)': signal['score'] * (2/signal['score']) if signal['score'] != 0 else 0, # Placeholder
                '波動分析 (MACD)': signal['score'] * (2/signal['score']) if signal['score'] != 0 else 0, # Placeholder
                'K線形態分析': signal['score'] * (1.5/signal['score']) if signal['score'] != 0 else 0, # Placeholder
            }
            # 這裡我們需要真實的單項得分，但 generate_expert_fusion_signal 中沒有直接返回
            # 為了簡化，我們只展示總分和 FA 評分
            factor_data.append([
                name.split(" ")[0].split("(")[0], # 因子名稱
                signal.get('score', 0.0) if name.startswith('趨勢分析') else 0.0, # 簡化: 這裡用總分代替
                opinion
            ])
            
        # 加上基本面評分
        factor_data.append([
            "基本面分析", 
            fa_rating / 9 * 3, # 9分制轉換為 -3~3
            fa_rating_result['Message']
        ])
        
        # 最終總分行
        factor_data.append([
            "整體融合評分", 
            signal['score'], 
            f"最終行動：**{signal['action']}** (信心指數: {int(signal['confidence'])}%)"
        ])

        factor_df = pd.DataFrame(factor_data, columns=['分析因子', '得分 (-5.0 ~ +5.0)', '結論'])
        
        # 應用樣式
        # 修正點: 使用 style_factor_score_wrapper 來應用自定義顏色到分數欄位
        styled_factor_df = factor_df.style.apply(
            style_factor_score_wrapper,
            axis=1, # 確保應用到每一行 (因為分數是針對整行結論的)
            subset=['得分 (-5.0 ~ +5.0)']
        )
        
        # 顯示表格
        st.dataframe(
            styled_factor_df,
            column_config={
                "分析因子": st.column_config.Column("分析因子", help="技術分析與基本面的評估面向"),
                "得分 (-5.0 ~ +5.0)": st.column_config.ProgressColumn(
                    "得分 (-5.0 ~ +5.0)", 
                    help="各專家給予的量化分數，分數越高代表多頭信號越強。", 
                    format="%.2f", 
                    min_value=-5.0, 
                    max_value=5.0
                ),
                "結論": st.column_config.Column("專家結論", help="AI基於指標與數據的具體判讀結果"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown(f"**詳細交易策略**: {signal['strategy']}")
        st.caption("ℹ️ **設計師提示**: 得分條顏色會根據數值自動變化，同時分數文字顏色也會被自定義樣式染色。")

        st.markdown("---")
        
        # ----------------- 完整技術指標表格 -----------------
        st.subheader(f"🔍 關鍵技術指標詳情")
        
        if not technical_df.empty:
            
            # 根據技術指標的顏色欄位應用顏色樣式
            def style_technical_color(s):
                return [s['顏色'].iloc[0]] * len(s) # 將顏色應用於整行
            
            # 移除顏色列，用於顯示
            technical_df_display = technical_df.drop(columns=['顏色'])

            # 使用 Streamlit Dataframe 內建的 column_config 替代部分 Styler 功能
            st.dataframe(
                technical_df_display,
                use_container_width=True,
                column_config={
                    "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                    "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的專業解讀"),
                }
            )
            st.caption("ℹ️ **設計師提示**: 表格顏色會根據指標的趨勢/風險等級自動變化（**紅色=多頭/強化信號**（類似低風險買入），**綠色=空頭/削弱信號**（類似高風險賣出），**橙色=中性/警告**）。")

        else:
            st.info("無足夠數據生成關鍵技術指標表格。")
        
        st.markdown("---")
        
        st.subheader(f"📊 完整技術分析圖表")
        chart = create_comprehensive_chart(df, final_symbol_to_analyze, selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          # 使用 HTML 語法來控制顏色 (橙色調：#cc6600)，改用內聯 CSS 確保生效
          st.markdown(
              """
              <h1 style='color: #cc6600; font-size: 32px; font-weight: bold;'>🚀 歡迎使用 AI 趨勢分析儀表板</h1>
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
          st.markdown("---")
          st.subheader("🛡️ AI 量化策略邏輯：")
          st.markdown("""
              - **數據來源**：Yahoo Finance (yf)
              - **核心引擎**：**專家融合模型**（趨勢、動能、波動性、K線形態、基本面）
              - **交易策略**：基於 ATR (真實平均波動範圍) 設置動態的**進場參考點、止盈(TP)與止損(SL)**。
              - **評分標準**：將複雜指標轉換為 **-5.0 到 +5.0** 的統一評分體系，分數越高代表多頭信號越強，並生成 **0-100% 信心指數**。
          """)


if __name__ == '__main__':
    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = None
    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame()
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'signal' not in st.session_state:
        st.session_state['signal'] = {}
    if 'company_info' not in st.session_state:
        st.session_state['company_info'] = {}
    if 'fa_rating_result' not in st.session_state:
        st.session_state['fa_rating_result'] = {}
    if 'technical_df' not in st.session_state:
        st.session_state['technical_df'] = pd.DataFrame()
    if 'currency_symbol' not in st.session_state:
        st.session_state['currency_symbol'] = '$'
    
    main()
