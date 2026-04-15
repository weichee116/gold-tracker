import requests
from bs4 import BeautifulSoup

def get_cimb_gold_rates():
    # CIMB 黄金挂牌价的官方公示页面
    url = "https://www.cimb.com.my/en/personal/help-support/rates-charges/interest-rates-charges/interest-rates/gold-investment-account.html"
    
    # 必须添加 User-Agent 伪装成正常桌面浏览器，否则极其容易被银行防火墙拦截 (抛出 403 Forbidden 错误)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 发送请求获取网页内容
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        
        # 使用 HTML 解析器解析网页源文件
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取网页中的所有表格
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                # 清除 HTML 标签与多余空格，只保留纯文本内容
                cols_text = [ele.text.strip() for ele in cols]
                
                # 寻找关键数据特征：定位到包含 'CIMB Clicks' (线上交易渠道) 的那一行
                if len(cols_text) >= 3 and "CIMB Clicks" in cols_text[0]:
                    # 提取银行卖出价和买入价，需移除可能存在的逗号后转为浮点数计算
                    bank_selling = float(cols_text[1].replace(',', ''))
                    bank_buying = float(cols_text[2].replace(',', ''))
                    
                    # 投资者最关心的：计算买卖利差 (Spread)
                    spread = round(bank_selling - bank_buying, 4)
                    
                    return {
                        "Bank": "CIMB eGIA",
                        "Bank Selling (RM/g)": bank_selling,
                        "Bank Buying (RM/g)": bank_buying,
                        "Spread (RM)": spread
                    }
                    
        return "未能定位到价格表格，请检查银行网页结构是否发生改版。"

    except requests.exceptions.RequestException as e:
        return f"网络请求失败 (可能触发反爬或网络波动): {e}"
    except Exception as e:
        return f"数据清洗报错: {e}"

# 本地测试入口
if __name__ == "__main__":
    print(get_cimb_gold_rates())