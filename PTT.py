import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import os

# 建立 Flask 網頁伺服器
app = Flask(__name__)

# 用來存放最新 LOG 的變數
logs = []

def fetch_ptt_job():
    global logs
    board = "Gossiping"
    url = f"https://www.ptt.cc/bbs/{board}/index.html"
    cookies = {"over18": "1"}
    
    while True:
        try:
            res = requests.get(url, cookies=cookies, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.select("div.r-ent")
            
            current_time = time.strftime('%H:%M:%S')
            new_data = f"==== 更新時間 ({current_time}) ====<br>"
            
            for art in articles[:10]: # 抓前10則
                title_tag = art.select_one("div.title a")
                if title_tag:
                    title = title_tag.text
                    link = "https://www.ptt.cc" + title_tag["href"]
                    new_data += f"· {title} | <a href='{link}' target='_blank'>連結</a><br>"
            
            # 把最新的放在最上面，只保留最近 5 次紀錄
            logs.insert(0, new_data + "<hr>")
            logs = logs[:5]
            
            print(f"[{current_time}] 已抓取最新文章")
        except Exception as e:
            print(f"抓取錯誤: {e}")
        
        time.sleep(60)

# 定義網頁的首頁
@app.route('/')
def home():
    if not logs:
        return "正在初始化數據，請稍候..."
    return "<h1>PTT 即時監控系統</h1>" + "".join(logs)

if __name__ == "__main__":
    # 開啟一個線程專門跑爬蟲，避免卡住網頁伺服器
    thread = threading.Thread(target=fetch_ptt_job)
    thread.daemon = True
    thread.start()

    # 啟動網頁伺服器，Render 會給予一個 PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
