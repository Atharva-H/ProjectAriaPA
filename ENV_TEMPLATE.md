# Environment Variables Template

Copy these variables and set them in your Render dashboard or local `.env` file.

## Backend Environment Variables

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database (auto-set by Render from database service)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Authentication
JWT_SECRET=generate-a-secure-random-string-here
FRONTEND_URL=https://your-frontend-url.onrender.com
CORS_ALLOW_ORIGINS=https://your-frontend-url.onrender.com

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-backend-url.onrender.com/auth/google/callback
GOOGLE_CALENDAR_REDIRECT_URI=https://your-backend-url.onrender.com/integrations/google/calendar/callback
GOOGLE_GMAIL_REDIRECT_URI=https://your-backend-url.onrender.com/integrations/google/gmail/callback

# Twilio WhatsApp (if using)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://your-backend-url.onrender.com/whatsapp/webhook

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=false

# Tally Database (if using)
TALLY_DB_HOST=localhost
TALLY_DB_PORT=5432
TALLY_DB_USER=readonly_user
TALLY_DB_PASSWORD=secure_password
TALLY_DB_MAX_CONNECTIONS=10
TALLY_DB_MIN_CONNECTIONS=2

# Working Hours
WORK_START_HOUR=9
WORK_END_HOUR=18
```

## Frontend Environment Variables

```bash
VITE_API_URL=https://your-backend-url.onrender.com
```

## Local Development

For local development, create a `.env` file in the `backend/` directory with:

```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://user:password@localhost:5432/projectaria
JWT_SECRET=dev-secret-key-change-in-production
FRONTEND_URL=http://localhost:5173
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
# ... add other variables as needed
```

And in the `frontend/` directory, create a `.env` file with:

```bash
VITE_API_URL=http://localhost:8000
```

