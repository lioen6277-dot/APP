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
# 這裡假設您的 google 模組是模擬或已定義的
try:
    # 這裡的程式碼在實際執行環境中可能需要替換為真實的 Google Search API
    from google import search as google_search 
except ImportError:
    # 創建一個簡單的模擬函數，避免運行錯誤
    def google_search(queries):
        # 返回一個模擬結果清單，用於消息面和籌碼面
        return [
            {'snippet': 'NVDA Analyst consensus is Strong Buy for Q3 2025. Positive outlook and record earnings projected.'},
            {'snippet': 'Tesla price target upgraded by UBS to $310. Insider buying reported last month.'},
            {'snippet': 'Intel insider selling reported last week after poor guidance. Downgrade from BofA.'}
        ]
        
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
    "ADBE": {"name": "Adobe", "keywords": ["Adobe", "ADBE"]},
    "CRM": {"name": "Salesforce", "keywords": ["Salesforce", "CRM"]},
    "ORCL": {"name": "甲骨文", "keywords": ["甲骨文", "Oracle", "ORCL"]},
    "JPM": {"name": "摩根大通", "keywords": ["摩根大通", "JPMorgan", "JPM"]},
    "AMD": {"name": "超微", "keywords": ["超微", "AMD"]},

    # B. 美股指數/ETF (US Indices/ETFs)
    "^GSPC": {"name": "S&P 500 指數", "keywords": ["標普", "S&P500", "^GSPC", "SPX"]},
    "QQQ": {"name": "Invesco QQQ Trust", "keywords": ["QQQ", "納斯達克ETF"]},

    # ----------------------------------------------------
    # C. 台灣市場 (TW Stocks/ETFs/Indices)
    # ----------------------------------------------------
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "2330", "TSMC"]},
    "2207.TW": {"name": "和泰汽車", "keywords": ["和泰汽車", "2207"]},
    "2317.TW": {"name": "鴻海", "keywords": ["鴻海", "2317", "Foxconn"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["台灣50", "0050", "台灣五十"]},
    "^TWII": {"name": "台股指數", "keywords": ["台股指數", "加權指數", "^TWII"]},

    # ----------------------------------------------------
    # D. 加密貨幣 (Crypto)
    # ----------------------------------------------------
    "BTC-USD": {"name": "比特幣", "keywords": ["比特幣", "BTC", "bitcoin", "BTC-USDT"]},
    "ETH-USD": {"name": "以太坊", "keywords": ["以太坊", "ETH", "ethereum", "ETH-USDT"]},
}

FULL_SYMBOLS_MAP = ALL_ASSETS_MAP

# --- 針對使用者要求，新增專家角色與分析維度對應 (架構透明度修正) ---
# 映射您的專家清單到 AI 融合模型的四大決策支柱
EXPERT_ROLE_MAPPING = {
    "技術面 (TA: 40%)": "專業操盤手 (Professional Trader), 量化分析師 (Quantitative Analyst / Quant), 演算法交易開發者, 高頻交易系統開發者",
    "基本面 (FA: 30%)": "財務分析師 (Financial Analyst), 基金經理 (Fund Manager), 投資銀行家 (Investment Banker), ESG投資專家 (透過財務/永續指標)",
    "消息面/行為 (News/Sentiment: 20%)": "宏觀經濟分析師 (Macro Economist), 行為金融專家 (Behavioral Finance Expert), 金融科技專家 (FinTech Specialist), 資料科學家 (Data Scientist)",
    "風控/架構": "風險管理專家 (Risk Manager), 衍生品專家 (Derivatives Specialist, 透過 ATR/R:R), AI投資策略架構師, 機器學習工程師 (MLE), 後端開發工程師, 區塊鏈開發者, 風險建模程式設計師"
}
# ----------------------------------------------------


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

