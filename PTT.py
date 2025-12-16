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

# --------- PTT 爬蟲 / Bot ---------
def ptt_bot_task():
    url = "https://www.ptt.cc/bbs/Gossiping/index.html"
    cookies = {"over18": "1"}
    seen_posts = set()  # 記錄已抓過的文章
    server_url = f"http://localhost:{PORT}"  # 自己的 HTTP server 地址

    while True:
        try:
            # 定期保活 Render
            try:
                requests.get(server_url, timeout=5)
            except:
                pass  # 保活失敗也不用理會

            r = requests.get(url, cookies=cookies, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            titles = soup.select("div.title a")

            new_posts = []
            for a in titles:
                link = "https://www.ptt.cc" + a["href"]
                if link not in seen_posts:
                    new_posts.append((a.text.strip(), link))
                    seen_posts.add(link)

            if new_posts:
                print("==== 新文章 ====")
                for title, link in new_posts:
                    print(title, link)
            else:
                print("沒有新文章。")

        except requests.RequestException as e:
            print("抓取失敗:", e)

        time.sleep(60)  # 每 60 秒抓一次

# --------- 主程式 ---------
if __name__ == "__main__":
    # 開啟 HTTP server 保持 Render 活動
    threading.Thread(target=run_server, daemon=True).start()
    # 啟動 PTT bot
    ptt_bot_task()
