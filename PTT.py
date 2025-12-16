import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import os
import re

app = Flask(__name__)

# 全域變數，存放資料
gossiping_logs = []
beauty_images = []

def fetch_data():
    global gossiping_logs, beauty_images
    cookies = {"over18": "1"}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    while True:
        try:
            # --- 1. 抓取八卦版最新 ---
            res = requests.get("https://www.ptt.cc/bbs/Gossiping/index.html", cookies=cookies, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            arts = soup.select("div.r-ent")
            g_content = f"<div class='section-title'>八卦版最新 ({time.strftime('%H:%M:%S')})</div>"
            for art in arts[:8]:
                t_tag = art.select_one("div.title a")
                if t_tag:
                    g_content += f"<div class='post'>· <a href='https://www.ptt.cc{t_tag['href']}' target='_blank'>{t_tag.text}</a></div>"
            gossiping_logs = [g_content]

            # --- 2. 抓取表特版 30 推以上 ---
            res_b = requests.get("https://www.ptt.cc/bbs/Beauty/index.html", cookies=cookies, timeout=10)
            soup_b = BeautifulSoup(res_b.text, "html.parser")
            beauty_list = []
            for art in soup_b.select("div.r-ent"):
                push = art.select_one("div.nrec span")
                push_num = 100 if push and push.text == "爆" else int(push.text) if push and push.text.isdigit() else 0
                
                t_tag = art.select_one("div.title a")
                if t_tag and "[正妹]" in t_tag.text and push_num >= 30:
                    # 進入文章抓第一張圖當縮圖
                    art_res = requests.get("https://www.ptt.cc" + t_tag["href"], cookies=cookies)
                    img_match = re.search(r'https?://[i.]*imgur\.com/[A-Za-z0-9]+\.(?:jpg|jpeg|png|gif)', art_res.text)
                    img_url = img_match.group(0) if img_match else ""
                    
                    beauty_list.append({
                        "title": t_tag.text,
                        "link": "https://www.ptt.cc" + t_tag["href"],
                        "push": push_num,
                        "img": img_url
                    })
            beauty_images = beauty_list

            print(f"[{time.strftime('%H:%M:%S')}] 數據已更新")
        except Exception as e:
            print(f"錯誤: {e}")
        
        time.sleep(60)

@app.route('/')
def home():
    style = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        .section-title { font-size: 1.5em; border-left: 5px solid #007bff; padding-left: 10px; margin: 20px 0; color: #007bff; }
        .post { background: #1e1e1e; padding: 10px; border-bottom: 1px solid #333; }
        .post a { color: #82b1ff; text-decoration: none; }
        .beauty-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .beauty-card { background: #1e1e1e; border-radius: 8px; overflow: hidden; border: 1px solid #333; }
        .beauty-card img { width: 100%; height: 150px; object-fit: cover; background: #000; }
        .beauty-info { padding: 8px; font-size: 0.9em; }
        .push-tag { background: #ff5252; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; }
    </style>
    """
    
    # 組合八卦版內容
    g_html = "".join(gossiping_logs) if gossiping_logs else "載入中..."
    
    # 組合表特版內容
    b_html = "<div class='section-title'>表特精選 (30推+)</div><div class='beauty-grid'>"
    for item in beauty_images:
        img_tag = f"<img src='{item['img']}'>" if item['img'] else "<div style='height:150px; background:#333; text-align:center; line-height:150px;'>無圖片</div>"
        b_html += f"""
        <div class='beauty-card'>
            <a href='{item['link']}' target='_blank'>
                {img_tag}
                <div class='beauty-info'>
                    <span class='push-tag'>{item['push']}推</span> {item['title']}
                </div>
            </a>
        </div>
        """
    b_html += "</div>"
    
    meta = "<meta http-equiv='refresh' content='60'>"
    return f"<html><head>{meta}{style}</head><body><div class='container'>{g_html}{b_html}</div></body></html>"

if __name__ == "__main__":
    t = threading.Thread(target=fetch_data)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
