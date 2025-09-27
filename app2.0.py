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
    page_title="🤖 AI趨勢分析儀表板 📈", # 已更新分頁標題，新增 📈 圖標
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

# 🚀 您的【所有資產清單】(ALL_ASSETS_MAP) - 涵蓋美股、台股、加密貨幣、指數、ETF
# 此清單已大幅擴展，以滿足使用者對「所有股票和加密貨幣」的需求。\
ALL_ASSETS_MAP = {
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

# FULL_SYMBOLS_MAP 現在使用完整的資產清單
FULL_SYMBOLS_MAP = ALL_ASSETS_MAP


# ==============================================================================
# 🎯 新增兩層選擇的類別與熱門選項映射 (基於 FULL_SYMBOLS_MAP)
# ==============================================================================
CATEGORY_MAP = {
    # US Stocks & ETFs & Indices
    "美股 (US) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if not (c.endswith(".TW") or c.endswith("-USD") or c.startswith("^TWII"))],
    # Taiwan Stocks & ETFs & Index
    "台股 (TW) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith(".TW") or c.startswith("^TWII")],
    # Crypto
    "加密貨幣 (Crypto)": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith("-USD")],
}

# 建立第二層 Selectbox 的選項 {顯示名稱: 代碼}
CATEGORY_HOT_OPTIONS = {}
for category, codes in CATEGORY_MAP.items():
    options = {}
    # 增加排序以提升用戶體驗
    sorted_codes = sorted(codes) 
    for code in sorted_codes:
        info = FULL_SYMBOLS_MAP.get(code)
        if info:
            options[f"{code} - {info['name']}"] = code
    CATEGORY_HOT_OPTIONS[category] = options
    
    
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
# 2. 數據獲取與緩存 (Cache Optimization)
# ==============================================================================

@st.cache_data(ttl=600) 
def get_stock_data(symbol, period, interval):
    """從 YFinance 獲取歷史數據。"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty or len(df) < 50: return pd.DataFrame()
        return df.tail(500).copy()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600) 
def get_company_info(symbol):
    """獲取基本公司資訊"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 優先從 FULL_SYMBOLS_MAP 獲取中文名稱，否則使用 yfinance 的名稱
        display_name = next((data["name"] for code, data in FULL_SYMBOLS_MAP.items() if code == symbol), 
                            info.get('shortName', info.get('longName', symbol)))
        
        if '-USD' in symbol: display_name = f"{display_name} (加密貨幣)"
        pe_ratio = info.get('trailingPE', info.get('forwardPE', 'N/A'))
        return {'name': display_name, 'sector': info.get('sector', 'N/A'), 'market_cap': info.get('marketCap', 0), 'pe_ratio': pe_ratio }
    except Exception:
        return {'name': symbol, 'sector': 'N/A', 'market_cap': 0, 'pe_ratio': 'N/A'}


# ==============================================================================
# 3. 核心分析函數 (FA + TA 策略)
# ==============================================================================

