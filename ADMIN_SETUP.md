# DashTrade Superadmin Setup Guide

Complete guide for setting up DashTrade with superadmin access.

## 🚀 Quick Setup (One Command!)

Run the automated setup script:

```bash
python finalize_setup.py
```

This single command will:
1. ✅ Verify your DATABASE_URL is set
2. ✅ Test database connection
3. ✅ Run complete database migration
4. ✅ Create your superadmin account

## Step-by-Step Instructions

### 1. Set Up Database

**Option A: Neon.tech (Recommended)**
1. Go to https://neon.tech
2. Sign up (free)
3. Create new project
4. Copy connection string
5. Add to Replit Secrets:
   - Key: `DATABASE_URL`
   - Value: `postgresql://user:pass@host/db`

**Option B: Supabase**
1. Go to https://supabase.com
2. Create project
3. Copy database URL from settings

**Option C: Other PostgreSQL**
- Use any PostgreSQL provider
- Just need the connection string

### 2. Run Finalization Script

```bash
python finalize_setup.py
```

**You'll see:**
```
======================================================================
       DashTrade Setup Finalization
======================================================================

🔌 Testing database connection...
✅ Database connection successful!

📊 Running database migration...
======================================================================
Creating users table with role support...
  ✅ Users table created
Updating watchlist table...
  ✅ Watchlist table updated
...

✅ Database migration completed successfully!

👑 Creating Superadmin Account
======================================================================

Please provide superadmin account details:
----------------------------------------------------------------------
Username: yourusername
Email: you@email.com
Full Name (optional): Your Name
Password (min 6 chars): ******
Confirm Password: ******

🔐 Creating superadmin account...

✅ Superadmin account created successfully!
======================================================================

👤 Username: yourusername
📧 Email: you@email.com
👑 Role: SUPERADMIN

======================================================================
🎉 Setup Complete!
======================================================================

✅ Database configured
✅ Tables migrated
✅ Superadmin account created

📱 Next Steps:
  1. Run: streamlit run app.py
  2. Login with your superadmin credentials
  3. Start trading!
```

### 3. Launch Application

```bash
streamlit run app.py
```

Or click the **Run** button in Replit!

### 4. Login as Superadmin

1. Navigate to your app URL
2. Enter your superadmin credentials
3. Click "Login"

**You'll see:**
- "👤 yourusername" in sidebar
- "👑 Admin Panel" mode available
- Full access to all features

## 👑 Superadmin Features

### Admin Panel Access

Navigate to **👑 Admin Panel** in the sidebar mode selector.

### User Management

**View All Users:**
- See complete user list with details
- Username, email, role, status
- Creation date, last login
- Active/inactive status

**Manage Roles:**
1. Go to "Manage User" expander
2. Select user to manage
3. Change role dropdown
4. Click "Update Role"

**Available Roles:**
- **user** - Standard user access
- **admin** - View users, limited management
- **superadmin** - Full system access

**Enable/Disable Users:**
1. Select user
2. Click "Toggle Active Status"
3. User immediately enabled/disabled

**Delete Users:**
1. Select user (not superadmin)
2. Click "🗑️ Delete User"
3. Click again to confirm
4. User and all data deleted

### System Statistics

View comprehensive stats:
- Total user count
- Your watchlist size
- Active alerts count
- System information
- Permission overview

## 🔐 Role Permissions

### Superadmin (You!)
✅ Full system access
✅ View all users
✅ Manage user roles
✅ Enable/disable accounts
✅ Delete users
✅ System administration

### Admin
✅ View all users
✅ System statistics
⚠️ Limited user management
❌ Cannot change roles
❌ Cannot delete users

### User
✅ Personal trading features
✅ Watchlist management
✅ Alert creation
✅ Strategy building
❌ No admin access

## 🛡️ Security Features

**Superadmin Protection:**
- Cannot be deleted
- Cannot change own role
- Cannot disable own account
- Protected in database

**Password Security:**
- Minimum 6 characters
- Bcrypt encryption
- Hidden input during setup
- Never stored in plain text

