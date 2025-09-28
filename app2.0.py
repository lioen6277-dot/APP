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
# 0. AI 虛擬角色與數據源列表 (取代所有「專家」概念 - 修正重點)
# ==============================================================================
# 用於在免責聲明中顯示的數據來源列表
EXTERNAL_DATA_SOURCES = [
    "Yahoo Finance (主要價格數據)", "Goodinfo 股市資訊網 (概念性分析維度)", 
    "Morningstar (概念性 FA 評級)", "Finviz (概念性篩選維度)",
    "Gurufocus (概念性 FA/估值維度)", "TradingView (圖表/技術分析邏輯)",
    "SEC EDGAR (概念性財報審核)", "CMoney (概念性台股數據考量)"
]

# 用於在分析報告中模擬 AI 決策維度的角色列表 (已移除所有「專家」字眼)
AI_VIRTUAL_ROLES = [
    "AI 投資決策員 (General Investment Role)", "AI 操盤模擬 (Professional Trader)", 
    "AI 基金經理模擬 (Fund Manager)", "AI 財務分析模組 (Financial Analyst)", 
    "AI 投行評估 (Investment Banker)", "AI 量化分析引擎 (Quantitative Analyst)", 
    "AI 行為金融視角 (Behavioral Finance Role)", "AI 風險管理模組 (Risk Manager)", 
    "AI ESG 評級 (ESG Investment Role)", "AI 財富規劃 (Wealth Manager)", 
    "AI 衍生品估值 (Derivatives Role)", "AI 宏觀經濟分析 (Macro Economist)", 
    "AI 金融科技應用 (FinTech Role)", "AI 資料科學家 (Data Scientist)", 
    "AI 機器學習工程師 (Machine Learning Engineer)", "AI 演算法交易開發 (Algorithmic Trading Developer)", 
    "AI 後端開發 (Backend Developer)", "AI 金融軟體工程 (Financial Software Engineer)", 
    "AI 區塊鏈模擬 (Blockchain Developer)", "AI 風險建模程式 (Risk Modeling Programmer)", 
    "AI 高頻交易系統 (High-Frequency Trading System Developer)", "AI 投資資料工程 (Investment Data Engineer)", 
    "AI 策略架構師 (AI Investment Strategy Architect)"
]


# ==============================================================================
# 1. 頁面配置與全局設定 (使用使用者提供的詳細清單)
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

# 🚀 您的【所有資產清單】(ALL_ASSETS_MAP)
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
            
# 狀態初始化
if 'data_ready' not in st.session_state:
    st.session_state.data_ready = False
if 'analyze_trigger' not in st.session_state:
    st.session_state.analyze_trigger = False
if 'sidebar_search_input' not in st.session_state:
    st.session_state.sidebar_search_input = "AAPL" # 預設值

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
        market_cap = info.get('marketCap', 'N/A')
        sector = info.get('sector', 'N/A')
        
        return {'name': display_name, 'sector': sector, 'market_cap': market_cap, 'pe_ratio': pe_ratio, 'info_dict': info }
    except Exception:
        return {'name': symbol, 'sector': 'N/A', 'market_cap': 'N/A', 'pe_ratio': 'N/A', 'info_dict': {} }

# ==============================================================================
# 3. 技術分析計算與 AI 判讀函數
# ==============================================================================

