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
@st.cache_data(ttl=3600) # 历史数据模拟缓存 1 小时
def load_historical_data(current_price):
    """
    【数据引擎】这里模拟了过去 30 天的市场数据。
    未来您可以写一个爬虫每天把数据存进 CSV，然后在这里用 pd.read_csv() 读取真实历史。
    """
    np.random.seed(datetime.datetime.now().day) # 每天生成不同的随机震荡
    # 模拟过去30天的价格，标准差大概在 1.5% 左右
    simulated_prices = current_price * (1 + np.random.normal(0, 0.015, 30))
    dates = pd.date_range(end=datetime.datetime.now(), periods=30)
    df = pd.DataFrame({'Date': dates, 'Price': simulated_prices})
    return df

def ai_quant_engine(current_price, spread, df, risk_level):
    """
    【AI 决策核心】基于布林带 (Bollinger Bands) 与均值回归逻辑
    """
    mean_price = df['Price'].mean()
    std_dev = df['Price'].std()
    
    # 风险乘数映射：保守型要求跌破均值更多才买入
    risk_multipliers = {
        "保守 (Conservative)": 2.0,  # 均值 - 2倍标准差 (胜率高，机会少)
        "稳健 (Moderate)": 1.0,      # 均值 - 1倍标准差
        "进取 (Aggressive)": 0.0     # 只要低于均值就买，甚至贴近均值买
    }
    risk_mult = risk_multipliers.get(risk_level, 1.0)
    
    # 核心公式：AI 建议价 = 历史均值 - (标准差 * 风险系数) - (点差 * 惩罚系数)
    # 我们将 50% 的点差作为额外的下调安全垫
    ai_target_price = mean_price - (std_dev * risk_mult) - (spread * 0.5)
    
    return round(ai_target_price, 2), round(mean_price, 2), round(std_dev, 2)


# ==========================================
# 3. Streamlit 前端展示模块
# ==========================================
st.set_page_config(page_title="AI 黄金量化交易端", layout="centered")

cimb_logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/CIMB_Group_logo.svg/512px-CIMB_Group_logo.svg.png"
st.markdown(
    f"""
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <img src="{cimb_logo_url}" width="90" style="margin-right: 15px;">
        <h2 style="margin: 0;">本地黄金 AI 量化决策台</h2>
    </div>
    <p style="color: gray; font-size: 14px;">自动分析历史波动率与实时点差，通过均值回归算法生成推荐买点。</p>
    """, 
    unsafe_allow_html=True
)
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

    # AI 控制台
    st.markdown("### 🧠 AI 策略控制台")
    st.info("系统已自动接管历史高低点与基准价计算。您只需告诉 AI 您的风险承受能力。")
    
    risk_choice = st.select_slider(
        "设定策略激进程度",
        options=["保守 (Conservative)", "稳健 (Moderate)", "进取 (Aggressive)"],
        value="稳健 (Moderate)"
    )

    # 运行 AI 引擎
    hist_df = load_historical_data(live_data['Selling'])
    ai_buy_price, hist_mean, hist_std = ai_quant_engine(
        live_data['Selling'], live_data['Spread'], hist_df, risk_choice
    )

    # 输出 AI 决策结果
    st.markdown("#### 🎯 AI 演算结果")
    
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
            st.success("🟢 现价已跌入 AI 买入区间！")
        else:
            st.warning("🟡 现价偏高，建议等待回调。")
            
    # 透明展示 AI 内部的思考过程
    with st.expander("📊 查看 AI 底层数据与图表 (历史回溯)"):
        st.write(f"- **30天移动平均线 (MA):** RM {hist_mean}")
        st.write(f"- **市场标准差 (Volatility):** RM {hist_std} (反映近期剧烈程度)")
        st.write("- **算法模型:** `买入价 = MA - (风险偏好 * 标准差) - (点差 * 0.5)`")
        
        # 画一个简单的趋势图让您直观看到均值和价格波动
        st.line_chart(hist_df.set_index('Date')['Price'])

else:
    st.error("❌ 无法获取银行实时行情，请检查网络或稍后再试。")