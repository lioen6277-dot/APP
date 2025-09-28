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
# 此清單已大幅擴展，以滿足使用者對「所有股票和加密貨幣」的需求。
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
        # 此處更新 session state 是正確的，因為 st.text_input 不再使用 value 參數
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
        if fa_rating >= 0.9: # 只有指數/ETF 才會到 1.0，給予最高加分
            score += 3
            expert_opinions['基本面驗證 (FA)'] = "FA 頂級評級，大幅強化多頭信心 (主要為指數/ETF)"
        elif fa_rating >= FA_THRESHOLD: # 正常美股個股可能達到此區間 (0.7 ~ 0.9)
            score += 1
            expert_opinions['基本面驗證 (FA)'] = "FA 良好評級，溫和強化多頭信心"
        elif fa_rating < FA_THRESHOLD and fa_rating > 0.6: # FA 中性 (0.5)，不加分，但也不扣分，除非 TA 趨勢極差
            expert_opinions['基本面驗證 (FA)'] = "FA 中性評級 (或數據不適用)，TA 獨立分析"
        elif fa_rating < FA_THRESHOLD and score > 0: # FA 差 (低於 0.3)，且 TA 鼓勵買入，則削弱 TA 信號
            score = max(0, score - 2)
            expert_opinions['基本面驗證 (FA)'] = "FA 評級差，削弱 TA 買入信號"
    else:
        expert_opinions['基本面驗證 (FA)'] = "短期分析，FA 不參與計分"
        
    # === (D) 最終決策與風控設定 ===
    
    # 最終決策
    if score >= 6:
        recommendation, action, action_color = "高度信心買入", "買進 (Buy)", 'red'
    elif score >= 2:
        recommendation, action, action_color = "買入建議", "買進 (Buy)", 'red'
    elif score <= -6:
        recommendation, action, action_color = "高度信心賣出", "賣出 (Sell/Short)", 'green'
    elif score <= -2:
        recommendation, action, action_color = "賣出建議", "賣出 (Sell/Short)", 'green'
    else:
        recommendation, action, action_color = "觀望/中性", "觀望", 'orange'
        
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
        'recommendation': recommendation,
        'confidence': confidence,
        'score': score,
        'current_price': current_price,
        'entry_price': entry_suggestion,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'action': action,
        'atr': atr,
        'strategy': strategy_label,
        'expert_opinions': expert_opinions,
        'action_color': action_color
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
                if value <= 30: 
                    status, color = "🔴 嚴重超賣 (潛在反彈)", "red"
                elif value >= 70:
                    status, color = "🟢 嚴重超買 (潛在回調)", "green"
                elif value > 55:
                    status, color = "🔴 強勢多頭動能", "red"
                elif value < 45:
                    status, color = "🟢 弱勢空頭動能", "green"
                else:
                    status, color = "🟡 中性動能", "orange"
                display_val = f"{value:.2f}"
            
            elif name == 'ADX (14)':
                adx_pos = latest.get('ADX_pos', 0)
                adx_neg = latest.get('ADx_neg', 0)
                
                if value >= 25:
                    if adx_pos > adx_neg:
                        status, color = f"🔴 強勢趨勢 (多頭)", "red"
                    else:
                        status, color = f"🟢 強勢趨勢 (空頭)", "green"
                elif value < 20:
                    status, color = "🟡 盤整或趨勢微弱", "orange"
                else:
                    status, color = "🟡 趨勢形成中", "orange"
                display_val = f"{value:.2f}"
                
            elif name == 'MACD (柱狀圖)':
                if value > 0: 
                    status, color = "🔴 多頭動能增強", "red"
                elif value < 0:
                    status, color = "🟢 空頭動能增強", "green"
                else:
                    status, color = "🟡 動能中性", "orange"
                display_val = f"{value:.4f}"
                
            elif name == 'ATR (14)':
                # ATR 主要用於風控參考，顏色不代表方向
                status, color = "🔵 波動性指標", "blue"
                display_val = f"{value:.4f}"
            
            result_data.append([name, display_val, status, color])
            
        elif name == 'EMA (5/200)':
            ema5, ema200 = value['ema5'], value['ema200']
            if pd.isna(ema5) or pd.isna(ema200) or pd.isna(close):
                 result_data.append([name, "N/A", "數據不足", "grey"])
                 continue
                 
            # 5日 EMA 判斷
            if close > ema5:
                status5, color5 = "🔴 短期強勢", "red"
            else:
                status5, color5 = "🟢 短期弱勢", "green"
                
            # 200日 EMA 判斷
            if close > ema200:
                status200, color200 = "🔴 長期牛市", "red"
            else:
                status200, color200 = "🟢 長期熊市", "green"
                
            result_data.append(['EMA (5日)', f"{ema5:.4f}", status5, color5])
            result_data.append(['EMA (200日)', f"{ema200:.4f}", status200, color200])

        elif name == 'KD (K/D)':
            k, d = value['k'], value['d']
            if pd.isna(k) or pd.isna(d):
                 result_data.append([name, "N/A", "數據不足", "grey"])
                 continue

            # 判斷 K/D 交叉
            prev_k = df['Stoch_K'].iloc[-2]
            prev_d = df['Stoch_D'].iloc[-2]
            
            status_kd = "🟡 中性"
            color_kd = "orange"
            
            if k > d and prev_k <= prev_d:
                status_kd = "🔴 KD 黃金交叉 (買進)"
                color_kd = "red"
            elif k < d and prev_k >= prev_d:
                status_kd = "🟢 KD 死亡交叉 (賣出)"
                color_kd = "green"
            elif k >= 80 and d >= 80:
                status_kd = "🟢 嚴重超買區 (賣出警告)"
                color_kd = "green"
            elif k <= 20 and d <= 20:
                status_kd = "🔴 嚴重超賣區 (買進警告)"
                color_kd = "red"
            
            result_data.append(['KD (K值)', f"{k:.2f}", status_kd, color_kd])
            result_data.append(['KD (D值)', f"{d:.2f}", "參考 K 值", "grey"])


    final_df = pd.DataFrame(result_data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    final_df = final_df.drop(columns=['顏色']) # Streamlit 的 dataframe 不支持直接傳入顏色
    
    # 創建一個 CSS/HTML 樣式函數 (使用 markdown 模擬顏色)
    # 這裡將使用 Streamlit 的 st.dataframe 預設樣式，無法直接應用自定義顏色。
    # 為了保持功能性，先返回 DataFrame，樣式提示會在 markdown 中提供。
    
    return final_df

@st.cache_data(ttl=60) 
def create_comprehensive_chart(df: pd.DataFrame, symbol: str, selected_period: str):
    """
    創建包含 K 線、MACD、RSI 的綜合 Plotly 圖表。
    """
    if df.empty or len(df) < 50:
        return go.Figure().add_annotation(
            text="無足夠數據顯示圖表", 
            xref="paper", yref="paper", 
            x=0.5, y=0.5, 
            showarrow=False, 
            font=dict(size=20)
        )
        
    # 1. 創建子圖結構
    # 比例: K線(4), MACD(2), RSI(1)
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.02, 
        row_heights=[0.6, 0.2, 0.2]
    )

    # 2. K線圖 (Row 1)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線',
        showlegend=False,
        increasing_line_color='red', # 上漲 K 線顏色
        decreasing_line_color='green' # 下跌 K 線顏色
    ), row=1, col=1)

    # 均線 (EMA) - 5, 12, 26, 200
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_5'], line=dict(color='orange', width=1), name='EMA-5'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_12'], line=dict(color='purple', width=1), name='EMA-12'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_26'], line=dict(color='brown', width=1), name='EMA-26'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='blue', width=2, dash='dot'), name='EMA-200 (多空分界線)'), row=1, col=1)

    # 3. MACD (Row 2)
    # MACD Line
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='blue', width=1.5), name='MACD Line'), row=2, col=1)
    # Signal Line
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='orange', width=1.5, dash='dash'), name='Signal Line'), row=2, col=1)
    # Histogram
    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['MACD_Hist'], 
        name='MACD 柱',
        marker_color=['red' if h >= 0 else 'green' for h in df['MACD_Hist']], # 根據正負設置顏色
        opacity=0.6,
        showlegend=False
    ), row=2, col=1)


    # 4. RSI (Row 3)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
    # 劃定超買/超賣區
    fig.add_hline(y=70, line_dash="dash", line_color="green", opacity=0.8, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="red", opacity=0.8, row=3, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="grey", opacity=0.5, row=3, col=1)

    # 5. 更新佈局
    fig.update_layout(
        title=f'{symbol} - AI 趨勢分析圖表 ({selected_period})',
        title_x=0.5,
        hovermode="x unified",
        xaxis=dict(rangeslider_visible=False), # 隱藏底部的範圍滑塊
        yaxis1=dict(title='價格', domain=[0.4, 1.0]),
        yaxis2=dict(title='MACD', domain=[0.2, 0.4]),
        yaxis3=dict(title='RSI', domain=[0.0, 0.2]),
        height=700,
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 確保 K 線圖的 X 軸不顯示日期，避免重複
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    # 僅在最後的 RSI 圖上顯示日期
    fig.update_xaxes(showticklabels=True, row=3, col=1)
    
    return fig

# ==============================================================================
# 6. 主應用程式邏輯
# ==============================================================================

def main():
    
    # 🚩 關鍵修正：會話狀態初始化，用於控制渲染
    if 'last_search_symbol' not in st.session_state: st.session_state['last_search_symbol'] = "2330.TW" 
    # NEW FIX: Explicitly initialize the key for the text input widget 💥
    if 'sidebar_search_input' not in st.session_state: st.session_state['sidebar_search_input'] = st.session_state['last_search_symbol']
    if 'analyze_trigger' not in st.session_state: st.session_state['analyze_trigger'] = False
    if 'data_ready' not in st.session_state: st.session_state['data_ready'] = False
    if 'category_select_box' not in st.session_state: st.session_state['category_select_box'] = list(CATEGORY_MAP.keys())[0]
    if 'symbol_select_box' not in st.session_state: st.session_state['symbol_select_box'] = "請選擇標的..."
    
    
    # 側邊欄佈局
    st.sidebar.title("🛠️ 分析參數設定")
    
    # --- 1. 時間週期選擇 ---
    st.sidebar.markdown("1. ⏳ **選擇分析時間週期**")
    selected_period_key = st.sidebar.selectbox(
        "選擇週期",
        options=list(PERIOD_MAP.keys()),
        index=2, # 預設選擇 '1 日 (中長線)'
        key="period_select_box",
        label_visibility="collapsed"
    )
    
    # --- 2. 快速選擇 (兩層 Selectbox) ---
    st.sidebar.markdown("2. 🚀 **快速選擇熱門標的**")
    
    # 第一層：類別選擇
    category_options = list(CATEGORY_MAP.keys())
    selected_category = st.sidebar.selectbox(
        "選擇類別",
        options=category_options,
        key="category_select_box",
        label_visibility="collapsed"
    )
    
    # 第二層：標的選擇 (使用 on_change callback 來更新 Text Input)
    hot_options_list = ["請選擇標的..."] + list(CATEGORY_HOT_OPTIONS[selected_category].keys())
    st.sidebar.selectbox(
        "選擇標的",
        options=hot_options_list,
        key="symbol_select_box",
        on_change=update_search_input, # 關鍵：選擇後更新 Text Input 的值
        label_visibility="collapsed"
    )
    
    # --- 3. 輸入股票代碼或中文名稱 (Text Input) ---
    st.sidebar.markdown("3. 🔍 **輸入股票代碼或中文名稱**")
    
    # 💥 FIX: 移除 'value' 參數，避免 Streamlit 報錯
    # "The widget with key "sidebar_search_input" was created with a default value but also had its value set via the Session State API."
    # Streamlit 會自動從 st.session_state['sidebar_search_input'] 讀取初始值。
    selected_query = st.sidebar.text_input(
        "🔍 輸入股票代碼或中文名稱", 
        placeholder="例如：AAPL, 台積電, 廣達, BTC-USD", 
        key="sidebar_search_input", # 關鍵：使用 key 讓 Streamlit 管理狀態
        label_visibility="collapsed"
    )
    
    # --- 4. 分析按鈕 ---
    analyze_button_clicked = st.sidebar.button("🤖 啟動 AI 分析", type="primary", use_container_width=True, key="analyze_button")
    
    # 核心分析邏輯
    if analyze_button_clicked or st.session_state.get('analyze_trigger', False):
        
        # 0. 重置觸發器並解析標的
        if st.session_state.get('analyze_trigger', False):
             st.session_state.analyze_trigger = False # 重置自動觸發器
             
        # 解析用戶輸入的代碼
        final_symbol_to_analyze = get_symbol_from_query(st.session_state.sidebar_search_input)
        
        # 1. 獲取數據
        with st.spinner(f"正在分析 {final_symbol_to_analyze} 的數據... 請稍候 (約 5-15 秒)"):
            period, interval = PERIOD_MAP[selected_period_key]
            
            # a. 獲取股價歷史數據
            df = get_stock_data(final_symbol_to_analyze, period, interval)
            
            # b. 獲取公司基本資訊
            company_info = get_company_info(final_symbol_to_analyze)
        
        # 檢查數據是否有效
        if df.empty:
            st.error(f"❌ 錯誤：無法獲取 {final_symbol_to_analyze} 的歷史數據。請檢查代碼是否正確，或此標的數據在 Yahoo Finance 上不可用。")
            st.session_state['data_ready'] = False
            return # 終止執行

        # 數據獲取成功，開始分析
        st.session_state['data_ready'] = True
        st.session_state['last_search_symbol'] = final_symbol_to_analyze # 儲存最後一次成功分析的代碼

        # 2. 基本面 (FA) 和技術面 (TA) 計算
        is_long_term_analysis = selected_period_key in ["1 日 (中長線)", "1 週 (長期)"]
        fa_results = calculate_fundamental_rating(final_symbol_to_analyze)
        df = calculate_technical_indicators(df)
        
        # 3. 融合決策與信號生成
        fusion_signal = generate_expert_fusion_signal(
            df, 
            fa_rating=fa_results['Combined_Rating'], 
            is_long_term=is_long_term_analysis
        )
        
        # --- 顯示結果 ---
        st.header(f"📈 {company_info['name']} ({final_symbol_to_analyze}) - {selected_period_key} AI 趨勢分析")
        st.markdown(f"**市場/板塊:** {company_info['sector']} | **市值:** {'${:,.0f}'.format(company_info['market_cap']) if company_info['market_cap'] > 0 else 'N/A'} | **當前 PE:** {company_info['pe_ratio']}")
        st.markdown("---\n")
        
        # 顯示 AI 最終決策
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # 總體趨勢判讀 (圓形圖)
            st.metric(
                label="總體趨勢信心度 (0-100%)", 
                value=f"{fusion_signal['confidence']:.0f}%", 
                delta=f"分數: {fusion_signal['score']}",
                delta_color='off'
            )
            
        with col2:
            st.metric(
                label="✅ 最終建議", 
                value=fusion_signal['action'],
                delta=fusion_signal['recommendation'],
                delta_color=fusion_signal['action_color']
            )

        with col3:
            st.markdown(f"**🔬 FA 基本面摘要:** {fa_results['Message']}")
            st.markdown(f"**📊 TA 策略摘要:** {fusion_signal['expert_opinions'].get('最終策略與結論', fusion_signal['strategy'])}")

        st.markdown("\n---\n")
        
        # 交易策略與風險控制建議
        st.subheader(f"🛡️ 交易策略與風控建議 (基於 ATR)")
        
        col_risk_1, col_risk_2, col_risk_3, col_risk_4 = st.columns(4)
        
        current_price = fusion_signal['current_price']
        
        col_risk_1.metric("當前價格", f"{current_price:.2f}")
        col_risk_2.metric("建議入場價", f"{fusion_signal['entry_price']:.2f}", delta_color='off')
        
        # 止損/止盈顯示顏色
        sl_color = 'green' if '買進' in fusion_signal['action'] else ('red' if '賣出' in fusion_signal['action'] else 'off')
        tp_color = 'red' if '買進' in fusion_signal['action'] else ('green' if '賣出' in fusion_signal['action'] else 'off')
        
        # 觀望狀態下，不顯示 delta
        if fusion_signal['action'] == '觀望':
            sl_delta, tp_delta = 'N/A', 'N/A'
            sl_color, tp_color = 'off', 'off'
        else:
            sl_delta = f"{fusion_signal['stop_loss'] - current_price:.2f}"
            tp_delta = f"{fusion_signal['take_profit'] - current_price:.2f}"
            
        
        col_risk_3.metric("🚨 建議止損價 (SL)", f"{fusion_signal['stop_loss']:.2f}", delta=sl_delta, delta_color=sl_color)
        col_risk_4.metric("💰 建議止盈價 (TP)", f"{fusion_signal['take_profit']:.2f}", delta=tp_delta, delta_color=tp_color)
        
        st.caption(f"ℹ️ **風險提示:** 此策略基於 {fusion_signal['atr']:.4f} ATR 計算。止損距離為 2x ATR，止盈距離為 4x ATR (風險報酬比 1:2)。")
        
        st.markdown("---\n")
        
        # 詳細技術指標表格
        st.subheader(f"📋 關鍵技術指標評估 (最新數據)")
        technical_df = get_technical_data_df(df)
        
        if not technical_df.empty:
            st.dataframe(
                technical_df,
                hide_index=True,
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
         st.info("請在左側選擇或輸入標的，然後點擊「🤖 啟動 AI 分析」按鈕開始分析。")

if __name__ == "__main__":
    main()