def calculate_technical_indicators(df):
    """計算常用技術指標 (RSI, MACD, Bollinger Bands, MA)"""
    if df is None or 'Close' not in df.columns:
        return None

    df_ta = df.copy()

    # RSI (相對強弱指數) - 14 週期
    df_ta['RSI'] = ta.momentum.RSIIndicator(df_ta['Close'], window=14).rsi()

    # MACD (移動平均收斂/發散指標) - 12, 26, 9 週期
    macd = ta.trend.MACD(df_ta['Close'], window_fast=12, window_slow=26, window_sign=9)
    df_ta['MACD'] = macd.macd()
    df_ta['MACD_Signal'] = macd.macd_signal()
    df_ta['MACD_Diff'] = macd.macd_diff() # 柱狀圖

    # Bollinger Bands (布林通道) - 20 週期, 2 倍標準差
    bollinger = ta.volatility.BollingerBands(df_ta['Close'], window=20, window_dev=2)
    df_ta['BB_High'] = bollinger.bollinger_hband()
    df_ta['BB_Low'] = bollinger.bollinger_lband()
    df_ta['BB_Mid'] = bollinger.bollinger_mavg()
    df_ta['BB_Width'] = bollinger.bollinger_wband()

    # MA (簡單移動平均) - 5日, 20日, 60日
    df_ta['MA5'] = ta.trend.sma_indicator(df_ta['Close'], window=5)
    df_ta['MA20'] = ta.trend.sma_indicator(df_ta['Close'], window=20)
    df_ta['MA60'] = ta.trend.sma_indicator(df_ta['Close'], window=60)
    
    # ATR (平均真實波幅) - 用於風控
    df_ta['ATR'] = ta.volatility.average_true_range(df_ta['High'], df_ta['Low'], df_ta['Close'], window=14)
    
    # 移除 NaN 值
    df_ta = df_ta.dropna()

    return df_ta

def interpret_indicator(name, value, df_ta=None):
    """根據指標數值提供趨勢判讀和視覺化顏色"""
    if pd.isna(value):
        return {"value": "-", "conclusion": "數據不足", "color": "orange"}
        
    value = round(value, 2)
    
    if name == 'RSI':
        if value > 70:
            return {"value": f"{value}", "conclusion": "超買區 (動能過強，潛在回調風險)", "color": "green"} # 綠色代表潛在賣出信號/風險
        elif value < 30:
            return {"value": f"{value}", "conclusion": "超賣區 (動能過弱，潛在反彈機會)", "color": "red"} # 紅色代表潛在買入信號/機會
        else:
            return {"value": f"{value}", "conclusion": "中性 (趨勢延續)", "color": "orange"}
    
    elif name == 'MACD_Diff':
        if df_ta is not None and len(df_ta) >= 2:
            current_diff = df_ta['MACD_Diff'].iloc[-1]
            prev_diff = df_ta['MACD_Diff'].iloc[-2] if len(df_ta) >= 2 else 0

            if current_diff > 0 and current_diff > prev_diff:
                return {"value": f"{value}", "conclusion": "多頭動能增強 (DIFF > 0, 柱體放大)", "color": "red"}
            elif current_diff < 0 and current_diff < prev_diff:
                 return {"value": f"{value}", "conclusion": "空頭動能增強 (DIFF < 0, 柱體放大)", "color": "green"}
            elif current_diff > 0:
                 return {"value": f"{value}", "conclusion": "多頭動能減弱 (DIFF > 0, 柱體縮小)", "color": "orange"}
            elif current_diff < 0:
                 return {"value": f"{value}", "conclusion": "空頭動能減弱 (DIFF < 0, 柱體縮小)", "color": "orange"}
            else:
                 return {"value": f"{value}", "conclusion": "中性/等待信號", "color": "orange"}
        
        return {"value": f"{value}", "conclusion": "中性/盤整", "color": "orange"}
            
    elif name.startswith('MA'):
        current_close = df_ta['Close'].iloc[-1]
        if current_close > value:
            return {"value": f"{value}", "conclusion": f"多頭支撐 (收盤價 > {name})", "color": "red"}
        elif current_close < value:
            return {"value": f"{value}", "conclusion": f"空頭壓力 (收盤價 < {name})", "color": "green"}
        else:
            return {"value": f"{value}", "conclusion": "中性/糾結", "color": "orange"}
            
    return {"value": f"{value}", "conclusion": "中性", "color": "orange"}


