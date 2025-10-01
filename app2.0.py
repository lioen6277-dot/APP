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
    page_title="AI專業趨勢分析 (APP5.0)", 
    page_icon="📈", 
    layout="wide"
)

# 週期映射：(YFinance Period, YFinance Interval)
PERIOD_MAP = { 
    "30 分": ("60d", "30m"), 
    "4 小時": ("1y", "60m"), 
    "1 日": ("5y", "1d"), 
    "1 週": ("max", "1wk")
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
    "PEPE-USD": {"name": "佩佩幣", "keywords": ["佩佩幣", "PEPE", "PEPE-USDT"]},

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
# 2. 輔助函式定義 (數據獲取與基礎資訊)
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
        return df.iloc[:-1] # 移除當前未收盤的 K 棒
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
        return {"name": name, "category": category, "currency": currency, "yf_info": yf_info}
    except:
        return {"name": symbol, "category": "未分類", "currency": "USD", "yf_info": {}}
    
@st.cache_data
def get_currency_symbol(symbol):
    currency_code = get_company_info(symbol).get('currency', 'USD')
    if currency_code == 'TWD': return 'NT$'
    elif currency_code == 'USD': return '$'
    elif currency_code == 'HKD': return 'HK$'
    else: return currency_code + ' '

# ==============================================================================
# 3. 核心分析模組 (嚴格遵循您的參數要求)
# ==============================================================================

def calculate_technical_indicators(df):
    """
    核心技術指標計算，嚴格遵循參數設定:
    EMA: 10/50/200, MACD: 8/17/9, RSI/ADX/ATR: 9
    """
    
    # 1. 進階移動平均線 (EMA)
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    
    # 2. MACD (8/17/9)
    macd_instance = ta.trend.MACD(df['Close'], window_fast=8, window_slow=17, window_sign=9)
    df['MACD_Line'] = macd_instance.macd()
    df['MACD_Signal'] = macd_instance.macd_signal()
    df['MACD'] = macd_instance.macd_diff() # 柱狀圖
    
    # 3. RSI (9)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=9)
    
    # 4. 經典布林通道 (20, 2)
    df['BB_High'] = ta.volatility.bollinger_hband(df['Close'], window=20, window_dev=2)
    df['BB_Low'] = ta.volatility.bollinger_lband(df['Close'], window=20, window_dev=2)
    
    # 5. ATR (9) - 風險控制基石
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=9)
    
    # 6. ADX (9) - 趨勢強度濾鏡
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=9)
    
    # 7. SMA 20 (用於回測基準，作為傳統指標參考)
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

            if ema_10 > ema_50 and ema_50 > ema_200:
                conclusion, color = f"**強多頭：MA 多頭排列** (10>50>200)", "red"
            elif ema_10 < ema_50 and ema_50 < ema_200:
                conclusion, color = f"**強空頭：MA 空頭排列** (10<50<200)", "green"
            elif last_row['Close'] > ema_50 and last_row['Close'] > ema_200:
                conclusion, color = f"中長線偏多：價格站上 EMA 50/200", "orange"
            else:
                conclusion, color = "中性：MA 糾結或趨勢發展中", "blue"
        
        elif 'RSI' in name:
            if value > 70:
                conclusion, color = "警告：超買區域 (70)，潛在回調", "green" 
            elif value < 30:
                conclusion, color = "強化：超賣區域 (30)，潛在反彈", "red"
            elif value > 50:
                conclusion, color = "多頭：RSI > 50，位於強勢區間", "red"
            else:
                conclusion, color = "空頭：RSI < 50，位於弱勢區間", "green"


        elif 'MACD' in name:
            if value > 0 and value > prev_row['MACD']:
                conclusion, color = "強化：多頭動能增強 (紅柱放大)", "red"
            elif value < 0 and value < prev_row['MACD']:
                conclusion, color = "削弱：空頭動能增強 (綠柱放大)", "green"
            else:
                conclusion, color = "中性：動能盤整 (柱狀收縮)", "orange"
        
        elif 'ADX' in name:
            if value >= 40:
                conclusion, color = "強趨勢：極強勢趨勢 (多或空)", "red"
            elif value >= 25:
                conclusion, color = "強趨勢：確認強勢趨勢 (ADX > 25)", "orange"
            else:
                conclusion, color = "盤整：弱勢或橫盤整理 (ADX < 25)", "blue"

        elif 'ATR' in name:
            # 衡量當前波動性與過去 30 週期平均的差異
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

