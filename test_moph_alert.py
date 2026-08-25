#!/usr/bin/env python3
"""
==============================================================================
 ไฟล์ทดสอบส่งแจ้งเตือนผ่าน MOPH Alert v3.1
 MOPH Alert v3.1 - Test Notification Script
==============================================================================

 วัตถุประสงค์:
   ไฟล์นี้ใช้สำหรับทดสอบการส่งแจ้งเตือนผ่านระบบ MOPH Alert v3.1
   โดยไม่ต้องติดตั้งโปรแกรม QueueNotify เต็มรูปแบบ

 Prerequisite (สิ่งที่ต้องมีก่อนใช้งาน):
   pip install requests

 วิธีใช้งาน:
   1. กรอก CLIENT_KEY และ SECRET_KEY ของคุณด้านล่าง
   2. ระบุเลขบัตรประชาชน 13 หลักของผู้รับในตัวแปร TEST_CID
   3. รันสคริปต์:  python3 test_moph_alert.py

 API Endpoint:
   POST https://morpromt2c.moph.go.th/alert/v3.1/messages

 ข้อควรระวัง:
   - อย่า commit ไฟล์นี้ลง git หลังจากกรอก credentials จริงแล้ว
   - เลขบัตรประชาชนเป็นข้อมูลส่วนบุคคล (PDPA) — ระวังการ log

==============================================================================
"""

import os
import requests
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env (ไม่ต้องฮาร์ดโค้ด credentials ลงในไฟล์นี้)
load_dotenv()

# ==============================================================================
# ⚙️  ตั้งค่า Credentials (แก้ไขตรงนี้)
# ==============================================================================

CLIENT_KEY  = os.getenv("MOPH_CLIENT_KEY", "YOUR_CLIENT_KEY")   # ← ตั้งใน .env
SECRET_KEY  = os.getenv("MOPH_SECRET_KEY", "YOUR_SECRET_KEY")   # ← ตั้งใน .env

# เลขบัตรประชาชนของผู้รับ (13 หลัก) — ต้องเป็นบัญชีที่ผูก MOPH Connect แล้ว
TEST_CID    = os.getenv("MOPH_TEST_CID", "1234567890123")   # ← ตั้งใน .env

# ==============================================================================
# 🌐  ค่าคงที่ของ API (ปกติไม่ต้องแก้)
# ==============================================================================

BASE_URL    = "https://morpromt2c.moph.go.th/alert/v3.1"
TIMEOUT_SEC = 60    # รอ response สูงสุด 60 วินาที


# ==============================================================================
# 📦  สร้าง Payload ประเภทต่าง ๆ
# ==============================================================================

def build_text_payload(cid: str, text: str) -> dict:
    """สร้าง payload แบบ Text ธรรมดา (ง่ายที่สุด)"""
    return {
        "cid": [cid],
        "messages": [
            {
                "type": "text",
                "text": text,
            }
        ],
        "message_title": "ข้อความทดสอบ",
        "message_html": f"<p>{text}</p>",
        "message_text": text,
        "message_type": "HPT",
    }


def build_flex_payload(cid: str, title: str, body: str, hospital_name: str = "โรงพยาบาลตัวอย่าง") -> dict:
    """
    สร้าง payload แบบ Flex Message (รองรับ layout / สี / ปุ่ม)
    นี่คือรูปแบบที่ QueueNotify ใช้ส่งแจ้งเตือนคิว
    """
    flex_bubble = {
        "type": "bubble",
        "styles": {
            "header": {"backgroundColor": "#005A9C"}
        },
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": hospital_name,
                    "color": "#FFFFFF",
                    "size": "sm",
                    "weight": "bold",
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
                    "text": title,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#005A9C",
                    "wrap": True,
                },
                {
                    "type": "separator",
                    "margin": "md",
                },
                {
                    "type": "text",
                    "text": body,
                    "wrap": True,
                    "size": "md",
                    "color": "#333333",
                },
                {
                    "type": "text",
                    "text": f"เวลา: {datetime.now().strftime('%H:%M น.')}",
                    "size": "xs",
                    "color": "#999999",
                    "margin": "md",
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "ส่งผ่านระบบ MOPH Alert",
                    "size": "xxs",
                    "color": "#AAAAAA",
                    "align": "center",
                }
            ],
        },
    }

    return {
        "cid": [cid],
        "messages": [
            {
                "type": "flex",
                "altText": f"{title} — {body}",   # ข้อความสั้นสำหรับ notification bar
                "contents": flex_bubble,
            }
        ],
        "message_title": title,
        "message_html": f"<strong>{title}</strong><br>{body}",
        "message_text": f"{title}\n{body}",
        "message_type": "HPT",
    }


# ==============================================================================
# 🚀  ฟังก์ชันส่งข้อความหลัก
# ==============================================================================

