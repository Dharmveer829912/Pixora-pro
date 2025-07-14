# Usage Guide

## 1. Requirements

- Python 3.8+
- Flask
- cloudflared binary installed and accessible from terminal

## 2. Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## 3. Run the Tool

```bash
cd src
python server.py
```

Enter a valid URL (your HTML page, redirect page etc.) to be shown in the iframe.

## 4. Access Uploads

Visit: `http://localhost:8080/videos` or the public cloudflare URL to view saved video chunks.
