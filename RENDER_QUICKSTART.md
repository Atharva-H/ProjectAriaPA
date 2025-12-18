# 🚀 Render Deployment Quick Start

## Yes, you can deploy everything on Render's free tier! ✅

- **PostgreSQL**: Free for 90 days, then $7/month
- **Backend**: Free (spins down after 15 min inactivity)
- **Frontend**: Free (always available)

## Quick Deploy (5 minutes)

### Step 1: Push to Git
```bash
git add .
git commit -m "Add Render deployment configuration"
git push
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Blueprint"**
3. Connect your Git repository
4. Render will detect `render.yaml` automatically
5. Click **"Apply"** to create all services

### Step 3: Configure Environment Variables

After services are created, set these in Render dashboard:

#### Backend Service → Environment:
```
FRONTEND_URL=https://projectaria-frontend.onrender.com
CORS_ALLOW_ORIGINS=https://projectaria-frontend.onrender.com
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://projectaria-backend.onrender.com/auth/google/callback
GOOGLE_CALENDAR_REDIRECT_URI=https://projectaria-backend.onrender.com/integrations/google/calendar/callback
GOOGLE_GMAIL_REDIRECT_URI=https://projectaria-backend.onrender.com/integrations/google/gmail/callback
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://projectaria-backend.onrender.com/whatsapp/webhook
```

#### Frontend Service → Environment:
```
VITE_API_URL=https://projectaria-backend.onrender.com
```

**Note**: Replace `projectaria-backend` and `projectaria-frontend` with your actual service names.

### Step 4: Wait for Deployment

- Database: ~2 minutes
- Backend: ~5-10 minutes (first time)
- Frontend: ~3-5 minutes

### Step 5: Test

1. **Backend**: `https://your-backend.onrender.com/` → Should show health message
2. **Frontend**: `https://your-frontend.onrender.com` → Should load your app

## 🎉 Done!

Your app is now live on Render's free tier!

## 📝 Next Steps

- Update Google OAuth redirect URIs in Google Cloud Console
- Update Twilio webhook URL in Twilio dashboard
- Monitor logs in Render dashboard
- Set up custom domains (optional)

## 🆘 Need Help?

See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for detailed documentation.

