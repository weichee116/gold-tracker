import requests
from bs4 import BeautifulSoup
import streamlit as st
import datetime

# ==========================================
# 1. 数据抓取模块 (带智能缓存防止被封IP)
# ==========================================
# 设置缓存有效期为 600 秒 (10分钟)，拖动滑块测算时不会重复爬取网页
@st.cache_data(ttl=600) 
def get_cimb_gold_rates():
    url = "https://www.cimb.com.my/en/personal/help-support/rates-charges/interest-rates-charges/interest-rates/gold-investment-account.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
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
                    spread = round(bank_selling - bank_buying, 4)
                    
                    return {
                        "Bank": "CIMB eGIA",
                        "Bank Selling (RM/g)": bank_selling,
                        "Bank Buying (RM/g)": bank_buying,
                        "Spread (RM)": spread
                    }
        return None # 抓取失败返回 None
    except Exception as e:
        return None

# ==========================================
# 2. 网页前端与动态测算 UI 模块
# ==========================================

st.set_page_config(page_title="本地黄金利差与买点监控", layout="centered")

# --- 顶部：实时行情区 ---
cimb_logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/CIMB_Group_logo.svg/512px-CIMB_Group_logo.svg.png"

st.markdown(
    f"""
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <img src="{cimb_logo_url}" width="100" style="margin-right: 15px;">
        <h2 style="margin: 0;">大马黄金交易测算台</h2>
    </div>
    <p style="color: gray; font-size: 14px;">实时追踪 CIMB eGIA 买卖点差，动态计算推荐入场区间。</p>
    """, 
    unsafe_allow_html=True
)
st.divider()

# 获取实时数据
live_data = get_cimb_gold_rates()

if live_data:
    st.success(f"✅ 实时行情已连线 (数据缓存刷新于: {datetime.datetime.now().strftime('%H:%M:%S')})")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📈 当前挂牌卖出 (您买入价)", value=f"RM {live_data['Bank Selling (RM/g)']}")
    with col2:
        st.metric(label="📉 当前挂牌买入 (您卖出价)", value=f"RM {live_data['Bank Buying (RM/g)']}")
    with col3:
        st.metric(label="⚖️ 银行抽水点差 (Spread)", value=f"RM {live_data['Spread (RM)']}")
    
    st.divider()

    # --- 核心：交互式动态买点测算区 ---
    st.markdown("### 🎯 动态推荐买点测算 (策略模拟)")
    st.info("💡 调整下方参数，系统将基于您的风险偏好和历史波动，自动计算建议入场价。")

    # 参数输入区
    with st.container():
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            # 默认近一年历史低点示例，用户可自行修改
            hist_low = st.number_input("📉 设定期望历史低位支撑 (RM/g)", value=380.0, step=1.0)
        with row1_col2:
            # 默认近一年历史高点示例，用户可自行修改
            hist_high = st.number_input("📈 设定期望历史高位阻力 (RM/g)", value=420.0, step=1.0)

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            risk_level = st.selectbox("⚖️ 您的风险偏好等级", ["保守型 (Conservative)", "稳健型 (Moderate)", "进取型 (Aggressive)"])
        with row2_col2:
            buffer_pct = st.slider("🛡️ 差价缓冲安全垫 (%)", min_value=0, max_value=100, value=50, 
                                   help="0%代表完全不考虑点差，100%代表将整个点差作为安全垫扣除")

    # --- 测算逻辑 ---
    # 根据风险偏好决定吃进历史波幅的比例 (保守=贴近低位买，进取=接受较高位买)
    risk_factors = {"保守型 (Conservative)": 0.15, "稳健型 (Moderate)": 0.35, "进取型 (Aggressive)": 0.60}
    
    price_range = hist_high - hist_low
    # 基础目标价
    base_target = hist_low + (price_range * risk_factors[risk_level])
    
    # 将银行点差 (Spread) 结合安全垫计算，进一步压低推荐买入价
    buffer_deduction = live_data['Spread (RM)'] * (buffer_pct / 100.0)
    recommended_buy_price = round(base_target - buffer_deduction, 2)

    # --- 测算结果展示 ---
    st.markdown("#### 📊 智能演算结果")
    
    res_col1, res_col2 = st.columns([1, 2])
    with res_col1:
        st.metric(label="✨ 策略推荐买入价位", value=f"RM {recommended_buy_price}", 
                  delta=f"距离现价差 RM {round(live_data['Bank Selling (RM/g)'] - recommended_buy_price, 2)}", 
                  delta_color="inverse")
    
    with res_col2:
        # 用进度条做一个简易的可视化：当前现价处于什么位置
        current_price = live_data['Bank Selling (RM/g)']
        if current_price > hist_high:
            progress_val = 100
        elif current_price < hist_low:
            progress_val = 0
        else:
            progress_val = int(((current_price - hist_low) / price_range) * 100)
            
        st.markdown(f"**当前金价处于您设定区间的：{progress_val}% 水位**")
        st.progress(progress_val)
        
        if current_price <= recommended_buy_price:
            st.success("✅ **现价已进入推荐买入区间！** (适合分批建仓)")
        else:
            st.warning("⏳ 现价高于推荐买位，建议继续耐心等待或采用定投策略。")

    st.caption("⚠️ 免责声明：以上测算数据仅基于数学逻辑模拟，不构成任何真实投资建议。投资需谨慎。")

else:
    st.error("❌ 无法获取银行实时行情，请检查网络或稍后再试。")