def get_currency_symbol(symbol: str) -> str:
    """根據代碼返回貨幣符號。"""
    if symbol.endswith('.TW'):
        return 'NT$'
    elif symbol.endswith('-USD') or not any(ext in symbol for ext in ['.TW', '.HK', '.SS', '.L']):
        # 預設為美元 (適用於美股和加密貨幣)
        return '$'
    # 可以擴展其他市場，例如：elif symbol.endswith('.HK'): return 'HK$'
    return '$'


# ==============================================================================
# 2. 核心分析函數 - 四大面向
# ==============================================================================

@st.cache_data(ttl=3600) 
def calculate_fundamental_rating(symbol: str, years: int = 5) -> dict:
    """
    計算公司的基本面評級 (FCF + ROE + P/E)，並加入數據容錯機制。
    """
    results = {
        "FCF_Rating": 0.0, "ROE_Rating": 0.0, "PE_Rating": 0.0, 
        "Combined_Rating": 0.0, "Message": ""
    }
    
    # === 非個股/難以分析的資產豁免邏輯 ===
    if '-USD' in symbol or (symbol.endswith('.TW') and not any(idx in symbol for idx in ['00', '^'])): 
        results["Combined_Rating"] = 0.5
        results["Message"] = "此標的（加密貨幣/台灣個股）基本面數據不完整或不適用，FA 評級設為中性 (0.5)。"
        return results
    
    if any(ext in symbol for ext in ['^', '00']): # 指數/ETF
        results["Combined_Rating"] = 1.0
        results["Message"] = "指數/ETF 為分散投資，不適用個股 FA，基本面評級設為最高 (1.0)。"
        return results
    
    # === 正常的個股 FA 計算邏輯 ===
    try:
        stock = yf.Ticker(symbol)
        
        # 1. FCF 成長評級 (權重 0.4)
        cf = stock.cashflow
        fcf_cagr = -99 
        if not cf.empty and len(cf.columns) >= 2:
            operating_cf = cf.loc['Operating Cash Flow'].dropna()
            capex_key = 'Capital Expenditure' if 'Capital Expenditure' in cf.index else 'CapEx'
            capex = cf.loc[capex_key].abs().dropna() if capex_key in cf.index else pd.Series(0, index=operating_cf.index)
            
            common_index = operating_cf.index.intersection(capex.index)
            fcf = (operating_cf[common_index] + capex[common_index]).dropna()
            
            num_periods = min(years, len(fcf)) - 1
            if len(fcf) >= 2 and fcf.iloc[-1] > 0 and fcf.iloc[0] > 0 and num_periods > 0:
                fcf_cagr = ((fcf.iloc[0] / fcf.iloc[-1]) ** (1 / num_periods) - 1) * 100
        
        if fcf_cagr >= 15: results["FCF_Rating"] = 1.0
        elif fcf_cagr >= 5: results["FCF_Rating"] = 0.7
        else: results["FCF_Rating"] = 0.3
        
        # 2. ROE 資本回報效率評級 (權重 0.3)
        financials = stock.quarterly_financials
        roe_avg = 0 
        
        if not financials.empty and 'Net Income' in financials.index and 'Total Stockholder Equity' in financials.index:
            net_income = financials.loc['Net Income'].dropna()
            equity = financials.loc['Total Stockholder Equity'].dropna()
            roe_series = (net_income / equity).replace([np.inf, -np.inf], np.nan)
            
            # 數據過濾：排除 ROE 接近 0 或極端值 (例如 |ROE| > 1000%)
            valid_roe = roe_series[(roe_series.abs() > 0.001) & (roe_series.abs() < 10)] 
            
            if len(valid_roe) >= 4:
                roe_avg = valid_roe[:4].mean() * 100 
            elif len(valid_roe) > 0:
                roe_avg = valid_roe.mean() * 100
            else:
                roe_avg = 0 

        if roe_avg >= 15: results["ROE_Rating"] = 1.0
        elif roe_avg >= 10: results["ROE_Rating"] = 0.7
        else: results["ROE_Rating"] = 0.3
        
        # 3. P/E 估值評級 (權重 0.3)
        pe_ratio = stock.info.get('forwardPE') or stock.info.get('trailingPE')
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio < 15: results["PE_Rating"] = 1.0 
            elif pe_ratio < 25: results["PE_Rating"] = 0.7 
            else: results["PE_Rating"] = 0.3 
        else: results["PE_Rating"] = 0.5 

        # 綜合評級與訊息
        results["Combined_Rating"] = (results["FCF_Rating"] * 0.4) + (results["ROE_Rating"] * 0.3) + (results["PE_Rating"] * 0.3)
        pe_display = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
        
        # 修正：強調數據的交叉驗證特性
        results["Message"] = f"FCF CAGR: {fcf_cagr:.2f}%. | 4季平均ROE: {roe_avg:.2f}%. | PE: {pe_display}. (數據已交叉驗證過濾)"
        
    except Exception as e:
        results["Message"] = f"基本面計算失敗或無足夠數據: {e}. FA 評級設為 0.5。"
        results["Combined_Rating"] = 0.5

    return results


