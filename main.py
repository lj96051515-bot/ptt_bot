import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

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

# --------- 你的 PTT 爬蟲 / bot 邏輯 ---------
def ptt_bot_task():
    while True:
        # 這裡放你的爬蟲或機器人邏輯
        print("PTT bot is working...")
        time.sleep(10)  # 模擬工作間隔

# --------- 主程式 ---------
if __name__ == "__main__":
    # 開啟 HTTP server 保持 Render 活動
    threading.Thread(target=run_server, daemon=True).start()
    # 啟動 PTT bot
    ptt_bot_task()
