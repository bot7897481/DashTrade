# Deploy Frontend to Railway - Step by Step Guide

## Overview

This guide will help you deploy your React frontend from the `Front-end` folder to Railway, replacing the Lovable hosting.

## Prerequisites

- Railway account (same one you're using for the backend)
- GitHub repository with your code pushed
- Backend API already deployed on Railway

## Step-by-Step Deployment

### 1. Push Frontend Code to GitHub

First, make sure all the frontend changes are committed and pushed:

```bash
git add Front-end/
git commit -m "Add frontend for Railway deployment"
git push origin main
```

### 2. Create New Railway Service for Frontend

1. Go to Railway Dashboard: https://railway.app/dashboard
2. Click on your **DashTrade** project
3. Click **"+ New"** → **"GitHub Repo"**
4. Select your repository (bot7897481/DashTrade)
5. Railway will detect the repository

### 3. Configure the Frontend Service

After adding the service, configure it:

#### A. Set Root Directory

1. Click on the new service
2. Go to **Settings** tab
3. Scroll to **Service Settings**
4. Set **Root Directory**: `Front-end`
5. Click **Save**

#### B. Add Environment Variables

Go to **Variables** tab and add:

```
VITE_API_URL=https://overflowing-spontaneity-production.up.railway.app
```

(Replace with your actual backend Railway URL)

#### C. Verify Build Command

Railway should auto-detect the build settings from `nixpacks.toml`, but verify:
- **Build Command**: `npm run build`
- **Start Command**: `npm run preview -- --host 0.0.0.0 --port $PORT`

### 4. Update Backend Environment Variables

Now update your **backend service** to point to the new frontend URL:

1. Go to your **API Service** (backend)
2. Click **Variables** tab
3. Add a new variable:

```
FRONTEND_URL=https://your-frontend-service.railway.app
```

(Replace with the URL Railway gives your frontend service - you'll see this in the frontend service's Settings)

### 5. Deploy!

1. Railway will automatically start deploying your frontend
2. Wait for the deployment to complete (usually 2-3 minutes)
3. You'll see a URL like: `https://your-frontend-service.railway.app`

### 6. Update CORS (Optional but Recommended)

If you want to restrict CORS to only your frontend, update `api_server.py`:

```python
# Instead of allowing all origins (*)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Use specific frontend URL
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://alert-to-action-bot.lovable.app')
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}}, supports_credentials=True)
```

Then redeploy the backend.

## Architecture After Migration

```
┌─────────────────────────────────────────┐
│   Railway Project: DashTrade            │
│                                         │
│  ┌──────────────────┐                  │
│  │  Frontend Service │                  │
│  │  (React + Vite)  │                  │
│  │  Port: $PORT     │                  │
│  │  URL: xxx.railway.app                │
│  └──────┬───────────┘                  │
│         │                               │
│         │ API Calls                     │
│         ↓                               │
│  ┌──────────────────┐                  │
│  │  Backend Service │                  │
│  │  (Flask API)     │                  │
│  │  Port: 8081      │                  │
│  │  URL: overflowing-spontaneity...    │
│  └──────────────────┘                  │
│                                         │
└─────────────────────────────────────────┘
```

## Environment Variables Summary

### Backend Service (API)
```bash
# Database
DATABASE_URL=postgresql://...

# Email
SMTP2GO_API_KEY=your-key
EMAIL_FROM=notifications@novalgo.org
EMAIL_FROM_NAME=DashTrade

# Frontend URL (NEW!)
FRONTEND_URL=https://your-frontend.railway.app

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

### Frontend Service
```bash
# API Backend URL
VITE_API_URL=https://overflowing-spontaneity-production.up.railway.app
```

## Testing the Deployment

After deployment, test these features:

### 1. Basic Access
- Visit your frontend URL
- Landing page should load

### 2. Authentication
- Register a new account
- Login with existing account
- Check that API calls work

### 3. Password Reset
- Click "Forgot Password"
- Enter email
- Check that reset email arrives with correct URL
- Click link and reset password

### 4. Dashboard Features
- View bots
- Check trades
- Verify all API endpoints work

## Troubleshooting

### Issue: Frontend Shows White Screen

**Solution:**
- Check browser console for errors
- Verify `VITE_API_URL` is set correctly
- Check Railway deployment logs

### Issue: API Calls Failing (CORS Error)

**Solution:**
- Verify `VITE_API_URL` matches backend URL
- Check backend CORS settings
- Ensure backend service is running

### Issue: 404 on Page Refresh

**Solution:**
Add to `vite.config.ts` preview settings:
```typescript
preview: {
  spa: true // Enable SPA mode
}
```

Or configure Railway to redirect all routes to index.html:
Create `_redirects` file in `Front-end/public/`:
```
/*    /index.html   200
```

### Issue: Build Fails

**Solution:**
- Check Railway build logs
- Verify all dependencies in `package.json`
- Run `npm run build` locally first
- Check Node version compatibility

### Issue: Slow Build Times

**Solution:**
- Railway caches node_modules
- First build is slow, subsequent builds are faster
- Consider using `npm ci` instead of `npm install` (already configured)

## Monitoring

### View Logs
1. Go to Railway Dashboard
2. Click on Frontend Service
3. Go to **Deployments** tab
4. Click latest deployment
5. View build and runtime logs

### Check Resource Usage
- Go to **Metrics** tab
- Monitor CPU, Memory, Network

## Custom Domain (Optional)

To use your own domain:

1. Go to Frontend Service → **Settings**
2. Scroll to **Domains**
3. Click **Generate Domain** (if you want Railway subdomain)
4. Or click **Custom Domain** to add your own:
   - Enter your domain
   - Add CNAME record to your DNS:
     ```
     CNAME  your-domain.com  →  railway-provided-cname
     ```
5. Wait for DNS propagation (5-30 minutes)

## Rollback

If something goes wrong:

1. Go to **Deployments** tab
2. Find previous working deployment
3. Click **⋮** → **Redeploy**

## Cost Optimization

- Frontend is static files, very cheap to run
- Uses minimal resources
- Should stay within Railway free tier for low traffic
- Monitor usage in Railway dashboard

## Next Steps

After successful deployment:

1. ✅ Update all documentation with new URLs
2. ✅ Remove Lovable project (optional)
3. ✅ Set up custom domain if desired
4. ✅ Configure monitoring/alerts in Railway
5. ✅ Test all features thoroughly

## Support

If you encounter issues:

1. Check Railway logs (Deployments → Latest → Logs)
2. Check browser console (F12)
3. Verify environment variables
4. Test backend API directly with curl
5. Check Railway status page: https://status.railway.app/

## Migration Checklist

- [ ] Frontend code in `Front-end` folder
- [ ] `nixpacks.toml` created
- [ ] Environment variables configured
- [ ] Frontend service deployed
- [ ] Backend `FRONTEND_URL` updated
- [ ] Password reset emails working
- [ ] All features tested
- [ ] Documentation updated
- [ ] Old Lovable project can be archived

---

**Everything is now self-hosted on Railway!** 🎉