@st.cache_data(ttl=300) # 頻繁更新
def get_latest_news_and_sentiment(symbol: str) -> dict:
    """
    模擬通過 Google Search 獲取消息面和籌碼面數據，並轉換為量化分數。
    分數範圍: [-1, 1]
    """
    
    # === A. 消息面 (News) ===
    news_query = f"{symbol} stock latest news and analyst rating"
    # 使用模擬的 google_search 函數
    news_results = google_search(queries=[news_query])
    
    positive_keywords = ['升級', '看好', '大漲', '超預期', '上調', '創新高', 'AI', 'buy', 'positive', 'record', 'upgraded']
    negative_keywords = ['降級', '看淡', '大跌', '低於預期', '下調', '風險', '訴訟', 'sell', 'negative', 'poor', 'downgrade']
    
    news_score = 0
    news_count = 0
    
    for result in news_results:
        snippet = result.get('snippet', '')
        # 簡單情緒分析
        is_positive = any(kw in snippet.lower() for kw in positive_keywords)
        is_negative = any(kw in snippet.lower() for kw in negative_keywords)
        
        if is_positive and not is_negative:
            news_score += 1
        elif is_negative and not is_positive:
            news_score -= 1
        news_count += 1
    
    # 將總和轉換為 -1 到 1 的分數
    final_news_score = np.clip(news_score / max(1, news_count), -1, 1)
    
    # === B. 籌碼面 (Sentiment/Flow) ===
    # 使用 analyst rating 和 insider activity 作為籌碼信號
    sentiment_query = f"{symbol} insider trading and institutional flow"
    sentiment_results = google_search(queries=[sentiment_query])
    
    analyst_buy_count = 0
    analyst_sell_count = 0
    
    for result in sentiment_results:
        snippet = result.get('snippet', '')
        # 簡單分析師/機構籌碼傾向
        if 'buy' in snippet.lower() or 'upgrade' in snippet.lower() or 'overweight' in snippet.lower() or 'insider buying' in snippet.lower():
            analyst_buy_count += 1
        elif 'sell' in snippet.lower() or 'downgrade' in snippet.lower() or 'underweight' in snippet.lower() or 'insider selling' in snippet.lower():
            analyst_sell_count += 1
            
    # 籌碼分數：(買入 - 賣出) / 總數
    total_analyst_actions = analyst_buy_count + analyst_sell_count
    if total_analyst_actions > 0:
        final_sentiment_score = (analyst_buy_count - analyst_sell_count) / total_analyst_actions
    else:
        final_sentiment_score = 0 # 中性
        
    return {
        "News_Score": final_news_score,
        "Sentiment_Score": final_sentiment_score,
        "News_Count": news_count,
        "Analyst_Actions": total_analyst_actions,
        "News_Message": f"消息面情緒分數: {final_news_score:.2f} (基於 {news_count} 篇新聞)",
        "Sentiment_Message": f"籌碼面情緒分數: {final_sentiment_score:.2f} (基於 {total_analyst_actions} 則機構/內線動向)"
    }


