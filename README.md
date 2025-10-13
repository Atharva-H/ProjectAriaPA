# ProjectAria.PA 🧠

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An AI-powered personal assistant backend that helps MSME CEOs manage their business through natural conversations. Connect Google Calendar, WhatsApp, and AI to interact with your data like you're talking to your company.

## 🎯 Key Features

- **Smart Calendar Management** - Natural language queries to Google Calendar
- **WhatsApp Integration** - Two-way messaging with AI-powered responses
- **AI Understanding** - ChatGPT/Gemini Pro for intent recognition
- **Secure Auth** - Google OAuth 2.0 with JWT sessions
- **Enterprise Logging** - Structured logs with user context

## 🛠️ Tech Stack

- Backend: FastAPI
- Database: PostgreSQL/SQLite
- AI: OpenAI GPT / Google Gemini
- Messaging: Twilio WhatsApp API
- Auth: Google OAuth 2.0
- Logging: Python logging + ContextVars

## 🚀 Quick Start

1. **Setup Environment**
    ```bash
    git clone https://github.com/<username>/ProjectAriaPA
    cd ProjectAriaPA
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Configure Environment**
    ```bash
    # Create .env file with:
    GOOGLE_CLIENT_ID=xxx
    GOOGLE_CLIENT_SECRET=xxx
    JWT_SECRET=xxx
    TWILIO_ACCOUNT_SID=xxx
    TWILIO_AUTH_TOKEN=xxx
    OPENAI_API_KEY=xxx  # or GEMINI_API_KEY
    ```

3. **Run Server**
    ```bash
    uvicorn app.main:app --reload
    ```

## 📚 API Routes

| Route | Purpose |
|-------|---------|
| `/auth/login` | Google OAuth login |
| `/calendar/today` | Today's events |
| `/whatsapp/webhook` | Twilio messages |
| `/users/me` | User profile |

## 💬 WhatsApp Commands

- "What's my schedule today?" → Fetches calendar events
- "Any meetings tomorrow?" → Checks tomorrow's schedule
- "Help" → Shows command list

## 📝 Example Logs

```log
2025-10-13 19:30:55 [INFO] [ProjectAria.Twilio] [user_id=user@example.com]: WhatsApp message processed
```

## 🔜 Roadmap

- [ ] Natural language function calling
- [ ] Meeting scheduling via WhatsApp
- [ ] Gmail/Drive integration
- [ ] Redis caching
- [ ] Production deployment

## 👥 Contributing

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Open PR

## 📞 Contact

Atharva Humar
- Email: projectaria.pa@gmail.com
- Role: Founder & CEO, Paricott

## 📄 License

MIT License - feel free to use and modify!

---

⭐ Star this repo if you find it helpful!