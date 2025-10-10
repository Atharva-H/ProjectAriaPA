from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from twilio.rest import Client
import datetime, pytz, os

app = FastAPI()

# Google OAuth setup
flow = Flow.from_client_secrets_file(
    "credentials.json",
    scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    redirect_uri="http://localhost:8080/oauth2callback"
)

# Twilio credentials (put your own)
TWILIO_SID = "ACfbfe18be6c048ccf919436118491da54"  # your Twilio Account SID
TWILIO_AUTH_TOKEN = "eae4bed9aa3c018155fa6108b9c3954a"  # your Auth Token
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"  # Twilio sandbox number
WHATSAPP_TO = "whatsapp:+919109986560"  # your personal WhatsApp number

@app.get("/")
def home():
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

@app.get("/oauth2callback")
def oauth2callback(request: Request):
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    service = build("calendar", "v3", credentials=credentials)

    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=23, minute=59, second=59).isoformat()

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])

    if not events:
        msg = "No meetings scheduled for today."
    else:
        msg = "📅 *Your Meetings for Today:*\n\n"
        for event in events:
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "No title")
            meet_link = event.get("hangoutLink", "No Google Meet link")
            msg += f"🕒 {start_time}\n📌 {summary}\n🔗 {meet_link}\n\n"

    # Send via Twilio WhatsApp
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        body=msg,
        to=WHATSAPP_TO
    )

    return {"message": "Meetings fetched and sent to WhatsApp!", "sid": message.sid}