# ==============================================================================
# 4. 估值分析模組 (Valuation Analysis)
# ==============================================================================

def get_valuation_analysis(info):
    """
    執行綜合估值分析，融合 P/E, P/B, PEG, 以及財務健康度 (FCF/Debt)。
    總分 10 分。
    """
    yf_info = info.get('yf_info', {})
    symbol = info.get('name')
    
    # 排除指數和加密貨幣
    if info.get('category') in ["指數", "加密貨幣 (Crypto)"]:
        return {
            "Total_Score": 0, 
            "Message": "不適用：指數或加密貨幣無標準基本面數據。",
            "Details_DF": pd.DataFrame()
        }

    # 獲取關鍵指標
    roe = yf_info.get('returnOnEquity', np.nan) 
    trailingPE = yf_info.get('trailingPE', np.nan) 
    priceToBook = yf_info.get('priceToBook', np.nan)
    freeCashFlow = yf_info.get('freeCashflow', 0) 
    totalCash = yf_info.get('totalCash', 0)
    totalDebt = yf_info.get('totalDebt', 0) 
    
    # 成長率估計 (用於 PEG) - 採用 5 年預期成長率
    try:
        growth_rate_5yr = yf_info.get('fiveYearAverageReturn', 0) * 100
        if not growth_rate_5yr or growth_rate_5yr <= 0:
             # 嘗試用分析師預期
             growth_rate_5yr = yf_info.get('earningsGrowth', 0) * 100
    except:
        growth_rate_5yr = 0
        
    
    # --- 評分邏輯 (總分 10) ---

    # 1. 成長與效率評分 (ROE) (總分 3)
    roe_score = 0
    if roe > 0.15: roe_score = 3 # 您的頂級標準
    elif roe > 0.10: roe_score = 2
    elif roe > 0: roe_score = 1

    # 2. 估值評分 (P/E & P/B) (總分 4)
    valuation_score = 0
    # P/E 評分
    if trailingPE > 0 and trailingPE < 15: valuation_score += 2 # 優秀
    elif trailingPE > 0 and trailingPE < 25: valuation_score += 1 # 良好
    
    # P/B 評分 (適用於金融、傳統行業)
    if priceToBook > 0 and priceToBook < 2: valuation_score += 2 # 優秀 (低估)
    elif priceToBook > 0 and priceToBook < 3.5: valuation_score += 1 # 良好
    
    # 3. 成長速度評分 (PEG) (總分 3)
    peg_ratio = np.nan
    peg_score = 0
    if trailingPE > 0 and growth_rate_5yr > 0:
        peg_ratio = trailingPE / growth_rate_5yr
        if peg_ratio <= 1: peg_score = 3 # 頂級 (被低估)
        elif peg_ratio <= 1.5: peg_score = 2 # 良好
        elif peg_ratio <= 2.5: peg_score = 1 # 尚可
        
    # 4. 財務健康度 (FCF/Debt) (已融入總分，不單獨計分)
    cash_debt_ratio = (totalCash / totalDebt) if totalDebt and totalDebt != 0 else np.nan 

    # 綜合總分
    total_score = roe_score + valuation_score + peg_score

    # 評級解讀
    if total_score >= 8:
        message = "頂級優異 (強護城河)：基本面極健康，估值合理甚至低估，成長性強，適合長期持有。"
    elif total_score >= 5:
        message = "良好穩健：財務結構穩固，但在估值或成長速度方面有改進空間。"
    elif total_score >= 2:
        message = "中性警示：估值偏高或存在財務壓力，需警惕風險。"
    else:
        message = "基本面較弱：財務指標不佳或數據缺失，不建議盲目進場。"

    # 輸出詳細表格
    data = [
        ["ROE (股東權益報酬率)", f"{roe*100:,.2f}%" if not np.isnan(roe) else "N/A", "效率/成長", f"要求 > 15%，當前得分 {roe_score}/3"],
        ["P/E (本益比)", f"{trailingPE:,.2f}" if not np.isnan(trailingPE) else "N/A", "估值", f"要求 < 25，已獲取 {valuation_score/4*100:.0f}% 估值分數"],
        ["P/B (股價淨值比)", f"{priceToBook:,.2f}" if not np.isnan(priceToBook) else "N/A", "估值", ""],
        ["PEG (成長型估值)", f"{peg_ratio:,.2f}" if not np.isnan(peg_ratio) else "N/A", "成長性", f"要求 < 1.5，當前得分 {peg_score}/3 (基於 5年成長率 {growth_rate_5yr:.2f}%)"],
        ["FCF / 總負債", f"Ratio {cash_debt_ratio:,.2f}" if not np.isnan(cash_debt_ratio) else "N/A", "財務健康度", f"自由現金流{'(正)' if freeCashFlow > 0 else '(負)'}，要求比率 > 1"]
    ]
    details_df = pd.DataFrame(data, columns=['指標名稱', '數值', '類別', '分析結論']).set_index('指標名稱')
    
    return { "Total_Score": total_score, "Message": message, "Details_DF": details_df, "fa_normalized_score": total_score / 10 * 6 }