# 🚩 數據處理緩存，保持穩定
@st.cache_data(ttl=3600) 
def calculate_fundamental_rating(symbol: str, years: int = 5) -> dict:
    """
    計算公司的基本面評級 (FCF + ROE + P/E)。
    【修正點：增強 ROE 數據的容錯性】
    """
    results = {
        "FCF_Rating": 0.0, "ROE_Rating": 0.0, "PE_Rating": 0.0, 
        "Combined_Rating": 0.0, "Message": ""
    }
    
    # === 修正後的非個股/難以分析的資產豁免邏輯 ===
    
    if '-USD' in symbol: # 針對加密貨幣
        results["Combined_Rating"] = 0.5
        results["Message"] = "加密貨幣無傳統基本面 (FCF/ROE/PE) 依據，FA 評級設為中性 (0.5)。分析僅依賴 TA。"
        return results
    
    # 針對台灣個股 (非指數/ETF，通常數據不完整或難以取得)
    if symbol.endswith('.TW') and not any(idx in symbol for idx in ['00', '^']): 
        # 台灣個股由於 yfinance 數據穩定性問題，一律視為中性
        results["Combined_Rating"] = 0.5
        results["Message"] = "台灣個股的基本面數據可能不完整，FA 評級設為中性 (0.5)。分析主要依賴 TA。"
        return results
        
    if any(ext in symbol for ext in ['^', '00']): # 指數/ETF
        results["Combined_Rating"] = 1.0
        results["Message"] = "指數/ETF 為分散投資，不適用個股 FA，基本面評級設為最高 (1.0)。"
        return results
    
    # === 正常的個股 FA 計算邏輯 (針對美股) ===
        
    try:
        stock = yf.Ticker(symbol)
        
        # FCF 成長評級 (權重 0.4)
        cf = stock.cashflow
        fcf_cagr = -99 
        if not cf.empty and len(cf.columns) >= 2:
            operating_cf = cf.loc['Operating Cash Flow'].dropna()
            # 確保 Capital Expenditure 存在且為數值
            capex = cf.loc['Capital Expenditure'].dropna().abs() if 'Capital Expenditure' in cf.index else pd.Series(0, index=operating_cf.index)
            
            # 確保 FCF 計算的 Series 長度一致
            common_index = operating_cf.index.intersection(capex.index)
            operating_cf = operating_cf[common_index]
            capex = capex[common_index]
            
            fcf = (operating_cf + capex).dropna() # FCF = Operating CF - CapEx
            
            num_periods = min(years, len(fcf)) - 1
            if len(fcf) >= 2 and fcf.iloc[-1] > 0 and fcf.iloc[0] > 0 and num_periods > 0:
                # 採用最近的數據作為 "現在"，最遠的數據作為 "過去"
                fcf_cagr = ((fcf.iloc[0] / fcf.iloc[-1]) ** (1 / num_periods) - 1) * 100
        
        if fcf_cagr >= 15: results["FCF_Rating"] = 1.0
        elif fcf_cagr >= 5: results["FCF_Rating"] = 0.7
        else: results["FCF_Rating"] = 0.3
        
        # ROE 資本回報效率評級 (權重 0.3)
        financials = stock.quarterly_financials
        roe_avg = 0 
        
        if not financials.empty and 'Net Income' in financials.index and 'Total Stockholder Equity' in financials.index:
            net_income = financials.loc['Net Income'].dropna()
            equity = financials.loc['Total Stockholder Equity'].dropna()
            
            # 1. 計算 ROE
            roe_series = (net_income / equity).replace([np.inf, -np.inf], np.nan)
            
            # 2. 🚩 修正：數據過濾 - 篩選掉極端異常或 0 的數據
            # 排除 ROE 接近 0 或極端值 (例如 |ROE| > 100%)
            valid_roe = roe_series[(roe_series.abs() > 0.0001) & (roe_series.abs() < 10)] 
            
            # 3. 計算近四季的平均 ROE
            if len(valid_roe) >= 4:
                roe_avg = valid_roe[:4].mean() * 100 
            elif len(valid_roe) > 0:
                # 如果少於 4 季，則用所有有效 ROE 的平均值
                roe_avg = valid_roe.mean() * 100
            else:
                roe_avg = 0 # 如果沒有任何有效數據，則設為 0

        
        if roe_avg >= 15: results["ROE_Rating"] = 1.0
        elif roe_avg >= 10: results["ROE_Rating"] = 0.7
        else: results["ROE_Rating"] = 0.3
        
        # P/E 估值評級 (權重 0.3)
        pe_ratio = stock.info.get('forwardPE') or stock.info.get('trailingPE')
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio < 15: results["PE_Rating"] = 1.0 
            elif pe_ratio < 25: results["PE_Rating"] = 0.7 
            else: results["PE_Rating"] = 0.3 
        else: results["PE_Rating"] = 0.5 

        # 綜合評級
        results["Combined_Rating"] = (results["FCF_Rating"] * 0.4) + (results["ROE_Rating"] * 0.3) + (results["PE_Rating"] * 0.3)
        
        # 🚩 修正：顯示 PE/ROE 數據時，使用更可靠的格式
        pe_display = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
        results["Message"] = f"FCF CAGR: {fcf_cagr:.2f}%. | 4季平均ROE: {roe_avg:.2f}%. | PE: {pe_display}."
        
    except Exception as e:
        results["Message"] = f"基本面計算失敗或無足夠數據: {e}"

    return results

