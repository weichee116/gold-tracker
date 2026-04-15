import requests
from bs4 import BeautifulSoup
import streamlit as st  # 新增：引入 Streamlit 库

def get_cimb_gold_rates():
    # ... (抓取逻辑与之前完全一致) ...
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

# ====== 关键修改部分：适配 Streamlit 网页显示 ======

st.title("🏦 马来西亚本地银行黄金利差监控")
st.markdown("当前测试数据源：**CIMB eGIA**")

# 添加一个交互按钮
if st.button("获取最新 CIMB 价格"):
    # 加一个加载动画，提升体验
    with st.spinner("正在模拟浏览器前往 CIMB 官网抓取数据..."):
        result = get_cimb_gold_rates()
        
        if isinstance(result, dict):
            st.success("✅ 抓取成功！")
            # 以漂亮的 JSON 结构卡片显示在网页上
            st.json(result)  
        else:
            st.error(f"❌ 抓取失败：{result}")