# GitHub Actions Setup Guide

This guide shows you how to set up automatic deployment from GitHub to your Azure VM.

---

## Prerequisites

You must have completed the Azure VM setup first (see `AZURE_DEPLOYMENT_GUIDE.md`).

You'll need:
- ✅ Azure VM running
- ✅ DashTrade deployed on the VM
- ✅ SSH access to the VM
- ✅ Deploy script created (`/opt/dashtrade/deploy.sh`)

---

## Step 1: Get Your VM SSH Private Key

On your **local machine** (not the VM), you should have the SSH key you used to create the VM.

If you created the VM with a generated key:
1. It was downloaded as a `.pem` file when you created the VM
2. Find this file (usually in Downloads folder)
3. Open it with a text editor
4. Copy the entire contents (from `-----BEGIN` to `-----END`)

**Example:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
(many lines)
...
-----END OPENSSH PRIVATE KEY-----
```

---

## Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository: `https://github.com/bot7897481/DashTrade`
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**

Add these 3 secrets:

### Secret 1: AZURE_SSH_KEY
- **Name:** `AZURE_SSH_KEY`
- **Value:** (Paste your entire SSH private key from Step 1)
- Click **Add secret**

### Secret 2: AZURE_VM_IP
- **Name:** `AZURE_VM_IP`
- **Value:** Your VM's public IP address (e.g., `20.123.45.67`)
- Click **Add secret**

### Secret 3: AZURE_SSH_USER
- **Name:** `AZURE_SSH_USER`
- **Value:** `azureuser` (or whatever username you used when creating the VM)
- Click **Add secret**

**You should now have 3 secrets:**
```
✅ AZURE_SSH_KEY
✅ AZURE_VM_IP
✅ AZURE_SSH_USER
```

---

## Step 3: Understand the GitHub Actions Workflow

The workflow file is already created at: `.github/workflows/deploy-to-azure.yml`

**What it does:**
1. Triggers when you push to your branch or main
2. Connects to your Azure VM via SSH
3. Runs the deployment script
4. Verifies services are running
5. Reports success or failure

**When it runs:**
- ✅ Every time you push to `claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd`
- ✅ Every time you push to `main`
- ✅ Manually via "Actions" tab in GitHub

---

## Step 4: Test the Workflow

### Method 1: Make a test change and push

```bash
# In your local Claude Code environment
cd /home/user/DashTrade

# Make a small test change (add a comment to a file)
echo "# Test deployment" >> README.md

# Commit and push
git add README.md
git commit -m "Test: Trigger GitHub Actions deployment"
git push origin claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
```

### Method 2: Manually trigger workflow

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Deploy to Azure VM** workflow
4. Click **Run workflow** button
5. Select your branch
6. Click **Run workflow**

---

## Step 5: Monitor the Deployment

1. Go to **Actions** tab in GitHub
2. Click on the running workflow
3. Click on the **deploy** job
4. Watch the steps execute in real-time

**What you'll see:**
```
📥 Checkout code           ✅
🔐 Setup SSH              ✅
🚀 Deploy to Azure VM     ✅ (runs deploy.sh on VM)
✅ Verify Deployment      ✅
🎉 Deployment Complete    ✅
```

**Total time:** ~2-3 minutes

---

## Step 6: Verify Deployment Worked

After the workflow completes:

1. **Check GitHub Actions:**
   - ✅ All steps should be green
   - ❌ If any step is red, click on it to see the error

2. **Check your app:**
   - Open browser: `http://YOUR_VM_IP`
   - You should see your latest changes!

3. **Check logs on VM (if issues):**
   ```bash
   ssh -i your-key.pem azureuser@YOUR_VM_IP
   sudo journalctl -u dashtrade-streamlit -n 50 --no-pager
   ```

---

## Workflow Explained

### Triggers
```yaml
on:
  push:
    branches:
      - claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd
      - main
  workflow_dispatch:  # Allows manual triggering
```

This means the workflow runs:
- ✅ When you push to your branch
- ✅ When you push to main
- ✅ When you manually trigger it

### Steps

**1. Checkout code**
- Downloads your repository code to the GitHub runner

**2. Setup SSH**
- Configures SSH connection to your Azure VM
- Uses the secrets you added