# 🚩 數據處理緩存，保持穩定
@st.cache_data(ttl=60) 
def calculate_technical_indicators(df):
    """
    ✅ 完整技術指標計算：使用 ta 庫確保穩定性。
    (MACD, RSI, KD, ADX, ATR, 多 EMA)
    """
    if df.empty: return df
    
    # 趨勢
    df['EMA_5'] = ta.trend.ema_indicator(df['Close'], window=5, fillna=False)
    df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12, fillna=False)
    df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26, fillna=False)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50, fillna=False) 
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200, fillna=False) 
    
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14, fillna=False)
    df['ADX_pos'] = ta.trend.adx_pos(df['High'], df['Low'], df['Close'], window=14, fillna=False)
    df['ADX_neg'] = ta.trend.adx_neg(df['High'], df['Low'], df['Close'], window=14, fillna=False)
    
    # 動能
    macd_instance = ta.trend.MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9, fillna=False)
    df['MACD_Line'] = macd_instance.macd()
    df['MACD_Signal'] = macd_instance.macd_signal()
    df['MACD_Hist'] = macd_instance.macd_diff()
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14, fillna=False)
    
    # KD (Stochastic Oscillator)
    stoch_instance = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3, fillna=False)
    df['Stoch_K'] = stoch_instance.stoch()
    df['Stoch_D'] = stoch_instance.stoch_signal()

    # 波動性 (用於風控)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14, fillna=False)
    
    # 確保所有核心指標計算完成後再刪除 NaNs
    df.dropna(how='all', subset=['Close', 'EMA_50', 'MACD_Hist', 'RSI', 'ATR'], inplace=True)
    return df


# ==============================================================================
# 4. 融合決策與信號生成 (FA + TA 專注策略)
# ==============================================================================

