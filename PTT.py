import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import os

app = Flask(__name__)
gossip_posts = []

def fetch_gossip_boom():
    global gossip_posts
    while True:
        try:
            cookies = {"over18": "1"}
            all_data = []
            
            # PTT 搜尋結果一頁有 20 則，抓 50 頁剛好是 1000 則
            print("正在跨時空抓取八卦版 1000 則爆文...")
            for i in range(1, 51):
                # 直接使用搜尋參數 q=recommend:100 (只看爆文)
                search_url = f"https://www.ptt.cc/bbs/Gossiping/search?page={i}&q=recommend%3A100"
                res = requests.get(search_url, cookies=cookies, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                
                arts = soup.select("div.r-ent")
                if not arts: # 如果沒東西了就停止
                    break
                
                for art in arts:
                    t_tag = art.select_one("div.title a")
                    if t_tag:
                        all_data.append({
                            "title": t_tag.text,
                            "url": "https://www.ptt.cc" + t_tag["href"],
                            "push": "爆",
                            "author": art.select_one("div.author").text if art.select_one("div.author") else "unknown",
                            "date": art.select_one("div.date").text
                        })
                
                # 稍微休息，避免被 PTT 擋掉
                if i % 10 == 0:
                    time.sleep(0.5)
            
            gossip_posts = all_data
            print(f"抓取完成！共存儲 {len(gossip_posts)} 則爆文標題")
            
        except Exception as e:
            print(f"抓取失敗: {e}")
        
        # 爆文更新不快，每 30 分鐘更新一次即可
        time.sleep(1800)

@app.route('/')
def home():
    style = """
    <style>
        body { font-family: sans-serif; background: #121212; color: #eee; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        .header { background: #f44336; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .search-box { width: 100%; padding: 12px; margin-bottom: 20px; border: none; border-radius: 4px; background: #333; color: white; font-size: 16px; }
        .post-item { display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #333; background: #1e1e1e; margin-bottom: 5px; border-radius: 4px; }
        .push { color: #ff5252; font-weight: bold; width: 50px; text-align: center; font-size: 1.1em; }
        .title { flex-grow: 1; text-decoration: none; color: #82b1ff; font-weight: bold; }
        .title:hover { text-decoration: underline; }
        .meta { font-size: 12px; color: #888; margin-left: 10px; }
    </style>
    """
    
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
        rows += f"""
        <div class='post-item'>
            <span class='push'>{p['push']}</span>
            <a class='title' href='{p['url']}' target='_blank'>{p['title']}</a>
            <span class='meta'>{p['date']} | {p['author']}</span>
        </div>
        """

    return f"""
    <html>
        <head>
            <title>八卦版爆文考古器</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            {style}
        </head>
        <body>
            <div class='container'>
                <div class='header'><h1>八卦版 1000 則爆文考古器</h1></div>
                <input type="text" id="searchInput" onkeyup="searchPosts()" placeholder="在 1000 則爆文中搜尋關鍵字..." class="search-box">
                <div id="postList">{rows if rows else '<h2>正在時光旅行中...預計 30 秒後完成抓取，請稍候刷新。</h2>'}</div>
            </div>
            {script}
        </body>
    </html>
    """

if __name__ == "__main__":
    threading.Thread(target=fetch_gossip_boom, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
