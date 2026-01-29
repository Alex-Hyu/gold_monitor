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
FRED_API_KEY = "c804807c4d5649ebeba394d4ab50f3c1"

st.set_page_config(layout="wide", page_title="Gold/Silver Macro Quant Pro")

# ==========================================
# 2. 数据抓取逻辑
# ==========================================

@st.cache_data(ttl=3600)
def get_macro_and_position_data():
    """抓取 FRED 宏观指标及 CFTC 持仓数据"""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        # DFII10: 10Y实际利率
        # T10YIE: 10Y盈亏平衡通胀率
        # 为了展示 CFTC 头寸，我们尝试抓取相关指标
        # 注意：CFTC 数据通常为周更
        data_dict = {
            'Real_Yield_10Y': fred.get_series('DFII10'),
            'Inflation_10Y': fred.get_series('T10YIE'),
            # 下面是美联储数据库中关于黄金的持仓或存量参考
            'Central_Bank_Gold': fred.get_series('WORLDGOLD') # 全球官方黄金储备参考
        }
        
        df = pd.DataFrame(data_dict).tail(200)
        df = df.ffill()
        return df
    except Exception as e:
        st.error(f"FRED宏观数据抓取失败: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_etf_holdings_data():
    """通过份额变动估算 ETF 持仓流入流出"""
    try:
        gld = yf.Ticker("GLD")
        slv = yf.Ticker("SLV")
        
        # 获取发行在外的份额 (Shares Outstanding)
        # 份额增加 = 资金流入 = 实物增持
        gld_shares = gld.info.get('sharesOutstanding', 0)
        slv_shares = slv.info.get('sharesOutstanding', 0)
        gld_aum = gld.info.get('totalAssets', 0)
        
        return {
            'gld_shares': gld_shares,
            'slv_shares': slv_shares,
            'gld_aum': gld_aum
        }
    except:
        return {'gld_shares': 0, 'slv_shares': 0, 'gld_aum': 0}

@st.cache_data(ttl=300)
def get_realtime_prices():
    """抓取实时价格及成交量"""
    tickers = ["GLD", "SLV", "DX-Y.NYB", "^TNX"]
    data = yf.download(tickers, period="5d", interval="5m")
    if data.empty:
        return pd.DataFrame()
    return data['Close'], data['Volume']

# ==========================================
# 3. 页面布局
# ==========================================

st.title("🏆 黄金白银全维度仪表盘 (含持仓监控)")

# 加载数据
with st.spinner('正在同步全球宏观、ETF持仓及实时数据...'):
    df_macro = get_macro_and_position_data()
    df_price, df_vol = get_realtime_prices()
    etf_data = get_etf_holdings_data()

if not df_price.empty:
    # --- 第一层：实时行情 ---
    m1, m2, m3, m4 = st.columns(4)
    curr_gld = df_price['GLD'].iloc[-1]
    curr_slv = df_price['SLV'].iloc[-1]
    curr_dxy = df_price['DX-Y.NYB'].iloc[-1]
    
    m1.metric("GLD 价格", f"${curr_gld:.2f}", f"{curr_gld - df_price['GLD'].iloc[-2]:.2f}")
    m2.metric("SLV 价格", f"${curr_slv:.2f}", f"{curr_slv - df_price['SLV'].iloc[-2]:.2f}")
    m3.metric("DXY 指数", f"{curr_dxy:.2f}", f"{curr_dxy - df_price['DX-Y.NYB'].iloc[-2]:.2f}", delta_color="inverse")
    m4.metric("金银比", f"{(curr_gld/curr_slv):.2f}")

    # --- 第二层：深度持仓看板 ---
    st.markdown("---")
    st.subheader("🕵️ 机构与头寸监控 (Holdings & Sentiment)")
    e1, e2, e3 = st.columns(3)
    
    with e1:
        # ETF 份额监控
        st.write("**GLD 实物流入(份额)**")
        st.title(f"{etf_data['gld_shares'] / 1e6:.1f}M")
        st.caption("份额增加意味着机构正在创建新的 ETF 单元，是强力买入信号。")

    with e2:
        # CFTC 代理指标 (此处展示 FRED 抓取的黄金储备或持仓趋势)
        st.write("**全球黄金储备趋势**")
        if not df_macro.empty:
            st.line_chart(df_macro['Central_Bank_Gold'].tail(50))
        st.caption("源自美联储数据库：长期储备增加支撑金价中线底部。")

    with e3:
        # 实时成交量激增监控 (日内期权关键)
        vol_change = df_vol['GLD'].iloc[-1] / df_vol['GLD'].rolling(20).mean().iloc[-1]
        st.write("**日内成交量爆发率**")
        st.title(f"{vol_change:.2f}x")
        st.caption("若成交量 > 2x 且价格突破，通常是期权 Gamma 爆发的起点。")

    # --- 第三层：宏观定价与决策信号 ---
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📡 决策信号灯")
        # 综合评分逻辑
        dxy_trend = curr_dxy - df_price['DX-Y.NYB'].iloc[-12]
        real_yield = df_macro['Real_Yield_10Y'].iloc[-1] if not df_macro.empty else 0
        
        score = 0
        if dxy_trend < 0: score += 1
        if real_yield < (df_macro['Real_Yield_10Y'].iloc[-5] if not df_macro.empty else 0): score += 1
        if curr_gld > df_price['GLD'].rolling(20).mean().iloc[-1]: score += 1
        
        if score >= 2:
            st.success(f"评分: {score} | 多头强势")
        elif score <= 0:
            st.error(f"评分: {score} | 空头强势")
        else:
            st.warning(f"评分: {score} | 震荡洗盘")
        
        st.write("**因子详情：**")
        st.write(f"1. 美元(1H): {'📉 走弱' if dxy_trend < 0 else '📈 走强'}")
        st.write(f"2. 实际利率: {real_yield:.2f}%")

    with c2:
        st.subheader("📊 走势共振 (GLD vs DXY)")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df_price.index, y=df_price['GLD'], name="GLD", line=dict(color="gold")), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_price.index, y=df_price['DX-Y.NYB'], name="DXY (右轴)", line=dict(color="white", dash='dot')), secondary_y=True)
        fig.update_layout(height=400, template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("无法加载实时行情，请检查网络连接。")

st.caption("注：ETF份额由 yfinance 实时获取；宏观储备数据由 FRED 每小时更新。")