# 🚩 數據處理緩存，保持穩定
@st.cache_data(ttl=60) 
def generate_expert_fusion_signal(df: pd.DataFrame, fa_rating: float, is_long_term: bool) -> dict:
    """
    生成融合 FA/TA 的最終交易決策、信心度與風控參數。
    Score 範圍: [-10, 10]
    """
    if df.empty or len(df) < 2:
        return {'recommendation': "數據不足，觀望", 'confidence': 50, 'score': 0, 'action': "觀望", 'atr': 0, 'entry_price': 0, 'stop_loss': 0, 'take_profit': 0, 'strategy': "N/A", 'expert_opinions': {}, 'current_price': 0, 'action_color': 'orange'}

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    current_price = latest['Close']
    
    # 🎯 基於 ATR 的精確風控參數 (R:R=2:1)
    atr = latest.get('ATR', current_price * 0.015) 
    risk_dist = 2 * atr 
    risk_reward = 2 
    
    score = 0
    strategy_label = "TA 動能策略"
    expert_opinions = {}
    FA_THRESHOLD = 0.7 
    
    # === (A) 技術分析 TA Score (權重高) ===
    
    # 1. 趨勢判斷 (EMA-200)
    is_long_term_bull = latest.get('EMA_200', -1) > 0 and current_price > latest['EMA_200']
    if is_long_term_bull: 
        score += 4
        expert_opinions['趨勢判斷 (EMA)'] = "長期牛市確立 (Price > EMA-200)"
    else:
        score = score - 1 # 趨勢不佳扣分
        expert_opinions['趨勢判斷 (EMA)'] = "長期熊市/盤整"
    
    # 2. MACD 動能轉折 (黃金/死亡交叉)
    macd_cross_buy = (latest['MACD_Line'] > latest['MACD_Signal']) and (previous['MACD_Line'] <= previous['MACD_Signal'])
    macd_cross_sell = (latest['MACD_Line'] < latest['MACD_Signal']) and (previous['MACD_Line'] >= previous['MACD_Signal'])

    if macd_cross_buy: 
        score += 3
        expert_opinions['動能轉折 (MACD)'] = "MACD 黃金交叉 (買進信號)"
    elif macd_cross_sell: 
        score -= 3
        expert_opinions['動能轉折 (MACD)'] = "MACD 死亡交叉 (賣出信號)"
    elif latest['MACD_Hist'] > 0: 
        score += 1
        expert_opinions['動能轉折 (MACD)'] = "動能柱持續增長 (> 0)"
    elif latest['MACD_Hist'] < 0: 
        score -= 1
        expert_opinions['動能轉折 (MACD)'] = "動能柱持續減弱 (< 0)"
        
    # 3. RSI 超買超賣與動能強度
    rsi = latest['RSI']
    if rsi < 30: 
        score += 2
        expert_opinions['動能強度 (RSI)'] = "嚴重超賣 (潛在反彈)"
    elif rsi > 70: 
        score -= 2
        expert_opinions['動能強度 (RSI)'] = "嚴重超買 (潛在回調)"
    elif rsi > 55: 
        score += 1
        expert_opinions['動能強度 (RSI)'] = "強勢區間"
    elif rsi < 45: 
        score -= 1
        expert_opinions['動能強度 (RSI)'] = "弱勢區間"
    
    # === (B) 基本面 FA Score (僅長線有效，作為篩選器) ===
    
    if is_long_term:
        if fa_rating >= 0.9: 
            # 只有指數/ETF 才會到 1.0，給予最高加分
            score += 3 
            expert_opinions['基本面驗證 (FA)'] = "FA 頂級評級，大幅強化多頭信心 (主要為指數/ETF)"
        elif fa_rating >= FA_THRESHOLD: 
            # 正常美股個股可能達到此區間 (0.7 ~ 0.9)
            score += 1 
            expert_opinions['基本面驗證 (FA)'] = "FA 良好評級，溫和強化多頭信心"
        elif fa_rating < FA_THRESHOLD and fa_rating > 0.6: 
            # FA 中性 (0.5)，不加分，但也不扣分，除非 TA 趨勢極差
            expert_opinions['基本面驗證 (FA)'] = "FA 中性評級 (或數據不適用)，TA 獨立分析"
        elif fa_rating < FA_THRESHOLD and score > 0: 
            # FA 差 (低於 0.3)，且 TA 鼓勵買入，則削弱 TA 信號
            score = max(0, score - 2) 
            expert_opinions['基本面驗證 (FA)'] = "FA 評級差，削弱 TA 買入信號"
    else:
        expert_opinions['基本面驗證 (FA)'] = "短期分析，FA 不參與計分"


    # === (D) 最終決策與風控設定 ===
    
    # 最終決策
    if score >= 6: recommendation, action, action_color = "高度信心買入", "買進 (Buy)", 'red'
    elif score >= 2: recommendation, action, action_color = "買入建議", "買進 (Buy)", 'red'
    elif score <= -6: recommendation, action, action_color = "高度信心賣出", "賣出 (Sell/Short)", 'green'
    elif score <= -2: recommendation, action, action_color = "賣出建議", "賣出 (Sell/Short)", 'green'
    else: recommendation, action, action_color = "觀望/中性", "觀望", 'orange'

    # 風控價格
    entry_suggestion = current_price
    if '買進' in action:
        stop_loss = current_price - risk_dist
        take_profit = current_price + (risk_dist * risk_reward)
    elif '賣出' in action:
        stop_loss = current_price + risk_dist
        take_profit = current_price - (risk_dist * risk_reward)
    else:
        # 觀望狀態下，止損止盈範圍縮小至 1 倍 ATR 
        stop_loss = current_price - atr
        take_profit = current_price + atr
    
    confidence = np.clip(50 + score * 5, 30, 95) # 將分數轉換為信心度 (30%-95% 之間)
    
    expert_opinions['最終策略與結論'] = f"{strategy_label}：{recommendation} (總量化分數: {score})"
    
    return {
        'recommendation': recommendation, 'confidence': confidence, 'score': score, 
        'current_price': current_price, 'entry_price': entry_suggestion, 
        'stop_loss': stop_loss, 'take_profit': take_profit, 'action': action, 
        'atr': atr, 'strategy': strategy_label, 'expert_opinions': expert_opinions, 'action_color': action_color
    }

# ==============================================================================
# 5. 視覺化輔助函數
# ==============================================================================

