#!/usr/bin/env python3
"""
ทดสอบว่า MOPH Alert v3.1 ส่ง "รูปภาพ" ได้หรือไม่ — 2 รูปแบบ

  CASE A : standalone image message  (LINE type: "image")
  CASE B : flex bubble ที่มี hero image  (แบบที่เอกสาร สธ. ยกตัวอย่างไว้)

รันด้วย:  PYTHONUTF8=1 .venv/Scripts/python.exe test_image_message.py
"""
import os, json, requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("MOPH_CLIENT_KEY")
SECRET_KEY = os.getenv("MOPH_SECRET_KEY")
CID        = os.getenv("MOPH_TEST_CID")
URL        = "https://morpromt2c.moph.go.th/alert/v3.1/messages"

# รูปสาธารณะของ สธ. เอง (อ้างอิงจากตัวอย่างในคู่มือ API MOPH Alert)
IMG = "https://phr1.moph.go.th/moph_account_center1.png"

HEADERS = {
    "Content-Type": "application/json",
    "client-key":   CLIENT_KEY,
    "secret-key":   SECRET_KEY,
}


def post(label: str, payload: dict):
    print(f"\n{'='*60}\n▶ {label}\n{'='*60}")
    r = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
    print(f"HTTP {r.status_code}")
    print(f"Response: {r.text[:600]}")
    return r


# ── CASE A : standalone image message ────────────────────────────────
case_a = {
    "cid": [CID],
    "messages": [
        {
            "type": "image",
            "originalContentUrl": IMG,
            "previewImageUrl": IMG,
        }
    ],
    "message_title": "ทดสอบส่งรูป (standalone image)",
    "message_html":  f'<p>ทดสอบส่งรูป</p><img src="{IMG}" style="max-width:100%">',
    "message_text":  "ทดสอบส่งรูปแบบ image message",
    "message_type":  "HPT",
}

# ── CASE B : flex + hero image ───────────────────────────────────────
case_b = {
    "cid": [CID],
    "messages": [
        {
            "type": "flex",
            "altText": "ทดสอบส่งรูปแบบ flex hero",
            "contents": {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": IMG,
                    "size": "full",
                    "aspectRatio": "20:9",
                    "aspectMode": "cover",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ทดสอบส่งรูปผ่าน Flex hero image",
                            "wrap": True,
                            "weight": "bold",
                        }
                    ],
                },
            },
        }
    ],
    "message_title": "ทดสอบส่งรูป (flex hero)",
    "message_html":  f'<p>ทดสอบ flex hero</p><img src="{IMG}" style="max-width:100%">',
    "message_text":  "ทดสอบส่งรูปแบบ flex hero image",
    "message_type":  "HPT",
}


if __name__ == "__main__":
    print(f"CID: {CID}\nIMG: {IMG}")
    ra = post("CASE A — standalone image message", case_a)
    rb = post("CASE B — flex + hero image", case_b)

    print(f"\n{'='*60}\n📊 สรุป\n{'='*60}")
    print(f"  CASE A (image)     : HTTP {ra.status_code} → {ra.text[:120]}")
    print(f"  CASE B (flex hero) : HTTP {rb.status_code} → {rb.text[:120]}")
