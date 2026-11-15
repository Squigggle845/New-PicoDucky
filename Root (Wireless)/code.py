import os
import time
import board
import digitalio
import wifi
import socketpool
from duckyinpython import run_ducky_file, run_ducky_text

# 1. Safe-Mode Switch (GP0 to GND)
safe_pin = digitalio.DigitalInOut(board.GP0)
safe_pin.direction = digitalio.Direction.INPUT
safe_pin.pull = digitalio.Pull.UP

time.sleep(2)

# 2. Read settings.toml
wifi_mode = os.getenv("WIFI_MODE", "AP").upper()
ssid = os.getenv("WIFI_SSID", "Pico2-BadUSB")
password = os.getenv("WIFI_PASSWORD", "duckypassword123")
auto_run = os.getenv("AUTO_RUN_ON_BOOT", 0)

if safe_pin.value and int(auto_run) == 1:
    run_ducky_file("payload.dd")

# 3. Start Wi-Fi (Access Point or Station Mode)
ip_address = "192.168.4.1"
try:
    if wifi_mode == "STA":
        print(f"Connecting to {ssid}...")
        wifi.radio.connect(ssid, password)
        ip_address = str(wifi.radio.ipv4_address)
    else:
        print(f"Starting hotspot {ssid}...")
        wifi.radio.start_ap(ssid=ssid, password=password, channel=6)
        ip_address = str(wifi.radio.ipv4_address_ap)
    print(f"Web UI ready at: http://{ip_address}")
except Exception as e:
    print("Wi-Fi Error:", e)

pool = socketpool.SocketPool(wifi.radio)
server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
server.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 80))
server.listen(2)

def url_decode(s):
    s = s.replace("+", " ")
    parts = s.split("%")
    res = [parts[0]]
    for item in parts[1:]:
        if len(item) >= 2:
            try:
                res.append(chr(int(item[:2], 16)) + item[2:])
            except ValueError:
                res.append("%" + item)
        else:
            res.append("%" + item)
    return "".join(res)

def list_payloads():
    try:
        return sorted([f for f in os.listdir("/") if f.endswith(".dd")])
    except Exception:
        return ["payload.dd"]

def send_all(conn, data_bytes):
    total_sent = 0
    while total_sent < len(data_bytes):
        sent = conn.send(data_bytes[total_sent:])
        if sent == 0:
            break
        total_sent += sent

def read_full_request(conn):
    buf = bytearray(1024)
    req_bytes = b""
    content_length = 0
    header_end = -1

    while True:
        try:
            n = conn.recv_into(buf)
            if n == 0:
                break
            req_bytes += bytes(buf[:n])

            if header_end == -1 and b"\r\n\r\n" in req_bytes:
                header_end = req_bytes.find(b"\r\n\r\n") + 4
                headers = req_bytes[:header_end].decode("utf-8", "ignore")
                for line in headers.splitlines():
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":", 1)[1].strip())

            if header_end != -1 and len(req_bytes) >= header_end + content_length:
                break
        except Exception:
            break

    return req_bytes.decode("utf-8", "ignore")

def render_html(status_msg="", current_script=""):
    buttons = ""
    for f in list_payloads():
        buttons += f'<a class="btn" href="/run?file={f}">&#9654; Run {f}</a>'
    if not current_script:
        try:
            with open("payload.dd", "r") as fp:
                current_script = fp.read()
        except Exception:
            current_script = "DELAY 500\nSTRING Hello from Pico 2 WH!"

    body = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pico 2 WH BadUSB</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#111827;color:#f3f4f6;padding:16px;max-width:500px;margin:auto;}}
h2{{color:#38bdf8;margin-top:0;}}
.status{{background:#1f2937;border-left:4px solid #10b981;padding:10px;margin-bottom:14px;border-radius:4px;}}
.btn{{display:block;background:#2563eb;color:#fff;text-decoration:none;padding:12px;margin:8px 0;border-radius:6px;text-align:center;font-weight:600;border:none;width:100%;font-size:16px;box-sizing:border-box;}}
.btn-run{{background:#059669;}}
textarea{{width:100%;height:170px;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:6px;padding:10px;font-family:monospace;box-sizing:border-box;}}
</style></head><body>
<h2>Pico 2 WH Control Panel</h2>
{f'<div class="status">{status_msg}</div>' if status_msg else ''}
<h3>Saved Payloads</h3>
{buttons}
<h3>Live DuckyScript 3.0 Runner</h3>
<form method="POST" action="/exec">
<textarea name="script">{current_script}</textarea>
<button class="btn btn-run" type="submit">&#9889; Execute Live Script</button>
</form></body></html>"""

    body_bytes = body.encode("utf-8")
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode("utf-8")
    return headers + body_bytes

# 4. Main HTTP Server Loop
while True:
    conn = None
    try:
        conn, addr = server.accept()
        conn.settimeout(2.0)
        req = read_full_request(conn)

        if req:
            first_line = req.splitlines()[0]
            parts = first_line.split(" ")
            method = parts[0] if len(parts) > 0 else "GET"
            path = parts[1] if len(parts) > 1 else "/"

            if path == "/favicon.ico":
                send_all(conn, b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
                conn.close()
                continue

            status = ""
            live_text = ""

            if method == "GET" and path.startswith("/run?file="):
                fname = url_decode(path.split("file=", 1)[1].split("&")[0])
                ok, status = run_ducky_file(fname)

            elif method == "POST" and path == "/exec":
                body = req.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in req else ""
                if "script=" in body:
                    live_text = url_decode(body.split("script=", 1)[1].split("&")[0])
                    run_ducky_text(live_text)
                    status = "Live DuckyScript executed!"

            response_bytes = render_html(status, live_text)
            send_all(conn, response_bytes)
    except Exception as e:
        print("Socket error:", e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass