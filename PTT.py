import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup

# --------- HTTP Server（保持 Render 活動用） ---------
PORT = int(os.environ.get("PORT", 8000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"PTT Bot is running!")

def run_server():
    httpd = HTTPServer(("", PORT), Handler)
    print(f"HTTP server running on port {PORT}")
    httpd.serve_forever()

# --------- PTT 爬蟲邏輯 ---------

def get_posts_from_url(url, cookies):
    """抓取單一頁面的文章標題與連結"""
    try:
        r = requests.get(url, cookies=cookies, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # 排除掉被刪除的文章 (沒有 <a> 標籤的)
        items = soup.select("div.r-ent")
        posts = []
        for item in items:
            title_tag = item.select_one("div.title a")
            if title_tag:
                posts.append({
                    "title": title_tag.text.strip(),
                    "link": "https://www.ptt.cc" + title_tag["href"]
                })
        return posts, soup
    except Exception as e:
        print(f"抓取錯誤: {e}")
        return [], None

def ptt_bot_task(history_pages=3):
    """
    history_pages: 想要往回抓多少頁舊文章
    """
    base_url = "https://www.ptt.cc"
    start_url = f"{base_url}/bbs/Gossiping/index.html"
    cookies = {"over18": "1"}

    print(f"開始抓取歷史文章，預計抓取 {history_pages} 頁...")

    # 1. 先抓最新一頁，找出「上頁」的頁碼
    posts, soup = get_posts_from_url(start_url, cookies)
    
    # 從分頁按鈕群找到「上頁」的連結
    paging_btns = soup.select("div.btn-group-paging a")
    prev_link = paging_btns[1]["href"] # 通常第二個是「上頁」
    
    # 提取頁碼數字 (例如從 /bbs/Gossiping/index39482.html 提取 39482)
    # 最新頁碼 = 上一頁頁碼 + 1
    last_page_num = int(prev_link.split("index")[1].split(".html")[0]) + 1

    # 2. 循環抓取舊頁面
    for i in range(last_page_num, last_page_num - history_pages, -1):
        target_url = f"{base_url}/bbs/Gossiping/index{i}.html"
        print(f"\n--- 正在抓取第 {i} 頁 ---")
        
        current_posts, _ = get_posts_from_url(target_url, cookies)
        
        for post in current_posts:
            print(f"[{i}頁] {post['title']} {post['link']}")
        
        # 稍微停頓，避免被 PTT 封鎖
        time.sleep(1)

    print("\n==== 歷史文章抓取完畢，開始每 60 秒監控新文章 ====")
    
    # 3. 進入原本的監控模式 (每分鐘抓一次最新頁)
    while True:
        posts, _ = get_posts_from_url(start_url, cookies)
        print(f"\n==== 最新文章更新 ({time.strftime('%H:%M:%S')}) ====")
        for post in posts[:5]:
            print(post['title'], post['link'])
        time.sleep(60)

# --------- 主程式 ---------
if __name__ == "__main__":
    # 開啟 HTTP server 保持 Render 活動
    threading.Thread(target=run_server, daemon=True).start()
    # 啟動 PTT bot，預設往前抓 3 頁
    ptt_bot_task(history_pages=3)

