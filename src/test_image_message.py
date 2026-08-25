#!/usr/bin/env python3
"""
ทดสอบว่า MOPH Alert v3.1 ส่ง "รูปภาพ" ได้หรือไม่ — 2 รูปแบบ

  CASE A : standalone image message  (LINE type: "image")
  CASE B : flex bubble ที่มี hero image  (แบบที่เอกสาร สธ. ยกตัวอย่างไว้)

ค่าที่ต้องตั้งใน .env :
  CLIENT_KEY, SECRET_KEY, CID_1 (และ CID_2, CID_3, ... ถ้ามีหลายคน)

รันด้วย:  PYTHONUTF8=1 .venv/Scripts/python.exe src/test_image_message.py
"""
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("CLIENT_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
URL        = "https://morpromt2c.moph.go.th/alert/v3.1/messages"

# URL รูปอ่านจาก .env — อัปโหลดขึ้น host ได้ด้วย  python src/upload_image.py <ไฟล์>
# LINE บังคับ HTTPS และจำกัด preview ไม่เกิน 1 MB จึงต้องใช้ไฟล์ย่อแยกต่างหาก
IMG         = os.getenv("IMG_URL", "")          # ต้นฉบับ (ไม่เกิน 10 MB)
IMG_PREVIEW = os.getenv("IMG_PREVIEW_URL", "")  # รูปย่อ (ไม่เกิน 1 MB)

HEADERS = {
    "Content-Type": "application/json",
    "client-key":   CLIENT_KEY,
    "secret-key":   SECRET_KEY,
}


def load_cids() -> list:
    """อ่านผู้รับจาก .env ที่ตั้งชื่อเป็น CID_1, CID_2, CID_3, ..."""
    found = []
    for key, value in os.environ.items():
        m = re.fullmatch(r"CID_(\d+)", key)
        if m and value.strip():
            found.append((int(m.group(1)), value.strip()))
    return [cid for _, cid in sorted(found)]


CIDS = load_cids()


def post(label: str, payload: dict):
    print(f"\n{'='*60}\n▶ {label}\n{'='*60}")
    r = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
    print(f"HTTP {r.status_code}")
    print(f"Response: {r.text[:600]}")
    return r


def build_image_payload(cids: list) -> dict:
    """CASE A : standalone image message"""
    return {
        "cid": cids,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": IMG,
                "previewImageUrl": IMG_PREVIEW,
            }
        ],
        "message_title": "3 เก็บ 3 ป้องกัน — ป้องกันโรคจากยุงลาย",
        "message_html":  f'<p>3 เก็บ 3 ป้องกัน ป้องกันโรคจากยุงลาย</p><img src="{IMG}" style="max-width:100%">',
        "message_text":  "3 เก็บ 3 ป้องกัน — เก็บบ้าน เก็บขยะ เก็บน้ำ ป้องกันไข้เลือดออก ไข้ปวดข้อยุงลาย และโรคติดเชื้อไวรัสซิกา",
        "message_type":  "HPT",
    }


def build_flex_image_payload(cids: list) -> dict:
    """CASE B : flex + hero image"""
    return {
        "cid": cids,
        "messages": [
            {
                "type": "flex",
                "altText": "3 เก็บ 3 ป้องกัน — ป้องกันโรคจากยุงลาย",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": IMG,
                        "size": "full",
                        "aspectRatio": "2:3",
                        "aspectMode": "cover",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "3 เก็บ 3 ป้องกัน\nเก็บบ้าน เก็บขยะ เก็บน้ำ ทุกสัปดาห์",
                                "wrap": True,
                                "weight": "bold",
                            }
                        ],
                    },
                },
            }
        ],
        "message_title": "3 เก็บ 3 ป้องกัน (flex)",
        "message_html":  f'<p>3 เก็บ 3 ป้องกัน ป้องกันโรคจากยุงลาย</p><img src="{IMG}" style="max-width:100%">',
        "message_text":  "3 เก็บ 3 ป้องกัน — เก็บบ้าน เก็บขยะ เก็บน้ำ ทุกสัปดาห์",
        "message_type":  "HPT",
    }


if __name__ == "__main__":
    if not CLIENT_KEY or not SECRET_KEY:
        raise SystemExit("❌ กรุณาตั้ง CLIENT_KEY และ SECRET_KEY ในไฟล์ .env")
    if not CIDS:
        raise SystemExit("❌ ไม่พบผู้รับ — กรุณาตั้ง CID_1 (และ CID_2, ...) ในไฟล์ .env")
    if not IMG or not IMG_PREVIEW:
        raise SystemExit(
            "❌ กรุณาตั้ง IMG_URL และ IMG_PREVIEW_URL ในไฟล์ .env\n"
            "   สร้างได้ด้วย:  python src/upload_image.py <รูปต้นฉบับ> <รูปย่อ>"
        )

    print(f"👥 ผู้รับ {len(CIDS)} ราย: {', '.join(CIDS)}")
    print(f"🖼️  original: {IMG}")
    print(f"🖼️  preview : {IMG_PREVIEW}")

    ra = post("CASE A — standalone image message", build_image_payload(CIDS))
    rb = post("CASE B — flex + hero image", build_flex_image_payload(CIDS))

    print(f"\n{'='*60}\n📊 สรุป\n{'='*60}")
    print(f"  CASE A (image)     : HTTP {ra.status_code} → {ra.text[:120]}")
    print(f"  CASE B (flex hero) : HTTP {rb.status_code} → {rb.text[:120]}")
