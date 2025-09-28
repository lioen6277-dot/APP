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
    """從 YFinance 獲取歷史數據，並增強魯棒性。"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        # 🚩 修正 1. 檢查核心欄位完整性
        if df.empty or 'Close' not in df.columns or len(df) < 50:
            return pd.DataFrame()

        # 🚩 修正 2. 數據清洗：前向填充 (ffill) 處理數據缺口
        # 適用於低流動性資產或盤中數據的偶發缺口
        df.ffill(inplace=True) 
        df.dropna(subset=['Close', 'Open', 'High', 'Low'], inplace=True) # 確保價格非 NaN

        return df.tail(500).copy()
    
    except Exception:
        # 捕捉 ticker 獲取失敗或 API 連線失敗等問題
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
    【修正點：增強 FCF CAGR 和 ROE 數據的容錯性】
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
        fcf_cagr = 0.0 
        
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
            
            if len(fcf) >= 2 and num_periods > 0:
                fcf_end = fcf.iloc[0] # 最新的 FCF (最近的季度/年份)
                fcf_start = fcf.iloc[-1] # 最遠的 FCF (過去的季度/年份)

                # 🚩 FCF CAGR 修正：針對 Quant 和 Financial Analyst 的魯棒性邏輯
                if fcf_start > 0 and fcf_end > 0:
                    # 情況 1: 雙方均為正 (正常 CAGR 計算)
                    fcf_cagr = ((fcf_end / fcf_start) ** (1 / num_periods) - 1) * 100
                elif fcf_start < 0 and fcf_end > 0:
                    # 情況 2: 從負轉正，視為強烈利好 (給予最高分)
                    fcf_cagr = 25.0 
                elif fcf_start < 0 and fcf_end < 0:
                    # 情況 3: 持續為負，視為利空 (給予極低分)
                    fcf_cagr = -10.0
                elif fcf_start > 0 and fcf_end < 0:
                    # 情況 4: 從正轉負，視為嚴重利空 (給予極低分)
                    fcf_cagr = -50.0 
                else: 
                    # 包含 FCF 接近 0 或數據異常，保持 0.0
                    fcf_cagr = 0.0

        
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
            
            # 2. 🚩 ROE 修正：收緊極端值過濾門檻 (Financial Analyst 標準)
            # 將極端值門檻收緊至 5.0 (500%)，排除異常數據污染
            valid_roe = roe_series[(roe_series.abs() > 0.0001) & (roe_series.abs() < 5)] 
            
            # 3. 計算近四季的平均 ROE
            if len(valid_roe) >= 4:
                # 採用最新的 4 個有效季度 ROE
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
    
    # 🚩 修正：數據前處理，確保序列連續性 (Algorithmic Trading 標準實踐)
    df.ffill(inplace=True) 
    
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
# 4. 融合決策與信號生成 (FA + TA 策略)
# ==============================================================================

# 🚩 數據處理緩存，保持穩定
@st.cache_data(ttl=60) 
def generate_expert_fusion_signal(df: pd.DataFrame, fa_rating: float, is_long_term: bool) -> dict:
    """
    生成融合 FA/TA 的最終交易決策、信心度與風控參數。
    Score 範圍: [-10, 10]
    """
    if df.empty or len(df) < 2: 
        return {'recommendation': "數據不足，觀望", 'confidence': 50, 'score': 0, 'action': "觀望", 'atr': 0, 'entry_price': 0, 'stop_loss': 0, 'take_profit': 0, 'strategy': "N/A", 'ai_opinions': {}, 'current_price': 0, 'action_color': 'orange'}
    
    # 變更: expert_opinions -> ai_opinions
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    current_price = latest['Close']
    
    # 🎯 基於 ATR 的精確風控參數 (R:R=2:1)
    atr = latest.get('ATR', current_price * 0.015) 
    risk_dist = 2 * atr # 止損距離設為 2 倍 ATR (波動性決定風險)
    risk_reward = 2 # 盈虧比設定為 2:1
    
    score = 0
    strategy_label = "TA 動能策略"
    ai_opinions = {} # 變更: expert_opinions -> ai_opinions
    FA_THRESHOLD = 0.7 
    
    # === (A) 技術分析 TA Score (權重高) ===
    
    # 1. 趨勢判斷 (EMA-200)
    is_long_term_bull = latest.get('EMA_200', -1) > 0 and current_price > latest['EMA_200']
    if is_long_term_bull:
        score += 4
        ai_opinions['趨勢判斷 (EMA)'] = "長期牛市確立 (Price > EMA-200)"
    else:
        score = score - 1 # 趨勢不佳扣分
        ai_opinions['趨勢判斷 (EMA)'] = "長期熊市/盤整"

    # 2. MACD 動能轉折 (黃金/死亡交叉)
    macd_cross_buy = (latest['MACD_Line'] > latest['MACD_Signal']) and (previous['MACD_Line'] <= previous['MACD_Signal'])
    macd_cross_sell = (latest['MACD_Line'] < latest['MACD_Signal']) and (previous['MACD_Line'] >= previous['MACD_Signal'])
    
    if macd_cross_buy:
        score += 3
        ai_opinions['動能轉折 (MACD)'] = "MACD 黃金交叉 (買進信號)"
    elif macd_cross_sell:
        score -= 3
        ai_opinions['動能轉折 (MACD)'] = "MACD 死亡交叉 (賣出信號)"
    elif latest['MACD_Hist'] > 0:
        score += 1
        ai_opinions['動能轉折 (MACD)'] = "動能柱持續增長 (> 0)"
    elif latest['MACD_Hist'] < 0:
        score -= 1
        ai_opinions['動能轉折 (MACD)'] = "動能柱持續減弱 (< 0)"

    # 3. RSI 超買超賣與動能強度
    rsi = latest['RSI']
    if rsi < 30:
        score += 2
        ai_opinions['動能強度 (RSI)'] = "嚴重超賣 (潛在反彈)"
    elif rsi > 70:
        score -= 2
        ai_opinions['動能強度 (RSI)'] = "嚴重超買 (潛在回調)"
    elif rsi > 55:
        score += 1
        ai_opinions['動能強度 (RSI)'] = "強勢區間"
    elif rsi < 45:
        score -= 1
        ai_opinions['動能強度 (RSI)'] = "弱勢區間"
        
    # === (B) 基本面 FA Score (僅長線有效，作為篩選器) ===
    if is_long_term:
        if fa_rating >= 0.9: # 只有指數/ETF 才會到 1.0，給予最高加分
            score += 3
            ai_opinions['基本面驗證 (FA)'] = "FA 頂級評級，大幅強化多頭信心 (主要為指數/ETF)"
        elif fa_rating >= FA_THRESHOLD: # 正常美股個股可能達到此區間 (0.7 ~ 0.9)
            score += 1
            ai_opinions['基本面驗證 (FA)'] = "FA 良好評級，溫和強化多頭信心"
        elif fa_rating < FA_THRESHOLD and fa_rating > 0.6: # FA 中性 (0.5)，不加分，但也不扣分
            ai_opinions['基本面驗證 (FA)'] = "FA 中性評級 (或數據不適用)，TA 獨立分析"
        elif fa_rating < FA_THRESHOLD and score > 0: # FA 差 (低於 0.3)，且 TA 鼓勵買入，則削弱 TA 信號
            score = max(0, score - 2)
            ai_opinions['基本面驗證 (FA)'] = "FA 評級差，削弱 TA 買入信號"
    else:
        ai_opinions['基本面驗證 (FA)'] = "短期分析，FA 不參與計分"
        
    # === (C) 最終決策與風控計算 (量化模型輸出) ===
    
    # 決定行動 (Action)
    if score >= 6:
        action = "強力買入"
        confidence = 90
        # 買入後，止損設在低於現價 risk_dist 處，止盈設在高於現價 (risk_dist * risk_reward) 處
        stop_loss = current_price - risk_dist
        take_profit = current_price + (risk_dist * risk_reward)
    elif score >= 2:
        action = "買入"
        confidence = 75
        stop_loss = current_price - risk_dist
        take_profit = current_price + (risk_dist * risk_reward)
    elif score <= -6:
        action = "強力賣出/放空"
        confidence = 90
        # 放空後，止損設在高於現價 risk_dist 處，止盈設在低於現價 (risk_dist * risk_reward) 處
        stop_loss = current_price + risk_dist
        take_profit = current_price - (risk_dist * risk_reward)
    elif score <= -2:
        action = "賣出/減碼"
        confidence = 75
        stop_loss = current_price + risk_dist
        take_profit = current_price - (risk_dist * risk_reward)
    else:
        action = "觀望/持倉"
        confidence = 50
        stop_loss = 0
        take_profit = 0
    
    # 風控結果格式化
    entry_price = round(current_price, 4)
    if stop_loss != 0: stop_loss = round(stop_loss, 4)
    if take_profit != 0: take_profit = round(take_profit, 4)
    
    # 根據行動設定顏色
    action_color = 'green' if '買入' in action else ('red' if '賣出' in action or '空' in action else 'orange')

    return {
        'recommendation': action,
        'confidence': confidence, 
        'score': score,
        'action': action,
        'atr': round(atr, 4),
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'strategy': strategy_label,
        'ai_opinions': ai_opinions,
        'current_price': entry_price,
        'action_color': action_color
    }

# ==============================================================================
# 5. 顯示輔助函數 (新增)
# ==============================================================================

def get_color_for_action(action):
    """根據行動返回 Streamlit markdown 顏色代碼"""
    if '買入' in action or '多' in action:
        return 'green'
    elif '賣出' in action or '空' in action:
        return 'red'
    else:
        return 'orange'

def get_technical_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成關鍵技術指標的摘要表格。
    """
    if df.empty:
        return pd.DataFrame()

    latest = df.iloc[-1]
    
    # 判斷指標趨勢和顏色
    def analyze_rsi(val):
        if val > 70: return ("超買區", '⚠️')
        if val < 30: return ("超賣區", '✅')
        if val > 50: return ("多頭強勢", '🔺')
        return ("空頭弱勢", '🔻')
    
    def analyze_macd(hist):
        if hist > 0 and hist > df.iloc[-2]['MACD_Hist']: return ("動能增強 (多)", '🔥')
        if hist > 0: return ("多頭區間", '🔺')
        if hist < 0 and hist < df.iloc[-2]['MACD_Hist']: return ("動能減弱 (空)", '💧')
        return ("空頭區間", '🔻')

    def analyze_stoch(k, d):
        if k > 80 or d > 80: return ("高檔鈍化/超買", '⚠️')
        if k < 20 or d < 20: return ("低檔鈍化/超賣", '✅')
        if k > d: return ("金叉向上", '🔺')
        return ("死叉向下", '🔻')

    def analyze_adx(adx, pos, neg):
        if adx > 25 and pos > neg: return ("趨勢強勁 (多)", '💪')
        if adx > 25 and neg > pos: return ("趨勢強勁 (空)", '💨')
        return ("趨勢微弱/盤整", '〰️')

    # 建立表格數據
    data = {
        "指標名稱": ["收盤價 (Price)", "RSI (14)", "MACD Histogram", "KD (Stoch K/D)", "ADX (14)"],
        "最新值": [
            f"{latest['Close']:.4f}",
            f"{latest['RSI']:.2f}",
            f"{latest['MACD_Hist']:.4f}",
            f"K:{latest['Stoch_K']:.2f} / D:{latest['Stoch_D']:.2f}",
            f"{latest['ADX']:.2f}"
        ],
        "分析結論": [
            f"最新價: {latest['Close']:.4f}",
            f"{analyze_rsi(latest['RSI'])[1]} {analyze_rsi(latest['RSI'])[0]}",
            f"{analyze_macd(latest['MACD_Hist'])[1]} {analyze_macd(latest['MACD_Hist'])[0]}",
            f"{analyze_stoch(latest['Stoch_K'], latest['Stoch_D'])[1]} {analyze_stoch(latest['Stoch_K'], latest['Stoch_D'])[0]}",
            f"{analyze_adx(latest['ADX'], latest['ADX_pos'], latest['ADX_neg'])[1]} {analyze_adx(latest['ADX'], latest['ADX_pos'], latest['ADX_neg'])[0]}"
        ]
    }
    
    summary_df = pd.DataFrame(data)

    # 設置顏色
    def style_row(row):
        style = [''] * len(row)
        if "超賣" in row["分析結論"] or "金叉" in row["分析結論"] or "多頭" in row["分析結論"]:
            style = ['background-color: #f7f7f7', 'color: red; font-weight: bold', 'color: red']
        elif "超買" in row["分析結論"] or "死叉" in row["分析結論"] or "空頭" in row["分析結論"]:
            style = ['background-color: #f7f7f7', 'color: green; font-weight: bold', 'color: green']
        return style
        
    # 這裡只返回 DataFrame，Streamlit 的表格會自動處理樣式
    return summary_df.set_index("指標名稱")


def create_comprehensive_chart(df: pd.DataFrame, symbol: str, period: str) -> go.Figure:
    """
    創建包含 K 線、交易量、MACD、RSI 的綜合 Plotly 圖表。
    """
    if df.empty:
        return go.Figure()
        
    # 1. 設置子圖結構: 4 行，共享 X 軸
    # K線+均線 (2.5), Volume (1), MACD (1), RSI (1)
    fig = make_subplots(rows=4, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[2.5, 1, 1, 1],
                        subplot_titles=(f'{symbol} K線圖與均線 ({period})', '成交量 (Volume)', 'MACD (12, 26, 9)', 'RSI (14)'))

    # --- Row 1: K線圖與均線 (Candlestick + EMAs) ---
    
    # A. K線圖
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'],
                                 name='K線',
                                 increasing_line_color='red', 
                                 decreasing_line_color='green'), 
                  row=1, col=1)

    # B. EMA 均線
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_12'], name='EMA 12', line=dict(color='yellow', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_26'], name='EMA 26', line=dict(color='purple', width=1)), row=1, col=1)
    if 'EMA_50' in df.columns: # 僅在日線以上顯示長期均線
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], name='EMA 50', line=dict(color='blue', width=1.5)), row=1, col=1)

    # --- Row 2: 成交量 (Volume) ---
    colors = ['red' if df['Close'][i] > df['Open'][i] else 'green' for i in range(len(df))]
    
    # 檢查 Volume 是否存在 (加密貨幣可能沒有 Volume 欄位)
    if 'Volume' in df.columns and df['Volume'].sum() > 0:
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors), row=2, col=1)
        fig.update_yaxes(title_text='Volume', row=2, col=1)
    else:
        # 如果沒有 Volume，則隱藏該行並調整標題
        fig.update_yaxes(visible=False, row=2, col=1)
        fig.update_layout(title_text=f'{symbol} K線圖與均線 ({period}) - (無交易量數據)')
        fig.layout.annotations[0].text = f'{symbol} K線圖與均線 ({period})'
        fig.layout.annotations[1].text = ' ' # 清空 Volume 標題

    # --- Row 3: MACD ---
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], name='MACD Line', line=dict(color='#007FFF', width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal Line', line=dict(color='#FF7F50', width=1.5)), row=3, col=1)
    
    # MACD Histogram 柱狀圖
    hist_colors = ['red' if h > 0 else 'green' for h in df['MACD_Hist']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram', marker_color=hist_colors), row=3, col=1)
    fig.update_yaxes(title_text='MACD', row=3, col=1)

    # --- Row 4: RSI ---
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='orange', width=1.5)), row=4, col=1)
    
    # RSI 超買/超賣線
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1, annotation_text="超買 (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1, annotation_text="超賣 (30)")
    fig.update_yaxes(title_text='RSI', range=[0, 100], row=4, col=1)
    
    # --- 全局佈局優化 ---
    fig.update_layout(
        height=900, 
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        template="plotly_white", # 更改為乾淨的白色模板
        margin=dict(l=20, r=20, t=40, b=20) # 調整邊距
    )
    
    # 隱藏非 K 線圖的 X 軸標籤
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(showticklabels=False, row=3, col=1)
    
    return fig