# 🚩 數據處理緩存，保持穩定
@st.cache_data(ttl=60) 
def get_technical_data_df(df):
    """
    生成專業級的 st.dataframe 視覺化表格數據。
    【顏色邏輯：紅多綠空】
    """
    if df.empty or len(df) < 1: return pd.DataFrame()

    latest = df.iloc[-1]
    close = latest.get('Close', np.nan)
    
    indicators = {
        'RSI (14)': latest.get('RSI', np.nan),
        'ADX (14)': latest.get('ADX', np.nan),
        'MACD (柱狀圖)': latest.get('MACD_Hist', np.nan),
        'EMA (5/200)': {'ema5': latest.get('EMA_5', np.nan), 'ema200': latest.get('EMA_200', np.nan)},
        'KD (K/D)': {'k': latest.get('Stoch_K', np.nan), 'd': latest.get('Stoch_D', np.nan)},
        'ATR (14)': latest.get('ATR', np.nan)
    }
    
    result_data = []

    for name, value in indicators.items():
        status, color, display_val = "N/A", "grey", "N/A"
        
        if name in ['RSI (14)', 'ADX (14)', 'MACD (柱狀圖)', 'ATR (14)']:
            if pd.isna(value): pass
            elif name == 'RSI (14)':
                # 紅色=多頭/強化: 超賣(潛在反彈), 強勢區間
                if value <= 30: status, color = "🔴 嚴重超賣 (潛在反彈)", "red"
                elif value >= 70: status, color = "🟢 嚴重超買 (潛在回調)", "green"
                elif value > 55: status, color = "🔴 強勢多頭動能", "red"
                elif value < 45: status, color = "🟢 弱勢空頭動能", "green"
                else: status, color = "🟡 中性動能", "orange"
                display_val = f"{value:.2f}"
            elif name == 'ADX (14)':
                adx_pos = latest.get('ADX_pos', 0)
                adx_neg = latest.get('ADX_neg', 0)
                if value >= 25: 
                    if adx_pos > adx_neg:
                        status, color = "🔴 趨勢強勁 (多頭佔優)", "red"
                    else:
                        status, color = "🟢 趨勢強勁 (空頭佔優)", "green"
                elif value < 20: 
                    status, color = "🟡 趨勢疲弱/盤整 (<20)", "orange"
                else: 
                    status, color = "🟡 趨勢發展中", "orange" # 介於 20-25 之間視為中性發展
                display_val = f"{value:.2f}"
            elif name == 'MACD (柱狀圖)':
                # 紅色=多頭/強化: 動能柱 > 0
                if value > 0: status, color = "🔴 多頭動能持續", "red"
                elif value < 0: status, color = "🟢 空頭動能持續", "green"
                else: status, color = "🟡 零線附近", "orange"
                display_val = f"{value:.3f}"
            elif name == 'ATR (14)':
                # ATR 是風險指標。低風險(正常/穩定) = 紅色；高風險(極高波動) = 綠色。
                if close == 0 or pd.isna(value): pass
                else:
                    volatility_ratio = value / close
                    if volatility_ratio > 0.05: status, color = "🟢 極高波動性 (高風險)", "green" 
                    elif volatility_ratio > 0.025: status, color = "🟡 高波動性 (警告)", "orange"
                    else: status, color = "🔴 正常波動性 (低風險)", "red" 
                    display_val = f"{value:.3f}"
        
        elif name == 'EMA (5/200)':
            ema5, ema200 = value['ema5'], value['ema200']
            if not pd.isna(ema5) and not pd.isna(ema200):
                # 紅色=多頭/強化: 價格 > EMA200 且 短線 > 長線
                if close > ema200 and ema5 > ema200: status, color = "🔴 長期牛市趨勢確立", "red"
                elif close < ema200 and ema5 < ema200: status, color = "🟢 長期熊市趨勢確立", "green"
                else: status, color = "🟡 趨勢不明/轉換中", "orange"
                display_val = f"{ema5:.2f} / {ema200:.2f}"
        elif name == 'KD (K/D)':
            k, d = value['k'], value['d']
            if not pd.isna(k) and not pd.isna(d):
                # 紅色=多頭/強化: 低檔超賣區(潛在反彈), K線向上
                if k < 20 or d < 20: status, color = "🔴 低檔超賣區 (潛在反彈)", "red"
                elif k > 80 or d > 80: status, color = "🟢 高檔超買區 (潛在回調)", "green"
                elif k > d: status, color = "🔴 K線向上 (多頭動能)", "red"
                else: status, color = "🟢 K線向下 (空頭動能)", "green"
                display_val = f"{k:.2f} / {d:.2f}"

        result_data.append([name, display_val, status, color])

    df_table = pd.DataFrame(result_data, columns=['技術指標', '最新值', '分析結論', '顏色'])
    df_table.set_index('技術指標', inplace=True)
    return df_table[['最新值', '分析結論', '顏色']]

