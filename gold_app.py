{\rtf1\ansi\ansicpg936\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import yfinance as yf\
import pandas as pd\
import pandas_datareader.data as web\
import plotly.graph_objects as go\
from plotly.subplots import make_subplots\
import datetime\
import os\
\
# ==========================================\
# 1. \uc0\u37197 \u32622  FRED API KEY\
# ==========================================\
os.environ["FRED_API_KEY"] = "c804807c4d5649ebeba394d4ab50f3c1"\
\
st.set_page_config(layout="wide", page_title="Gold/Silver Macro Quant Pro")\
\
# ==========================================\
# 2. \uc0\u25968 \u25454 \u25235 \u21462 \u36923 \u36753 \
# ==========================================\
\
@st.cache_data(ttl=3600)  # \uc0\u23439 \u35266 \u25968 \u25454 \u27599 \u23567 \u26102 \u26356 \u26032 \u19968 \u27425 \u21363 \u21487 \
def get_fred_macro_data():\
    """\uc0\u20174 \u32654 \u32852 \u20648 \u33719 \u21462 \u26680 \u24515 \u23450 \u20215 \u25351 \u26631 """\
    start = datetime.datetime.now() - datetime.timedelta(days=180)\
    end = datetime.datetime.now()\
    try:\
        # DFII10: 10Y\uc0\u23454 \u38469 \u21033 \u29575  (\u40644 \u37329 \u36127 \u30456 \u20851 \u20043 \u29579 )\
        # T10YIE: 10Y\uc0\u30408 \u20111 \u24179 \u34913 \u36890 \u32960 \u29575  (\u25239 \u36890 \u32960 \u36923 \u36753 )\
        # WALCL: \uc0\u32654 \u32852 \u20648 \u36164 \u20135 \u36127 \u20538 \u34920  (\u27969 \u21160 \u24615 \u36923 \u36753 )\
        df = web.DataReader(["DFII10", "T10YIE", "WALCL"], "fred", start, end)\
        df.columns = ['Real_Yield_10Y', 'Inflation_10Y', 'Fed_Balance']\
        # \uc0\u22635 \u20805 \u32570 \u22833 \u20540 \u65288 FRED\u21608 \u26411 \u19981 \u26356 \u26032 \u65289 \
        df = df.fillna(method='ffill')\
        return df\
    except Exception as e:\
        st.error(f"FRED\uc0\u25968 \u25454 \u25235 \u21462 \u22833 \u36133 \u65292 \u35831 \u26816 \u26597 API Key\u25110 \u32593 \u32476 : \{e\}")\
        return pd.DataFrame()\
\
@st.cache_data(ttl=300) # \uc0\u24066 \u22330 \u20215 \u26684 \u27599 5\u20998 \u38047 \u21047 \u26032 \
def get_realtime_prices():\
    """\uc0\u33719 \u21462 \u40644 \u37329 \u12289 \u30333 \u38134 \u12289 \u32654 \u20803 \u12289 \u32654 \u20538 \u23454 \u26102 \u20215 \u26684 """\
    tickers = \{\
        "GLD": "GLD", \
        "SLV": "SLV", \
        "DXY": "DX-Y.NYB", \
        "US10Y": "^TNX"\
    \}\
    data = yf.download(list(tickers.values()), period="5d", interval="5m")\
    return data['Close']\
\
# ==========================================\
# 3. \uc0\u39029 \u38754 \u26680 \u24515 \u36923 \u36753 \
# ==========================================\
\
st.title("\uc0\u55356 \u57286  \u40644 \u37329 \u30333 \u38134 \u23439 \u35266 \u20840 \u32500 \u24230 \u20202 \u34920 \u30424  (FRED API \u23448 \u26041 \u29256 )")\
st.caption("\uc0\u24403 \u21069 \u30417 \u25511 \u28857 \u65306 10Y\u23454 \u38469 \u21033 \u29575 \u12289 \u32654 \u20803 \u25351 \u25968 \u12289 \u37329 \u38134 \u27604 \u12289 \u26085 \u20869 \u26399 \u26435 \u21160 \u37327 ")\
\
# \uc0\u21152 \u36733 \u25968 \u25454 \
with st.spinner('\uc0\u27491 \u22312 \u21516 \u27493 \u20840 \u29699 \u23439 \u35266 \u21450 \u23454 \u26102 \u20215 \u26684 \u25968 \u25454 ...'):\
    df_macro = get_fred_macro_data()\
    df_price = get_realtime_prices()\
\
if not df_price.empty and not df_macro.empty:\
    # --- \uc0\u39030 \u23618  Metric \u30475 \u26495  ---\
    m1, m2, m3, m4 = st.columns(4)\
    \
    curr_gld = df_price['GLD'].iloc[-1]\
    curr_dxy = df_price['DX-Y.NYB'].iloc[-1]\
    curr_real_yield = df_macro['Real_Yield_10Y'].iloc[-1]\
    curr_gsr = curr_gld / df_price['SLV'].iloc[-1]\
    \
    # \uc0\u35745 \u31639 \u21464 \u21270 \u37327 \
    dxy_change = curr_dxy - df_price['DX-Y.NYB'].iloc[-12] # \uc0\u36807 \u21435 1\u23567 \u26102 \
    gld_change = curr_gld - df_price['GLD'].iloc[-2]\
    \
    m1.metric("GLD \uc0\u23454 \u26102 \u20215 ", f"$\{curr_gld:.2f\}", f"\{gld_change:.2f\}")\
    m2.metric("DXY \uc0\u32654 \u20803 \u25351 \u25968 ", f"\{curr_dxy:.2f\}", f"\{dxy_change:.2f\}", delta_color="inverse")\
    m3.metric("10Y \uc0\u23454 \u38469 \u21033 \u29575 ", f"\{curr_real_yield:.2f\}%", f"\{curr_real_yield - df_macro['Real_Yield_10Y'].iloc[-2]:.2f\}%", delta_color="inverse")\
    m4.metric("\uc0\u37329 \u38134 \u27604  (GSR)", f"\{curr_gsr:.2f\}")\
\
    # --- \uc0\u20013 \u38388 \u23618 \u65306 \u20449 \u21495 \u35302 \u21457 \u24341 \u25806  ---\
    st.markdown("---")\
    c1, c2 = st.columns([1, 2])\
    \
    with c1:\
        st.subheader("\uc0\u55357 \u56545  \u26085 \u20869 \u26399 \u26435 \u20915 \u31574 \u20449 \u21495 ")\
        \
        # \uc0\u36923 \u36753 \u65306 \u23454 \u38469 \u21033 \u29575  < 1% \u19988 \u27491 \u22312 \u19979 \u38477  + \u32654 \u20803 \u36208 \u24369  = \u40644 \u37329 /\u30333 \u38134 \u20080 \u20837  Call\
        score = 0\
        if dxy_change < 0: score += 1\
        if curr_real_yield < df_macro['Real_Yield_10Y'].iloc[-2]: score += 1\
        if curr_gld > df_price['GLD'].rolling(20).mean().iloc[-1]: score += 1\
        \
        if score >= 2:\
            st.success(f"\uc0\u32508 \u21512 \u35780 \u20998 : \{score\} | \u29366 \u24577 \u65306 \u22810 \u22836 \u20849 \u25391 \u24378 \u21170 ")\
            st.info("\uc0\u55357 \u56481  \u24314 \u35758 \u65306 \u35266 \u23519  GLD 5min \u22238 \u35843 \u19981 \u30772  VWAP \u24067 \u23616  Call")\
        elif score <= 0:\
            st.error(f"\uc0\u32508 \u21512 \u35780 \u20998 : \{score\} | \u29366 \u24577 \u65306 \u31354 \u22836 \u21160 \u33021 \u21344 \u20248 ")\
            st.info("\uc0\u55357 \u56481  \u24314 \u35758 \u65306 \u35880 \u38450 \u36339 \u27700 \u65292 \u21487 \u20851 \u27880  Put \u26426 \u20250 ")\
        else:\
            st.warning(f"\uc0\u32508 \u21512 \u35780 \u20998 : \{score\} | \u29366 \u24577 \u65306 \u38663 \u33633 \u20559 \u24369 ")\
            st.info("\uc0\u55357 \u56481  \u24314 \u35758 \u65306 \u20449 \u21495 \u19981 \u32479 \u19968 \u65292 \u32553 \u20943 \u20179 \u20301 ")\
\
        # \uc0\u35814 \u32454 \u22240 \u23376 \
        st.write(f"- \uc0\u32654 \u20803 \u25351 \u25968  (1H): \{'\u55357 \u56521  \u36208 \u24369  (\u21033 \u22909 )' if dxy_change < 0 else '\u55357 \u56520  \u36208 \u24378  (\u21033 \u31354 )'\}")\
        st.write(f"- 10Y\uc0\u23454 \u38469 \u21033 \u29575 : \{'\u55357 \u56521  \u19979 \u38477  (\u21033 \u22909 )' if curr_real_yield < df_macro['Real_Yield_10Y'].iloc[-2] else '\u55357 \u56520  \u22238 \u21319  (\u21033 \u31354 )'\}")\
        st.write(f"- \uc0\u20215 \u26684 \u21160 \u33021  (MA20): \{'\u55357 \u57314  \u22343 \u32447 \u19978 \u26041 ' if curr_gld > df_price['GLD'].rolling(20).mean().iloc[-1] else '\u55357 \u56628  \u22343 \u32447 \u19979 \u26041 '\}")\
\
    with c2:\
        st.subheader("\uc0\u55357 \u56522  \u36328 \u24066 \u22330 \u23545 \u27604 \u22270  (GLD vs Real Yield)")\
        # \uc0\u32472 \u21046 \u32972 \u31163 \u35266 \u23519 \u22270 \
        fig = make_subplots(specs=[[\{"secondary_y": True\}]])\
        fig.add_trace(go.Scatter(x=df_price.index, y=df_price['GLD'], name="GLD \uc0\u20215 \u26684 ", line=dict(color="gold")), secondary_y=False)\
        fig.add_trace(go.Scatter(x=df_macro.index[-20:], y=df_macro['Real_Yield_10Y'].iloc[-20:], name="10Y\uc0\u23454 \u38469 \u21033 \u29575  (\u21491 \u36724 )", line=dict(color="cyan")), secondary_y=True)\
        \
        fig.update_layout(height=350, template="plotly_dark", margin=dict(l=10,r=10,t=30,b=10))\
        st.plotly_chart(fig, use_container_width=True)\
\
    # --- \uc0\u24213 \u23618 \u65306 \u36235 \u21183 \u19982 \u23439 \u35266 \u32972 \u26223  ---\
    st.markdown("---")\
    st.subheader("\uc0\u55357 \u56517  \u23439 \u35266 \u32972 \u26223 \u36235 \u21183  (\u36807 \u21435 180\u22825 )")\
    \
    col_a, col_b = st.columns(2)\
    with col_a:\
        # \uc0\u36890 \u32960 \u39044 \u26399 \u36208 \u21183 \
        st.write("10Y \uc0\u30408 \u20111 \u24179 \u34913 \u36890 \u32960 \u29575  (Inflation Expectation)")\
        st.line_chart(df_macro['Inflation_10Y'])\
    with col_b:\
        # \uc0\u32852 \u20648 \u32553 \u34920 \u36827 \u24230 \
        st.write("\uc0\u32654 \u32852 \u20648 \u36164 \u20135 \u36127 \u20538 \u34920 \u35268 \u27169  (WALCL)")\
        st.area_chart(df_macro['Fed_Balance'])\
\
else:\
    st.warning("\uc0\u31561 \u24453 \u25968 \u25454 \u21152 \u36733 \u20013 ... \u22914 \u26524 \u38271 \u26102 \u38388 \u26080 \u21453 \u24212 \u65292 \u35831 \u26816 \u26597 \u20320 \u30340 \u32593 \u32476 \u26159 \u21542 \u33021 \u35775 \u38382  Yahoo Finance \u21644  FRED\u12290 ")\
\
# \uc0\u24213 \u37096 \u35828 \u26126 \
st.caption(f"\uc0\u26368 \u21518 \u26356 \u26032 \u26102 \u38388 : \{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')\} | \u25968 \u25454 \u28304 : FRED & Yahoo Finance")}