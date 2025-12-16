import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import os
import re

app = Flask(__name__)
beauty_posts = []

def get_real_image_url(ptt_link):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(ptt_link, cookies={"over18": "1"}, headers=headers, timeout=5)
        # 匹配 Imgur 連結
        match = re.search(r'https?://(?:i\.)?imgur\.com/[A-Za-z0-9]+', res.text)
        if match:
            url = match.group(0)
            if "i.imgur.com" not in url:
                url = url.replace("imgur.com", "i.imgur.com") + ".jpg"
            elif not url.endswith(('.jpg', '.png', '.jpeg')):
                url += ".jpg"
            return url
    except:
        pass
    return None

def fetch_beauty_massive():
    global beauty_posts
    while True:
        try:
            cookies = {"over18": "1"}
            base_url = "https://www.ptt.cc/bbs/Beauty/index.html"
            res = requests.get(base_url, cookies=cookies, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 取得最新頁碼
            prev_link = soup.select("div.btn-group-paging a")[1]["href"]
            latest_page = int(re.search(r'index(\d+)\.html', prev_link).group(1)) + 1
            
            all_temp_posts = []
            # --- 關鍵修正：往回翻 10 頁 ---
            print("正在深度掃描最近 10 頁的文章...")
            for p in range(latest_page, latest_page - 10, -1):
                p_url = f"https://www.ptt.cc/bbs/Beauty/index{p}.html"
                p_res = requests.get(p_url, cookies=cookies, timeout=10)
                p_soup = BeautifulSoup(p_res.text, "html.parser")
                
                for art in p_soup.select("div.r-ent"):
                    push = art.select_one("div.nrec span")
                    push_num = 100 if push and push.text == "爆" else int(push.text) if (push and push.text.isdigit()) else 0
                    
                    t_tag = art.select_one("div.title a")
                    if t_tag and "[正妹]" in t_tag.text and push_num >= 30:
                        art_url = "https://www.ptt.cc" + t_tag["href"]
                        # 避免重複抓取
                        if not any(d['url'] == art_url for d in all_temp_posts):
                            img = get_real_image_url(art_url)
                            if img:
                                all_temp_posts.append({
                                    "title": t_tag.text,
                                    "url": art_url,
                                    "img": img,
                                    "push": push_num
                                })
            
            # 按推文數排序，把「爆」的排最前面
            beauty_posts = sorted(all_temp_posts, key=lambda x: x['push'], reverse=True)
            print(f"深度抓取完成，共 {len(beauty_posts)} 篇")
            
        except Exception as e:
            print(f"抓取發生錯誤: {e}")
        
        time.sleep(600) # 10分鐘掃一次就好，避免被PTT封鎖

@app.route('/')
def home():
    style = """
    <style>
        body { font-family: sans-serif; background: #000; color: #fff; margin: 0; }
        .header { background: #ff4081; padding: 20px; text-align: center; position: sticky; top: 0; z-index: 100; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; padding: 15px; }
        .card { position: relative; border-radius: 10px; overflow: hidden; background: #222; height: 400px; }
        .card img { width: 100%; height: 100%; object-fit: cover; }
        .overlay { position: absolute; bottom: 0; background: linear-gradient(transparent, rgba(0,0,0,0.8)); width: 100%; padding: 15px; box-sizing: border-box; }
        .push-badge { background: #ff4081; padding: 2px 8px; border-radius: 5px; font-weight: bold; margin-right: 5px; }
        a { color: white; text-decoration: none; font-size: 14px; }
    </style>
    """
    cards = "".join([f"""
        <div class='card'>
            <a href='{p['url']}' target='_blank'>
                <img src='{p['img']}' loading='lazy'>
                <div class='overlay'>
                    <span class='push-badge'>{p['push']}推</span> {p['title']}
                </div>
            </a>
        </div>
    """ for p in beauty_posts])

    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{style}</head>
        <body>
            <div class='header'><h1>PTT 正妹雷達 (近期熱門)</h1></div>
            <div class='grid'>{cards if cards else '<h2>正在深入挖掘 PTT 歷史資料，請 30 秒後重新整理...</h2>'}</div>
        </body>
    </html>
    """

if __name__ == "__main__":
    threading.Thread(target=fetch_beauty_massive, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