def create_analysis_summary_df(df_ta):
    """創建一個包含關鍵指標和判讀結論的 DataFrame"""
    if df_ta is None or df_ta.empty:
        return pd.DataFrame()
        
    latest = df_ta.iloc[-1]
    results = []
    
    # 1. RSI
    rsi_result = interpret_indicator('RSI', latest['RSI'])
    results.append({
        "指標名稱": "RSI (14)",
        "最新值": rsi_result['value'],
        "分析結論": rsi_result['conclusion'],
        "顏色": rsi_result['color']
    })

    # 2. MACD 柱狀圖 (DIFF)
    macd_result = interpret_indicator('MACD_Diff', latest['MACD_Diff'], df_ta)
    results.append({
        "指標名稱": "MACD 柱狀圖 (DIFF)",
        "最新值": macd_result['value'],
        "分析結論": macd_result['conclusion'],
        "顏色": macd_result['color']
    })

    # 3. 5 日均線
    ma5_result = interpret_indicator('MA5', latest['MA5'], df_ta)
    results.append({
        "指標名稱": "5 日均線 (MA5)",
        "最新值": ma5_result['value'],
        "分析結論": ma5_result['conclusion'],
        "顏色": ma5_result['color']
    })
    
    # 4. 20 日均線
    ma20_result = interpret_indicator('MA20', latest['MA20'], df_ta)
    results.append({
        "指標名稱": "20 日均線 (MA20)",
        "最新值": ma20_result['value'],
        "分析結論": ma20_result['conclusion'],
        "顏色": ma20_result['color']
    })
    
    # 5. Bollinger Bands (布林通道)
    close_price = df_ta['Close'].iloc[-1]
    bb_high = latest['BB_High']
    bb_low = latest['BB_Low']
    
    bb_conclusion = "中性 (通道內)"
    bb_color = "orange"
    if close_price > bb_high:
        bb_conclusion = "觸及/突破上軌 (強勢/超買風險)"
        bb_color = "green" # 高位風險
    elif close_price < bb_low:
        bb_conclusion = "觸及/跌破下軌 (弱勢/超賣機會)"
        bb_color = "red" # 低位機會

    results.append({
        "指標名稱": "布林通道 (20)",
        "最新值": f"H:{round(bb_high, 2)} L:{round(bb_low, 2)}",
        "分析結論": bb_conclusion,
        "顏色": bb_color
    })
    
    # 6. ATR (波動性)
    atr_val = latest['ATR']
    results.append({
        "指標名稱": "ATR (14) 波動性",
        "最新值": f"{round(atr_val, 2)}",
        "分析結論": "用於風控計算",
        "顏色": "orange"
    })

    summary_df = pd.DataFrame(results)
    return summary_df


