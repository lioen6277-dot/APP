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
        return df.iloc[:-1] # 移除最後一筆可能不完整的資料
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
    
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['MACD'] = ta.trend.macd_diff(df['Close'])
    df['RSI'] = ta.momentum.rsi(df['Close'])
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'])
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'])
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['Stoch_K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    
    return df

def get_technical_data_df(df):
    
    if df.empty or len(df) < 50: 
        return pd.DataFrame()

    last_row = df.iloc[-1]
    
    indicators = {}
    
    # 趨勢指標
    indicators['收盤價 vs SMA-20'] = last_row['Close']
    indicators['收盤價 vs EMA-50'] = last_row['Close']
    
    # 動能指標
    indicators['RSI (14)'] = last_row['RSI']
    indicators['Stochastics (%K)'] = last_row['Stoch_K']
    indicators['MACD 柱狀圖 (Signal)'] = last_row['MACD']
    
    # 波動性與通道
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
                color = "green" # 綠色代表潛在賣出信號/風險
            elif value < 30:
                conclusion = "強化：超賣區域，潛在反彈"
                color = "red" # 紅色代表潛在買入信號/強化
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == 'Stochastics (%K)':
            if value > 80:
                conclusion = "警告：接近超買區域"
                color = "green"
            elif value < 20:
                conclusion = "強化：接近超賣區域"
                color = "red"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == 'MACD 柱狀圖 (Signal)':
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
            avg_atr = df['ATR'].mean()
            if value > avg_atr * 1.5:
                conclusion = "警告：極高波動性"
                color = "green"
            elif value < avg_atr * 0.5:
                conclusion = "中性：低波動性"
                color = "orange"
            else:
                conclusion = "中性：正常波動性"
                color = "blue"

        elif name == '布林通道 (BB)':
            high = last_row['BB_High']
            low = last_row['BB_Low']
            range_pct = (high - low) / low
            if value > high:
                conclusion = "警告：價格位於上軌外側 (超強勢)"
                color = "red"
            elif value < low:
                conclusion = "強化：價格位於下軌外側 (超弱勢)"
                color = "green"
            else:
                conclusion = f"中性：在上下軌間 ({range_pct*100:.2f}% 寬度)"
                color = "blue"

        data.append([name, value, conclusion, color])
        
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
        if roe > 0.15:
            roe_score = 3
        elif roe > 0.08:
            roe_score = 2
        elif roe > 0:
            roe_score = 1
            
        # 估值評分 (PE)
        pe_score = 0
        if pe < 15:
            pe_score = 3
        elif pe < 25:
            pe_score = 2
        elif pe < 35:
            pe_score = 1
            
        # 現金流與償債能力
        cf_score = 0
        if freeCashFlow > 0.05 * marketCap and cash_debt_ratio > 1.5:
            cf_score = 3
        elif freeCashFlow > 0 and cash_debt_ratio > 1:
            cf_score = 2
        elif freeCashFlow > 0:
            cf_score = 1
            
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
        # st.warning(f"基本面數據獲取失敗或不適用: {e}") # Debugging
        return {
            "Combined_Rating": 1.0,
            "Message": f"基本面數據獲取失敗或不適用 (例如指數/加密貨幣)。",
            "Details": None
        }

# 【修正點 1.1: 函式名稱更新】將 'expert' 改為 'ai'
def generate_ai_fusion_signal(df, fa_rating, is_long_term=True):
    if df.empty:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'ai_opinions': {}} # 【修正點 1.2: 鍵名更新】
    
    last_row = df.iloc[-1]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    
    # 【修正點 1.3: 意見字典更新】
    ai_opinions = {}

    # 1. 趨勢AI (均線)
    trend_score = 0
    if last_row['Close'] > last_row['SMA_20'] and last_row['Close'] > last_row['EMA_50']:
        trend_score += 3
        ai_opinions['趨勢AI'] = "強勁多頭：短期(SMA-20)與中長線(EMA-50)趨勢皆向上。"
    elif last_row['Close'] > last_row['SMA_20'] or last_row['Close'] > last_row['EMA_50']:
        trend_score += 1.5
        ai_opinions['趨勢AI'] = "偏向多頭：價格位於至少一條主要均線之上。"
    else:
        trend_score -= 2
        ai_opinions['趨勢AI'] = "偏向空頭：價格位於主要均線之下，趨勢疲軟。"

    # 2. 動能AI (RSI, MACD)
    momentum_score = 0
    if last_row['RSI'] < 40 and last_row['MACD'] < 0:
        momentum_score -= 2
        ai_opinions['動能AI'] = "強勁空頭動能：RSI和MACD均顯示賣壓增強。"
    elif last_row['RSI'] > 60 and last_row['MACD'] > 0:
        momentum_score += 3
        ai_opinions['動能AI'] = "強勁多頭動能：RSI和MACD均顯示買盤強勁。"
    else:
        momentum_score += 0
        ai_opinions['動能AI'] = "中性動能：指標波動於正常區間，無明顯極端信號。"
        
    # 3. 風險AI (ATR, BB)
    risk_score = 0
    if last_row['Close'] > last_row['BB_High'] or last_row['Close'] < last_row['BB_Low']:
        risk_score -= 1 # 價格在通道外，波動極大，風險高
        ai_opinions['風險AI'] = "警告：價格已突破布林通道，極高波動性/超買超賣風險。"
    else:
        risk_score += 1
        ai_opinions['風險AI'] = "低風險：價格在布林通道內，波動正常。"

    # 4. 基本面AI (只用於中長線)
    fundamental_score = 0
    if is_long_term:
        fa_rating_val = fa_rating.get("Combined_Rating", 0)
        fundamental_score = (fa_rating_val / 9) * 4 # 權重分配
        ai_opinions['基本面AI'] = fa_rating.get("Message", "數據不足或不適用。")
    else:
        ai_opinions['基本面AI'] = "短期分析，基本面影響權重較低。"

    # 綜合評分 (總分範圍約 -4 到 10)
    total_score = trend_score + momentum_score + risk_score + fundamental_score
    
    # 根據總分決定行動
    action = "中性觀望"
    confidence = 0
    
    if total_score >= 8:
        action = "強烈買入"
        confidence = 90
    elif total_score >= 5:
        action = "買入"
        confidence = 70
    elif total_score <= -4:
        action = "強烈賣出"
        confidence = 90
    elif total_score <= -1:
        action = "賣出"
        confidence = 70
    elif total_score >= 1.5 and total_score < 5:
        action = "區間操作/謹慎買入"
        confidence = 55
    else:
        action = "中性觀望"
        confidence = 50

    # 策略建議 (基於 ATR 設定止盈/損)
    # 止盈: 價格 + 2 * ATR
    # 止損: 價格 - 1 * ATR (買入) 或 價格 + 1 * ATR (賣出)
    take_profit = current_price + 2 * atr_value
    stop_loss = current_price - 1 * atr_value
    strategy = f"入場價格約 {current_price:.2f}"
    
    if "買入" in action:
        strategy += f"，建議止盈約 {take_profit:.2f}，止損約 {stop_loss:.2f} (風險回報比約 2:1)"
    elif "賣出" in action:
        take_profit = current_price - 2 * atr_value
        stop_loss = current_price + 1 * atr_value
        strategy += f"，建議止盈約 {take_profit:.2f}，止損約 {stop_loss:.2f} (風險回報比約 2:1)"
    else:
        strategy = "暫無明確方向，建議等待信號出現或持續區間操作。"
        take_profit = 0
        stop_loss = 0

    return {
        'action': action,
        'score': total_score,
        'confidence': confidence,
        'strategy': strategy,
        'entry_price': current_price,
        'take_profit': take_profit,
        'stop_loss': stop_loss,
        'current_price': current_price,
        'ai_opinions': ai_opinions # 【修正點 1.4: 返回鍵名更新】
    }


