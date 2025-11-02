# Ultimate Network Tool - Deployment Guide

Complete guide for building, testing, and deploying the Ultimate Network Tool with Electron and auto-updates.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Testing During Development](#testing-during-development)
4. [Building for Production](#building-for-production)
5. [GitHub Auto-Update Setup](#github-auto-update-setup)
6. [Creating a Release](#creating-a-release)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Python 3.8+**
   - Download: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Node.js 18+**
   - Download: https://nodejs.org/
   - LTS version recommended

3. **Git**
   - Download: https://git-scm.com/
   - Required for version control and GitHub releases

4. **Npcap** (Windows packet capture driver)
   - Download: https://npcap.com/
   - Required for network packet capture features

### Optional (for icon creation)

- Image editor (Photoshop, GIMP, etc.)
- Online .ico converter: https://convertio.co/png-ico/

---

## Development Setup

### 1. Clone/Navigate to Project

```bash
cd "C:\Users\bas\Digidots\All-Data-Digidots-Basrose - Prive\Digidots apps\Ultimate network tool - UNT"
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 3. Install Node.js Dependencies

```bash
npm install
```

### 4. Add Application Icon (Important!)

1. Create or find a PNG icon (512x512 recommended)
2. Convert to .ico format with multiple sizes using:
   - https://convertio.co/png-ico/
   - https://icoconvert.com/
3. Save as `assets/icon.ico`

**Note**: The build will fail without an icon file!

---

## Testing During Development

### Option 1: Run Flask Only (Fastest for testing backend)

```bash
python app.py
```

Then open browser: http://localhost:5000

**Use this when:**
- Testing Flask backend changes
- Testing network features
- Quick iteration on Python code

---

### Option 2: Run in Electron Dev Mode (Test full app)

```bash
npm run dev
```

This will:
- Start Flask server using Python directly (not .exe)
- Launch Electron window
- Enable hot reload for Flask changes (restart app to see changes)
- **No auto-update checks** (--dev flag disables them)

**Use this when:**
- Testing the Electron wrapper
- Testing the full user experience
- Verifying window behavior
- Testing before building

**How it works:**
- The `--dev` flag in `electron/main.js` detects development mode
- Flask runs directly from Python (no PyInstaller build needed)
- Faster startup, easier debugging

---

### Option 3: Test Production Build Locally

```bash
# Build everything
npm run build

# Run the built version
npm start
```

This will:
- Build Python app with PyInstaller → `dist/app/app.exe`
- Build Electron installer → `release/Ultimate Network Tool Setup.exe`
- Run from the built executable (production mode)
- **Enable auto-update checks** (will check GitHub for updates)

**Use this when:**
- Testing the final production build
- Verifying auto-update functionality
- Testing installer behavior
- Final QA before release

---

## Building for Production

### Local Build (Manual)

```bash
# Build everything at once
npm run build
```

This creates:
- `dist/app/` - PyInstaller bundled Flask app
- `release/Ultimate Network Tool Setup.exe` - Electron installer (~150-250MB)

### What Gets Bundled:

The installer includes:
- ✅ Electron runtime
- ✅ Python Flask app (as .exe, no Python needed!)
- ✅ All Python dependencies
- ✅ Static files (HTML, CSS, JS)
- ✅ Templates
- ✅ Auto-updater

**User only needs:**
- Windows 10/11
- Npcap driver
- Admin privileges

No Python, no pip, no dependencies!

---

## GitHub Auto-Update Setup

### 1. Create GitHub Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Ultimate Network Tool with Electron"

# Create GitHub repo at: https://github.com/new
# Name it: ultimate-network-tool

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/ultimate-network-tool.git
git branch -M main
git push -u origin main
```

### 2. Update package.json

Edit `package.json` and update the publish section:

```json
"publish": [
  {
    "provider": "github",
    "owner": "YOUR_GITHUB_USERNAME",  // ← Change this
    "repo": "ultimate-network-tool",
    "private": false
  }
]
```

### 3. How Auto-Update Works

```
User launches app
    ↓
Electron checks GitHub Releases API
    ↓
Compares current version with latest release
    ↓
If new version found:
    - Shows "Update Available" dialog
    - User clicks "Download"
    - Downloads in background
    - Shows progress bar
    - When done: "Restart to install"
    ↓
User restarts → Update installed!
```

### 4. Testing Auto-Updates

To test auto-updates during development:

1. Build and install version 1.0.0:
   ```bash
   npm run build
   # Install the .exe from release/ folder
   ```

2. Change version in `package.json` to 1.0.1:
   ```json
   "version": "1.0.1",
   ```

3. Create a new release on GitHub (see next section)

4. Run the installed app (version 1.0.0)

5. After 5 seconds, you should see "Update Available" dialog

6. Click "Download" and watch the update process

---

## Creating a Release

### Automated Build (Recommended)

GitHub Actions will automatically build and create a release when you push a version tag.

```bash
# 1. Update version in package.json
# Edit package.json: "version": "1.0.0" → "1.0.1"

# 2. Commit the version change
git add package.json
git commit -m "Bump version to 1.0.1"
git push

# 3. Create and push a version tag
git tag v1.0.1
git push origin v1.0.1
```

**What happens:**
1. GitHub Actions detects the `v1.0.1` tag
2. Runs the build workflow (`.github/workflows/build.yml`)
3. Builds the installer on Windows runner
4. Creates a GitHub Release
5. Uploads the installer to the release
6. Users get auto-update notification!

**View progress:**
- https://github.com/YOUR_USERNAME/ultimate-network-tool/actions

---

### Manual Release (Alternative)

If you prefer to build locally and upload manually:

```bash
# 1. Build locally
npm run build

# 2. Go to GitHub → Releases → "Create a new release"
# 3. Create a tag: v1.0.0
# 4. Upload: release/Ultimate Network Tool Setup.exe
# 5. Publish release
```

---

## Project Structure

```
Ultimate Network Tool/
├── .github/
│   └── workflows/
│       └── build.yml              # GitHub Actions build workflow
├── assets/
│   ├── icon.ico                   # App icon (YOU NEED TO ADD THIS!)
│   └── README.md                  # Icon requirements
├── electron/
│   ├── main.js                    # Electron main process
│   └── preload.js                 # Security preload script
├── templates/                     # Flask HTML templates
├── static/                        # CSS, JS, images
├── modules/                       # Python modules
├── logs/                          # Runtime logs (created at runtime)
├── dist/                          # PyInstaller output (created by build)
├── release/                       # Electron installer (created by build)
├── app.py                         # Flask main server
├── app.spec                       # PyInstaller configuration
├── package.json                   # Node.js dependencies & build config
├── requirements.txt               # Python dependencies
├── DEPLOYMENT.md                  # This file!
└── README.md                      # Project readme
```

---

## Troubleshooting

### Build Issues

**Problem**: PyInstaller fails with import errors

```bash
# Solution: Add missing imports to app.spec hiddenimports
# Edit app.spec and add to hiddenimports list
```

**Problem**: Electron build fails - "icon not found"

```bash
# Solution: Add icon.ico to assets/ folder
# See: assets/README.md
```

**Problem**: Flask doesn't start in Electron

```bash
# Solution: Check logs in Electron DevTools
# In Electron window: Ctrl+Shift+I to open DevTools
# Look for Flask startup errors in Console
```

---

### Auto-Update Issues

**Problem**: Updates not detected

```bash
# Check:
1. Is app running in dev mode? (Updates disabled with --dev flag)
2. Is GitHub repo public?
3. Is package.json publish section correct?
4. Are there any releases on GitHub?
```

**Problem**: "Update available" but download fails

```bash
# Check:
1. GitHub release has .exe file attached
2. File name matches: "Ultimate Network Tool Setup X.X.X.exe"
3. Internet connection is working
4. Check DevTools console for errors
```

---

### GitHub Actions Issues

**Problem**: Build workflow fails

```bash
# Common fixes:
1. Check Node.js version compatibility
2. Check Python version compatibility
3. Verify all dependencies in requirements.txt are installable on Windows
4. Check workflow logs: GitHub → Actions → Click failed workflow
```

**Problem**: Release created but no .exe attached

```bash
# Check:
1. Build step completed successfully
2. Artifact path is correct: release/*.exe
3. Check workflow file: .github/workflows/build.yml
```

---

## Version Numbering

Follow semantic versioning (https://semver.org/):

- **Major version** (1.0.0 → 2.0.0): Breaking changes
- **Minor version** (1.0.0 → 1.1.0): New features, backwards compatible
- **Patch version** (1.0.0 → 1.0.1): Bug fixes

### Update checklist:

1. ✅ Change version in `package.json`
2. ✅ Commit and push
3. ✅ Create git tag: `git tag v1.0.1`
4. ✅ Push tag: `git push origin v1.0.1`
5. ✅ Wait for GitHub Actions to build
6. ✅ Test the release installer
7. ✅ Users get auto-update!

---

## Distribution

### For End Users:

1. Download installer: `Ultimate Network Tool Setup.exe`
2. Run installer (requires admin)
3. Install Npcap if not already installed
4. Launch app
5. Updates download automatically!

### For IT Deployment:

Use silent install:
```bash
"Ultimate Network Tool Setup.exe" /S
```

---

## Summary

### Development Workflow:

```bash
# Quick backend testing
python app.py

# Full app testing
npm run dev

# Build production
npm run build
```

### Release Workflow:

```bash
# 1. Update version in package.json
# 2. Commit and push
git add package.json
git commit -m "Bump version to 1.0.1"
git push

# 3. Create and push tag
git tag v1.0.1
git push origin v1.0.1

# 4. GitHub Actions builds automatically
# 5. Release created with installer
# 6. Users get auto-update notification!
```

---

## Need Help?

- Electron docs: https://www.electronjs.org/docs
- electron-builder: https://www.electron.build/
- electron-updater: https://www.electron.build/auto-update
- PyInstaller: https://pyinstaller.org/
- GitHub Actions: https://docs.github.com/en/actions

---

**Happy deploying!** 🚀
