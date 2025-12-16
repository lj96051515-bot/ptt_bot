import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import os
import re

app = Flask(__name__)
gossip_posts = []

def fetch_gossip_100():
    global gossip_posts
    while True:
        try:
            cookies = {"over18": "1"}
            # 先抓首頁取得最新頁碼
            res = requests.get("https://www.ptt.cc/bbs/Gossiping/index.html", cookies=cookies, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            prev_link = soup.select("div.btn-group-paging a")[1]["href"]
            latest_page = int(re.search(r'index(\d+)\.html', prev_link).group(1)) + 1
            
            all_data = []
            # --- 核心：掃描 100 頁 ---
            print(f"正在掃描八卦版 100 頁 (從第 {latest_page} 頁開始)...")
            for p in range(latest_page, latest_page - 100, -1):
                p_url = f"https://www.ptt.cc/bbs/Gossiping/index{p}.html"
                p_res = requests.get(p_url, cookies=cookies, timeout=10)
                p_soup = BeautifulSoup(p_res.text, "html.parser")
                
                for art in p_soup.select("div.r-ent"):
                    t_tag = art.select_one("div.title a")
                    if t_tag:
                        # 處理推文數
                        nrec = art.select_one("div.nrec span")
                        push = nrec.text if nrec else "0"
                        
                        all_data.append({
                            "title": t_tag.text,
                            "url": "https://www.ptt.cc" + t_tag["href"],
                            "push": push,
                            "author": art.select_one("div.author").text if art.select_one("div.author") else "unknown",
                            "date": art.select_one("div.date").text
                        })
                # 每抓 10 頁稍微休息一下，避免被封
                if p % 10 == 0:
                    time.sleep(0.5)
            
            gossip_posts = all_data
            print(f"掃描完成！共抓取 {len(gossip_posts)} 條標題")
            
        except Exception as e:
            print(f"抓取失敗: {e}")
        
        # 八卦版更新快，建議每 10 分鐘大更新一次即可
        time.sleep(600)

@app.route('/')
def home():
    style = """
    <style>
        body { font-family: sans-serif; background: #f0f2f5; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .search-box { width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; }
        .post-item { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        .push { width: 40px; text-align: center; font-weight: bold; margin-right: 15px; }
        .push-hot { color: #f00; }
        .title { flex-grow: 1; text-decoration: none; color: #1c1e21; }
        .title:hover { color: #1877f2; }
        .meta { font-size: 12px; color: #65676b; margin-left: 10px; }
    </style>
    """
    
    # 搜尋功能的簡單 JavaScript
    script = """
    <script>
    function searchPosts() {
        let input = document.getElementById('searchInput').value.toLowerCase();
        let posts = document.getElementsByClassName('post-item');
        for (let i = 0; i < posts.length; i++) {
            let title = posts[i].getElementsByClassName('title')[0].innerText.toLowerCase();
            posts[i].style.display = title.includes(input) ? "" : "none";
        }
    }
    </script>
    """
    
    rows = ""
    for p in gossip_posts:
        push_class = "push-hot" if "爆" in p['push'] or (p['push'].isdigit() and int(p['push']) > 50) else ""
        rows += f"""
        <div class='post-item'>
            <span class='push {push_class}'>{p['push']}</span>
            <a class='title' href='{p['url']}' target='_blank'>{p['title']}</a>
            <span class='meta'>{p['date']} | {p['author']}</span>
        </div>
        """

    return f"""
    <html>
        <head>
            <title>八卦 100 頁考古器</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            {style}
        </head>
        <body>
            <div class='container'>
                <h1>八卦版 100 頁考古器</h1>
                <input type="text" id="searchInput" onkeyup="searchPosts()" placeholder="輸入關鍵字搜尋標題..." class="search-box">
                <div id="postList">{rows if rows else '<h2>正在挖掘資料中，請稍候並刷新網頁...</h2>'}</div>
            </div>
            {script}
        </body>
    </html>
    """

if __name__ == "__main__":
    threading.Thread(target=fetch_gossip_100, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
