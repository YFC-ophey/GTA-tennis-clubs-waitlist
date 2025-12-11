# Setup Guide

## Prerequisites

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **Git** (for cloning repository)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist.git
cd GTA-tennis-clubs-waitlist
```

### 2. Create Virtual Environment (Recommended)

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Data File

Ensure `data/GTA_Tennis_clubs_data_.xlsx` exists with correct structure:

**Sheet 1: `data`**
- Columns: `Club Name`, `Website URL`
- Contains all 306 clubs

**Sheet 2: `run`**
- Columns: `Club Name`, `Location`, `Email`, `Club Type`, `Membership Status`, `Waitlist Length`, `Number of Courts`, `Court Surface`, `Operating Season`, `Website URL`, `Date Scraped`, `URL Status`
- Contains processed clubs with complete data

### 5. Run Application

```bash
python app.py
```

You should see:
```
============================================================
🎾 GTA TENNIS CLUBS DASHBOARD - CHAMPIONSHIP EDITION
============================================================

📊 Required Data Fields (9 total):
   1. Club Name
   2. Location
   3. Email
   4. Club Type
   5. Membership Status
   6. Current Waitlist Length
   7. Number of Courts
   8. Court Surface
   9. Operating Season

🌐 Access dashboard at: http://localhost:5001
============================================================
```

### 6. Access Dashboard

Open your browser to: **http://localhost:5001**

## Troubleshooting

### Port Already in Use

If port 5001 is taken:

**Option 1: Kill the process**
```bash
# macOS/Linux
lsof -ti:5001 | xargs kill -9

# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

**Option 2: Change port**
Edit `app.py` line:
```python
app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False)
```

### Module Not Found

```bash
pip install --upgrade -r requirements.txt
```

### Excel File Not Found

Update path in `app.py`:
```python
DATA_FILE = 'data/GTA_Tennis_clubs_data_.xlsx'
```

### Dashboard Not Loading

1. Check server is running in terminal
2. Clear browser cache
3. Try incognito/private mode
4. Check browser console for errors (F12)

## Configuration

### Changing Data File Location

Edit `app.py`:
```python
DATA_FILE = '/path/to/your/file.xlsx'
```

### Adjusting Batch Size

In dashboard, modify the batch size in the API call or edit the default in `app.py`:
```python
batch_size = data.get('batch_size', 20)  # Change 10 to 20
```

## Next Steps

1. Review the [API Documentation](API.md)
2. Read the [Scraping Guide](SCRAPING_GUIDE.md)
3. Start scraping clubs using the dashboard