# 🚩 確保圖表函數的 key 屬性與調用時一致，避免 DOM 渲染錯誤
def create_comprehensive_chart(df, symbol, period):
    """創建詳細技術分析圖表 (保持價格 K 線顏色為紅漲綠跌)"""
    if df.empty: return go.Figure()
        
    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        subplot_titles=(
            f'{symbol} 價格 & 技術分析 (時間週期: {period})', 
            'MACD (動能)', 'RSI (動能) & KD (超買超賣)', 'ADX (趨勢強度) & 方向指標', '成交量'
        ),
        row_width=[0.3, 0.1, 0.1, 0.1, 0.1]
    )
    
    # ... (圖表繪製邏輯保持不變) ...
    # 1. 主價格圖 (使用亞洲習慣：紅漲綠跌)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
        name='價格', 
        increasing_line_color='red', 
        decreasing_line_color='green' 
    ), row=1, col=1)
    
    # 移動平均線 (MAs)
    if 'EMA_5' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA_5'], name='EMA 5', line=dict(color='#FFD700', width=1)), row=1, col=1)
    if 'EMA_200' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], name='EMA 200', line=dict(color='#808080', width=2)), row=1, col=1)

    # 2. MACD (使用紅漲綠跌邏輯)
    if 'MACD_Hist' in df.columns:
        macd_hist_colors = ['red' if val >= 0 else 'green' for val in df['MACD_Hist'].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD 柱', marker_color=macd_hist_colors), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], name='MACD 線', line=dict(color='#3498DB', width=1)), row=2, col=1)
    
    # 3. RSI & KD
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#9B59B6')), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="超買 (70)", row=3, col=1) 
        fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="超賣 (30)", row=3, col=1) 
        if 'Stoch_K' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Stoch_K'], name='K 線', line=dict(color='#F39C12')), row=3, col=1)
    
    # 4. ADX 
    if 'ADX' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['ADX'], name='ADX', line=dict(color='#000000', width=2)), row=4, col=1)
        fig.add_hline(y=25, line_dash="dot", line_color="#7F8C8D", annotation_text="強趨勢線 (25)", row=4, col=1) 

    # 5. 成交量 (Volume)
    if 'Volume' in df.columns and (df['Volume'] > 0).any():
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color='#BDC3C7'), row=5, col=1)
    else:
        if len(fig.layout.annotations) > 4: 
            fig.layout.annotations[4].update(text='成交量 (此標的無數據)') 
        fig.update_yaxes(visible=False, row=5, col=1)
    
    # 更新佈局
    fig.update_layout(
        height=950, 
        showlegend=True, 
        title_text=f"📈 {symbol} - 完整技術分析圖", 
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI/KD", row=3, col=1)
    fig.update_yaxes(title_text="ADX", row=4, col=1)
    fig.update_yaxes(title_text="成交量", row=5, col=1)
    return fig


# ==============================================================================
# 6. Streamlit 應用程式主體 (Main App Logic)
# ==============================================================================

def get_currency_symbol(symbol: str) -> str:
    """根據代碼返回貨幣符號。"""
    if symbol.endswith('.TW'):
        return 'NT$'
    elif symbol.endswith('-USD') or not any(ext in symbol for ext in ['.TW', '.HK', '.SS', '.L']):
        # 預設為美元 (適用於美股和加密貨幣)
        return '$'
    # 可以擴展其他市場，例如：elif symbol.endswith('.HK'): return 'HK$'
    return '$'


def main():
    
    # 🚩 關鍵修正：將主標題替換為自定義 HTML 樣式的 st.markdown 以達到「放大」效果，並使用淡橙色 (#FFA07A)
    # 此處已更新為您請求的標題：🤖 AI 趨勢分析📈
    st.markdown("<h1 style='text-align: center; color: #FFA07A; font-size: 3.5em; padding-bottom: 0.5em;'>🤖 AI 趨勢分析📈</h1>", unsafe_allow_html=True)
    st.markdown("---") 

    # 🚩 關鍵修正：會話狀態初始化，用於控制渲染
    if 'last_search_symbol' not in st.session_state: st.session_state['last_search_symbol'] = "2330.TW" 
    if 'analyze_trigger' not in st.session_state: st.session_state['analyze_trigger'] = False
    if 'data_ready' not in st.session_state: st.session_state['data_ready'] = False


    st.sidebar.header("⚙️ 分析設定")
    
    # 初始化 Category
    if 'selected_category' not in st.session_state: 
        st.session_state['selected_category'] = list(CATEGORY_HOT_OPTIONS.keys())[0] # Default to the first category
        
    # --- 1. 選擇資產類別 (第一層 Selectbox) ---
    st.sidebar.markdown("1. 🚀 **快速選擇熱門標的 (選擇資產類別)**")
    
    selected_category = st.sidebar.selectbox(
        "選擇資產類別",
        list(CATEGORY_HOT_OPTIONS.keys()),
        key="category_select_box",
        label_visibility="collapsed"
    )
    
    # 儲存選中的類別
    st.session_state['selected_category'] = selected_category
    
    # --- 2. 選擇標的代碼 (第二層 Selectbox) ---
    st.sidebar.markdown("2. **選擇相關類型的標的代碼**")
    
    current_category_options_display = ["請選擇標的..."] + list(CATEGORY_HOT_OPTIONS[selected_category].keys())
    
    # 找出當前 symbol 是否在列表中的預設值
    current_symbol_code = st.session_state.get('last_search_symbol', "2330.TW")
    default_symbol_index = 0
    
    # Check if the last analyzed symbol belongs to the currently selected category
    for i, display_name in enumerate(current_category_options_display):
        if display_name.startswith(current_symbol_code):
             default_symbol_index = i
             break

    st.sidebar.selectbox(
        f"選擇 {selected_category} 標的",
        current_category_options_display,
        index=default_symbol_index,
        key="symbol_select_box", # 第二層 Selectbox 的 key
        on_change=update_search_input, # 新增回調函數
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    
    # --- 3. 輸入股票代碼或中文名稱 (Text Input) ---
    st.sidebar.markdown("3. 🔍 **輸入股票代碼或中文名稱**")
    
    # The value should be driven by the selectbox/callback or the last analyzed symbol
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
    
    # 當代碼變更時，觸發分析，並重設資料準備狀態
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
    analyze_button_clicked = st.sidebar.button("📊 執行專家分析", type="primary", key="main_analyze_button") 

    # === 主要分析邏輯 (Main Analysis Logic) ===
    if analyze_button_clicked or st.session_state['analyze_trigger']:
        
        # 🚩 關鍵修正：啟動分析時，將數據準備狀態設為 False
        st.session_state['data_ready'] = False
        st.session_state['analyze_trigger'] = False 
        
        try:
            with st.spinner(f"🔍 正在啟動顧問團，獲取並分析 **{final_symbol_to_analyze}** 的數據 ({selected_period_key})..."):
                
                df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval) 
                
                if df.empty:
                    # 💡 修正：如果解析結果仍是中文，顯示更準確的代碼提示
                    # 嘗試從 FULL_SYMBOLS_MAP 中找到標準代碼
                    display_symbol = final_symbol_to_analyze
                    for code, data in FULL_SYMBOLS_MAP.items():
                        if data["name"] == final_symbol_to_analyze:
                            display_symbol = code
                            break
                    
                    st.error(f"❌ **數據不足或代碼無效。** 請確認代碼 **{display_symbol}** 是否正確。")
                    st.info(f"💡 **提醒：** 台灣股票需要以 **代碼.TW** 格式輸入 (例如：**2330.TW**)。")
                    st.session_state['data_ready'] = False 
                else:
                    # 數據獲取成功，開始分析
                    company_info = get_company_info(final_symbol_to_analyze) 
                    currency_symbol = get_currency_symbol(final_symbol_to_analyze) 
                    
                    df = calculate_technical_indicators(df) 
                    fa_result = calculate_fundamental_rating(final_symbol_to_analyze)
                    analysis = generate_expert_fusion_signal(
                        df, 
                        fa_rating=fa_result['Combined_Rating'], 
                        is_long_term=is_long_term
                    )
                    
                    # 🚩 關鍵修正：將所有分析結果存入 Session State
                    st.session_state['analysis_results'] = {
                        'df': df,
                        'company_info': company_info,
                        'currency_symbol': currency_symbol,
                        'fa_result': fa_result,
                        'analysis': analysis,
                        'selected_period_key': selected_period_key,
                        'final_symbol_to_analyze': final_symbol_to_analyze
                    }
                    
                    # 🚩 關鍵修正：所有數據準備好後，將狀態設為 True
                    st.session_state['data_ready'] = True

        except Exception as e:
            st.error(f"❌ 分析 {final_symbol_to_analyze} 時發生未預期的錯誤: {str(e)}")
            st.info("💡 請檢查代碼格式或嘗試其他分析週期。")
            st.session_state['data_ready'] = False 
    
    # === 🚩 關鍵修正：使用 `if` 條件渲染整個結果區塊 ===
    if st.session_state.get('data_ready', False):
        
        # 從 Session State 中讀取分析結果
        results = st.session_state['analysis_results']
        df = results['df']
        company_info = results['company_info']
        currency_symbol = results['currency_symbol']
        fa_result = results['fa_result']
        analysis = results['analysis']
        selected_period_key = results['selected_period_key']
        final_symbol_to_analyze = results['final_symbol_to_analyze'] # 使用 state 儲存的代碼
        
        # --- 結果呈現 ---
        
        # 🎯 已移除 「專家融合分析」
        st.header(f"📈 **{company_info['name']}** ({final_symbol_to_analyze})") 
        
        # 計算漲跌幅
        current_price = analysis['current_price']
        prev_close = df['Close'].iloc[-2] if len(df) >= 2 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        price_delta_color = 'inverse' if change < 0 else 'normal'

        st.markdown(f"**分析週期:** **{selected_period_key}** | **FA 評級:** **{fa_result['Combined_Rating']:.2f}**")
        st.markdown(f"**基本面診斷:** {fa_result['Message']}")
        st.markdown("---")
        
        st.subheader("💡 核心行動與量化評分")
        
        st.markdown(
            """
            <style>
            /* 調整 MetricValue 字體大小 */
            [data-testid="stMetricValue"] { font-size: 20px; }
            /* 調整 MetricLabel 字體大小 */
            [data-testid="stMetricLabel"] { font-size: 13px; }
            /* 調整 MetricDelta 字體大小 */
            [data-testid="stMetricDelta"] { font-size: 12px; }
            /* 為核心行動建議標籤設定顏色 */
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
            st.metric("🛡️ 信心指數", f"{analysis['confidence']:.0f}%", help="分析團隊對此建議的信心度")
        
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
        
        st.subheader("📊 關鍵技術指標數據與專業判讀 (交叉驗證細節)")
        
        expert_df = pd.DataFrame(analysis['expert_opinions'].items(), columns=['專家領域', '判斷結果'])
        expert_df.loc[len(expert_df)] = ['基本面 FCF/ROE/PE 診斷', fa_result['Message']]
        
        def style_expert_opinion(s):
            is_positive = s.str.contains('牛市|買進|多頭|強化|利多|增長|頂級|良好|潛在反彈|K線向上|正常波動性', case=False)
            is_negative = s.str.contains('熊市|賣出|空頭|削弱|利空|下跌|不足|潛在回調|K線向下|極高波動性', case=False)
            is_neutral = s.str.contains('盤整|警告|中性|觀望|趨勢發展中|不適用|不完整', case=False) 
            
            colors = np.select(
                [is_negative, is_positive, is_neutral],
                ['color: #1e8449; font-weight: bold;', 'color: #cc0000; font-weight: bold;', 'color: #cc6600;'],
                default='color: #888888;'
            )
            return [f'background-color: transparent; {c}' for c in colors]

        styled_expert_df = expert_df.style.apply(style_expert_opinion, subset=['判斷結果'], axis=0)

        st.dataframe(
            styled_expert_df, 
            use_container_width=True,
            key=f"expert_df_{final_symbol_to_analyze}_{selected_period_key}",
            column_config={
                "專家領域": st.column_config.Column("專家領域", help="FA/TA 分析範疇"),
                "判斷結果": st.column_config.Column("判斷結果", help="專家對該領域的量化判讀與結論"),
            }
        )
        
        st.caption("ℹ️ **設計師提示:** 判讀結果顏色：**紅色=多頭/強化信號** (類似低風險買入)，**綠色=空頭/削弱信號** (類似高風險賣出)，**橙色=中性/警告**。")

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
    
    # 首次載入或數據未準備好時的提示
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
         st.info("請在左側選擇或輸入標的，然後點擊 **『執行專家分析』** 開始。")


if __name__ == '__main__':
    if 'last_search_symbol' not in st.session_state:
        st.session_state['last_search_symbol'] = "2330.TW"
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
        
    main()
    
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位專家的量化觀點，但**僅供教育與參考用途**。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")
