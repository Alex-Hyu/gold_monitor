import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os

# ==========================================
# 1. 配置 FRED API KEY
# ==========================================
os.environ["FRED_API_KEY"] = "c804807c4d5649ebeba394d4ab50f3c1"

st.set_page_config(layout="wide", page_title="Gold/Silver Macro Quant Pro")

# ==========================================
# 2. 数据抓取逻辑
# ==========================================

@st.cache_data(ttl=3600)  # 宏观数据每小时更新一次即可
def get_fred_macro_data():
    """从美联储获取核心定价指标"""
    start = datetime.datetime.now() - datetime.timedelta(days=180)
    end = datetime.datetime.now()
    try:
        # DFII10: 10Y实际利率 (黄金负相关之王)
        # T10YIE: 10Y盈亏平衡通胀率 (抗通胀逻辑)
        # WALCL: 美联储资产负债表 (流动性逻辑)
        df = web.DataReader(["DFII10", "T10YIE", "WALCL"], "fred", start, end)
        df.columns = ['Real_Yield_10Y', 'Inflation_10Y', 'Fed_Balance']
        # 填充缺失值（FRED周末不更新）
        df = df.fillna(method='ffill')
        return df
    except Exception as e:
        st.error(f"FRED数据抓取失败，请检查API Key或网络: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300) # 市场价格每5分钟刷新
def get_realtime_prices():
    """获取黄金、白银、美元、美债实时价格"""
    tickers = {
        "GLD": "GLD", 
        "SLV": "SLV", 
        "DXY": "DX-Y.NYB", 
        "US10Y": "^TNX"
    }
    data = yf.download(list(tickers.values()), period="5d", interval="5m")
    return data['Close']

# ==========================================
# 3. 页面核心逻辑
# ==========================================

st.title("🏆 黄金白银宏观全维度仪表盘 (FRED API 官方版)")
st.caption("当前监控点：10Y实际利率、美元指数、金银比、日内期权动量")

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
    dxy_change = curr_dxy - df_price['DX-Y.NYB'].iloc[-12] # 过去1小时
    gld_change = curr_gld - df_price['GLD'].iloc[-2]
    
    m1.metric("GLD 实时价", f"${curr_gld:.2f}", f"{gld_change:.2f}")
    m2.metric("DXY 美元指数", f"{curr_dxy:.2f}", f"{dxy_change:.2f}", delta_color="inverse")
    m3.metric("10Y 实际利率", f"{curr_real_yield:.2f}%", f"{curr_real_yield - df_macro['Real_Yield_10Y'].iloc[-2]:.2f}%", delta_color="inverse")
    m4.metric("金银比 (GSR)", f"{curr_gsr:.2f}")

    # --- 中间层：信号触发引擎 ---
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📡 日内期权决策信号")
        
        # 逻辑：实际利率 < 1% 且正在下降 + 美元走弱 = 黄金/白银买入 Call
        score = 0
        if dxy_change < 0: score += 1
        if curr_real_yield < df_macro['Real_Yield_10Y'].iloc[-2]: score += 1
        if curr_gld > df_price['GLD'].rolling(20).mean().iloc[-1]: score += 1
        
        if score >= 2:
            st.success(f"综合评分: {score} | 状态：多头共振强劲")
            st.info("💡 建议：观察 GLD 5min 回调不破 VWAP 布局 Call")
        elif score <= 0:
            st.error(f"综合评分: {score} | 状态：空头动能占优")
            st.info("💡 建议：谨防跳水，可关注 Put 机会")
        else:
            st.warning(f"综合评分: {score} | 状态：震荡偏弱")
            st.info("💡 建议：信号不统一，缩减仓位")

        # 详细因子
        st.write(f"- 美元指数 (1H): {'📉 走弱 (利好)' if dxy_change < 0 else '📈 走强 (利空)'}")
        st.write(f"- 10Y实际利率: {'📉 下降 (利好)' if curr_real_yield < df_macro['Real_Yield_10Y'].iloc[-2] else '📈 回升 (利空)'}")
        st.write(f"- 价格动能 (MA20): {'🟢 均线上方' if curr_gld > df_price['GLD'].rolling(20).mean().iloc[-1] else '🔴 均线下方'}")

    with c2:
        st.subheader("📊 跨市场对比图 (GLD vs Real Yield)")
        # 绘制背离观察图
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df_price.index, y=df_price['GLD'], name="GLD 价格", line=dict(color="gold")), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_macro.index[-20:], y=df_macro['Real_Yield_10Y'].iloc[-20:], name="10Y实际利率 (右轴)", line=dict(color="cyan")), secondary_y=True)
        
        fig.update_layout(height=350, template="plotly_dark", margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig, use_container_width=True)

    # --- 底层：趋势与宏观背景 ---
    st.markdown("---")
    st.subheader("📅 宏观背景趋势 (过去180天)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        # 通胀预期走势
        st.write("10Y 盈亏平衡通胀率 (Inflation Expectation)")
        st.line_chart(df_macro['Inflation_10Y'])
    with col_b:
        # 联储缩表进度
        st.write("美联储资产负债表规模 (WALCL)")
        st.area_chart(df_macro['Fed_Balance'])

else:
    st.warning("等待数据加载中... 如果长时间无反应，请检查你的网络是否能访问 Yahoo Finance 和 FRED。")

# 底部说明
st.caption(f"最后更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据源: FRED & Yahoo Finance")