**Data Isolation:**
- Each user has separate data
- Watchlists are private
- Alerts are user-specific
- Complete data separation

## 📋 Common Admin Tasks

### Creating Additional Admins

1. Run setup again: `python finalize_setup.py`
2. Choose to create another admin
3. Enter new admin credentials
4. Select role (admin or superadmin)

### Promoting User to Admin

1. Login as superadmin
2. Go to 👑 Admin Panel
3. Select user to promote
4. Change role to "admin"
5. Click "Update Role"

### Disabling Problematic User

1. Go to Admin Panel
2. User Management tab
3. Select user
4. Click "Toggle Active Status"
5. User cannot login anymore

### Deleting User Account

1. Go to Admin Panel
2. Select user (not superadmin)
3. Click "🗑️ Delete User"
4. Confirm deletion
5. All user data removed

## 🔧 Troubleshooting

### "DATABASE_URL not set"

**Fix:**
```bash
# Check if set
echo $DATABASE_URL

# Set for session
export DATABASE_URL='postgresql://...'

# Or add to Replit Secrets (permanent)
```

### "Connection failed"

**Check:**
- Database URL format correct
- PostgreSQL server running
- Network/firewall allowing connection
- Credentials are valid

### "Superadmin already exists"

**Options:**
- Login with existing account
- Create additional superadmin
- Reset password (contact DB admin)

### "Cannot create superadmin"

**Reasons:**
- Username already taken
- Email already registered
- Password too short
- Database connection issue

### Migration Errors

**Solution:**
```bash
# Try running migration separately
python migrate_database.py

# Then create admin
python finalize_setup.py
```

## 📊 Database Schema

### Users Table
```sql
users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255),
  full_name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'user',  -- user/admin/superadmin
  created_at TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
)
```

### Role Hierarchy
```
superadmin (you!)
    ↓
  admin
    ↓
  user
```

## 🎯 Post-Setup Checklist

After running finalize_setup.py:

- [ ] Can login as superadmin
- [ ] See Admin Panel in sidebar
- [ ] View all users in admin panel
- [ ] Can change user roles
- [ ] Can enable/disable users
- [ ] System stats display correctly
- [ ] All trading features work
- [ ] Watchlist is personal
- [ ] Alerts are private

## 💡 Pro Tips

1. **Backup Superadmin Credentials**
   - Save in password manager
   - Create backup superadmin
   - Don't lose access!

2. **Regular User Management**
   - Review users weekly
   - Disable inactive accounts
   - Monitor for abuse

3. **Role Management**
   - Start users as "user"
   - Promote trustworthy users to "admin"
   - Limit superadmins (1-2 max)

4. **Security Best Practices**
   - Use strong passwords
   - Enable HTTPS (automatic on Replit)
   - Monitor login activity
   - Regular database backups

5. **Scale Considerations**
   - One database per environment
   - Separate dev/prod databases
   - Monitor database size
   - Plan for growth

## 🆘 Need Help?

**Check These:**
- QUICKSTART.md - Fast setup guide
- DEPLOYMENT_GUIDE.md - Production setup
- AUTHENTICATION_SETUP.md - Auth details

**Run Diagnostics:**
```bash
python setup_database.py  # Check database
python test_auth.py       # Test auth system
python finalize_setup.py  # Complete setup
```

**Common Commands:**
```bash
# Check database
python setup_database.py

# Run migration only
python migrate_database.py

# Complete setup (recommended)
python finalize_setup.py

# Start application
streamlit run app.py
```

## 📈 Next Steps

After setup is complete:

1. **Login** with superadmin
2. **Create test user** (register second account)
3. **Test user management** in Admin Panel
4. **Add stocks** to watchlist
5. **Create alerts** for monitoring
6. **Backtest strategies** with historical data
7. **Invite team members** (they register normally)
8. **Promote trusted users** to admin if needed

---

## 🎉 Congratulations!

You're now a DashTrade superadmin with full control over:
- ✅ User management
- ✅ Role assignments
- ✅ System administration
- ✅ Complete trading platform

**Happy trading! 📈**

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Access Level**: SUPERADMIN ONLY