# ==============================================================================
# 6. Streamlit 應用程式主邏輯 (新增)
# ==============================================================================

# 🚩 1. 初始化 Session State (確保所有引用的 key 存在)
if 'sidebar_search_input' not in st.session_state:
    st.session_state.sidebar_search_input = "NVDA" 
if 'analyze_trigger' not in st.session_state:
    st.session_state.analyze_trigger = True
if 'last_search_symbol' not in st.session_state:
    st.session_state.last_search_symbol = "NVDA"
if 'data_ready' not in st.session_state:
    st.session_state.data_ready = False


# 🚩 2. 側邊欄佈局
with st.sidebar:
    st.title("🔎 標的篩選與分析設定")
    
    # 2.1. 標的類別選擇
    category_selection = st.selectbox(
        "🚀 選擇資產類別",
        options=CATEGORY_HOT_OPTIONS.keys(),
        key="asset_category_select"
    )

    # 2.2. 熱門標的選擇 (第二層)
    selected_options = ["請選擇標的..."] + list(CATEGORY_HOT_OPTIONS.get(category_selection, {}).keys())
    st.selectbox(
        "🎯 快速選擇熱門標的",
        options=selected_options,
        index=0, # 預設選中 Placeholder
        key="symbol_select_box",
        on_change=update_search_input # 變更時呼叫回調函數
    )
    
    st.markdown("---")
    
    # 2.3. 手動輸入/自動填充欄位 (使用 session state key)
    query_input = st.text_input(
        "📝 **或手動輸入 YF 代碼/名稱**",
        value=st.session_state.sidebar_search_input,
        key="manual_query_input",
        placeholder="例如: TSLA, 2330, BTC-USD",
        help="輸入 YFinance 代碼、股票中文名稱或關鍵字"
    )
    
    # 2.4. 週期選擇
    period_options = list(PERIOD_MAP.keys())
    selected_period_key = st.selectbox(
        "⏱️ **選擇分析週期**",
        options=period_options,
        index=2, # 預設選擇 1 日 (中長線)
        key="period_selection"
    )

    st.markdown("---")

    # 2.5. 分析按鈕
    analyze_button_clicked = st.button("🤖 執行 AI 綜合分析", use_container_width=True)
    
    # 2.6. 確保按鈕點擊後更新分析觸發狀態
    if analyze_button_clicked:
        # 如果手動輸入與上次不同，則更新
        if query_input != st.session_state.last_search_symbol:
            st.session_state.last_search_symbol = query_input
            st.session_state.analyze_trigger = True
        else:
            st.session_state.analyze_trigger = True # 即使相同，點擊按鈕也應觸發分析
    
    # 2.7. 隱藏的分析觸發器
    # 如果使用者只是改變了下拉選單 (on_change)，analyze_trigger 會設為 True
    # 只有當分析完成後，我們才將其重置為 False

