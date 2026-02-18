# Push to GitHub

## Quick Setup (Recommended)

Run these commands in your terminal:

```bash
cd /Users/santiagoweight/projects/flaky

# Authenticate with GitHub (one-time setup)
gh auth login

# Create repository and push
gh repo create flaky --public --source=. --remote=origin --push
```

This will:
1. Authenticate you with GitHub
2. Create a new public repository called "flaky"
3. Add it as the remote "origin"
4. Push all commits

## Manual Setup (Alternative)

If you prefer to create the repo manually on GitHub:

### 1. Create Repository on GitHub
- Go to https://github.com/new
- Repository name: `flaky`
- Description: "Binary eval framework for non-deterministic workloads"
- Choose Public or Private
- **Don't** initialize with README (we already have one)
- Click "Create repository"

### 2. Push Your Code
```bash
cd /Users/santiagoweight/projects/flaky

# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/flaky.git

# Push to GitHub
git push -u origin main
```

## After Pushing

### View Your Repository
```bash
# Open in browser
gh repo view --web

# Or manually go to:
# https://github.com/YOUR_USERNAME/flaky
```

### Enable GitHub Actions
1. Go to your repository on GitHub
2. Click "Actions" tab
3. GitHub Actions should auto-enable
4. Add `ANTHROPIC_API_KEY` to repository secrets:
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key

### Set Up Branch Protection (Optional)
1. Go to Settings → Branches
2. Add rule for `main` branch:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

## Repository Features

Once pushed, your repository will have:

### ✅ Automatic CI/CD
- Tests run on every push
- PR comments with eval results
- Status checks for branch protection

### ✅ Complete Documentation
- README with quick start
- TESTING guide
- GIT_GUIDE for workflows
- STATUS page

### ✅ Professional Structure
```
flaky/
├── .github/workflows/     # CI/CD
├── flaky/                 # Core library
├── demo/                  # Demo app
├── web/                   # Web application
├── tests/                 # Test suite
└── docs (*.md)           # Documentation
```

### ✅ Test Coverage
- 45 unit tests
- 9 backend tests
- 6 integration tests
- E2E tests

## Quick Commands

```bash
# Check current status
git status
git remote -v

# View commits
git log --oneline

# Push future changes
git add -A
git commit -m "Your commit message"
git push

# Create a pull request
gh pr create --title "Feature name" --body "Description"
```

## Troubleshooting

### Authentication Issues
```bash
# Check auth status
gh auth status

# Re-authenticate
gh auth login

# Use SSH instead of HTTPS
gh auth setup-git
```

### Push Rejected
```bash
# Pull latest changes first
git pull origin main --rebase

# Then push
git push origin main
```

### Wrong Remote URL
```bash
# Check current remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/YOUR_USERNAME/flaky.git
```

## Next Steps After Pushing

1. **Star your own repo** ⭐ (why not!)
2. **Add topics** to help others find it:
   - `python`
   - `testing`
   - `evaluation`
   - `llm`
   - `reliability`
3. **Share the link** with your team
4. **Create issues** for future features
5. **Set up project board** for task tracking

## Repository URL

After pushing, your repository will be at:
```
https://github.com/YOUR_USERNAME/flaky
```

Replace `YOUR_USERNAME` with your GitHub username.
