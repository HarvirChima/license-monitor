"""
GitHub Enterprise License Monitor with Slack Notifications

This script checks your GitHub Enterprise license consumption
and sends a Slack alert when usage exceeds a configurable threshold.

Requirements:
    pip install requests

Environment Variables:
    GITHUB_TOKEN          - GitHub PAT with `manage_billing:enterprise` or `read:enterprise` scope
    GITHUB_ENTERPRISE     - Your enterprise slug (e.g., "my-company")
    SLACK_WEBHOOK_URL     - Slack Incoming Webhook URL for your channel
    LICENSE_THRESHOLD_PCT - (Optional) Alert threshold percentage, default 90
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone


# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_ENTERPRISE = os.environ.get("GITHUB_ENTERPRISE")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
LICENSE_THRESHOLD_PCT = int(os.environ.get("LICENSE_THRESHOLD_PCT", 90))

GITHUB_API_BASE = "https://api.github.com"


def get_license_info() -> dict:
    """Fetch license/consumption info for the GitHub Enterprise."""
    url = f"{GITHUB_API_BASE}/enterprises/{GITHUB_ENTERPRISE}/consumed-licenses"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def check_license_usage(license_data: dict) -> dict:
    """Evaluate license usage against the threshold."""
    total_seats = license_data.get("total_seats_purchased", 0)
    seats_consumed = license_data.get("total_seats_consumed", 0)

    if total_seats == 0:
        return {
            "status": "error",
            "message": "Could not determine total seats purchased.",
        }

    usage_pct = (seats_consumed / total_seats) * 100
    seats_remaining = total_seats - seats_consumed

    return {
        "status": "critical" if seats_consumed >= total_seats else
                  "warning" if usage_pct >= LICENSE_THRESHOLD_PCT else
                  "ok",
        "total_seats": total_seats,
        "seats_consumed": seats_consumed,
        "seats_remaining": seats_remaining,
        "usage_pct": round(usage_pct, 1),
    }


def build_slack_message(usage: dict) -> dict:
    """Build a Slack Block Kit message based on license usage status."""

    status_emoji = {
        "critical": "🔴",
        "warning": "🟡",
        "ok": "🟢",
    }
    status_text = {
        "critical": "CRITICAL — No licenses remaining!",
        "warning": f"WARNING — Usage above {LICENSE_THRESHOLD_PCT}% threshold",
        "ok": "OK — License usage is within normal range",
    }

    emoji = status_emoji.get(usage["status"], "❓")
    text = status_text.get(usage["status"], "Unknown status")

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} GitHub Enterprise License Alert",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* {text}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Enterprise:*\n`{GITHUB_ENTERPRISE}`"},
                    {"type": "mrkdwn", "text": f"*Usage:*\n{usage['usage_pct']}%"},
                    {"type": "mrkdwn", "text": f"*Seats Consumed:*\n{usage['seats_consumed']} / {usage['total_seats']}"},
                    {"type": "mrkdwn", "text": f"*Seats Remaining:*\n{usage['seats_remaining']}"},
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Checked at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Threshold set to {LICENSE_THRESHOLD_PCT}%",
                    }
                ],
            },
        ]
    }


def send_slack_notification(message: dict):
    """Post the message payload to the Slack Incoming Webhook."""
    response = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(message),
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    print("Slack notification sent successfully.")


def main():
    # --- Validate config ---
    missing = [
        name
        for name, val in [
            ("GITHUB_TOKEN", GITHUB_TOKEN),
            ("GITHUB_ENTERPRISE", GITHUB_ENTERPRISE),
            ("SLACK_WEBHOOK_URL", SLACK_WEBHOOK_URL),
        ]
        if not val
    ]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    # --- Fetch & evaluate ---
    print(f"Checking license usage for enterprise: {GITHUB_ENTERPRISE} ...")
    license_data = get_license_info()
    usage = check_license_usage(license_data)

    print(f"Seats consumed: {usage['seats_consumed']} / {usage['total_seats']} ({usage['usage_pct']}%)")
    print(f"Status: {usage['status']}")

    # --- Notify if threshold breached ---
    if usage["status"] in ("warning", "critical"):
        message = build_slack_message(usage)
        send_slack_notification(message)
    else:
        print("Usage is within normal range. No notification sent.")


if __name__ == "__main__":
    main()
