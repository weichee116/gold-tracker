import datetime # 顶部记得加这个，用来显示更新时间

# ====== 关键修改部分：适配 Streamlit 网页显示 ======

st.title("🏦 大马银行黄金利差监控器")
st.markdown("实时追踪本地银行实体金/纸黄金买卖点差，寻找最佳入场时机。")

# 添加一个好看的分割线
st.divider()

st.markdown("#### 🟡 当前监控：CIMB eGIA")

# 把按钮设置为主色调 (type="primary")，视觉更突出
if st.button("🔄 获取最新实时行情", type="primary"):
    with st.spinner("正在模拟浏览器前往 CIMB 官网抓取数据..."):
        result = get_cimb_gold_rates()
        
        if isinstance(result, dict):
            st.success(f"✅ 数据抓取成功！(更新时间: {datetime.datetime.now().strftime('%H:%M:%S')})")
            
            # --- ✨ 核心美化排版区 ---
            # 创建三个并排的列
            col1, col2, col3 = st.columns(3)
            
            # 使用 metric 组件展示核心指标，非常像专业的看盘软件
            with col1:
                st.metric(
                    label="📈 银行卖出价 (您买入)", 
                    value=f"RM {result['Bank Selling (RM/g)']}"
                )
            
            with col2:
                st.metric(
                    label="📉 银行买入价 (您卖出)", 
                    value=f"RM {result['Bank Buying (RM/g)']}"
                )
            
            with col3:
                # 重点突出利差
                st.metric(
                    label="⚖️ 买卖利差 (Spread)", 
                    value=f"RM {result['Spread (RM)']}"
                )
            # ---------------------------

            st.divider()
            
            # 把原本丑丑的 JSON 折叠起来，平时不占地方，但 Debug 时可以点开看
            with st.expander("🛠️ 查看开发者原始数据 (JSON)"):
                st.json(result)
                
        else:
            st.error(f"❌ 抓取失败：{result}")