def create_comprehensive_chart(df, symbol_name, period_key):
    """
    創建包含 K 線圖、MACD、RSI 的綜合 Plotly 圖表。
    """
    # 創建子圖: 4 行, 1 列. 高度比例: K線(4), MACD(2), RSI(1), Stoch(1)
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        row_heights=[0.6, 0.15, 0.15, 0.1],
        specs=[[{"rowspan": 1}], [{"rowspan": 1}], [{"rowspan": 1}], [{"rowspan": 1}]]
    )

    # ------------------------------------
    # Row 1: K線圖 (Candlestick)
    # ------------------------------------
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='K線',
            showlegend=False
        ), row=1, col=1
    )
    
    # 均線
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='blue', width=1), name='SMA-20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='EMA-50'), row=1, col=1)
    # 布林通道
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='red', width=0.5, dash='dash'), name='BB上軌'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='green', width=0.5, dash='dash'), name='BB下軌'), row=1, col=1)


    # ------------------------------------
    # Row 2: MACD
    # ------------------------------------
    # MACD 柱狀圖 (Histogram)
    macd_hist_color = ['red' if val >= 0 else 'green' for val in df['MACD']]
    fig.add_trace(
        go.Bar(
            x=df.index, 
            y=df['MACD'], 
            name='MACD Hist', 
            marker_color=macd_hist_color,
            showlegend=False
        ), row=2, col=1
    )
    # MACD Line & Signal Line (使用 TA 庫的預設值)
    fig.add_trace(go.Scatter(x=df.index, y=ta.trend.macd_line(df['Close']), line=dict(color='#008000', width=1), name='MACD Line', showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ta.trend.macd_signal(df['Close']), line=dict(color='#FF00FF', width=1), name='Signal Line', showlegend=False), row=2, col=1)

    # ------------------------------------
    # Row 3: RSI
    # ------------------------------------
    fig.add_trace(
        go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#A31515', width=1), name='RSI', showlegend=False), 
        row=3, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="grey", row=3, col=1, annotation_text="超買 (70)", annotation_position="top left", annotation_font_size=10)
    fig.add_hline(y=30, line_dash="dash", line_color="grey", row=3, col=1, annotation_text="超賣 (30)", annotation_position="bottom left", annotation_font_size=10)
    
    # ------------------------------------
    # Row 4: Stochastics (%K)
    # ------------------------------------
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Stoch_K'], line=dict(color='#00CED1', width=1), name='%K', showlegend=False), 
        row=4, col=1
    )
    fig.add_hline(y=80, line_dash="dot", line_color="red", row=4, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="green", row=4, col=1)

    # ------------------------------------
    # 佈局與美化
    # ------------------------------------
    fig.update_layout(
        title=f"**{symbol_name}** - 綜合技術分析 ({period_key})",
        xaxis_rangeslider_visible=False, # 隱藏底部的滑塊
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=20),
        height=700
    )
    
    # 調整 Y 軸標題
    fig.update_yaxes(title_text="價格 / 均線", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100]) # 鎖定 RSI 範圍
    fig.update_yaxes(title_text="%K", row=4, col=1, range=[0, 100]) # 鎖定 %K 範圍
    
    # 移除子圖間的 X 軸刻度，除了最後一個
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(showticklabels=False, row=3, col=1)
    
    return fig