# 🚩 3. 主頁面內容
st.title("📈 融合技術與基本面 AI 趨勢分析儀表板")
st.caption("本工具結合 FA (基本面) 與 TA (技術分析) 模型，為美股、台股、加密貨幣提供量化交易信號與風控建議。")

# 檢查是否應該觸發分析
if analyze_button_clicked or st.session_state.analyze_trigger:
    
    # 3.1. 解析最終代碼
    final_symbol_to_analyze = get_symbol_from_query(query_input)
    st.session_state.last_search_symbol = final_symbol_to_analyze
    st.session_state.analyze_trigger = False # 分析開始，重置觸發器
    st.session_state.data_ready = False
    
    period_code, interval_code = PERIOD_MAP[selected_period_key]
    
    with st.spinner(f"正在分析 {final_symbol_to_analyze} ({selected_period_key}) 的數據..."):
        
        # 3.2. 獲取數據與資訊
        df = get_stock_data(final_symbol_to_analyze, period_code, interval_code)
        company_info = get_company_info(final_symbol_to_analyze)
        
        # 3.3. 數據驗證
        if df.empty:
            st.error(f"⚠️ **數據獲取失敗或數據不足！** 請檢查代碼 **{final_symbol_to_analyze}** 是否正確，或該標的不支援 **{selected_period_key}** 週期。")
            st.session_state.data_ready = False
        else:
            st.session_state.data_ready = True
            
            # 3.4. 執行核心分析
            fa_results = calculate_fundamental_rating(final_symbol_to_analyze)
            df_with_ta = calculate_technical_indicators(df)
            
            # 判斷是否為長週期，以決定 FA 權重
            is_long_term_analysis = selected_period_key in ["1 日 (中長線)", "1 週 (長期)"]
            
            signal_results = generate_expert_fusion_signal(
                df_with_ta, 
                fa_results["Combined_Rating"], 
                is_long_term_analysis
            )

    # 3.5. 結果展示
    if st.session_state.data_ready:
        
        st.header(f"✨ {company_info['name']} ({final_symbol_to_analyze}) - 綜合分析報告")
        st.subheader(f"週期: {selected_period_key} | 最新價: ${signal_results['current_price']:.4f}")
        
        st.markdown("---")
        
        # --- A. 總結決策與風控 ---
        col1, col2, col3 = st.columns([1, 1, 1])
        
        action_color = signal_results['action_color']
        
        with col1:
            st.markdown(f"**🤖 最終決策 (AI Score: {signal_results['score']})**")
            st.markdown(f"## :{action_color}[{signal_results['recommendation']}]")
            st.caption(f"信心度: {signal_results['confidence']}%")

        with col2:
            st.metric(label="✅ **建議進場價 (最新收盤)**", value=f"${signal_results['entry_price']:.4f}")
            st.metric(label="⚠️ **ATR (波動性)**", value=f"{signal_results['atr']:.4f}")

        with col3:
            # 確保止損/止盈只有在有行動時才顯示
            sl_value = f"${signal_results['stop_loss']:.4f}" if signal_results['stop_loss'] != 0 else "N/A"
            tp_value = f"${signal_results['take_profit']:.4f}" if signal_results['take_profit'] != 0 else "N/A"
            st.metric(label="🛑 **建議止損價 (SL)**", value=sl_value)
            st.metric(label="🎯 **建議止盈價 (TP)**", value=tp_value)
        
        st.markdown(f"ℹ️ *風控策略依據最新 **ATR** (真實平均波動範圍) 計算，採用 **盈虧比 2:1**。*")
        
        st.markdown("---")

        # --- B. 分項分析細節 (使用 Expander) ---
        analysis_expander = st.expander("🔬 詳細分析與基本面/技術面評語", expanded=True)
        
        with analysis_expander:
            tab1, tab2 = st.tabs(["📊 技術面 TA 評語", "🏦 基本面 FA 數據"])
            
            with tab1:
                st.subheader("技術面 (TA) 決策分解")
                
                # 顯示 AI 決策意見
                for key, opinion in signal_results['ai_opinions'].items():
                    if "FA" not in key: # 只顯示 TA 相關意見
                        color_code = 'red' if '多頭' in opinion or '買進' in opinion else ('green' if '空頭' in opinion or '賣出' in opinion else 'orange')
                        st.markdown(f"**{key}**: :{color_code}[{opinion}]")
                
            with tab2:
                st.subheader("基本面 (FA) 評級與數據")
                st.markdown(f"**綜合評級**: :{get_color_for_action(fa_results['Combined_Rating'])}[{fa_results['Combined_Rating']:.2f} / 1.0]")
                st.markdown(f"**詳細數據**: {fa_results['Message']}")
                st.caption("FA 評級僅在長週期分析中（日/週線）作為重要權重因子。加密貨幣和台灣個股（數據不全）將使用中性評級。")
                
                st.subheader("公司資訊概覽")
                st.markdown(f"**產業/板塊**: {company_info.get('sector', 'N/A')}")
                st.markdown(f"**市值**: {company_info['market_cap']:,} (USD) / N/A")
                st.markdown(f"**P/E (TTM/Fwd)**: {company_info.get('pe_ratio', 'N/A')}")

        st.markdown("---")

        # --- C. 關鍵技術指標表格與圖表 ---
        
        st.subheader("📋 關鍵技術指標摘要")
        technical_df = get_technical_summary_df(df_with_ta)
        
        if not technical_df.empty:
            # 使用 Streamlit data_editor 呈現數據，增加視覺效果
            st.dataframe(
                technical_df,
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
        chart = create_comprehensive_chart(df_with_ta, final_symbol_to_analyze, selected_period_key) 
        
        st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")
    
    # 首次載入或數據未準備好時的提示
    elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
         # 修正: 執行專家分析 -> 執行AI分析
         st.info("請在左側選擇或輸入標的，然後點擊 **'🤖 執行 AI 綜合分析'** 按鈕，以開始分析。")

# --- 結束 ---