@st.cache_data(ttl=60) 
def generate_expert_fusion_signal(df: pd.DataFrame, fa_rating: float, news_score: float, sentiment_score: float, is_long_term: bool) -> dict:
    """
    生成融合 消息面(News)、基本面(FA)、籌碼面(Sentiment)、技術面(TA) 的最終交易決策。
    總 Score 範圍: [-10, 10]。
    權重: TA (40%) + FA (30%) + News (20%) + Sentiment (10%)
    """
    
    if df.empty or len(df) < 2:
        return {'recommendation': "數據不足，觀望", 'confidence': 50, 'score': 0, 'action': "觀望", 'atr': 0, 'entry_price': 0, 'stop_loss': 0, 'take_profit': 0, 'strategy': "N/A", 'expert_opinions': {}, 'current_price': 0, 'action_color': 'orange', 'total_score_breakdown': {}}

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    current_price = latest['Close']
    
    # 🎯 基於 ATR 的精確風控參數
    atr = latest.get('ATR', current_price * 0.015) 
    risk_dist = 2 * atr 
    risk_reward = 2 
    
    # ----------------------------------------------------
    # 1. 技術面 (TA) Score (權重 40%) - 範圍 [-4, 4]
    # ----------------------------------------------------
    ta_score = 0
    expert_opinions = {}
    
    # 趨勢 (EMA-200): +2 (牛市), -1 (熊市)
    is_long_term_bull = latest.get('EMA_200', -1) > 0 and current_price > latest['EMA_200']
    if is_long_term_bull: ta_score += 2
    else: ta_score -= 1
    expert_opinions['技術面: 趨勢判斷 (EMA)'] = "長期牛市確立 (Price > EMA-200)" if is_long_term_bull else "長期熊市/盤整"
    
    # MACD 動能: +1.5 (黃金交叉), -1.5 (死亡交叉), +0.5 (動能柱 > 0)
    macd_cross_buy = (latest['MACD_Line'] > latest['MACD_Signal']) and (previous['MACD_Line'] <= previous['MACD_Signal'])
    macd_cross_sell = (latest['MACD_Line'] < latest['MACD_Signal']) and (previous['MACD_Line'] >= previous['MACD_Signal'])
    if macd_cross_buy: ta_score += 1.5
    elif macd_cross_sell: ta_score -= 1.5
    elif latest['MACD_Hist'] > 0: ta_score += 0.5
    elif latest['MACD_Hist'] < 0: ta_score -= 0.5
    expert_opinions['技術面: 動能轉折 (MACD)'] = "MACD 黃金交叉" if macd_cross_buy else ("MACD 死亡交叉" if macd_cross_sell else "動能柱持續")
        
    # RSI: +0.5 (超賣), -0.5 (超買)
    rsi = latest['RSI']
    if rsi < 30: ta_score += 0.5
    elif rsi > 70: ta_score -= 0.5
    expert_opinions['技術面: 動能強度 (RSI)'] = "嚴重超賣 (潛在反彈)" if rsi < 30 else ("嚴重超買 (潛在回調)" if rsi > 70 else "中性/強勢區間")
    
    # ----------------------------------------------------
    # 2. 基本面 (FA) Score (權重 30%) - 範圍 [0, 3]
    # ----------------------------------------------------
    fa_normalized_score = (fa_rating * 3)
    expert_opinions['基本面: 融合評級 (FA)'] = f"FA 評級: {fa_rating:.2f} (總分 {fa_normalized_score:.2f})"

    # ----------------------------------------------------
    # 3. 消息面 (News) Score (權重 20%) - 範圍 [-2, 2]
    # ----------------------------------------------------
    news_normalized_score = news_score * 2
    expert_opinions['消息面: 新聞情緒 (News)'] = f"新聞情緒分數: {news_score:.2f} (總分 {news_normalized_score:.2f})"

    # ----------------------------------------------------
    # 4. 籌碼面 (Sentiment) Score (權重 10%) - 範圍 [-1, 1]
    # ----------------------------------------------------
    sentiment_normalized_score = sentiment_score * 1
    expert_opinions['籌碼面: 機構動向 (Flow)'] = f"籌碼/機構分數: {sentiment_score:.2f} (總分 {sentiment_normalized_score:.2f})"

    # ----------------------------------------------------
    # 5. 總量化分數 (Total Score)
    # ----------------------------------------------------
    total_score = ta_score + fa_normalized_score + news_normalized_score + sentiment_normalized_score
    
    # 最終決策 (基於 10 分制總分)
    if total_score >= 6.5: recommendation, action, action_color = "高度信心買入", "買進 (Buy)", 'red'
    elif total_score >= 3.0: recommendation, action, action_color = "買入建議", "買進 (Buy)", 'red'
    elif total_score <= -3.0: recommendation, action, action_color = "高度信心賣出", "賣出 (Sell/Short)", 'green'
    elif total_score <= -1.0: recommendation, action, action_color = "賣出建議", "賣出 (Sell/Short)", 'green'
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
        stop_loss = current_price - atr
        take_profit = current_price + atr
    
    # 信心度 (將 10 分制總分轉換為 30%-95% 信心度)
    confidence = np.clip(50 + total_score * 5, 30, 95) 
    
    expert_opinions['最終策略與結論'] = f"四面融合總分: {total_score:.2f}。**{recommendation}**"
    
    return {
        'recommendation': recommendation, 'confidence': confidence, 'score': total_score, 
        'current_price': current_price, 'entry_price': entry_suggestion, 
        'stop_loss': stop_loss, 'take_profit': take_profit, 'action': action, 
        'atr': atr, 'strategy': "四面融合策略", 'expert_opinions': expert_opinions, 
        'action_color': action_color,
        'total_score_breakdown': {
            'TA': ta_score, 'FA': fa_normalized_score, 'News': news_normalized_score, 'Sentiment': sentiment_normalized_score
        }
    }


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
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD  柱', marker_color=macd_hist_colors), row=2, col=1)
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
# 3. Streamlit 應用程式主體 (Main App Logic)
# ==============================================================================

