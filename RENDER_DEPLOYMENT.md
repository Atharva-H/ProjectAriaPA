# Render Deployment Guide

This guide will help you deploy ProjectAria.PA to Render's free tier.

## 🎯 Overview

Yes, you can deploy all three components on Render's free tier:
- **PostgreSQL Database**: Free for 90 days, then $7/month
- **Backend Web Service**: Free tier (spins down after 15 min inactivity)
- **Frontend Static Site**: Free tier

## 📋 Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. Your project pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. All environment variables ready (see below)

## 🚀 Deployment Steps

### Option 1: Using render.yaml (Recommended - Infrastructure as Code)

1. **Connect your repository to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your Git repository
   - Render will automatically detect `render.yaml`

2. **Set Environment Variables**:
   After the services are created, you'll need to set these environment variables in the Render dashboard:

   **Backend Service Environment Variables:**
   ```
   FRONTEND_URL=https://your-frontend-url.onrender.com
   CORS_ALLOW_ORIGINS=https://your-frontend-url.onrender.com
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=https://your-backend-url.onrender.com/auth/google/callback
   GOOGLE_CALENDAR_REDIRECT_URI=https://your-backend-url.onrender.com/integrations/google/calendar/callback
   GOOGLE_GMAIL_REDIRECT_URI=https://your-backend-url.onrender.com/integrations/google/gmail/callback
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_WHATSAPP_FROM=your_twilio_whatsapp_number
   TWILIO_WEBHOOK_URL=https://your-backend-url.onrender.com/whatsapp/webhook
   ```

   **Frontend Service Environment Variables:**
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   ```

3. **Deploy**:
   - Render will automatically deploy all services
   - The database will be created first
   - Backend will run migrations automatically
   - Frontend will build and deploy

### Option 2: Manual Setup (Alternative)

If you prefer to set up services manually:

#### 1. Create PostgreSQL Database

1. Go to Render Dashboard → "New +" → "PostgreSQL"
2. Name: `projectaria-db`
3. Plan: **Free**
4. Click "Create Database"
5. Note the **Internal Database URL** (you'll need this)

#### 2. Create Backend Web Service

1. Go to Render Dashboard → "New +" → "Web Service"
2. Connect your repository
3. Configure:
   - **Name**: `projectaria-backend`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r backend/requirements.txt && cd backend && alembic upgrade head
     ```
   - **Start Command**: 
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: **Free**

4. **Add Environment Variables**:
   - `DATABASE_URL`: Use the database connection string from step 1
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `false`
   - `JWT_SECRET`: Generate a secure random string
   - `FRONTEND_URL`: Your frontend URL (set after creating frontend)
   - `CORS_ALLOW_ORIGINS`: Your frontend URL
   - Add all other required variables (see list above)

5. Click "Create Web Service"

#### 3. Create Frontend Static Site

1. Go to Render Dashboard → "New +" → "Static Site"
2. Connect your repository
3. Configure:
   - **Name**: `projectaria-frontend`
   - **Build Command**: 
     ```bash
     cd frontend && npm install && npm run build
     ```
   - **Publish Directory**: `frontend/dist`
   - **Plan**: **Free**

4. **Add Environment Variables**:
   - `VITE_API_URL`: Your backend URL (e.g., `https://projectaria-backend.onrender.com`)

5. Click "Create Static Site"

## 🔧 Important Configuration Notes

### Database Migrations

Migrations run automatically during backend deployment via the build command. If you need to run migrations manually:

```bash
cd backend
alembic upgrade head
```

### CORS Configuration

The backend automatically configures CORS based on the `ENVIRONMENT` variable:
- **Production**: Uses specific origins from `CORS_ALLOW_ORIGINS`
- **Development**: Allows all origins

Make sure to set `CORS_ALLOW_ORIGINS` to your frontend URL in production.

### WebSocket Support

If your app uses WebSockets, note that Render's free tier supports WebSockets, but the connection may timeout after inactivity. Consider upgrading to a paid plan for production use.

### Free Tier Limitations

- **Backend**: Spins down after 15 minutes of inactivity (first request after spin-down takes ~30 seconds)
- **Database**: Free for 90 days, then $7/month
- **Static Site**: Always available, no spin-down

## 🔐 Environment Variables Checklist

### Backend Required Variables:
- [ ] `DATABASE_URL` (auto-set from database service)
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `JWT_SECRET` (generate secure random string)
- [ ] `FRONTEND_URL`
- [ ] `CORS_ALLOW_ORIGINS`
- [ ] `GOOGLE_CLIENT_ID`
- [ ] `GOOGLE_CLIENT_SECRET`
- [ ] `GOOGLE_REDIRECT_URI`
- [ ] `GOOGLE_CALENDAR_REDIRECT_URI`
- [ ] `GOOGLE_GMAIL_REDIRECT_URI`
- [ ] `TWILIO_ACCOUNT_SID` (if using WhatsApp)
- [ ] `TWILIO_AUTH_TOKEN` (if using WhatsApp)
- [ ] `TWILIO_WHATSAPP_FROM` (if using WhatsApp)
- [ ] `TWILIO_WEBHOOK_URL` (if using WhatsApp)

### Frontend Required Variables:
- [ ] `VITE_API_URL` (your backend URL)

## 🧪 Testing Deployment

1. **Check Backend Health**:
   ```
   https://your-backend-url.onrender.com/
   ```
   Should return: `{"message": "✅ ProjectAria.PA backend is running successfully!"}`

2. **Check Frontend**:
   ```
   https://your-frontend-url.onrender.com
   ```
   Should load your React app

3. **Test API Connection**:
   - Open browser console on frontend
   - Check network requests to backend
   - Verify CORS headers are correct

## 🐛 Troubleshooting

### Backend won't start
- Check build logs for errors
- Verify all environment variables are set
- Check that database migrations completed successfully

### CORS errors
- Verify `CORS_ALLOW_ORIGINS` matches your frontend URL exactly
- Check that `FRONTEND_URL` is set correctly
- Ensure `ENVIRONMENT=production` is set

### Database connection errors
- Verify `DATABASE_URL` is set correctly
- Check that database service is running
- Ensure database migrations have run

### Frontend can't connect to backend
- Verify `VITE_API_URL` is set to your backend URL
- Check that backend service is running
- Verify CORS is configured correctly

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Free Tier](https://render.com/docs/free)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)

## 🔄 Updating Your Deployment

1. Push changes to your Git repository
2. Render will automatically detect changes and redeploy
3. Check deployment logs in Render dashboard

## 💡 Tips

1. **Keep services on same region**: Deploy all services in the same region for better performance
2. **Use Render's internal networking**: Services can communicate via internal hostnames
3. **Monitor logs**: Use Render's log viewer to debug issues
4. **Set up health checks**: Your backend already has a health endpoint at `/`
5. **Use environment groups**: For multiple environments (staging, production)

---

Need help? Check the [Render Community](https://community.render.com) or [Render Support](https://render.com/support).

