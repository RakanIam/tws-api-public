# Siri Shortcut – Schedule WhatsApp Business Messages

Schedule WhatsApp Business messages to be sent at a future date and time using a Siri Shortcut backed by a lightweight Python server.

**"Hey Siri, schedule a WhatsApp message"** → prompts for recipient, message, date/time → message is sent automatically at the scheduled time via the WhatsApp Business Cloud API.

## Architecture

```
┌──────────────┐      POST /schedule      ┌──────────────┐      At scheduled time      ┌──────────────────┐
│ Siri Shortcut│ ──────────────────────── │ Python Server │ ────────────────────────── │ WhatsApp Business│
│  (iPhone)    │   (to, message, send_at) │  (APScheduler)│   graph.facebook.com API   │   Cloud API      │
└──────────────┘                          └──────────────┘                             └──────────────────┘
```

## Prerequisites

1. **WhatsApp Business Cloud API access**
   - Go to [Meta for Developers](https://developers.facebook.com/)
   - Create an app with WhatsApp product enabled
   - Under WhatsApp → API Setup, note your:
     - **Phone Number ID**
     - **Permanent Access Token** (generate a system user token for production)

2. **A server** reachable from the internet (VPS, cloud VM, Raspberry Pi with port forwarding, etc.)

3. **Python 3.10+**

## Server Setup

```bash
cd siri-whatsapp-scheduler

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
nano .env

# Run the server
python server.py

# For production, use gunicorn:
gunicorn -w 2 -b 0.0.0.0:5050 server:app
```

## API Endpoints

### `POST /schedule` — Schedule a message
```json
{
  "to": "+966501234567",
  "message": "Hello! This is a scheduled message.",
  "send_at": "2026-07-01T09:00:00"
}
```
Header: `X-API-Key: your_api_key`

Response:
```json
{
  "success": true,
  "job_id": "a1b2c3d4",
  "to": "966501234567",
  "message": "Hello! This is a scheduled message.",
  "send_at": "2026-07-01T09:00:00+03:00"
}
```

### `GET /jobs` — List scheduled messages
### `DELETE /jobs/<job_id>` — Cancel a scheduled message
### `GET /health` — Server health check

## Siri Shortcut Setup

Create a new shortcut in the **Shortcuts** app on your iPhone:

### Step-by-step

1. **Open Shortcuts** → tap **+** to create a new shortcut

2. **Add action: Ask for Input** (Text)
   - Prompt: `Recipient phone number (with country code)`

3. **Add action: Set Variable**
   - Name: `PhoneNumber`

4. **Add action: Ask for Input** (Text)
   - Prompt: `Message to send`

5. **Add action: Set Variable**
   - Name: `MessageText`

6. **Add action: Ask for Input** (Date and Time)
   - Prompt: `When should this message be sent?`

7. **Add action: Format Date**
   - Format: Custom → `yyyy-MM-dd'T'HH:mm:ss`

8. **Add action: Set Variable**
   - Name: `SendAt`

9. **Add action: Get Contents of URL**
   - URL: `https://your-server.com/schedule`
   - Method: **POST**
   - Headers:
     - `Content-Type`: `application/json`
     - `X-API-Key`: `your_api_key_here`
   - Request Body (JSON):
     - `to`: `PhoneNumber` (variable)
     - `message`: `MessageText` (variable)
     - `send_at`: `SendAt` (variable)

10. **Add action: Get Dictionary Value**
    - Key: `success`

11. **Add action: If**
    - Condition: `is` → `true`
    - **Then**: Show Alert → `Message scheduled for [SendAt]`
    - **Otherwise**: Show Alert → `Failed to schedule. Check server.`

12. **Name the shortcut**: `Schedule WhatsApp Message`

13. **(Optional)** Tap the shortcut settings icon → enable **Show in Share Sheet** and **Use as Quick Action**

### Siri Voice Trigger

After saving, say: **"Hey Siri, Schedule WhatsApp Message"**

Siri will walk through each prompt (recipient, message, time) and confirm once scheduled.

## Shortcut for Frequent Contacts

You can create simplified shortcuts for frequent contacts that skip the phone number prompt:

1. Follow the same steps above but **remove steps 2-3**
2. In the URL body, hardcode the `to` field: `"to": "+966501234567"`
3. Name it: `Message Ahmad on WhatsApp`
4. Say: **"Hey Siri, message Ahmad on WhatsApp"**

## Security Notes

- The `API_KEY` prevents unauthorized access to your scheduling server
- Never commit your `.env` file (it's in `.gitignore`)
- For production, use HTTPS (e.g., behind nginx with Let's Encrypt)
- The WhatsApp API token has full send access — treat it like a password
- Consider IP allowlisting if your server is publicly accessible

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Unauthorized" from shortcut | Check that `X-API-Key` header matches `API_KEY` in `.env` |
| Message not sending at scheduled time | Verify server timezone matches your `.env` `TIMEZONE` setting |
| WhatsApp API 401 error | Regenerate your access token at developers.facebook.com |
| Phone number rejected | Use full international format without `+` (e.g., `966501234567`) |
| Server unreachable from iPhone | Ensure port 5050 is open and server has a public IP or domain |