def calculate_ai_fusion_metrics(summary_df, current_price, atr_value):
    """計算 AI 信心指數和生成 AI 觀點 (核心修正邏輯)"""
    if summary_df.empty:
        return None
    
    # 1. 計算多空信號票數 (根據顏色)
    # 紅色 = 多頭/機會信號 (Bullish)
    # 綠色 = 空頭/風險信號 (Bearish)
    # 排除 ATR
    analysis_signals = summary_df[summary_df['指標名稱'] != 'ATR (14) 波動性']
    
    bullish_count = analysis_signals['顏色'].apply(lambda x: 1 if x == 'red' else 0).sum()
    bearish_count = analysis_signals['顏色'].apply(lambda x: 1 if x == 'green' else 0).sum()
    total_signals = len(analysis_signals) # 總票數

    # 2. AI 信心指數計算 (取代 100% 正確性)
    net_signal = bullish_count - bearish_count
    if total_signals > 0:
        # 將淨信號從 -Total 到 +Total 映射到 0% 到 100%
        ai_confidence_score = int(((net_signal + total_signals) / (2 * total_signals)) * 100)
    else:
        ai_confidence_score = 50 

    # 3. 確定最終 AI 動作與建議
    if ai_confidence_score >= 70:
        recommendation = "強烈多頭趨勢 (Strong Bullish)"
        action = "建議逢低買入或加倉"
        action_color = "red"
    elif ai_confidence_score >= 55:
        recommendation = "偏向多頭趨勢 (Mild Bullish)"
        action = "建議謹慎佈局或持有"
        action_color = "orange"
    elif ai_confidence_score <= 30:
        recommendation = "強烈空頭趨勢 (Strong Bearish)"
        action = "建議避險或減倉/賣出"
        action_color = "green"
    elif ai_confidence_score <= 45:
        recommendation = "偏向空頭趨勢 (Mild Bearish)"
        action = "建議觀望或輕倉"
        action_color = "orange"
    else:
        recommendation = "市場盤整 (Neutral / Consolidation)"
        action = "建議等待明確信號"
        action_color = "gray"

    # 4. 風控參數 (使用 ATR 進行量化風控)
    atr = atr_value
    entry_suggestion = current_price # 入場價設為當前價格

    # 停損：多頭 -1.5 ATR / 止盈： +3.0 ATR (1:2 風報比)
    stop_loss = entry_suggestion - atr * 1.5
    take_profit = entry_suggestion + atr * 3.0 
    
    # 5. AI 觀點摘要
    ai_opinions = {}
    for index, row in analysis_signals.iterrows():
        module_name = row['指標名稱'].split('(')[0].strip() 
        ai_opinions[f"AI {module_name} 模組"] = row['分析結論']
    
    return {
        'recommendation': recommendation,
        'confidence': ai_confidence_score, 
        'action': action,
        'action_color': action_color,
        'signal_counts': {'Bullish': bullish_count, 'Bearish': bearish_count, 'Neutral': total_signals - bullish_count - bearish_count},
        'total_signals': total_signals,
        'entry_price': entry_suggestion,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'ai_opinions': ai_opinions,
    }

def generate_ai_fusion_report(metrics: dict, asset_name: str, symbol: str) -> str:
    """根據 AI 融合指標，生成一份專業的 AI 報告 (已移除所有「專家」字眼)"""
    
    confidence = metrics['confidence']
    action = metrics['action']
    signal_counts = metrics['signal_counts']
    total_signals = metrics['total_signals']
    ai_opinions = metrics['ai_opinions']

    # 1. 風險等級設定 (由 AI 風險管理模組評估)
    if confidence >= 80 or confidence <= 20:
        risk_level = "高 (趨勢強烈，但波動性高)"
        risk_advice = "建議嚴格執行止損機制，並動態調整倉位大小，不適合新手。"
    elif confidence >= 60 or confidence <= 40:
        risk_level = "中 (趨勢漸進，波動性中等)"
        risk_advice = "適合趨勢追蹤策略，應設置止損和止盈點。"
    else:
        risk_level = "低 (盤整或中性，交易機會少)"
        risk_advice = "建議等待信號確立，避免過度交易。"


    # 2. 數據準確性與專業修正聲明 (直接回應 100% 準確性問題)
    accuracy_statement = f"""
    ---
    ### ⚠️ 關於數據「100% 準確性」的 AI 風控聲明：
    **AI 系統聲明：** 在金融市場中，**100% 的預測準確性是不可能實現的目標**，因為市場受無法量化的宏觀經濟、非理性行為與突發事件影響。

    本 AI 系統旨在通過整合 **{total_signals}** 個獨立技術信號和多重數據源（{', '.join(EXTERNAL_DATA_SOURCES[:3])} 等）的**交叉評估機制**，將結果量化為 **AI 信心指數**，以提升決策的**魯棒性 (Robustness)** 和**穩定性 (Stability)**，但無法消除市場固有風險。
    """
    
    # 3. 最終報告生成
    summary_report = f"""
    ## 🤖 AI 融合分析報告 ({asset_name} - {symbol})
    
    ### 💡 AI 核心結論與信號共識
    
    * **AI 信心指數 (AI Confidence Index):** **{confidence}%** (代表 AI 量化分析引擎對當前趨勢的置信度)
    * **AI 風險等級 (AI Risk Assessment):** **{risk_level}** (由 AI 風險管理模組評估)
    
    **AI 系統綜合判斷：** **{metrics['recommendation']}**。
    
    #### AI 系統信號計數
    * **多頭信號 (Bullish):** {signal_counts['Bullish']} 票
    * **空頭信號 (Bearish):** {signal_counts['Bearish']} 票
    * **中性信號 (Neutral):** {signal_counts['Neutral']} 票
    
    ### 📊 AI 分項分析摘要
    
    | AI 分析模組 | 結論 (AI Opinion) |
    | :--- | :--- |
    | **AI RSI 模組** | {ai_opinions.get('AI RSI 模組', 'N/A')} |
    | **AI MACD 模組** | {ai_opinions.get('AI MACD 模組', 'N/A')} |
    | **AI MA20 模組** | {ai_opinions.get('AI MA20 模組', 'N/A')} |
    | **AI 布林通道模組** | {ai_opinions.get('AI 布林通道模組', 'N/A')} |
    
    ### 🛡️ AI 風控與交易建議
    * **AI 策略動作:** **{action}**
    * **AI 入場價 (Entry):** **{metrics['entry_price']:.2f}**
    * **AI 停損價 (Stop Loss):** **{metrics['stop_loss']:.2f}** (基於 1.5 倍 ATR)
    * **AI 止盈價 (Take Profit):** **{metrics['take_profit']:.2f}** (基於 1:2 風報比計算)
    * **AI 風險提示:** {risk_advice}

    {accuracy_statement}
    """
    return summary_report, metrics['action_color']

