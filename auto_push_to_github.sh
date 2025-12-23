#!/bin/bash
# Auto-push script for GitHub
# This script commits and pushes changes to GitHub automatically

set -e

echo "🚀 Auto-pushing changes to GitHub..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository"
    exit 1
fi

# Check if there are changes to commit
if git diff --quiet && git diff --cached --quiet; then
    echo "✅ No changes to commit"
    exit 0
fi

# Get the current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📦 Current branch: $BRANCH"

# Add all changes
echo "📝 Staging changes..."
git add .

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-commit: Update at $TIMESTAMP"

echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG" || {
    echo "⚠️  No changes to commit or commit failed"
    exit 0
}

# Push to GitHub
echo "⬆️  Pushing to GitHub..."
git push origin "$BRANCH" || {
    echo "❌ Failed to push to GitHub"
    echo "💡 Make sure you have:"
    echo "   1. GitHub remote configured (git remote -v)"
    echo "   2. Proper authentication (SSH keys or GitHub CLI)"
    exit 1
}

echo "✅ Successfully pushed to GitHub!"
echo "🔗 Railway will automatically deploy the changes"


