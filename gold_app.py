import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os

# ==========================================
# 1. 配置 FRED API KEY
# ==========================================
# 你的 API Key 已经直接硬编码在下面
FRED_API_KEY = "c804807c4d5649ebeba394d4ab50f3c1"

st.set_page_config(layout="wide", page_title="Gold/Silver Macro Quant Pro")

# ==========================================
# 2. 数据抓取逻辑
# ==========================================

@st.cache_data(ttl=3600)
def get_fred_macro_data():
    """使用 fredapi 获取核心定价指标"""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        # 获取数据 (DFII10: 10Y实际利率, T10YIE: 10Y盈亏平衡通胀率)
        # 我们抓取过去 180 天的数据
        real_yield = fred.get_series('DFII10')
        inflation = fred.get_series('T10YIE')
        
        # 将数据合并为 DataFrame
        df = pd.DataFrame({
            'Real_Yield_10Y': real_yield,
            'Inflation_10Y': inflation
        }).tail(180)
        
        df = df.ffill() # 填充缺失值
        return df
    except Exception as e:
        st.error(f"FRED数据抓取失败: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_realtime_prices():
    """获取黄金、白银、美元实时价格"""
    tickers = {
        "GLD": "GLD", 
        "SLV": "SLV", 
        "DXY": "DX-Y.NYB", 
        "US10Y": "^TNX"
    }
    # yfinance 抓取最近 5 天的数据
    data = yf.download(list(tickers.values()), period="5d", interval="5m")
    if data.empty:
        return pd.DataFrame()
    return data['Close']

# ==========================================
# 3. 页面核心逻辑
# ==========================================

st.title("🏆 黄金白银宏观全维度仪表盘")
st.caption("已修复 Python 3.13 兼容性问题")

# 加载数据
with st.spinner('正在同步全球宏观及实时价格数据...'):
    df_macro = get_fred_macro_data()
    df_price = get_realtime_prices()

if not df_price.empty and not df_macro.empty:
    # --- 顶层 Metric 看板 ---
    m1, m2, m3, m4 = st.columns(4)
    
    curr_gld = df_price['GLD'].iloc[-1]
    curr_dxy = df_price['DX-Y.NYB'].iloc[-1]
    curr_real_yield = df_macro['Real_Yield_10Y'].iloc[-1]
    curr_gsr = curr_gld / df_price['SLV'].iloc[-1]
    
    # 计算变化量
    dxy_change = curr_dxy - df_price['DX-Y.NYB'].iloc[-12] if len(df_price) > 12 else 0
    gld_change = curr_gld - df_price['GLD'].iloc[-2]
    
    m1.metric("GLD 实时价", f"${curr_gld:.2f}", f"{gld_change:.2f}")
    m2.metric("DXY 美元指数", f"{curr_dxy:.2f}", f"{dxy_change:.2f}", delta_color="inverse")
    m3.metric("10Y 实际利率", f"{curr_real_yield:.2f}%", f"{curr_real_yield - df_macro['Real_Yield_10Y'].iloc[-2]:.2f}%", delta_color="inverse")
    m4.metric("金银比 (GSR)", f"{curr_gsr:.2f}")

    # --- 中间层：图表展示 ---
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📡 决策信号灯")
        score = 0
        if dxy_change < 0: score += 1
        if curr_real_yield < df_macro['Real_Yield_10Y'].iloc[-2]: score += 1
        if curr_gld > df_price['GLD'].rolling(20).mean().iloc[-1]: score += 1
        
        if score >= 2:
            st.success(f"综合评分: {score} | 多头共振")
        elif score <= 0:
            st.error(f"综合评分: {score} | 空头占优")
        else:
            st.warning(f"综合评分: {score} | 震荡状态")
            
        st.write("数据更新于:", datetime.datetime.now().strftime("%H:%M:%S"))

    with c2:
        st.subheader("📊 走势对比 (GLD vs 实际利率)")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df_price.index, y=df_price['GLD'], name="GLD 价格", line=dict(color="gold")), secondary_y=False)
        # 将实际利率的时间索引处理成与价格图表接近
        fig.add_trace(go.Scatter(x=df_macro.index[-20:], y=df_macro['Real_Yield_10Y'].iloc[-20:], name="10Y 实际利率 (右轴)", line=dict(color="cyan")), secondary_y=True)
        
        fig.update_layout(height=400, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("数据抓取中，请稍后... 如果长时间无反应，请检查 GitHub 仓库中的 requirements.txt 是否已更新。")