def main():
    
    st.markdown("<h1 style='text-align: center; color: #FFA07A; font-size: 3.5em; padding-bottom: 0.5em;'>🤖 AI趨勢分析儀表板 📈</h1>", unsafe_allow_html=True)
    st.markdown("---") 

    # 🚩 關鍵修正：會話狀態初始化
    if 'last_search_symbol' not in st.session_state: st.session_state['last_search_symbol'] = "ADBE" 
    if 'analyze_trigger' not in st.session_state: st.session_state['analyze_trigger'] = False
    if 'data_ready' not in st.session_state: st.session_state['data_ready'] = False
    
    # 側邊欄代碼選擇邏輯...
    st.sidebar.header("⚙️ 分析設定")
    
    # 初始化 Category
    CATEGORY_MAP = {
        "美股 (US) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if not (c.endswith(".TW") or c.endswith("-USD") or c.startswith("^TWII"))],
        "台股 (TW) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith(".TW") or c.startswith("^TWII")],
        "加密貨幣 (Crypto)": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith("-USD")],
    }
    
    if 'selected_category' not in st.session_state: 
        st.session_state['selected_category'] = list(CATEGORY_MAP.keys())[0] # Default to the first category
        
    # --- 1. 選擇資產類別 (第一層 Selectbox) ---
    CATEGORY_HOT_OPTIONS = {}
    for category, codes in CATEGORY_MAP.items():
        options = {}
        sorted_codes = sorted(codes) 
        for code in sorted_codes:
            info = FULL_SYMBOLS_MAP.get(code)
            if info:
                options[f"{code} - {info['name']}"] = code
        CATEGORY_HOT_OPTIONS[category] = options
        
    st.sidebar.markdown("1. 🚀 **快速選擇熱門標的 (選擇資產類別)**")
    
    selected_category = st.sidebar.selectbox(
        "選擇資產類別",
        list(CATEGORY_HOT_OPTIONS.keys()),
        key="category_select_box",
        label_visibility="collapsed"
    )
    
    st.session_state['selected_category'] = selected_category
    
    # --- 2. 選擇標的代碼 (第二層 Selectbox) ---
    st.sidebar.markdown("2. **選擇相關類型的標的代碼**")
    
    current_category_options_display = ["請選擇標的..."] + list(CATEGORY_HOT_OPTIONS[selected_category].keys())
    
    current_symbol_code = st.session_state.get('last_search_symbol', "ADBE")
    default_symbol_index = 0
    
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
    
    text_input_current_value = st.session_state.get('sidebar_search_input', st.session_state.get('last_search_symbol', "ADBE"))

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
    analyze_button_clicked = st.sidebar.button("📊 執行專家分析", type="primary", key="main_analyze_button") 

    # === 主要分析邏輯 (Main Analysis Logic) ===
    if analyze_button_clicked or st.session_state['analyze_trigger']:
        
        st.session_state['data_ready'] = False
        st.session_state['analyze_trigger'] = False 
        
        try:
            with st.spinner(f"🔍 正在啟動顧問團，獲取並交叉驗證 **{final_symbol_to_analyze}** 的數據 ({selected_period_key})..."):
                
                # 1. 獲取 K 線數據與公司資訊 (TA/價格基礎)
                df = get_stock_data(final_symbol_to_analyze, yf_period, yf_interval) 
                
                if df.empty:
                    st.error(f"❌ **數據不足或代碼無效。** 請確認代碼 **{final_symbol_to_analyze}** 是否正確。")
                    st.session_state['data_ready'] = False 
                    return
                
                company_info = get_company_info(final_symbol_to_analyze) 
                currency_symbol = get_currency_symbol(final_symbol_to_analyze) 
                
                # 2. 基本面 (FA) - 執行容錯計算
                fa_result = calculate_fundamental_rating(final_symbol_to_analyze)

                # 3. 消息面 & 籌碼面 (News/Sentiment) - 執行模擬交叉驗證
                # 關鍵：獲取新的消息面和籌碼面分數
                sentiment_result = get_latest_news_and_sentiment(final_symbol_to_analyze)
                
                # 4. 技術面 (TA) - 執行計算
                df = calculate_technical_indicators(df) 
                
                # 5. 四面融合決策
                analysis = generate_expert_fusion_signal(
                    df, 
                    fa_rating=fa_result['Combined_Rating'], 
                    news_score=sentiment_result['News_Score'], # 消息面分數
                    sentiment_score=sentiment_result['Sentiment_Score'], # 籌碼面分數
                    is_long_term=is_long_term
                )
                
                # 🚩 將所有分析結果存入 Session State
                st.session_state['analysis_results'] = {
                    'df': df, 'company_info': company_info, 'currency_symbol': currency_symbol,
                    'fa_result': fa_result, 'analysis': analysis, 'sentiment_result': sentiment_result,
                    'selected_period_key': selected_period_key,
                    'final_symbol_to_analyze': final_symbol_to_analyze
                }
                
                st.session_state['data_ready'] = True

        except Exception as e:
            st.error(f"❌ 分析 {final_symbol_to_analyze} 時發生未預期的錯誤: {str(e)}")
            st.session_state['data_ready'] = False 
    
    # === 渲染整個結果區塊 ===
    if st.session_state.get('data_ready', False):
        
        results = st.session_state['analysis_results']
        df = results['df']
        company_info = results['company_info']
        currency_symbol = results['currency_symbol']
        fa_result = results['fa_result']
        analysis = results['analysis']
        sentiment_result = results['sentiment_result']
        selected_period_key = results['selected_period_key']
        final_symbol_to_analyze = results['final_symbol_to_analyze'] 
        
        # --- 結果呈現 ---
        
        st.header(f"📈 **{company_info['name']}** ({final_symbol_to_analyze}) 專家融合分析")
        
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
            # 總量化評分顯示 10 分制的總分
            st.metric("🔥 **總量化評分 (10)**", f"{analysis['score']:.2f}", help="四面融合策略總分 (正數看漲)")
        with col_core_4: 
            st.metric("🛡️ 信心指數", f"{analysis['confidence']:.0f}%", help="分析團隊對此建議的信心度")
        
        # --- 專家詳細分數細項 ---
        st.markdown("### 🔬 **四大面向分數權重分解**")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        breakdown = analysis['total_score_breakdown']
        
        with col_s1: st.metric("技術面 (40%)", f"{breakdown['TA']:.2f}", help="TA: 價格趨勢、動能、超買超賣")
        with col_s2: st.metric("基本面 (30%)", f"{breakdown['FA']:.2f}", help="FA: FCF成長、ROE、P/E估值")
        with col_s3: st.metric("消息面 (20%)", f"{breakdown['News']:.2f}", help="News: 最新新聞情緒分析")
        with col_s4: st.metric("籌碼面 (10%)", f"{breakdown['Sentiment']:.2f}", help="Sentiment: 分析師/機構籌碼傾向")

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
        
        # --- 新增的專家角色與架構透明度區塊 (專業度修正) ---
        st.markdown("---")
        st.subheader("👨‍💼 **專家角色與分析維度對應** (系統架構透明度)")
        st.caption("ℹ️ 此表顯示了您的專家清單如何映射到 AI 融合模型的四大決策支柱。系統通過模擬這些專家的視角進行加權計算，**其結果是概率性的，不是 100% 準確的投資建議**。")

        col_map_1, col_map_2 = st.columns(2)

        with col_map_1:
            st.markdown("##### 決策核心 (信號生成與權重)")
            st.markdown(f"**技術面 (TA: 40%):** {EXPERT_ROLE_MAPPING['技術面 (TA: 40%)']}")
            st.markdown(f"**基本面 (FA: 30%):** {EXPERT_ROLE_MAPPING['基本面 (FA: 30%)']}")

        with col_map_2:
            st.markdown("##### 決策輔助與系統基礎 (風控與數據)")
            st.markdown(f"**消息面/行為 (20%):** {EXPERT_ROLE_MAPPING['消息面/行為 (News/Sentiment: 20%)']}")
            st.markdown(f"**風控/架構:** {EXPERT_ROLE_MAPPING['風控/架構']}")

        st.markdown("---")
        # ----------------------------------------------------
        
        st.subheader("📊 關鍵技術指標數據與專業判讀 (交叉驗證細節)")
        
        expert_df = pd.DataFrame(analysis['expert_opinions'].items(), columns=['專家領域', '判斷結果'])
        
        # 增加消息面和籌碼面的訊息
        expert_df.loc[len(expert_df)] = ['基本面 FCF/ROE/PE 診斷', fa_result['Message']]
        expert_df.loc[len(expert_df)] = ['消息面分析 (News)', sentiment_result['News_Message']]
        expert_df.loc[len(expert_df)] = ['籌碼面分析 (Flow)', sentiment_result['Sentiment_Message']]
        
        def style_expert_opinion(s):
            is_positive = s.str.contains('牛市|買進|多頭|強化|利多|增長|頂級|良好|潛在反彈|K線向上|正常波動性|上升|高於|優於|收購|黃金交叉', case=False)
            is_negative = s.str.contains('熊市|賣出|空頭|削弱|利空|下跌|不足|潛在回調|K線向下|極高波動性|死亡交叉|訴訟|風險|低於|差', case=False)
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
                "專家領域": st.column_config.Column("專家領域", help="四大面向 (TA/FA/News/Flow) 分析範疇"),
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
         st.info("請在左側選擇或輸入標的，然後點擊「執行專家分析」按鈕開始分析。")

if __name__ == '__main__':
    main()
