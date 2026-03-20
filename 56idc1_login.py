import os
import platform
import time
import json
import socket
import signal
import subprocess
from typing import List, Dict, Optional

import requests
from seleniumbase import SB
from pyvirtualdisplay import Display
from urllib.parse import urlparse, parse_qs, unquote

# ==========================
# 基础配置
# ==========================
LOGIN_URL = "https://56idc.net/login"

# Hysteria2 代理 URL（可选）
HY2_PROXY_URL = os.getenv("HY2_PROXY_URL", "")

# SOCKS5 代理端口（可选，默认 51080）
SOCKS_PORT = int(os.getenv("SOCKS_PORT", "51080"))

# ==========================
# Xvfb
# ==========================
def setup_xvfb():
    if platform.system().lower() == "linux" and not os.environ.get("DISPLAY"):
        display = Display(visible=False, size=(1920, 1080))
        display.start()
        os.environ["DISPLAY"] = display.new_display_var
        print("🖥️ Xvfb 已启动")
        return display
    return None

# ==========================
# 脱敏
# ==========================
def mask_email(email: str) -> str:
    name, domain = email.split("@", 1)
    if len(name) <= 4:
        masked_name = name
    else:
        masked_name = f"{name[:2]}***{name[-2:]}"
    return f"{masked_name}@{domain}"

def mask_username(name: Optional[str]) -> str:
    if not name:
        return "***"
    return name[:2] + "***" + name[-2:]

def mask_ip(ip: str) -> str:
    return ip.rsplit(".", 1)[0] + ".***"

# ==========================
# Telegram
# ==========================
def tg_send(text: str, token: Optional[str], chat_id: Optional[str]):
    if not token or not chat_id:
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=15
    )

# ==========================
# 落地 IP
# ==========================
def check_ip(proxy: str) -> str:
    try:
        r = requests.get(
            "http://ip-api.com/json/?fields=status,query,countryCode",
            proxies={"http": proxy, "https": proxy},
            timeout=10
        ).json()
        if r.get("status") == "success":
            return f"{mask_ip(r['query'])} ({r['countryCode']})"
    except Exception:
        pass
    return "未知 IP"

# ==========================
# Hy2 代理
# ==========================
class Hy2Proxy:
    def __init__(self, url: str):
        self.url = url
        self.proc = None

    def start(self) -> bool:
        print("📡 启动 Hysteria2…")

        u = self.url.replace("hysteria2://", "").replace("hy2://", "")
        parsed = urlparse("scheme://" + u)
        params = parse_qs(parsed.query)

        cfg = {
            "server": f"{parsed.hostname}:{parsed.port}",
            "auth": unquote(parsed.username),
            "tls": {
                "sni": params.get("sni", [parsed.hostname])[0],
                "insecure": params.get("insecure", ["0"])[0] == "1",
                "alpn": params.get("alpn", ["h3"]),
            },
            "socks5": {"listen": f"127.0.0.1:{SOCKS_PORT}"}
        }

        cfg_path = "/tmp/hy2.json"
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)

        self.proc = subprocess.Popen(
            ["hysteria", "client", "-c", cfg_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        for _ in range(12):
            time.sleep(1)
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", SOCKS_PORT)) == 0:
                    print("✅ Hy2 SOCKS5 已就绪")
                    return True
        return False

    def stop(self):
        if self.proc:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            print("🛑 Hy2 已停止")

    @property
    def proxy(self):
        return f"socks5://127.0.0.1:{SOCKS_PORT}"

# ==========================
# 账号解析
# ==========================
def build_accounts() -> List[Dict[str, str]]:
    raw = os.getenv("IDC56_BATCH", "").strip()
    if not raw:
        raise RuntimeError("❌ IDC56_BATCH 未设置")

    accounts = []
    for idx, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        parts = [x.strip() for x in line.split(",")]
        if len(parts) < 2:
            raise RuntimeError(f"❌ 第 {idx} 行格式错误: 需要至少 email,password")
        
        email, pwd = parts[0], parts[1]
        tg_token = parts[2] if len(parts) > 2 else ""
        tg_chat = parts[3] if len(parts) > 3 else ""
        
        if len(parts) > 4:
            raise RuntimeError(f"❌ 第 {idx} 行格式错误: 最多 4 个字段")
        
        accounts.append({
            "email": email,
            "password": pwd,
            "tg_token": tg_token,
            "tg_chat": tg_chat,
        })
    
    if not accounts:
        raise RuntimeError("❌ IDC56_BATCH 中没有有效的账号")
    
    return accounts

# ==========================
# 登录
# ==========================
def login_one(acc: Dict[str, str], idx: int, proxy: str):
    with SB(uc=True, locale="en", test=True, proxy=proxy) as sb:
        print(f"🚀 [{idx}] UC 登录")

        sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
        sb.wait_for_element_visible("body", timeout=30)
        time.sleep(2)

        sb.type('input[name="username"]', acc["email"])
        sb.type('input[name="password"]', acc["password"])

        try:
            sb.uc_gui_click_captcha()
            time.sleep(3)
        except Exception:
            pass

        sb.click('button[type="submit"]')
        time.sleep(4)

        current_url = sb.get_current_url()
        print(f"📍 当前 URL: {current_url}")

        ok = (
            "clientarea.php" in current_url
            and any(c.get("name") == "cf_clearance" for c in sb.get_cookies())
        )

        username = sb.get_text("//div[@class='panel-body']/strong").strip()
        if ok:
            try:
                username = sb.get_text("//div[@class='panel-body']/strong").strip()
            except Exception:
                pass

        return ok, username

# ==========================
# 主流程
# ==========================
def main():
    display = setup_xvfb()
    proxy_mgr = Hy2Proxy(HY2_PROXY_URL)
    accounts = build_accounts()
    results = []

    try:
        if not proxy_mgr.start():
            raise RuntimeError("Hy2 启动失败")

        ip_info = check_ip(proxy_mgr.proxy)

        for i, acc in enumerate(accounts, 1):
            ok, username = login_one(acc, i, proxy_mgr.proxy)
            results.append({
                "ok": ok,
                "email": mask_email(acc["email"]),
                "username": mask_username(username),
                "tg_token": acc["tg_token"],
                "tg_chat": acc["tg_chat"],
            })

        # ✅ 汇总只发一条
        lines = []
        for r in results:
            if r["ok"]:
                lines.append(
                    "✅ 56idc.net 登录成功\n"
                    f"账号: {r['email']}\n"
                    f"用户名: {r['username']}\n"
                    f"IP: {ip_info}"
                )
            else:
                lines.append(
                    "❌ 56idc.net 登录失败\n"
                    f"账号: {r['email']}\n"
                    f"IP: {ip_info}"
                )

        summary = "\n\n".join(lines)

        sent = set()
        for r in results:
            key = (r["tg_token"], r["tg_chat"])
            if key not in sent:
                tg_send(summary, *key)
                sent.add(key)

        print(summary)

    finally:
        proxy_mgr.stop()
        if display:
            display.stop()

if __name__ == "__main__":
    main()
