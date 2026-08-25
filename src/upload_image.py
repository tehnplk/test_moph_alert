#!/usr/bin/env python3
"""
อัปโหลดรูปขึ้น host ฝากรูปสาธารณะ แล้วคืน URL แบบ HTTPS
สำหรับใช้เป็น originalContentUrl / previewImageUrl ของ MOPH Alert

host ที่ลองตามลำดับ (ไม่ต้องสมัคร ไม่ต้องใช้ API key):
  1. catbox.moe    — ไฟล์อยู่ถาวร
  2. 0x0.st        — สำรอง ไฟล์หมดอายุตามขนาด
  3. tmpfiles.org  — สำรอง อยู่ 1 ชม.

ใช้:  python src/upload_image.py <ไฟล์รูป> [ไฟล์รูปเพิ่มเติม ...]
"""
import sys
import requests

UA = {"User-Agent": "Mozilla/5.0 (moph-alert-test)"}


def up_catbox(path: str) -> str:
    with open(path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
            headers=UA,
            timeout=180,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("https://"):
        raise RuntimeError(f"catbox ตอบกลับผิดรูปแบบ: {url[:200]}")
    return url


def up_0x0(path: str) -> str:
    with open(path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f}, headers=UA, timeout=180)
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("https://"):
        raise RuntimeError(f"0x0.st ตอบกลับผิดรูปแบบ: {url[:200]}")
    return url


def up_tmpfiles(path: str) -> str:
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f},
                          headers=UA, timeout=180)
    r.raise_for_status()
    url = r.json()["data"]["url"]
    # tmpfiles คืน URL หน้าเว็บ ต้องแปลงเป็น direct link
    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")


HOSTS = [("catbox.moe", up_catbox), ("0x0.st", up_0x0), ("tmpfiles.org", up_tmpfiles)]


def upload(path: str) -> str:
    """อัปโหลดไปยัง host ตัวแรกที่สำเร็จ แล้วยืนยันว่าโหลดกลับมาได้จริง"""
    for name, fn in HOSTS:
        try:
            url = fn(path)
        except Exception as e:
            print(f"   ✗ {name}: {type(e).__name__}: {e}")
            continue

        # ยืนยันว่า LINE จะโหลดรูปนี้ได้จริง — host บางเจ้าคืน URL ที่ยังไม่พร้อม
        try:
            chk = requests.get(url, headers=UA, timeout=60)
            ctype = chk.headers.get("content-type", "")
            if chk.status_code == 200 and ctype.startswith("image/"):
                print(f"   ✓ {name}: {url}  ({ctype}, {len(chk.content)/1024:.0f} KB)")
                return url
            print(f"   ✗ {name}: ตรวจกลับไม่ผ่าน HTTP {chk.status_code} ctype={ctype}")
        except Exception as e:
            print(f"   ✗ {name}: ตรวจกลับล้มเหลว {type(e).__name__}")

    raise RuntimeError(f"อัปโหลด {path} ไม่สำเร็จสักเจ้า")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    results = {}
    for path in sys.argv[1:]:
        print(f"\n📤 {path}")
        results[path] = upload(path)

    print("\n" + "=" * 60)
    print("📋 URL ที่ได้ (เอาไปใส่ .env)")
    print("=" * 60)
    for path, url in results.items():
        print(f"{path}\n  → {url}")
