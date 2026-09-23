#!/usr/bin/env python3
"""Send one blood-pressure Flex alert to the two specified nurse recipients.

Run with --dry-run to inspect the payload; run with --send to submit it once.
Credentials are loaded from the project .env file.
"""

import argparse
import html
import json
import os
import sys

import requests
from dotenv import load_dotenv


URL = "https://morpromt2c.moph.go.th/alert/v3.1/messages"
RECIPIENTS = ["3909800556491", "3650100810887"]
TITLE = "แจ้งเตือนพยาบาลประจำจุด"
DETAILS = [
    "HN : 5123245",
    "ชื่อ : นายทดสอบ ระบบ  อายุ 51 ปี",
    "วัดความดันที่เครื่องหมายเลข 10",
    "BP  176 / 98   PUL  105",
]
WARNING = "[ ความดันสูงอันตราย]"


def build_payload():
    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#B71C1C",
            "paddingAll": "lg",
            "contents": [
                {"type": "text", "text": TITLE, "color": "#FFFFFF", "weight": "bold", "size": "lg", "wrap": True},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                *(
                    {"type": "text", "text": line, "size": "md", "color": "#263238", "wrap": True}
                    for line in DETAILS
                ),
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": WARNING, "size": "lg", "color": "#B71C1C", "weight": "bold", "wrap": True},
            ],
        },
    }
    message_text = "\n".join([TITLE, *DETAILS, WARNING])
    message_html = "<br>".join(html.escape(line) for line in [TITLE, *DETAILS, WARNING])
    return {
        "cid": RECIPIENTS,
        "messages": [{"type": "flex", "altText": message_text, "contents": bubble}],
        "message_title": TITLE,
        "message_html": message_html,
        "message_text": message_text,
        "message_type": "HPT",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true", help="print the payload without sending")
    action.add_argument("--send", action="store_true", help="send one request to MOPH Alert")
    args = parser.parse_args()

    payload = build_payload()
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    load_dotenv()
    client_key = os.getenv("CLIENT_KEY")
    secret_key = os.getenv("SECRET_KEY")
    if not client_key or not secret_key:
        print("Missing CLIENT_KEY or SECRET_KEY in .env", file=sys.stderr)
        return 1

    try:
        response = requests.post(
            URL,
            headers={"Content-Type": "application/json", "client-key": client_key, "secret-key": secret_key},
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP {response.status_code}")
    print(response.text[:1000])
    try:
        result = response.json()
    except ValueError:
        return 1
    return 0 if response.status_code == 200 and (result.get("message_code") == 200 or result.get("status") == "success") else 1


if __name__ == "__main__":
    sys.exit(main())