# ==============================================================================
# 5. 綜合判斷模組 (Comprehensive Judgment)
# ==============================================================================

def generate_expert_fusion_signal(df, fa_normalized_score, currency_symbol="$"):
    """
    融合了精確的技術分析標準、估值評分，並納入了 ATR R:R 2:1 的風險管理策略。
    fa_normalized_score: 已經正規化為 0-6 分的 FA 評分。
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
    
    # 1. 均線交叉與排列專家 (MA Cross & Alignment) - 總分 3.5
    ma_score = 0
    ema_10 = last_row['EMA_10']
    ema_50 = last_row['EMA_50']
    ema_200 = last_row['EMA_200']
    
    prev_10_above_50 = prev_row['EMA_10'] > prev_row['EMA_50']
    curr_10_above_50 = ema_10 > ema_50
    
    if not prev_10_above_50 and curr_10_above_50:
        ma_score = 3.5 # 黃金交叉
        expert_opinions['趨勢分析 (MA 交叉)'] = "**🚀 黃金交叉 (GC)**：EMA 10 向上穿越 EMA 50，強勁看漲信號！"
    elif prev_10_above_50 and not curr_10_above_50:
        ma_score = -3.5 # 死亡交叉
        expert_opinions['趨勢分析 (MA 交叉)'] = "**💀 死亡交叉 (DC)**：EMA 10 向下穿越 EMA 50，強勁看跌信號！"
    elif ema_10 > ema_50 and ema_50 > ema_200:
        ma_score = 2.0 # 強多頭排列 (10 > 50 > 200)
        expert_opinions['趨勢分析 (MA 排列)'] = "強勢多頭排列：**10 > 50 > 200**，趨勢結構穩固。"
    elif ema_10 < ema_50 and ema_50 < ema_200:
        ma_score = -2.0 # 強空頭排列
        expert_opinions['趨勢分析 (MA 排列)'] = "強勢空頭排列：**10 < 50 < 200**，趨勢結構崩潰。"
    elif curr_10_above_50:
        ma_score = 1.0
        expert_opinions['趨勢分析 (MA 排列)'] = "多頭：EMA 10 位於 EMA 50 之上。"
    else:
        ma_score = -1.0
        expert_opinions['趨勢分析 (MA 排列)'] = "空頭：EMA 10 位於 EMA 50 之下。"

    # 2. 動能專家 (RSI 9) - 總分 2.0
    momentum_score = 0
    rsi = last_row['RSI']
    if rsi > 70:
        momentum_score = -2.0 
        expert_opinions['動能分析 (RSI 9)'] = "警告：RSI > 70，極度超買，潛在回調壓力大。"
    elif rsi < 30:
        momentum_score = 2.0
        expert_opinions['動能分析 (RSI 9)'] = "強化：RSI < 30，極度超賣，潛在反彈空間大。"
    elif rsi > 50:
        momentum_score = 1.0
        expert_opinions['動能分析 (RSI 9)'] = "多頭：RSI > 50 中軸，維持在強勢區域。"
    else:
        momentum_score = -1.0
        expert_opinions['動能分析 (RSI 9)'] = "空頭：RSI < 50 中軸，維持在弱勢區域。"

    # 3. 趨勢強度專家 (MACD 8/17/9 & ADX 9) - 總分 3.0
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
    
    # ADX 確認
    if adx_value > 25: 
        strength_score *= 1.5 # 趨勢強度大於 25 時，強化信號
        expert_opinions['趨勢強度 (ADX 9)'] = f"**確認強趨勢**：ADX {adx_value:.2f} > 25，信號有效性高。"
    else:
        expert_opinions['趨勢強度 (ADX 9)'] = f"盤整：ADX {adx_value:.2f} < 25，信號有效性降低。"

    # 4. 融合評分 (納入 FA Score) - 技術面總分約 8.5
    fusion_score = ma_score + momentum_score + strength_score + fa_normalized_score # FA 佔 0-6 分

    # 最終行動
    action = "觀望 (Neutral)"
    if fusion_score >= 8.0:
        action = "強力買進 (Strong Buy)"
    elif fusion_score >= 4.0:
        action = "買進 (Buy)"
    elif fusion_score >= 1.0:
        action = "中性偏買 (Hold/Buy)"
    elif fusion_score <= -8.0:
        action = "強力賣出 (Strong Sell/Short)"
    elif fusion_score <= -4.0:
        action = "賣出 (Sell/Short)"
    elif fusion_score <= -1.0:
        action = "中性偏賣 (Hold/Sell)"
        
    # 信心指數 (MAX_SCORE = 14.5, roughly)
    MAX_SCORE = 15
    confidence = min(100, max(0, 50 + (fusion_score / MAX_SCORE) * 50))
    
    # 風險控制與交易策略 (R:R 2:1 的原則)
    risk_multiple = 2.0 # 使用 2.0 ATR 作為風險單位
    reward_multiple = 2.0 # 追求 2:1 的回報風險比
    entry_buffer = atr_value * 0.3 # 允許 0.3 ATR 的緩衝
    
    entry, stop_loss, take_profit = current_price, 0, 0
    strategy_desc = "當前信號不明確，建議觀望。"
    
    if action in ["強力買進 (Strong Buy)", "買進 (Buy)", "中性偏買 (Hold/Buy)"]:
        entry = current_price - entry_buffer
        stop_loss = entry - (atr_value * risk_multiple)
        take_profit = entry + (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議在 **{currency_symbol}{entry:.2f}** 附近尋找支撐或等待回調進場。風險回報比 2:1。"
    
    elif action in ["強力賣出 (Strong Sell/Short)", "賣出 (Sell/Short)", "中性偏賣 (Hold/Sell)"]:
        entry = current_price + entry_buffer
        stop_loss = entry + (atr_value * risk_multiple)
        take_profit = entry - (atr_value * risk_multiple * reward_multiple)
        strategy_desc = f"基於{action}信號，建議在 **{currency_symbol}{entry:.2f}** 附近尋找阻力或等待反彈做空。風險回報比 2:1。"


    expert_opinions['綜合估值評分'] = f"基本面綜合評分：{fa_normalized_score:.1f}/6.0。{fa_normalized_score/6*100:.0f}% 的分數強化了信號。"

    return {
        'action': action, 
        'score': round(fusion_score, 2), 
        'confidence': round(confidence, 1), 
        'strategy': strategy_desc, 
        'entry_price': round(entry, 2), 
        'take_profit': round(take_profit, 2), 
        'stop_loss': round(stop_loss, 2), 
        'current_price': round(current_price, 2), 
        'expert_opinions': expert_opinions, 
        'atr': round(atr_value, 4)
    }

# ==============================================================================
# 6. 圖表繪製與回測 (保持不變)
# ==============================================================================

def plot_candlestick_and_indicators(df, symbol):
    """
    繪製 K 線圖、EMA (10, 50, 200) 和布林通道。
    增加 MACD, RSI, ADX 三個子圖。
    """
    df_plot = df.dropna(subset=['EMA_200', 'MACD', 'RSI', 'ADX']).copy()
    if df_plot.empty:
        st.warning("數據不足，無法繪製圖表 (至少需要 200 週期數據來計算長線 EMA)。")
        return None

    fig = make_subplots(
        rows=5, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        row_heights=[0.5, 0.1, 0.1, 0.1, 0.1]
    )

    # 1. 主圖：K線, EMA, BB
    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot['Open'],
        high=df_plot['High'],
        low=df_plot['Low'],
        close=df_plot['Close'],
        name='K線',
        showlegend=True,
        increasing_line_color='#FF5733', # 紅色 (多頭)
        decreasing_line_color='#3399FF' # 藍色 (空頭)
    ), row=1, col=1)

    # 均線
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA_10'], line=dict(color='#FFEB3B', width=1.2), name='EMA 10'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA_50'], line=dict(color='#FF5733', width=1.5), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA_200'], line=dict(color='#000000', width=2), name='EMA 200'), row=1, col=1) # 濾鏡線

    # 布林通道
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BB_High'], line=dict(color='grey', width=0.5, dash='dash'), name='BB High'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BB_Low'], line=dict(color='grey', width=0.5, dash='dash'), name='BB Low', fill='none'), row=1, col=1)


    # 2. 交易量
    colors = ['#FF5733' if df_plot['Open'].iloc[i] < df_plot['Close'].iloc[i] else '#3399FF' for i in range(len(df_plot))]
    fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'], name='交易量', marker_color=colors, opacity=0.5, showlegend=False), row=2, col=1)

    # 3. MACD
    fig.add_trace(go.Bar(
        x=df_plot.index, y=df_plot['MACD'], 
        name='MACD', 
        marker_color=['#FF5733' if val >= 0 else '#3399FF' for val in df_plot['MACD']],
        showlegend=False
    ), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MACD_Signal'], line=dict(color='#FF0000', width=1), name='Signal', showlegend=False), row=3, col=1)
    
    # 4. RSI
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI'], line=dict(color='#00CC00', width=1.5), name='RSI', showlegend=False), row=4, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="grey", row=4, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)
    
    # 5. ADX
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ADX'], line=dict(color='purple', width=1.5), name='ADX', showlegend=False), row=5, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color="red", row=5, col=1) # 強趨勢分界線

    # 佈局設置
    title = f"<b>{symbol} - 價格與技術分析圖表</b>"
    fig.update_layout(
        title=title, 
        xaxis_rangeslider_visible=False, 
        hovermode="x unified",
        height=1000, 
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=20)
    )
    
    # 調整子圖標籤
    fig.update_yaxes(title_text='價格/BB/EMA', row=1, col=1, fixedrange=False)
    fig.update_yaxes(title_text='成交量', row=2, col=1, fixedrange=True)
    fig.update_yaxes(title_text='MACD', row=3, col=1, fixedrange=False)
    fig.update_yaxes(title_text='RSI(9)', row=4, col=1, fixedrange=True)
    fig.update_yaxes(title_text='ADX(9)', row=5, col=1, fixedrange=True)

    return fig

def run_backtest(df, initial_capital=100000, commission_rate=0.001):
    """
    執行基於 SMA 20 / EMA 50 交叉的簡單回測。
    策略: 黃金交叉買入 (做多)，死亡交叉清倉 (賣出)。
    """
    
    if df.empty or len(df) < 51:
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "數據不足 (少於 51 週期) 或計算錯誤。"}

    data = df.copy()
    
    # 黃金/死亡交叉信號
    # 假設 EMA_50 是長期均線, SMA_20 是中期均線 (作為經典 MA 交叉測試)
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
    
    capital_series = pd.Series(capital, index=data.index)
    
    if len(capital_series) < 2:
        max_drawdown = 0
    else:
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

# ==============================================================================
# 7. Streamlit 應用程式主邏輯
# ==============================================================================

def display_main_app():
    # --- 側邊欄輸入控制 ---
    st.sidebar.title("📈 參數設定與標的選擇")
    
    # 初始化 Session State
    if 'last_search_symbol' not in st.session_state: st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state: st.session_state['data_ready'] = False
    if 'sidebar_search_input' not in st.session_state: st.session_state['sidebar_search_input'] = "2330.TW"
    if 'category_selection' not in st.session_state: st.session_state['category_selection'] = "台股 (TW) - 個股/ETF/指數"
        
    def update_symbol_from_category(category):
        # 當類別改變時，更新熱門選項中的第一個作為預設值
        first_option = next(iter(CATEGORY_HOT_OPTIONS.get(category, {}).values()), "")
        if first_option:
            st.session_state['sidebar_search_input'] = first_option
            st.session_state['data_ready'] = False

    st.session_state['category_selection'] = st.sidebar.selectbox(
        "1. 選擇資產類別", 
        list(CATEGORY_MAP.keys()),
        index=list(CATEGORY_MAP.keys()).index(st.session_state['category_selection']),
        key='category_select',
        on_change=lambda: update_symbol_from_category(st.session_state['category_select'])
    )

    hot_options = CATEGORY_HOT_OPTIONS.get(st.session_state['category_selection'], {})
    
    selected_option_key = st.selectbox(
        "快速選擇熱門標的",
        list(hot_options.keys()),
        key='hot_select',
        index=list(hot_options.keys()).index(next((k for k, v in hot_options.items() if v == st.session_state['sidebar_search_input']), list(hot_options.keys())[0]))
    )
    st.session_state['sidebar_search_input'] = hot_options.get(selected_option_key, st.session_state['sidebar_search_input'])
    
    st.sidebar.text_input(
        "2. 或手動輸入代碼/名稱",
        value=st.session_state['sidebar_search_input'], 
        key='search_query_input'
    )
    
    # 決定最終要查詢的代碼
    symbol_to_query = get_symbol_from_query(st.session_state['search_query_input'])
    st.sidebar.info(f"最終代碼: **{symbol_to_query}**")
    
    selected_period_key = st.sidebar.selectbox(
        "3. 選擇分析週期",
        list(PERIOD_MAP.keys()),
        index=2 # 預設為 1 日
    )
    period, interval = PERIOD_MAP[selected_period_key]

    analyze_button_clicked = st.sidebar.button("📊 執行AI分析", type="primary")

    # --- 主內容區塊 ---
    if analyze_button_clicked or (st.session_state['data_ready'] and symbol_to_query == st.session_state['last_search_symbol']):
        
        st.session_state['last_search_symbol'] = symbol_to_query
        
        # 1. 數據獲取
        with st.spinner(f"正在分析 {symbol_to_query} - {selected_period_key} 數據..."):
            
            info = get_company_info(symbol_to_query)
            st.title(f"AI趨勢分析報告 - {info['name']} ({symbol_to_query})")
            st.markdown(f"**資產類別**：{info['category']} | **貨幣**：{info['currency']} | **分析週期**：{selected_period_key}")
            
            df = get_stock_data(symbol_to_query, period, interval)
            
            if df.empty or len(df) < 200:
                st.error(f"⚠️ 抱歉，無法獲取 {symbol_to_query} 數據或數據不足 200 週期，無法進行精準長線分析。請嘗試更長期的週期 (如 1 週)。")
                st.session_state['data_ready'] = False
                return

            # 2. 指標計算與分析
            df = calculate_technical_indicators(df)
            tech_df = get_technical_data_df(df)
            
            # 3. 估值分析
            fa_results = get_valuation_analysis(info)
            fa_score = fa_results['Total_Score']
            fa_normalized_score = fa_results.get('fa_normalized_score', 0)
            
            # 4. 綜合判斷與策略生成
            fusion_results = generate_expert_fusion_signal(df, fa_normalized_score, get_currency_symbol(symbol_to_query))

            st.session_state['data_ready'] = True
            
            # --- 報告輸出 ---
            
            # A. 綜合判斷 (最重要)
            st.markdown("---")
            st.header("🎯 I. 綜合判斷 (Comprehensive Judgment)")
            
            # 顏色映射
            action_color_map = {
                "強力買進 (Strong Buy)": "green", "買進 (Buy)": "green", "中性偏買 (Hold/Buy)": "orange",
                "觀望 (Neutral)": "blue", 
                "強力賣出 (Strong Sell/Short)": "red", "賣出 (Sell/Short)": "red", "中性偏賣 (Hold/Sell)": "orange",
                "數據不足": "grey"
            }
            action_color = action_color_map.get(fusion_results['action'], "grey")

            col_action, col_score, col_conf = st.columns(3)
            with col_action:
                st.metric("**AI 建議行動**", fusion_results['action'])
            with col_score:
                st.metric("**綜合分數 (總分 14.5)**", f"{fusion_results['score']}", delta_color="off")
            with col_conf:
                st.metric("**決策信心指數**", f"{fusion_results['confidence']:.1f}%")

            st.markdown(f"#### 💡 專家交易策略建議")
            st.markdown(f"**當前價格**: {get_currency_symbol(symbol_to_query)}{fusion_results['current_price']:.2f}")
            st.markdown(f"**策略說明**: **{fusion_results['strategy']}**")
            
            
            # 輸出詳細交易參數 (使用卡片)
            st.markdown("##### 風控參數 (基於 R:R 2:1 & ATR 9)")
            col_entry, col_tp, col_sl, col_atr = st.columns(4)
            currency_sym = get_currency_symbol(symbol_to_query)
            
            if fusion_results['entry_price'] > 0:
                col_entry.metric("建議進場點", f"{currency_sym}{fusion_results['entry_price']:.2f}")
                col_tp.metric("目標價 (TP)", f"{currency_sym}{fusion_results['take_profit']:.2f}", delta=f"R:R 2:1")
                col_sl.metric("止損價 (SL)", f"{currency_sym}{fusion_results['stop_loss']:.2f}", delta=f"風險單位 {fusion_results['atr']*2:.2f}")
            else:
                 col_entry.info("無明確交易信號")
                 col_tp.info("-")
                 col_sl.info("-")

            col_atr.metric("ATR (9)", f"{currency_sym}{fusion_results['atr']:.4f}", delta_color="off")

            
            st.markdown("##### 🔑 專家觀點詳解")
            opinion_data = [[k, v] for k, v in fusion_results['expert_opinions'].items()]
            opinion_df = pd.DataFrame(opinion_data, columns=['專家面向', '分析結論']).set_index('專家面向')
            st.dataframe(opinion_df, use_container_width=True)

            # B. 技術分析
            st.markdown("---")
            st.header("📈 II. 技術分析 (Technical Analysis)")
            st.subheader(f"週期：{selected_period_key} (EMA 10/50/200, MACD 8/17/9, RSI/ADX 9)")
            
            # 顯示判讀結果
            st.dataframe(tech_df.style.applymap(lambda x: 'background-color: #ffeaea' if '紅' in x or '買' in x or '強多' in x else ('background-color: #eafafa' if '綠' in x or '賣' in x or '強空' in x else ''), subset=['分析結論']), use_container_width=True)
            
            # 繪製圖表
            fig = plot_candlestick_and_indicators(df, symbol_to_query)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            # C. 估值分析
            st.markdown("---")
            st.header("📊 III. 估值分析 (Valuation Analysis)")
            st.subheader(f"綜合估值評分: {fa_score}/10.0 ({fa_results['Message']})")
            
            st.dataframe(fa_results['Details_DF'], use_container_width=True)


            # D. 量化回測
            st.markdown("---")
            st.header("🤖 IV. 量化回測 (Quantitative Backtest)")
            
            backtest_results = run_backtest(df)
            
            if backtest_results['total_trades'] > 0:
                
                col_bt_1, col_bt_2, col_bt_3, col_bt_4 = st.columns(4)
                
                col_bt_1.metric("**總回報率**", f"{backtest_results['total_return']:.2f}%", delta_color="normal")
                col_bt_2.metric("**勝率**", f"{backtest_results['win_rate']:.2f}%", delta_color="off")
                col_bt_3.metric("**最大回撤**", f"{backtest_results['max_drawdown']:.2f}%", delta_color="inverse")
                col_bt_4.metric("**交易次數**", f"{backtest_results['total_trades']}")
                
                st.info(f"回測策略：**MA 交叉 (SMA 20/EMA 50)**。{backtest_results['message']}")
                
                # 繪製資金曲線
                fig_capital = go.Figure()
                fig_capital.add_trace(go.Scatter(x=backtest_results['capital_curve'].index, y=backtest_results['capital_curve'], mode='lines', name='資金曲線'))
                fig_capital.update_layout(title='回測資金曲線', height=400, template="plotly_white")
                st.plotly_chart(fig_capital, use_container_width=True)
                
            else:
                st.warning(backtest_results['message'])


    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
          # 使用 HTML 語法來控制顏色 (橙色調：#cc6600)，改用內聯 CSS 確保生效
          st.markdown(
              """
              <h1 style='color: #cc6600; font-size: 32px; font-weight: bold;'>🚀 歡迎使用 AI 趨勢分析 APP5.0</h1>
              """, 
              unsafe_allow_html=True
          )
          
          st.info("請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 **『📊 執行AI分析』** 按鈕開始。")
          
          st.markdown("---")
          
          st.subheader("📝 V5.0 專業化升級：")
          st.markdown("1. **嚴格參數**: 技術指標 (MACD 8/17/9, RSI 9, ADX 9, EMA 10/50/200) 嚴格遵循專業配置。")
          st.markdown("2. **估值模組**: 新增 **估值分析 (Valuation)**，融合 P/E, P/B, PEG 等多因子評分。")
          st.markdown("3. **風險管理**: **綜合判斷** 中納入 ATR 風險控制與 **R:R 2:1** 交易策略建議。")
          
          st.markdown("---")
          
          st.subheader("📝 使用步驟：")
          st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
          st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
          st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分`、`1 日`、`1 周`）。")
          # 🔥 修正：將顏色改為 #ff9933
          st.markdown(f"4. **執行分析**：點擊 <span style='color: #ff9933; font-weight: bold;'>『📊 執行AI分析』**</span>，AI將融合基本面與技術面指標提供交易策略。", unsafe_allow_html=True)
          
          st.markdown("---")


if __name__ == '__main__':
    display_main_app()

