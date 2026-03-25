# GitHub Enterprise License Monitor

A lightweight Python script that monitors your **GitHub Enterprise Cloud** license (seat) consumption via the [GitHub REST API](https://docs.github.com/en/enterprise-cloud@latest/rest/enterprise-admin/licensing) and sends a **Slack notification** when usage exceeds a configurable threshold.

---

## How It Works

```
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────┐
│ GitHub Actions cron   │─────▶│ GitHub REST API       │─────▶│ Slack Webhook │
│ (or manual trigger)   │      │ /consumed-licenses    │      │ notification  │
└──────────────────────┘      └──────────────────────┘      └──────────────┘
```

1. The script calls the GitHub Enterprise **consumed-licenses** endpoint to retrieve the number of seats purchased and seats consumed.
2. It calculates the usage percentage and compares it to a configurable threshold (default: **90%**).
3. If usage meets or exceeds the threshold, a rich Slack message is posted to your channel via an [Incoming Webhook](https://api.slack.com/messaging/webhooks).

---

## Prerequisites

| Requirement | Details |
|---|---|
| **GitHub Enterprise Cloud** | The consumed-licenses API is only available for Enterprise Cloud accounts. |
| **GitHub Personal Access Token (PAT)** | A PAT (classic) with the `read:enterprise` or `manage_billing:enterprise` scope, **or** a fine-grained PAT with enterprise administration read access. The token owner must be an **enterprise owner**. |
| **Slack Incoming Webhook** | Create one from your Slack workspace at [https://api.slack.com/apps](https://api.slack.com/apps) → *Incoming Webhooks*. |
| **Python 3.9+** | Required to run the script locally. Not needed if you only run it via the included GitHub Actions workflow. |

---

## Quick Start

### 1 · Clone the repository

```bash
git clone https://github.com/<your-org>/license-monitor.git
cd license-monitor
```

### 2 · Install dependencies

```bash
pip install -r requirements.txt
```

### 3 · Set environment variables

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GITHUB_ENTERPRISE="your-enterprise-slug"
export SLACK_WEBHOOK_URL="<your-slack-webhook-url>"

# Optional – defaults to 90 if not set
export LICENSE_THRESHOLD_PCT="85"
```

> **Tip:** Your enterprise slug is the value that appears in `https://github.com/enterprises/<slug>`.

### 4 · Run the script

```bash
python github_license_monitor.py
```

**Example output (below threshold):**

```
Checking license usage for enterprise: my-company ...
Seats consumed: 120 / 200 (60.0%)
Status: ok
Usage is within normal range. No notification sent.
```

**Example output (above threshold):**

```
Checking license usage for enterprise: my-company ...
Seats consumed: 185 / 200 (92.5%)
Status: warning
Slack notification sent successfully.
```

---

## Running via GitHub Actions (Recommended)

The repository includes a ready-to-use workflow at [`.github/workflows/license-monitor.yaml`](.github/workflows/license-monitor.yaml) that runs every **6 hours** and can also be triggered manually.

### Set up repository secrets

Go to **Settings → Secrets and variables → Actions** in your repository and add the following secrets:

| Secret name | Description |
|---|---|
| `ENTERPRISE_PAT` | Your GitHub PAT with `read:enterprise` scope |
| `ENTERPRISE_SLUG` | Your GitHub Enterprise slug (e.g. `my-company`) |
| `SLACK_WEBHOOK_URL` | Your Slack Incoming Webhook URL |

### Adjust the schedule (optional)

Edit the cron expression in the workflow file to change the check frequency:

```yaml
on:
  schedule:
    - cron: "0 */6 * * *"   # Every 6 hours (default)
    # - cron: "0 9 * * 1-5" # Weekdays at 9 AM UTC
    # - cron: "0 0 * * *"   # Daily at midnight UTC
```

### Trigger a manual run

1. Go to the **Actions** tab in your repository.
2. Select the **GitHub License Monitor** workflow.
3. Click **Run workflow**.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_TOKEN` | Yes | — | GitHub PAT with `read:enterprise` or `manage_billing:enterprise` scope |
| `GITHUB_ENTERPRISE` | Yes | — | Your enterprise slug |
| `SLACK_WEBHOOK_URL` | Yes | — | Slack Incoming Webhook URL |
| `LICENSE_THRESHOLD_PCT` | No | `90` | Percentage threshold at which alerts are sent |

---

## Slack Message Preview

The script sends a rich Slack message using [Block Kit](https://api.slack.com/block-kit) when the threshold is breached:

```
🟡 GitHub Enterprise License Alert
──────────────────────────────────
Status: WARNING — Usage above 90% threshold

Enterprise:      my-company
Usage:           92.5%
Seats Consumed:  185 / 200
Seats Remaining: 15

Checked at 2026-03-25 05:45:00 UTC | Threshold set to 90%
```

The alert severity changes automatically:

| Status | Condition | Emoji |
|---|---|---|
| **OK** | Usage below threshold | 🟢 |
| **Warning** | Usage at or above threshold | 🟡 |
| **Critical** | All seats consumed (100%) | 🔴 |

---

## Creating a Slack Incoming Webhook

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click **Create New App → From scratch**.
2. Name the app (e.g. *License Monitor*) and select your workspace.
3. In the left sidebar, click **Incoming Webhooks** and toggle it **On**.
4. Click **Add New Webhook to Workspace** and select the channel you want notifications posted to.
5. Copy the generated **Webhook URL** – this is your `SLACK_WEBHOOK_URL`.

---

## Project Structure

```
license-monitor/
├── .github/
│   └── workflows/
│       └── license-monitor.yaml   # GitHub Actions workflow (scheduled + manual)
├── github_license_monitor.py      # Main monitoring script
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## Customization Ideas

- **Change the threshold** — Set `LICENSE_THRESHOLD_PCT` to any value between 1 and 100.
- **Always send a notification** — Remove the `if usage["status"] in ("warning", "critical")` guard in `main()` to send a Slack message on every run regardless of usage level.
- **Add multiple channels** — Duplicate the `send_slack_notification()` call with different webhook URLs.
- **Integrate with other platforms** — Replace or extend `send_slack_notification()` to post to Microsoft Teams, PagerDuty, email, etc.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `403 Forbidden` from the GitHub API | Ensure the PAT has the `read:enterprise` scope and that the token owner is an **enterprise owner**. |
| `404 Not Found` from the GitHub API | Verify `GITHUB_ENTERPRISE` matches your enterprise slug exactly (case-sensitive). |
| Slack message not appearing | Confirm the webhook URL is correct and that the Slack app is installed in the target channel. |
| Script exits with *"Missing required environment variables"* | Export all three required environment variables before running. |

---

## License

This project is provided as-is for reference purposes. Use and modify it freely to suit your organization's needs.
