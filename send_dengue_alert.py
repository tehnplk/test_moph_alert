#!/usr/bin/env python3
"""
ส่งแจ้งเตือนโรคไข้เลือดออก + โปสเตอร์ "3 เก็บ 3 ป้องกัน" ผ่าน MOPH Alert v3.1

ส่ง 2 bubble ใน request เดียว:
  bubble 1 : ข้อความแจ้งเตือนพบผู้ป่วยในชุมชน
  bubble 2 : โปสเตอร์ 3 เก็บ 3 ป้องกัน + ข้อความติดต่อสอบถามใต้รูป

ค่าที่ต้องตั้งใน .env :
  CLIENT_KEY, SECRET_KEY, CID_1 (CID_2, ...), IMG_URL, IMG_PREVIEW_URL

รันด้วย:  PYTHONUTF8=1 .venv/Scripts/python.exe send_dengue_alert.py
เพิ่ม --dry-run เพื่อดู payload โดยไม่ส่งจริง
"""
import os
import re
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY  = os.getenv("CLIENT_KEY", "")
SECRET_KEY  = os.getenv("SECRET_KEY", "")
IMG         = os.getenv("IMG_URL", "")
IMG_PREVIEW = os.getenv("IMG_PREVIEW_URL", "")
URL         = "https://morpromt2c.moph.go.th/alert/v3.1/messages"

HOSPITAL = "รพ.สต.อรัญญิก"

ALERT_TEXT = (
    "ขณะนี้พบผู้ป่วยโรคไข้เลือดออกในบริเวณชุมชนของท่าน "
    "โปรดระวังอย่าให้ยุงกัด หากมีอาการไข้ มีผื่นแดงที่ผิวหนัง "
    f"ให้เข้ารับบริการที่ {HOSPITAL} ทันที"
)
POSTER_CAPTION = f"สอบถามรายละเอียดเพิ่มเติมได้ที่ {HOSPITAL}"

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


def alert_bubble() -> dict:
    """bubble 1 : ข้อความแจ้งเตือน — ใช้โทนแดงให้อ่านแล้วรู้ว่าเป็นเรื่องด่วน"""
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#C62828",
            "paddingAll": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "⚠️ แจ้งเตือนโรคไข้เลือดออก",
                    "color": "#FFFFFF",
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True,
                }
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": ALERT_TEXT,
                    "wrap": True,
                    "size": "md",
                    "color": "#333333",
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "text",
                    "text": HOSPITAL,
                    "size": "sm",
                    "color": "#C62828",
                    "weight": "bold",
                    "margin": "md",
                },
            ],
        },
    }


def poster_bubble() -> dict:
    """bubble 2 : โปสเตอร์เต็มใบ + ข้อความติดต่อใต้รูป

    โปสเตอร์เป็นแนวตั้ง 1024x1536 จึงตั้ง aspectRatio 2:3 ให้ตรงอัตราส่วนจริง
    ไม่งั้น LINE จะ crop เหลือแค่หัวโปสเตอร์
    """
    return {
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
                    "text": POSTER_CAPTION,
                    "wrap": True,
                    "size": "md",
                    "weight": "bold",
                    "color": "#1B5E20",
                    "align": "center",
                }
            ],
        },
    }


def build_payload(cids: list) -> dict:
    return {
        "cid": cids,
        "messages": [
            {
                "type": "flex",
                "altText": "แจ้งเตือนโรคไข้เลือดออกในชุมชน",
                "contents": alert_bubble(),
            },
            {
                "type": "flex",
                "altText": "3 เก็บ 3 ป้องกัน — ป้องกันโรคจากยุงลาย",
                "contents": poster_bubble(),
            },
        ],
        "message_title": "แจ้งเตือนโรคไข้เลือดออก",
        "message_html": (
            f"<p><strong>⚠️ แจ้งเตือนโรคไข้เลือดออก</strong></p>"
            f"<p>{ALERT_TEXT}</p>"
            f'<img src="{IMG}" style="max-width:100%">'
            f"<p>{POSTER_CAPTION}</p>"
        ),
        "message_text": f"{ALERT_TEXT}\n\n{POSTER_CAPTION}",
        "message_type": "HPT",
    }


if __name__ == "__main__":
    if not CLIENT_KEY or not SECRET_KEY:
        raise SystemExit("❌ กรุณาตั้ง CLIENT_KEY และ SECRET_KEY ในไฟล์ .env")
    if not CIDS:
        raise SystemExit("❌ ไม่พบผู้รับ — กรุณาตั้ง CID_1 (และ CID_2, ...) ในไฟล์ .env")
    if not IMG:
        raise SystemExit(
            "❌ กรุณาตั้ง IMG_URL ในไฟล์ .env\n"
            "   สร้างได้ด้วย:  python upload_image.py <รูปต้นฉบับ> <รูปย่อ>"
        )

    payload = build_payload(CIDS)

    print(f"👥 ผู้รับ {len(CIDS)} ราย: {', '.join(CIDS)}")
    print(f"🖼️  โปสเตอร์: {IMG}")
    print(f"💬 bubble: {len(payload['messages'])} ใบ")

    if "--dry-run" in sys.argv:
        print("\n🧪 [DRY RUN] payload ที่จะส่ง:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(0)

    print("\n📤 กำลังส่ง...")
    r = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
    print(f"📥 HTTP {r.status_code}")
    print(f"📥 {r.text[:600]}")

    ok = r.status_code == 200 and '"message_code":200' in r.text and "error" not in r.text.lower()
    print("\n✅ ส่งสำเร็จ" if ok else "\n❌ ส่งไม่สำเร็จ — ตรวจ response ด้านบน")
    sys.exit(0 if ok else 1)
