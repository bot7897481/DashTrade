# DashTrade Quick Start Guide

Get your authenticated DashTrade app running in 5 minutes!

## 🚀 Quick Setup (3 Steps)

### Step 1: Get a Database URL

Choose the **easiest option** for you:

#### Option A: Neon.tech (Recommended - 2 minutes)

1. Go to https://neon.tech
2. Sign up with GitHub/Google (free)
3. Click "Create Project"
4. Copy the connection string
5. **Add to Replit Secrets**:
   - Click 🔒 in left sidebar
   - Key: `DATABASE_URL`
   - Value: paste the connection string

#### Option B: Supabase (Also great)

1. Go to https://supabase.com
2. Create free account
3. New Project → Copy database URL
4. Add to Replit Secrets

### Step 2: Run Migration

```bash
python migrate_database.py
```

Type `yes` when prompted. You'll see:
```
✓ Users table created
✓ Watchlist migrated
✓ Alerts migrated
✓ Preferences migrated
✓ Migration completed successfully!
```

### Step 3: Launch App

Click the **Run** button in Replit!

Or manually:
```bash
streamlit run app.py
```

## 🎉 First Login

1. Click "Create New Account"
2. Fill in your details:
   - Username: your_username
   - Email: you@email.com
   - Password: minimum 6 characters
3. Click "Create Account"
4. Login with your credentials

## ✅ You're Done!

Your DashTrade app now has:
- ✓ Secure authentication
- ✓ User registration
- ✓ Personal watchlists
- ✓ Private alerts
- ✓ HTTPS (automatic on Replit)
- ✓ Data isolation

## 🔧 Troubleshooting

### "DATABASE_URL not set"
- Check Replit Secrets (🔒 icon)
- Make sure key is exactly `DATABASE_URL`
- Value should start with `postgresql://`

### "Connection failed"
- Verify database URL is correct
- Check your database is active
- Try visiting your database dashboard

### "Import error"
Dependencies not installed:
```bash
pip install -e .
```

## 📚 Next Steps

- **Add stocks** to your watchlist
- **Create alerts** for price movements
- **Backtest strategies** with historical data
- **Compare stocks** with correlation analysis

## 🛠️ Advanced Setup

Need more details? Check these guides:
- `AUTHENTICATION_SETUP.md` - Full auth documentation
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `setup_database.py` - Database checker script
- `test_auth.py` - Test authentication system

## 🔐 Security Notes

- Passwords are encrypted with bcrypt
- Each user's data is completely isolated
- HTTPS is enabled automatically
- Session management is secure
- Never share your DATABASE_URL

## 💡 Pro Tips

1. **Bookmark your app URL** - Easy access anytime
2. **Enable Always-On** (Replit Hacker plan) - Never sleeps
3. **Add custom domain** - Professional look
4. **Regular backups** - Most cloud DBs do this automatically
5. **Monitor usage** - Check your database limits

## 🆘 Need Help?

1. Run diagnostics: `python setup_database.py`
2. Test authentication: `python test_auth.py`
3. Check logs in Replit console
4. Review the deployment guide

## 📊 Free Database Limits

| Provider | Storage | Best For |
|----------|---------|----------|
| Neon | 500 MB | Recommended |
| Supabase | 500 MB | Good features |
| ElephantSQL | 20 MB | Testing only |
| Railway | Varies | Full apps |

**500 MB = ~10,000+ watchlist entries!**

---

**Ready to trade?** Click Run and start analyzing! 📈

