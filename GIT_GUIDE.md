# Git Repository Guide

## Repository Status

✅ Git repository initialized
✅ Initial commit created (d67f288)
✅ 47 files committed (7,963 lines)

## Current State

```bash
Branch: main
Commits: 1
Files tracked: 47
Status: Clean working tree
```

## Common Git Commands

### Check Status
```bash
git status
git log --oneline
git log --stat
```

### Making Changes
```bash
# Stage specific files
git add flaky/case.py

# Stage all changes
git add -A

# Commit with message
git commit -m "Add new feature"

# Commit with detailed message
git commit -m "$(cat <<'EOF'
Short summary line

Detailed explanation of what changed and why.
Can span multiple lines.
EOF
)"
```

### Branching
```bash
# Create new branch
git checkout -b feature/new-eval-case

# Switch branches
git checkout main

# List branches
git branch -a

# Delete branch
git branch -d feature/old-feature
```

### Remote Repository

To push to GitHub/GitLab:

```bash
# Add remote
git remote add origin https://github.com/yourusername/flaky.git

# Push to remote
git push -u origin main

# Pull from remote
git pull origin main
```

### Viewing Changes
```bash
# See unstaged changes
git diff

# See staged changes
git diff --cached

# See changes in specific file
git diff flaky/case.py

# See commit history
git log --graph --oneline --all
```

### Undoing Changes
```bash
# Unstage file (keep changes)
git restore --staged flaky/case.py

# Discard changes in file
git restore flaky/case.py

# Amend last commit (if not pushed)
git commit --amend

# Reset to previous commit (careful!)
git reset --hard HEAD~1
```

## Recommended Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/add-timeout-support

# Make changes
# ... edit files ...

# Stage and commit
git add flaky/runner.py tests/test_runner.py
git commit -m "Add timeout support to test execution"

# Push to remote (if set up)
git push -u origin feature/add-timeout-support
```

### 2. Bug Fixes
```bash
# Create bugfix branch
git checkout -b fix/json-parsing-error

# Fix the bug
# ... edit files ...

# Commit with descriptive message
git commit -m "Fix JSON parsing error in reporter

- Handle empty test results gracefully
- Add error message for invalid JSON
- Update tests to cover edge case"

# Push
git push -u origin fix/json-parsing-error
```

### 3. Testing Changes
```bash
# Before committing, run tests
./run_all_tests.sh

# If tests pass, commit
git add -A
git commit -m "Your commit message"
```

## Commit Message Guidelines

### Good Commit Messages
```
Add parallel execution support

- Implement ProcessPoolExecutor for test isolation
- Add --max-workers CLI flag
- Update documentation with parallel mode examples
```

### Bad Commit Messages
```
fix stuff
update
changes
wip
```

### Conventional Commits (Optional)
```
feat: add timeout support to runner
fix: resolve JSON parsing error in reporter
docs: update README with installation steps
test: add integration tests for CLI
refactor: simplify test discovery logic
```

## Git Ignore

The `.gitignore` file excludes:
- `__pycache__/` - Python bytecode
- `*.pyc` - Compiled Python files
- `.env` - Environment variables
- `node_modules/` - Frontend dependencies
- `.pytest_cache/` - Test cache
- `dist/`, `build/` - Build artifacts

## Branches Strategy

### Recommended Structure
- `main` - Stable, production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `fix/*` - Bug fixes
- `test/*` - Test improvements
- `docs/*` - Documentation updates

### Example Flow
```bash
# Start new feature
git checkout -b feature/add-csv-export

# Work on feature
git add flaky/reporter.py
git commit -m "Add CSV export to reporter"

# Merge to develop
git checkout develop
git merge feature/add-csv-export

# When ready for release
git checkout main
git merge develop
git tag v0.2.0
```

## Tags for Releases

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Initial release"

# List tags
git tag -l

# Push tags to remote
git push origin --tags

# Checkout specific version
git checkout v0.1.0
```

## Useful Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = restore --staged
    last = log -1 HEAD
    visual = log --graph --oneline --all
```

Then use:
```bash
git st        # instead of git status
git co main   # instead of git checkout main
git visual    # see commit graph
```

## Current Repository Structure

```
flaky/
├── .git/                  # Git repository data
├── .github/workflows/     # CI/CD workflows
├── flaky/                 # Core library
├── demo/                  # Demo application
├── web/                   # Web application
├── tests/                 # Test suite
├── README.md             # Main documentation
├── TESTING.md            # Test guide
├── pyproject.toml        # Package configuration
└── .gitignore            # Git ignore rules
```

## Next Steps

1. **Set up remote repository**
   ```bash
   # On GitHub/GitLab, create new repo
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Enable GitHub Actions**
   - Push to GitHub
   - Actions will run automatically on push/PR
   - Add `ANTHROPIC_API_KEY` to repository secrets

3. **Create development branch**
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```

4. **Set up branch protection**
   - Protect `main` branch
   - Require PR reviews
   - Require status checks to pass
