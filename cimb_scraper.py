import requests
from bs4 import BeautifulSoup
import streamlit as st
import datetime

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
        return "未能定位到价格表格"
    except Exception as e:
        return f"抓取异常: {e}"

def get_tng_emas_rates():
    """
    TNG 代理抓取模块。
    由于 TNG eWallet 无公开网页，且 e-Mas 产品底层其实由 CIMB 提供，
    此处演示代码暂且复用 CIMB 的数据源，以便在 UI 上搭建多行对比结构。
    """
    cimb_data = get_cimb_gold_rates()
    
    if isinstance(cimb_data, dict):
        return {
            "Bank": "Touch 'n Go e-Mas",
            "Bank Selling (RM/g)": cimb_data['Bank Selling (RM/g)'],
            "Bank Buying (RM/g)": cimb_data['Bank Buying (RM/g)'],
            "Spread (RM)": cimb_data['Spread (RM)'],
            "Note": "App 封闭数据源 (当前与 CIMB eGIA 挂钩同步)"
        }
    return "TNG 数据源异常"


# --- 2. Streamlit 多平台网页前端模块 ---

# 页面基础设置
st.set_page_config(page_title="MY Gold Spread", layout="centered")

st.title("🏦 大马本地黄金利差监控器")
st.markdown("实时追踪本地银行/电子钱包的实体金与纸黄金买卖点差，寻找最佳入场时机。")
st.divider()

if st.button("🔄 一键获取全部平台行情", type="primary"):
    with st.spinner("正在并发获取各个平台的数据..."):
        
        # 分别调用各个平台的抓取函数
        cimb_result = get_cimb_gold_rates()
        tng_result = get_tng_emas_rates()
        
        st.success(f"✅ 数据更新完成！(更新时间: {datetime.datetime.now().strftime('%H:%M:%S')})")
        
        # 将结果放入列表，利用循环渲染，这种架构方便您以后无限添加新银行
        platforms = [cimb_result, tng_result]
        
        for res in platforms:
            if isinstance(res, dict):
                # 渲染单独的银行区块
                st.markdown(f"### 🟡 {res['Bank']}")
                
                # 如果有备注信息（比如 TNG 的代理说明），就显示出来
                if "Note" in res:
                    st.caption(f"ℹ️ {res['Note']}")
                    
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="📈 平台卖出 (您买入)", value=f"RM {res['Bank Selling (RM/g)']}")
                with col2:
                    st.metric(label="📉 平台买入 (您卖出)", value=f"RM {res['Bank Buying (RM/g)']}")
                with col3:
                    st.metric(label="⚖️ 买卖利差 (Spread)", value=f"RM {res['Spread (RM)']}")
                
                st.divider()
            else:
                st.error(f"❌ 抓取失败: {res}")