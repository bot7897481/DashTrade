# Railway Deployment Guide for DashTrade

## 🚂 Automatic GitHub to Railway Deployment

This guide will help you set up automatic deployments from your GitHub repository to Railway whenever you push code changes.

## Prerequisites

- GitHub repository with your DashTrade code
- Railway account (https://railway.com)
- PostgreSQL service on Railway

## Step 1: Connect Railway to GitHub

### Option A: New Railway Project from GitHub

1. **Go to Railway Dashboard**
   - Visit https://railway.app/dashboard
   - Click "New Project"

2. **Connect from GitHub**
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub account
   - Select your `DashTrade` repository

3. **Configure the Project**
   - Railway will automatically detect your `Procfile` and `requirements.txt`
   - The deployment will start automatically

### Option B: Connect Existing Railway Project

If you already have a Railway project:

1. **Go to your Railway Project**
   - Select your project from the dashboard

2. **Connect to GitHub**
   - Go to "Settings" tab
   - Find "GitHub" section
   - Click "Connect to GitHub"
   - Select your repository

3. **Enable Auto-Deploy**
   - In the Settings tab, enable "Automatic deployments"
   - Choose the branch you want to deploy from (usually `main`)

## Step 2: Set Up PostgreSQL Database

1. **Add PostgreSQL Service**
   ```
   + Add Service → Database → PostgreSQL
   ```

2. **Configure Environment Variables**
   - Railway automatically sets `DATABASE_URL` when you add PostgreSQL
   - The variable will be available to your app automatically
   - No manual configuration needed!

## Step 3: Configure Environment Variables (Optional)

Some optional environment variables you might want to set:

1. **In Railway Dashboard:**
   - Go to your project → Variables tab
   - Add any custom variables:

```
# Optional: API Keys for enhanced features
ALPHA_VANTAGE_API_KEY=your_key_here
YAHOO_FINANCE_API_KEY=your_key_here

# Optional: Email service (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Step 4: Deploy and Test

1. **Trigger Deployment**
   - Push to your main branch: `git push origin main`
   - Railway will automatically start deploying

2. **Monitor Deployment**
   - Watch the deployment logs in Railway dashboard
   - The `release` command will run `finalize_setup.py` to set up your database

3. **Access Your App**
   - Once deployed, Railway provides a public URL
   - Your app will be live at: `https://your-project-name.railway.app`

## Step 5: Default Admin Account

On first deployment, Railway will automatically create a default admin account:

- **Username:** `admin`
- **Password:** `admin123!`
- **Email:** `admin@dashtrade.app`

⚠️ **IMPORTANT:** Change the default password after first login!

## Troubleshooting

### Authentication Not Working

If authentication fails:

1. **Check Database Connection**
   ```bash
   # In Railway logs, look for:
   ✅ Database tables created successfully
   ✅ Default superadmin account created!
   ```

2. **Verify Environment Variables**
   - Go to Railway → Variables tab
   - Ensure `DATABASE_URL` is set (automatically by PostgreSQL service)

3. **Check Logs**
   - Go to Railway → Deployments tab
   - Click on latest deployment
   - Check build and runtime logs

### Deployment Fails

**Common Issues:**

1. **Missing Dependencies**
   - Ensure `requirements.txt` includes all dependencies
   - Check if `psycopg2-binary` is included

2. **Database Issues**
   - Ensure PostgreSQL service is added and healthy
   - Check if `DATABASE_URL` is properly formatted

3. **Build Errors**
   - Check Railway deployment logs for specific error messages
   - Ensure `Procfile` syntax is correct

### Manual Redeploy

If needed, you can trigger a manual redeploy:

1. Go to Railway project dashboard
2. Click "Deploy" button
3. Or push an empty commit: `git commit --allow-empty -m "Trigger deploy" && git push`

## Development Workflow

### Making Changes

1. **Develop Locally**
   ```bash
   # Make your changes
   git add .
   git commit -m "Your changes"
   ```

2. **Push to GitHub**
   ```bash
   git push origin main
   ```

3. **Automatic Deployment**
   - Railway detects the push
   - Runs `release: python finalize_setup.py` (database setup)
   - Builds and deploys your app
   - App is live within 2-5 minutes

### Environment Differences

- **Local Development:** Uses SQLite or local PostgreSQL
- **Railway Production:** Uses Railway PostgreSQL service
- Code automatically handles both environments

## Security Best Practices

1. **Change Default Credentials**
   - Immediately change the default admin password
   - Create user accounts for regular access

2. **Environment Variables**
   - Never commit sensitive data to GitHub
   - Use Railway's environment variables for secrets

3. **Database Security**
   - Railway PostgreSQL is secure by default
   - Database is not publicly accessible
   - Only your app can connect using `DATABASE_URL`

## Monitoring and Maintenance

### View Logs
```bash
# In Railway dashboard:
# Go to Deployments → Latest deployment → View Logs
```

### Database Management
- Use Railway's database tools
- Or connect externally using the `DATABASE_URL`

### Updates
- Push code changes to automatically update
- Railway handles scaling and maintenance

## Cost Optimization

Railway offers:
- **Free Tier:** 512 MB RAM, 1 GB storage
- **Hobby Plan:** $5/month for better performance
- **Pro Plans:** For production workloads

Monitor usage in Railway dashboard and upgrade as needed.

## Support

- **Railway Docs:** https://docs.railway.app/
- **Community:** https://discord.gg/railway
- **GitHub Issues:** Report issues in your repository

---

🎉 **Your DashTrade app is now automatically deployed from GitHub to Railway!**

Every push to your main branch will automatically update your live application.
