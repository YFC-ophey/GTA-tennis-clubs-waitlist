# GitHub Upload Instructions

Follow these steps to upload all files to your repository.

## Option 1: Using Git Command Line (Recommended)

### Step 1: Navigate to the folder
```bash
cd ~/Downloads/outputs/GTA-tennis-clubs-waitlist
```

### Step 2: Initialize Git (if not already done)
```bash
git init
git remote add origin https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist.git
```

### Step 3: Add all files
```bash
git add .
```

### Step 4: Commit changes
```bash
git commit -m "Complete dashboard rebuild with Wimbledon theme

- Added Flask web application with 9-field data collection
- Implemented Wimbledon-inspired UI (purple/green theme)
- Created comprehensive documentation (README, API, Setup, Scraping Guide)
- Added data export functionality
- Included batch scraping workflow
- Added proper .gitignore and requirements.txt"
```

### Step 5: Push to GitHub
```bash
git push -u origin main
```

If you get an error about branches, try:
```bash
git branch -M main
git push -u origin main
```

### Step 6: Verify on GitHub
Go to: https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist

---

## Option 2: Using GitHub Desktop

1. **Open GitHub Desktop**
2. **Add Repository**: File → Add Local Repository
3. **Browse** to: `~/Downloads/outputs/GTA-tennis-clubs-waitlist`
4. **Review Changes** in the left sidebar
5. **Commit**: Add commit message in bottom left
6. **Push**: Click "Push origin" button

---

## Option 3: Using GitHub Web Interface

### Step 1: Create ZIP file
```bash
cd ~/Downloads/outputs
zip -r GTA-tennis-clubs-waitlist.zip GTA-tennis-clubs-waitlist/
```

### Step 2: Go to your repository
https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist

### Step 3: Upload files
- Click "Add file" → "Upload files"
- Drag the unzipped folder contents
- Write commit message
- Click "Commit changes"

---

## What's Being Uploaded

```
GTA-tennis-clubs-waitlist/
├── README.md                       ✅ Comprehensive project overview
├── requirements.txt                ✅ Python dependencies
├── .gitignore                      ✅ Git ignore rules
├── app.py                          ✅ Flask application
├── templates/
│   └── dashboard.html              ✅ Wimbledon-themed dashboard
├── data/
│   └── GTA_Tennis_clubs_data_.xlsx ✅ Database (306 clubs)
└── docs/
    ├── SETUP.md                    ✅ Installation guide
    ├── API.md                      ✅ API documentation
    └── SCRAPING_GUIDE.md           ✅ Methodology guide
```

---

## Troubleshooting

### Authentication Issues

If you get prompted for username/password:

**Use Personal Access Token instead:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use token as password when prompted

### Large File Warning

If Excel file is too large:

**Option A: Use Git LFS**
```bash
git lfs install
git lfs track "*.xlsx"
git add .gitattributes
```

**Option B: Exclude from Git**
Add to `.gitignore`:
```
data/*.xlsx
```

Then users can download separately.

### Merge Conflicts

If remote has changes:
```bash
git pull origin main
# Resolve any conflicts
git add .
git commit -m "Resolved merge conflicts"
git push origin main
```

---

## After Upload

### Create GitHub Pages (Optional)

Host dashboard documentation:

1. Go to repository Settings
2. Pages → Source: Deploy from branch
3. Select `main` branch, `/docs` folder
4. Save

Your docs will be at:
`https://yfc-ophey.github.io/GTA-tennis-clubs-waitlist/`

### Add Topics

On repository main page:
- Click gear icon next to "About"
- Add topics: `tennis`, `web-scraping`, `flask`, `database`, `gta`, `sports`

### Enable Issues

Settings → Features → Check "Issues"

This lets people report bugs or suggest features.

---

## Verification Checklist

After upload, verify on GitHub:

- [ ] README displays properly with formatting
- [ ] All 4 docs files are in /docs folder
- [ ] app.py and requirements.txt are in root
- [ ] templates/dashboard.html exists
- [ ] data/GTA_Tennis_clubs_data_.xlsx is present
- [ ] .gitignore is working (no __pycache__, .DS_Store)
- [ ] Repository description is set
- [ ] Topics are added

---

## Next Steps

After successful upload:

1. **Star your own repo** (top right corner)
2. **Edit repository description**: "Comprehensive database of 306 GTA tennis clubs with automated scraping and Wimbledon-themed dashboard"
3. **Add a screenshot** to README (take screenshot of dashboard)
4. **Share the repo** with potential contributors or users

---

Need help? Contact GitHub support or ask Claude!
