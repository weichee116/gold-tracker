import requests
from bs4 import BeautifulSoup
import streamlit as st  # 必须在最上方告诉 Python 什么是 st
import datetime         # 引入时间库用来显示更新时间

# --- 1. 数据抓取模块 ---
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
        return "未能定位到价格表格，请检查银行网页结构是否发生改版。"
    except Exception as e:
        return f"抓取异常: {e}"

# --- 2. Streamlit 网页前端美化模块 ---
st.title("🏦 大马银行黄金利差监控器")
st.markdown("实时追踪本地银行实体金/纸黄金买卖点差，寻找最佳入场时机。")

st.divider()

st.markdown("#### 🟡 当前监控：CIMB eGIA")

if st.button("🔄 获取最新实时行情", type="primary"):
    with st.spinner("正在模拟浏览器前往 CIMB 官网抓取数据..."):
        result = get_cimb_gold_rates()
        
        if isinstance(result, dict):
            st.success(f"✅ 数据抓取成功！(更新时间: {datetime.datetime.now().strftime('%H:%M:%S')})")
            
            # 创建三个并排的列显示数据卡片
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="📈 银行卖出价 (您买入)", value=f"RM {result['Bank Selling (RM/g)']}")
            with col2:
                st.metric(label="📉 银行买入价 (您卖出)", value=f"RM {result['Bank Buying (RM/g)']}")
            with col3:
                st.metric(label="⚖️ 买卖利差 (Spread)", value=f"RM {result['Spread (RM)']}")

            st.divider()
            
            with st.expander("🛠️ 查看开发者原始数据 (JSON)"):
                st.json(result)
        else:
            st.error(f"❌ 抓取失败：{result}")