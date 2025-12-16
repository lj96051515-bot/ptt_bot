import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import os
import re

app = Flask(__name__)

# 存放抓到的正妹資料
beauty_posts = []

def get_real_image_url(ptt_link):
    """進入 PTT 文章抓取第一張 Imgur 圖片的直接連結"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(ptt_link, cookies={"over18": "1"}, headers=headers, timeout=5)
        # 尋找 imgur 連結 (包含 i.imgur 或 imgur.com)
        match = re.search(r'https?://(?:i\.)?imgur\.com/[A-Za-z0-9]+', res.text)
        if match:
            url = match.group(0)
            # 確保是直接圖檔連結，如果是網頁版網址就補上 .jpg
            if "i.imgur.com" not in url:
                url = url.replace("imgur.com", "i.imgur.com") + ".jpg"
            elif not url.endswith(('.jpg', '.png', '.jpeg')):
                url += ".jpg"
            return url
    except:
        pass
    return None

def fetch_beauty():
    global beauty_posts
    while True:
        try:
            url = "https://www.ptt.cc/bbs/Beauty/index.html"
            res = requests.get(url, cookies={"over18": "1"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            
            temp_list = []
            articles = soup.select("div.r-ent")
            
            for art in articles:
                push = art.select_one("div.nrec span")
                # 篩選 30 推以上
                push_num = 100 if push and push.text == "爆" else int(push.text) if (push and push.text.isdigit()) else 0
                
                t_tag = art.select_one("div.title a")
                if t_tag and "[正妹]" in t_tag.text and push_num >= 30:
                    art_url = "https://www.ptt.cc" + t_tag["href"]
                    img_url = get_real_image_url(art_url) # 去文章裡抓圖
                    
                    if img_url:
                        temp_list.append({
                            "title": t_tag.text,
                            "url": art_url,
                            "img": img_url,
                            "push": push_num
                        })
            
            beauty_posts = temp_list
            print(f"[{time.strftime('%H:%M:%S')}] 抓取完成，共有 {len(beauty_posts)} 篇正妹圖")
        except Exception as e:
            print(f"錯誤: {e}")
        
        time.sleep(300) # 每 5 分鐘掃描一次即可

@app.route('/')
def home():
    style = """
    <style>
        body { font-family: 'Microsoft JhengHei', sans-serif; background: #121212; color: #fff; text-align: center; }
        .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 20px; }
        .card { width: 300px; background: #1e1e1e; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5); transition: 0.3s; }
        .card:hover { transform: scale(1.05); }
        .card img { width: 100%; height: 350px; object-fit: cover; cursor: pointer; }
        .info { padding: 15px; font-size: 14px; }
        .push { color: #ff4081; font-weight: bold; font-size: 18px; }
        a { text-decoration: none; color: #4dabf5; }
        h1 { margin-top: 30px; color: #ff4081; }
    </style>
    """
    
    cards = ""
    for post in beauty_posts:
        cards += f"""
        <div class='card'>
            <a href='{post['url']}' target='_blank'>
                <img src='{post['img']}' onerror="this.src='https://via.placeholder.com/300x350?text=圖片載入失敗'">
                <div class='info'>
                    <span class='push'>{post['push']}推</span><br>
                    {post['title']}
                </div>
            </a>
        </div>
        """
    
    if not cards:
        cards = "<p>目前首頁尚無 30 推以上正妹，請稍候再重新整理...</p>"

    return f"""
    <html>
        <head>
            <title>PTT 正妹牆</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            {style}
        </head>
        <body>
            <h1>🔥 PTT 表特版精選 (30推+)</h1>
            <div class='grid'>{cards}</div>
        </body>
    </html>
    """

if __name__ == "__main__":
    threading.Thread(target=fetch_beauty, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
