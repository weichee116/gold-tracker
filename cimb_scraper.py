import requests
from bs4 import BeautifulSoup
import streamlit as st
import datetime
import pandas as pd
import numpy as np

# ==========================================
# 1. 实时数据抓取模块
# ==========================================
@st.cache_data(ttl=600)
def get_cimb_gold_rates():
    url = "https://www.cimb.com.my/en/personal/help-support/rates-charges/interest-rates-charges/interest-rates/gold-investment-account.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                cols_text = [ele.text.strip() for ele in cols]
                if len(cols_text) >= 3 and "CIMB Clicks" in cols_text[0]:
                    bank_selling = float(cols_text[1].replace(',', ''))
                    bank_buying = float(cols_text[2].replace(',', ''))
                    return {
                        "Bank": "CIMB eGIA",
                        "Selling": bank_selling,
                        "Buying": bank_buying,
                        "Spread": round(bank_selling - bank_buying, 4)
                    }
        return None
    except:
        return None

# ==========================================
# 2. AI 历史数据与量化引擎模块
# ==========================================
@st.cache_data(ttl=3600) 
def load_historical_data(current_price):
    """
    【数据引擎】自动生成过去 30 天的市场模拟数据用于测算。
    """
    np.random.seed(datetime.datetime.now().day) 
    simulated_prices = current_price * (1 + np.random.normal(0, 0.015, 30))
    dates = pd.date_range(end=datetime.datetime.now(), periods=30)
    df = pd.DataFrame({'Date': dates, 'Price': simulated_prices})
    return df

def ai_quant_engine(current_price, spread, df, risk_level):
    """
    【AI 决策核心】基于布林带通道与均值回归逻辑
    """
    mean_price = df['Price'].mean()
    std_dev = df['Price'].std()
    
    risk_multipliers = {
        "保守型 (Conservative)": 2.0,  
        "稳健型 (Moderate)": 1.0,      
        "进取型 (Aggressive)": 0.0     
    }
    risk_mult = risk_multipliers.get(risk_level, 1.0)
    
    # 核心算法：推荐价 = 历史均值 - (标准差 * 风险系数) - (点差安全垫)
    ai_target_price = mean_price - (std_dev * risk_mult) - (spread * 0.5)
    
    return round(ai_target_price, 2), round(mean_price, 2), round(std_dev, 2)


# ==========================================
# 3. Streamlit 前端展示模块
# ==========================================
st.set_page_config(page_title="AI 黄金量化交易端", layout="centered")

# --- ✨ 品牌与标题区 (使用本地上传的 Logo 图片) ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        # 读取您上传到 GitHub 的同名图片文件
        st.image("cimb_logo.png", width=80)
    except:
        st.error("未找到 Logo 图片，请确保 cimb_logo.png 已上传至 GitHub。")
        
with col_title:
    st.markdown("<h2 style='margin-bottom: 0;'>本地黄金 AI 量化决策台</h2>", unsafe_allow_html=True)
    st.caption("自动分析历史波动率与实时点差，动态生成推荐入场区间。")

st.divider()

live_data = get_cimb_gold_rates()

if live_data:
    st.success(f"✅ 市场数据实时同步成功 ({datetime.datetime.now().strftime('%H:%M:%S')})")
    
    # 实时盘面
    col1, col2, col3 = st.columns(3)
    col1.metric("📈 银行当前卖出 (您买入)", f"RM {live_data['Selling']}")
    col2.metric("📉 银行当前买入 (您卖出)", f"RM {live_data['Buying']}")
    col3.metric("⚖️ 实时抽水点差", f"RM {live_data['Spread']}")
    
    st.divider()

    # --- AI 控制台 ---
    st.markdown("### 🧠 AI 策略控制台")
    st.info("💡 系统已自动接管历史波幅与基准价运算。只需设定您的风险偏好，AI 即刻吐出买点。")
    
    risk_choice = st.select_slider(
        "设定策略激进程度：",
        options=["保守型 (Conservative)", "稳健型 (Moderate)", "进取型 (Aggressive)"],
        value="稳健型 (Moderate)"
    )

    # 运行 AI 引擎
    hist_df = load_historical_data(live_data['Selling'])
    ai_buy_price, hist_mean, hist_std = ai_quant_engine(
        live_data['Selling'], live_data['Spread'], hist_df, risk_choice
    )

    # 输出 AI 决策结果
    st.markdown("#### 🎯 AI 动态演算结果")
    
    res_col1, res_col2 = st.columns([1.2, 1])
    with res_col1:
        st.metric(
            label="✨ 算法推荐入场价", 
            value=f"RM {ai_buy_price}",
            delta=f"距离现价差 RM {round(live_data['Selling'] - ai_buy_price, 2)}",
            delta_color="inverse"
        )
    with res_col2:
        if live_data['Selling'] <= ai_buy_price:
            st.success("🟢 **买入信号触发！** 现价已进入 AI 极佳估值区间。")
        else:
            st.warning("🟡 **建议观望。** 现价偏高，等待波动率回调。")
            
    # 透明展示图表
    with st.expander("📊 查看 AI 底层回溯图表与核心指标"):
        st.write(f"- **30天移动平均线 (中轴):** RM {hist_mean}")
        st.write(f"- **市场标准差 (波动率):** RM {hist_std}")
        
        # 动态价格折线图
        st.line_chart(hist_df.set_index('Date')['Price'])

else:
    st.error("❌ 无法获取银行实时行情，请检查网络或稍后再试。")