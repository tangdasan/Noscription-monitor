import requests
import time
import threading
import json
import sqlite3

# URL列表
urls = [
    "https://api-worker.noscription.org/indexer/balance?npub=npub143htynnt0hsldhs664z45nefufvppnc27mt86mkdk4raqlwwy72",
    "https://api-worker.noscription.org/indexer/balance?npub=npub1t0zucp47enqcdla4jqykrj74a0dhc2dg0ze0m4knfeuq4wsajt",
]

def create_table():
    conn = sqlite3.connect("balance.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS balance (url TEXT PRIMARY KEY, value REAL)")
    conn.commit()
    conn.close()

def get_balance(url):
    response = requests.get(url)
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        balance = data[0].get("balance")
        return balance
    else:
        return None

def send_alert(url, old_balance, new_balance):
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token="
    headers = {"Content-Type": "application/json"}
    message = {
        "msgtype": "text",
        "text": {
            "content": f"URL: {url}\n余额发生变动！\n旧余额：{old_balance}\n新余额：{new_balance}"
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(message))
    if response.status_code == 200:
        print(f"URL: {url} 余额变动报警消息发送成功")
    else:
        print(f"URL: {url} 余额变动报警消息发送失败")

def process_url(url):
    conn = sqlite3.connect("balance.db")
    c = conn.cursor()
    while True:
        balance = get_balance(url)
        if balance is not None:
            c.execute("SELECT value FROM balance WHERE url=?", (url,))
            result = c.fetchone()
            if result is None:
                c.execute("INSERT INTO balance (url, value) VALUES (?, ?)", (url, balance))
                conn.commit()
            else:
                old_balance = result[0]
                if old_balance != balance:
                    send_alert(url, old_balance, balance)
                    c.execute("UPDATE balance SET value=? WHERE url=?", (balance, url))
                    conn.commit()
        time.sleep(60)  # 每隔60秒获取一次数据
    conn.close()

def main():
    create_table()
    threads = []
    for url in urls:
        thread = threading.Thread(target=process_url, args=(url,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