def send_alert(payload: dict, dry_run: bool = False):
    """
    ส่ง payload ไปยัง MOPH Alert v3.1

    Args:
        payload  : dict ที่ได้จาก build_*_payload()
        dry_run  : ถ้า True จะแสดง payload แต่ไม่ยิง HTTP จริง

    Returns:
        (success: bool, response_data: dict | error_message: str)
    """
    headers = {
        "Content-Type": "application/json",
        "client-key":   CLIENT_KEY,
        "secret-key":   SECRET_KEY,
    }
    url = f"{BASE_URL}/messages"

    print(f"\n{'='*60}")
    print(f"🔗 URL     : {url}")
    print(f"👥 CIDs    : {payload.get('cid', [])}")
    print(f"📋 Type    : {payload['messages'][0]['type']}")
    print(f"{'='*60}")

    if dry_run:
        print("\n🧪 [DRY RUN] Payload ที่จะส่ง:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("\n⚠️  DRY RUN — ไม่ได้ส่งจริง")
        return True, payload

    print("\n📤 กำลังส่ง...")
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_SEC,
        )

        print(f"📥 HTTP Status : {response.status_code}")
        print(f"📥 Response    : {response.text[:500]}")

        if response.status_code == 200:
            try:
                data = response.json()
                status = data.get("status") == "success" or data.get("message_code") == 200
                return status, data
            except json.JSONDecodeError:
                # บาง endpoint ตอบ plain text
                return True, response.text
        else:
            return False, response.text

    except requests.exceptions.Timeout:
        msg = f"Timeout: ไม่ได้รับ response ภายใน {TIMEOUT_SEC} วินาที"
        print(f"❌ {msg}")
        return False, msg

    except requests.exceptions.ConnectionError as e:
        msg = f"Connection Error: {e}"
        print(f"❌ {msg}")
        return False, msg


# ==============================================================================
# ✅  ตรวจสอบ Credentials และ CID เบื้องต้น
# ==============================================================================

def validate_config() -> bool:
    """ตรวจสอบว่ากรอก credentials และ CID ครบถ้วนก่อนส่ง"""
    errors = []

    if CLIENT_KEY == "YOUR_CLIENT_KEY" or not CLIENT_KEY:
        errors.append("กรุณาตั้งค่า CLIENT_KEY ในไฟล์นี้")

    if SECRET_KEY == "YOUR_SECRET_KEY" or not SECRET_KEY:
        errors.append("กรุณาตั้งค่า SECRET_KEY ในไฟล์นี้")

    if not TEST_CID.isdigit() or len(TEST_CID) != 13:
        errors.append(f"TEST_CID ต้องเป็นตัวเลข 13 หลัก (ปัจจุบัน: '{TEST_CID}')")

    if errors:
        print("\n⚠️  พบข้อผิดพลาดในการตั้งค่า:")
        for err in errors:
            print(f"  ❌ {err}")
        print("\n👉 แก้ไขตัวแปรที่ด้านบนของไฟล์ test_moph_alert.py แล้วลองใหม่\n")
        return False

    return True


# ==============================================================================
# 🏁  Main — รัน 2 กรณีทดสอบ
# ==============================================================================

def main():
    print("=" * 60)
    print("   MOPH Alert v3.1 — Test Script")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # --- ตรวจสอบ config ก่อน ---
    if not validate_config():
        sys.exit(1)

    # ────────────────────────────────────────────────
    # TEST 1: Text Message (แบบง่าย)
    # ────────────────────────────────────────────────
    print("\n\n📌 TEST 1: ส่ง Text Message ธรรมดา")
    print("-" * 40)

    text_payload = build_text_payload(
        cid=TEST_CID,
        text="สวัสดีครับ! นี่คือข้อความทดสอบจากระบบ MOPH Alert v3.1",
    )

    success1, resp1 = send_alert(text_payload)

    if success1:
        print("\n✅ TEST 1: สำเร็จ!")
    else:
        print(f"\n❌ TEST 1: ล้มเหลว → {resp1}")

    # ────────────────────────────────────────────────
    # TEST 2: Flex Message (แบบ rich card พร้อมสี)
    # ────────────────────────────────────────────────
    print("\n\n📌 TEST 2: ส่ง Flex Message (แบบ card)")
    print("-" * 40)

    flex_payload = build_flex_payload(
        cid=TEST_CID,
        title="แจ้งเตือนคิวใกล้ถึงแล้ว",
        body="ขณะนี้ท่านอยู่ในลำดับที่ 3\nกรุณาเตรียมตัวและมาที่จุดบริการ",
        hospital_name="โรงพยาบาลตัวอย่าง",
    )

    success2, resp2 = send_alert(flex_payload)

    if success2:
        print("\n✅ TEST 2: สำเร็จ!")
    else:
        print(f"\n❌ TEST 2: ล้มเหลว → {resp2}")

    # ────────────────────────────────────────────────
    # สรุปผล
    # ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 สรุปผลการทดสอบ")
    print("=" * 60)
    print(f"  TEST 1 (Text)  : {'✅ ผ่าน' if success1 else '❌ ไม่ผ่าน'}")
    print(f"  TEST 2 (Flex)  : {'✅ ผ่าน' if success2 else '❌ ไม่ผ่าน'}")
    print("=" * 60)

    if success1 and success2:
        print("\n🎉 ทุก test case ผ่าน! ระบบ MOPH Alert ทำงานปกติ")
    else:
        print("\n⚠️  มีบาง test case ไม่ผ่าน — ตรวจสอบ response ด้านบน")
        sys.exit(1)


if __name__ == "__main__":
    # ถ้าต้องการแค่ดู payload โดยไม่ยิงจริง ให้เปลี่ยน dry_run=True
    # ตัวอย่าง:
    #   payload = build_flex_payload(TEST_CID, "ทดสอบ", "เนื้อหา")
    #   send_alert(payload, dry_run=True)
    main()