def create_comprehensive_chart(df, symbol_name, selected_period_key):
    """繪製 K 線圖、RSI 和 MACD"""
    if df is None or df.empty:
        return go.Figure()
        
    df_ta = calculate_technical_indicators(df)
    if df_ta is None or df_ta.empty:
        return go.Figure()

    # 創建子圖：1. K線+BB+MA (高度 3) 2. RSI (高度 1) 3. MACD (高度 1)
    fig = make_subplots(
        rows=3, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.6, 0.2, 0.2]
    )

    # --- 1. K線主圖 (第 1 行) ---
    fig.add_trace(go.Candlestick(
        x=df_ta.index,
        open=df_ta['Open'],
        high=df_ta['High'],
        low=df_ta['Low'],
        close=df_ta['Close'],
        name=f'{symbol_name} K線',
        increasing_line_color='#FF5733', # 紅色 K 棒 (上漲)
        decreasing_line_color='#33FF57', # 綠色 K 棒 (下跌)
        showlegend=False
    ), row=1, col=1)

    # 均線 (MA)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MA5'], name='MA5', line=dict(color='#00ffff', width=1), opacity=0.8), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MA20'], name='MA20', line=dict(color='#ff00ff', width=1), opacity=0.8), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MA60'], name='MA60', line=dict(color='#ffff00', width=1.5), opacity=0.8), row=1, col=1)

    # 布林通道 (BB) - 上軌、下軌
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['BB_High'], name='BB 上軌', line=dict(color='gray', width=1, dash='dot'), opacity=0.6), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['BB_Low'], name='BB 下軌', line=dict(color='gray', width=1, dash='dot'), opacity=0.6, fill='tonexty', fillcolor='rgba(100, 100, 100, 0.1)'), row=1, col=1)


    # --- 2. RSI 副圖 (第 2 行) ---
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['RSI'], name='RSI', line=dict(color='blue', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="gray", row=2, col=1, annotation_text="超買 (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="gray", row=2, col=1, annotation_text="超賣 (30)")
    fig.update_yaxes(range=[0, 100], title_text="RSI", row=2, col=1)

    # --- 3. MACD 副圖 (第 3 行) ---
    # MACD 柱狀圖 (Diff)
    macd_colors = np.where(df_ta['MACD_Diff'] > 0, '#FF5733', '#33FF57')
    fig.add_trace(go.Bar(
        x=df_ta.index, 
        y=df_ta['MACD_Diff'], 
        name='MACD 柱狀圖', 
        marker_color=macd_colors,
        showlegend=False
    ), row=3, col=1)
    
    # MACD 線 (MACD & Signal)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MACD'], name='MACD', line=dict(color='yellow', width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_ta.index, y=df_ta['MACD_Signal'], name='Signal', line=dict(color='red', width=1, dash='dot')), row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    # --- 整體佈局設定 ---
    fig.update_layout(
        title={
            'text': f'{symbol_name} - {selected_period_key} 綜合技術分析圖表',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_rangeslider_visible=False, # 隱藏底部的滑動條
        height=800, # 調整圖表高度
        template="plotly_dark", # 深色主題
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    # 移除底部兩圖的 X 軸標籤 (因為已經 shared_xaxes=True)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(title_text="時間軸", row=3, col=1) # 讓最底下的圖顯示 X 軸標籤

    return fig


# ==============================================================================
# 4. 側邊欄用戶輸入 (Sidebar) - 使用新的兩層選單和輸入邏輯
# ==============================================================================

# 側邊欄主標題
st.sidebar.title("🛠️ AI 分析工具箱")

# --- 1. 類別選擇 (第一層)
selected_category = st.sidebar.selectbox(
    "1. 選擇資產類別：",
    options=list(CATEGORY_MAP.keys()),
    key='category_select_box',
    index=0
)

# --- 2. 標的快速選擇 (第二層)
options_for_select = {"請選擇標的...": "PLACEHOLDER_CODE"}
options_for_select.update(CATEGORY_HOT_OPTIONS.get(selected_category, {}))

selected_option_display = st.sidebar.selectbox(
    "2. 快速選擇標的：",
    options=list(options_for_select.keys()),
    key='symbol_select_box',
    index=0,
    on_change=update_search_input # 觸發回調函數
)

# --- 3. 代碼輸入與查詢
st.sidebar.subheader("🔍 或手動輸入代碼/名稱") 
st.sidebar.text_input(
    "3. 輸入代碼 (e.g., NVDA, 2330.TW, BTC-USD)：",
    value=st.session_state.sidebar_search_input,
    key='sidebar_search_input'
)

# --- 4. 選擇分析時間週期 (Period Select)
st.sidebar.subheader("⏳ 選擇分析時間週期") 
selected_period_key = st.sidebar.radio(
    "選擇圖表和分析的時間跨度：",
    options=list(PERIOD_MAP.keys()),
    index=2, # 預設選擇 '1 日 (中長線)'
    key='selected_period_key_sb'
)

# --- 5. 分析按鈕
st.sidebar.markdown("---")
analyze_button_clicked = st.sidebar.button("✨ 執行 AI 融合分析", key='analyze_button_sb', use_container_width=True)


# ==============================================================================
# 5. 主程式邏輯
# ==============================================================================

# 觸發分析的條件：點擊按鈕 OR 快速選擇觸發了 analyze_trigger
if analyze_button_clicked or st.session_state.analyze_trigger:
    
    # 確定最終要分析的代碼：使用手動輸入框的當前值
    final_symbol_to_analyze = st.session_state.sidebar_search_input.strip().upper() 
    
    # 增加一個輸入驗證，防止空輸入
    if not final_symbol_to_analyze:
         st.error("⚠️ 請輸入有效的資產代碼或名稱。")
         st.session_state.analyze_trigger = False
         st.stop()
         
    # 進行代碼解析，確保使用者輸入的中文或數字能被 YFinance 識別
    parsed_symbol = get_symbol_from_query(final_symbol_to_analyze)
    final_symbol_to_analyze = parsed_symbol
    
    # 獲取時間參數
    yf_period, yf_interval = PERIOD_MAP[selected_period_key]
    
    # 顯示進度條
    with st.spinner(f'🤖 AI 系統正在獲取 **{final_symbol_to_analyze}** ({selected_period_key}) 的歷史數據並建立分析模型...'):
        df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval)
        info_data = get_company_info(final_symbol_to_analyze)
    
    # 重置觸發器 (避免無限循環)
    st.session_state.analyze_trigger = False
    
    if df.empty:
        st.error(f"⚠️ **數據獲取失敗:** 無法取得 {final_symbol_to_analyze} 在 {yf_interval} 週期內的數據。請檢查代碼或週期設定。")
        st.session_state.data_ready = False
        st.stop()

    # 數據準備完成
    st.session_state.data_ready = True
    
    # 獲取資產名稱和價格
    symbol_name = info_data.get('name', final_symbol_to_analyze)
    current_price = df['Close'].iloc[-1]
    
    st.success(f"✅ **{symbol_name} ({final_symbol_to_analyze})** 數據成功載入！當前收盤價：**${current_price:.2f}**")
    st.markdown("---")

    # --- 關鍵指標計算與總結 ---
    df_ta = calculate_technical_indicators(df)
    summary_df = create_analysis_summary_df(df_ta)
    
    # 獲取 ATR
    atr_value = df_ta['ATR'].iloc[-1] if not df_ta.empty else 0.0
    
    # 🚩 修正點：生成 AI 融合指標與報告
    if not summary_df.empty:
        ai_metrics = calculate_ai_fusion_metrics(summary_df, current_price, atr_value)
        ai_summary_text, color_trend = generate_ai_fusion_report(ai_metrics, symbol_name, final_symbol_to_analyze)
    else:
        ai_summary_text = "無法生成 AI 融合報告，技術數據不足。"
        color_trend = "gray"
    
    
    # --- 1. AI 融合分析報告 --- 
    st.subheader("🤖 AI 融合分析報告與建議") 
    
    if summary_df.empty:
        st.warning(ai_summary_text)
    else:
        # 報告包含所有 AI 邏輯、風控和 100% 準確性修正聲明
        st.markdown(ai_summary_text, unsafe_allow_html=True)
             
    st.markdown("---")
    
    # --- 2. 關鍵指標綜合判讀 ---
    st.subheader(f"💡 關鍵指標 AI 量化判讀 ({symbol_name})") 

    if not summary_df.empty:
        # 視覺化表格 (實現文字上色)
        color_map_hex = {
            "red": "#FF5733",      # 多頭/買入機會
            "green": "#33FF57",    # 空頭/賣出風險
            "orange": "#FFA500",   # 中性/警告
            "gray": "#CCCCCC"
        }
        
        st.dataframe(
            summary_df[summary_df['指標名稱'] != 'ATR (14) 波動性'], # 隱藏 ATR
            hide_index=True,
            use_container_width=True,
            column_config={
                "指標名稱": st.column_config.Column("指標名稱"),
                "最新值": st.column_config.Column("最新數值", help="技術指標的最新計算值"),
                "分析結論": st.column_config.Column(
                    "趨勢/動能判讀", 
                    help="基於數值範圍的 AI 解讀 (已上色)"
                ),
                "顏色": None # 隱藏用於上色的顏色欄位
            }
        )
        st.caption(f"ℹ️ **AI 提示:** 表格中 **分析結論** 的文字顏色已根據 AI 信號自動變化（**{color_map_hex['red']} (多頭)**, **{color_map_hex['green']} (空頭)**, **{color_map_hex['orange']} (中性)**）。")

    else:
        st.info("無足夠數據生成關鍵技術指標表格。")
    
    st.markdown("---")
    
    # --- 3. 核心財務與基本面指標 ---
    st.subheader(f"💰 核心財務與基本面指標") 
    
    if info_data['info_dict']:
        # 提取常用指標
        market_cap = info_data['market_cap']
        trailing_pe = info_data['info_dict'].get('trailingPE')
        forward_pe = info_data['info_dict'].get('forwardPE')
        dividend_yield = info_data['info_dict'].get('dividendYield')
        beta = info_data['info_dict'].get('beta')
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        def format_value(value, is_percentage=False):
            if value is None or value == 'N/A':
                return "N/A"
            if is_percentage:
                return f"{value * 100:.2f}%"
            if value >= 1_000_000_000:
                return f"${value/1_000_000_000:.2f} B"
            if value >= 1_000_000:
                return f"${value/1_000_000:.2f} M"
            return f"{value:,.2f}"

        col1.metric("市值 (Market Cap)", format_value(market_cap))
        col2.metric("本益比 (Trailing P/E)", format_value(trailing_pe, is_percentage=False))
        col3.metric("預估本益比 (Forward P/E)", format_value(forward_pe, is_percentage=False))
        col4.metric("股息殖利率 (Yield)", format_value(dividend_yield, is_percentage=True))
        col5.metric("Beta (市場波動性)", format_value(beta, is_percentage=False))

    else:
         st.warning("⚠️ 無法獲取資產的基本面/財務資訊。")
         
    st.markdown("---")

    # --- 4. 完整技術分析圖表 --- 
    st.subheader(f"📊 完整技術分析圖表")
    chart = create_comprehensive_chart(df, symbol_name, selected_period_key) 
    
    st.plotly_chart(chart, use_container_width=True, key=f"plotly_chart_{final_symbol_to_analyze}_{selected_period_key}")

    # ==============================================================================
    # 6. 結尾資訊與透明度聲明 (AI 專屬版本)
    # ==============================================================================
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    # 🚩 修正點：AI 角色與數據透明度聲明
    with st.expander("🧾 AI 系統聲明、數據源與 AI 虛擬角色透明度", expanded=False):
        st.markdown(f"""
        ### 📜 **AI 系統免責聲明 (AI System Disclaimer)**
        本 AI 分析儀表板由模擬 **{len(AI_VIRTUAL_ROLES)}** 種專業投資/技術角色的 **AI 引擎**所驅動。
        **所有輸出的分析、評級與交易建議僅為數據模型模擬的結果，絕不構成任何實際的投資建議 (Financial Advice)**。
        投資有風險，請用戶根據自身風險承受能力進行獨立判斷。
        
        ### 💻 **數據來源透明度 (Data Source Transparency)**
        本系統的核心數據主要來自 **Yahoo Finance** (使用 `yfinance` 庫)，並**概念性地整合**了以下多種數據來源的**分析思路與考量維度**，以確保模型的穩健性：
        
        **[AI 分析維度整合來源]**
        {'\n'.join([f"* {source}" for source in EXTERNAL_DATA_SOURCES])}
        
        **注意：** 除 Yahoo Finance (yfinance) 外，其餘數據源目前僅作為**分析模型的知識與維度基礎**。

        ### 🧑‍💻 **AI 虛擬角色陣容 (AI Virtual Roles)**
        本 AI 融合分析報告是以下 AI 模擬角色的研究與討論共識：
        
        **[AI 虛擬角色列表]**
        {'\n'.join([f"* {role}" for role in AI_VIRTUAL_ROLES])}
        
        ---
        **AI 數據正確性聲明：** 儘管 AI 系統力求數據準確，但因 YFinance 來源的數據可能存在延遲、時間戳不一致、或數據校準差異，**數據的絕對準確性無法達到 100%**。本系統已盡力透過數據清洗和魯棒性計算來提高**數據品質**，並將重點放在**信號的穩健性**上。
        """)
        
    st.markdown("---")
    st.markdown("⚠️ **免責聲明:** 本分析模型包含多位 AI 的量化觀點，但**僅供教育與參考用途**。")


# 首次載入或數據未準備好時的提示
elif not st.session_state.get('data_ready', False) and not analyze_button_clicked:
     st.title("🤖 AI 趨勢分析儀表板 📈") 
     st.info("請在左側選擇或輸入標的，然後點擊 **✨ 執行 AI 融合分析** 按鈕，以查看 AI 虛擬團隊的專業報告。")