# 【修正點 2.1: 介面著色函式】
def color_cells(row):
    """根據 DataFrame 的 '顏色' 欄位為 '最新值', '分析結論', '顏色' 欄位上色"""
    # 確保只處理有顏色的欄位
    
    # Red (多頭/強化) -> Light Red/Orange for strong signal
    if row['顏色'] == 'red':
        # 0.2 alpha for light background
        styles = ['background-color: rgba(255, 69, 0, 0.2)'] * 3 
    # Green (空頭/削弱) -> Light Green/Teal for weak signal/high risk
    elif row['顏色'] == 'green':
        styles = ['background-color: rgba(60, 179, 113, 0.2)'] * 3 
    # Orange (中性/警告) -> Light Yellow/Orange for caution
    elif row['顏色'] == 'orange':
        styles = ['background-color: rgba(255, 165, 0, 0.2)'] * 3 
    # Blue (中性/波動)
    else: 
        styles = [''] * 3
        
    return styles
# ==============================================================================
# 3. Streamlit 主函式
# ==============================================================================

def main():
    # 頁面標題與說明
    st.title("🤖 AI 趨勢分析儀表板 📈")
    st.markdown("---")

    # 側邊欄：輸入與控制區
    with st.sidebar:
        st.header("🎯 標的與時間週期選擇")
        
        # 類別選擇 (第一層)
        category_selection = st.selectbox(
            "選擇資產類別:",
            list(CATEGORY_MAP.keys())
        )
        
        # 熱門標的選擇 (第二層)
        hot_options = CATEGORY_HOT_OPTIONS.get(category_selection, {})
        selected_code_name = st.selectbox(
            "選擇熱門標的:",
            list(hot_options.keys()),
            key='hot_symbol_select'
        )
        
        # 從選擇的名稱中取出代碼
        selected_symbol = hot_options.get(selected_code_name, "")
        
        # 自由輸入框
        user_input_symbol = st.text_input(
            "或自行輸入代碼/名稱 (如 NVDA, 2330, 比特幣):",
            value=selected_symbol,
            key='user_input_symbol'
        )
        
        # 時間週期選擇
        selected_period_key = st.selectbox(
            "選擇時間週期 (影響 K 線間隔):",
            list(PERIOD_MAP.keys()),
            key='period_select'
        )
        
        st.markdown("---")
        
        # 【修正點 3.1: 按鈕名稱更新】
        analyze_button_clicked = st.button("執行 AI 分析 🚀", use_container_width=True)
        st.caption("點擊後將重新獲取數據並分析。")
        
        # 側邊欄底部提示
        st.markdown("---")
        st.info("💡 **操作提示:** \n1. 選擇類別或輸入代碼。\n2. 選擇週期。\n3. 點擊『執行 AI 分析』。")
        
    # 主頁面：顯示分析結果
    
    # 獲取代碼並處理輸入
    symbol_to_analyze = user_input_symbol if user_input_symbol else selected_symbol
    final_symbol_to_analyze = get_symbol_from_query(symbol_to_analyze)

    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = ''
        st.session_state['data_ready'] = False

    # 觸發分析邏輯 (當按鈕被點擊 或 輸入/週期有變動)
    if analyze_button_clicked or (final_symbol_to_analyze and final_symbol_to_analyze != st.session_state.get('last_search_symbol', '')):
        
        if final_symbol_to_analyze:
            with st.spinner(f"正在分析 **{final_symbol_to_analyze}** 的數據..."):
                
                # 獲取參數
                period, interval = PERIOD_MAP[selected_period_key]
                
                # 1. 獲取數據
                df = get_stock_data(final_symbol_to_analyze, period, interval)
                company_info = get_company_info(final_symbol_to_analyze)
                currency_symbol = get_currency_symbol(final_symbol_to_analyze)
                
                st.session_state['last_search_symbol'] = final_symbol_to_analyze
                st.session_state['data_ready'] = not df.empty
                st.session_state['df'] = df
                st.session_state['company_info'] = company_info
                st.session_state['selected_period_key'] = selected_period_key
                st.session_state['currency_symbol'] = currency_symbol
        
        else:
            st.warning("請在左側輸入有效的資產代碼或名稱。")
            st.session_state['data_ready'] = False
            return # 終止執行

    # 顯示結果
    if st.session_state.get('data_ready', False):
        df = st.session_state['df']
        company_info = st.session_state['company_info']
        selected_period_key = st.session_state['selected_period_key']
        currency_symbol = st.session_state['currency_symbol']
        
        # --------------------------------------------------
        # 1. 標頭與基本資訊
        # --------------------------------------------------
        col1, col2, col3 = st.columns([1, 1.5, 3])
        
        # 價格資訊 (最後一行數據)
        if not df.empty:
            last_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) >= 2 else last_price
            change_amount = last_price - prev_price
            change_percent = (change_amount / prev_price) * 100 if prev_price else 0
            
            if change_amount > 0:
                color = "green" if company_info['category'] == "美股 (US)" or company_info['category'] == "加密貨幣 (Crypto)" else "red"
                delta_str = f"▲ {change_amount:,.2f} ({change_percent:+.2f}%)"
            elif change_amount < 0:
                color = "red" if company_info['category'] == "美股 (US)" or company_info['category'] == "加密貨幣 (Crypto)" else "green"
                delta_str = f"▼ {change_amount:,.2f} ({change_percent:+.2f}%)"
            else:
                color = "gray"
                delta_str = f"± 0.00 (0.00%)"
                
            # 標題
            with col1:
                st.subheader(f"{company_info['name']} ({final_symbol_to_analyze})")
                st.metric(
                    label=f"最新價格 ({currency_symbol})",
                    value=f"{last_price:,.2f}",
                    delta=delta_str,
                    delta_color=color # Streamlit 的 color 設置是: Green(正), Red(負), Blue/Gray(中性)
                )

            with col2:
                st.markdown(f"**類別**: {company_info['category']}")
                st.markdown(f"**週期**: {selected_period_key}")
                st.markdown(f"**數據量**: {len(df)} 筆資料 (從 {df.index[0].strftime('%Y-%m-%d')} 開始)")
                
        # 2. 獲取並顯示 AI 融合信號
        df = calculate_technical_indicators(df)
        fundamental_rating = calculate_fundamental_rating(final_symbol_to_analyze)
        
        is_long_term = "日" in selected_period_key or "週" in selected_period_key or "長線" in selected_period_key
        
        # 【修正點 3.2: 呼叫函式名稱更新】
        ai_signal = generate_ai_fusion_signal(df, fundamental_rating, is_long_term)
        
        # 3. AI 綜合判讀
        with col3:
            st.subheader(f"🧠 AI 綜合分析信號")
            signal_col1, signal_col2 = st.columns(2)
            
            with signal_col1:
                # 動作信號
                if "買入" in ai_signal['action']:
                    st.markdown(f"**建議動作**: <span style='font-size: 1.5em; color: #ff4b4b;'>**{ai_signal['action']}**</span>", unsafe_allow_html=True)
                elif "賣出" in ai_signal['action']:
                    st.markdown(f"**建議動作**: <span style='font-size: 1.5em; color: #00cc00;'>**{ai_signal['action']}**</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**建議動作**: <span style='font-size: 1.5em;'>**{ai_signal['action']}**</span>", unsafe_allow_html=True)

            with signal_col2:
                # 信心度
                st.metric(
                    label="AI 信心度",
                    value=f"{ai_signal['confidence']}%",
                    delta_color="off"
                )
            
            # 策略建議
            st.markdown(f"**策略建議**: {ai_signal['strategy']}")
        
        st.markdown("---")
        
        # --------------------------------------------------
        # 2. 基本面 & AI 意見區
        # --------------------------------------------------
        fa_col, tech_col = st.columns([1, 1])

        with fa_col:
            st.subheader(f"💰 基本面分析 ({company_info.get('category', '未分類')})")
            if fundamental_rating['Details']:
                rating_color = "red" if fundamental_rating['Combined_Rating'] >= 7 else ("orange" if fundamental_rating['Combined_Rating'] >= 5 else "green")
                st.markdown(f"**綜合評級**: <span style='color: {rating_color}; font-size: 1.2em;'>**{fundamental_rating['Combined_Rating']:.1f} / 9.0**</span>", unsafe_allow_html=True)
                st.markdown(f"**AI 解讀**: {fundamental_rating['Message']}")
                st.markdown(f"**當前 P/E**: {fundamental_rating['Details'].get('trailingPE', 'N/A'):.2f}")
            else:
                st.info(f"基本面數據不適用於 {company_info.get('category', '此標的')} 或數據缺失。")


        with tech_col:
            # 【修正點 3.3: 意見標題更新】
            st.subheader("💡 綜合 AI 意見")
            ai_opinions_df = pd.DataFrame(ai_signal['ai_opinions'].items(), columns=['AI模組', '觀點'])
            
            # 使用 markdown 格式化輸出
            for index, row in ai_opinions_df.iterrows():
                 st.markdown(f"**{row['AI模組']}**: {row['觀點']}")

        st.markdown("---")
        
        # --------------------------------------------------
        # 3. 關鍵技術指標表格 (應用顏色樣式)
        # --------------------------------------------------
        
        technical_df = get_technical_data_df(df)
        if not technical_df.empty:
            st.subheader("📊 關鍵技術指標判讀")
            
            # 【修正點 2.2: 應用樣式並隱藏輔助欄位】
            # 使用 .style.apply 應用顏色函式
            styled_df = technical_df.style.apply(color_cells, axis=1, subset=['最新值', '分析結論', '顏色'])

            st.dataframe(
                styled_df,
                use_container_width=True,
                key=f"technical_df_{final_symbol_to_analyze}_{selected_period_key}",
                column_config={
                    "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                    "分析結論": st.column_config.Column("趨勢/動能判讀", help="基於數值範圍的AI解讀"),
                    "顏色": None # 隱藏用於著色的輔助欄位
                }
            )
            st.caption("ℹ️ **設計師提示:** 表格顏色會根據指標的趨勢/風險等級自動變化（**紅色=多頭/強化信號**（類似低風險買入），**綠色=空頭/削弱信號**（類似高風險賣出），**橙色=中性/警告**）。")

        else:
            st.info("無足夠數據生成關鍵技術指標表格。")
        
        st.markdown("---")
        
        # --------------------------------------------------
        # 4. 完整技術分析圖表
        # --------------------------------------------------
        st.subheader(f"📈 完整技術分析圖表")
        chart = create_comprehensive_chart(df, company_info['name'], selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")
    
    # 首次載入或數據未準備好時的提示
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          # 【修正點 3.4: 提示資訊更新】
         st.info("請在左側選擇或輸入標的，然後點擊 **『執行 AI 分析』** 開始。")

    # ==============================================================================
    # 6. 結尾聲明區 (Disclaimer) 【修正點 4.1: 新增結尾聲明】
    # ==============================================================================
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位AI的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 開發團隊")


if __name__ == '__main__':
    # Streamlit Session State 初始化，確保變數存在
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = ''
        st.session_state['data_ready'] = False
        st.session_state['df'] = pd.DataFrame()
        st.session_state['company_info'] = {}
        st.session_state['selected_period_key'] = '1 日 (中長線)'
        st.session_state['currency_symbol'] = '$'
        
    main()