**3. Deploy to Azure VM**
- Connects to your VM
- Runs `/opt/dashtrade/deploy.sh`
- This script:
  - Pulls latest code
  - Installs dependencies
  - Restarts services

**4. Verify Deployment**
- Checks that services are running
- Fails the workflow if services aren't running

**5. Deployment Complete**
- Displays success message
- Shows your app URL

---

## Troubleshooting

### Error: "Permission denied (publickey)"

**Problem:** GitHub Actions can't connect to your VM

**Fix:**
1. Check that `AZURE_SSH_KEY` secret contains the **entire** private key
2. Check that `AZURE_VM_IP` is correct
3. Check that `AZURE_SSH_USER` is correct (usually `azureuser`)

---

### Error: "deploy.sh: No such file or directory"

**Problem:** Deploy script doesn't exist on the VM

**Fix:**
```bash
# Connect to VM
ssh -i your-key.pem azureuser@YOUR_VM_IP

# Create deploy script (see AZURE_DEPLOYMENT_GUIDE.md)
sudo nano /opt/dashtrade/deploy.sh
chmod +x /opt/dashtrade/deploy.sh
```

---

### Error: "Failed to restart dashtrade-streamlit"

**Problem:** Service failed to restart

**Fix:**
```bash
# Connect to VM
ssh -i your-key.pem azureuser@YOUR_VM_IP

# Check logs
sudo journalctl -u dashtrade-streamlit -n 100

# Common issues:
# - Missing dependency: pip install missing-package
# - Database error: check DATABASE_URL in .env
# - Port in use: sudo lsof -i :5000
```

---

### Workflow runs but app doesn't update

**Problem:** Code pulled but changes not showing

**Fix:**
```bash
# Connect to VM
ssh -i your-key.pem azureuser@YOUR_VM_IP

# Force restart services
sudo systemctl restart dashtrade-streamlit
sudo systemctl restart dashtrade-webhook

# Clear Streamlit cache
rm -rf /opt/dashtrade/.streamlit/cache
```

---

## Development Workflow

Now that GitHub Actions is set up, your workflow is:

```
1. Work in Claude Code
   ↓
2. Test locally (optional)
   ↓
3. Commit changes
   ↓
4. Push to GitHub
   ↓
5. GitHub Actions automatically deploys to Azure VM
   ↓
6. Check your live app at http://YOUR_VM_IP
```

**That's it!** No manual deployment needed. 🚀

---

## Advanced: Deploy to Production

If you want separate environments:

### Setup
1. Create another branch: `production`
2. Create another Azure VM (or use same VM with different ports)
3. Update workflow to deploy different branches to different VMs

### Example: Two Environments

**Development (your current branch):**
- Branch: `claude/learn-replit-01VJWXqcpk6TTxoc63oYcQHd`
- VM: `dev-vm` (20.123.45.67)
- URL: http://20.123.45.67

**Production:**
- Branch: `main`
- VM: `prod-vm` (40.111.22.33)
- URL: http://40.111.22.33

---

## Cost Optimization

**GitHub Actions:**
- ✅ **FREE** for public repositories
- ✅ **FREE** 2000 minutes/month for private repositories
- Each deployment uses ~2 minutes
- You can deploy ~1000 times/month for free!

**Azure VM:**
- Turn off VM when not in use to save money
- Use Azure's auto-shutdown feature
- Estimated cost: ~$45/month for B2s running 24/7

---

## Summary Checklist

Before you can use GitHub Actions:

- [ ] Azure VM is running
- [ ] DashTrade is deployed on VM
- [ ] `/opt/dashtrade/deploy.sh` exists and is executable
- [ ] `AZURE_SSH_KEY` secret added to GitHub
- [ ] `AZURE_VM_IP` secret added to GitHub
- [ ] `AZURE_SSH_USER` secret added to GitHub
- [ ] `.github/workflows/deploy-to-azure.yml` exists in your repo
- [ ] Pushed changes to trigger workflow

Once all checked:
✅ **You're done!** Every push to GitHub automatically deploys to Azure VM.

---

## Questions?

If deployment fails:
1. Check GitHub Actions logs
2. SSH to VM and check service logs
3. Verify all secrets are set correctly
4. Make sure deploy.sh script works manually first

Good luck! 🚀
