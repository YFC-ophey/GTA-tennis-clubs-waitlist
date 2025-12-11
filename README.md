# 🎾 GTA Tennis Clubs Waitlist Database

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive database and web dashboard for tracking **306 Greater Toronto Area tennis clubs** with automated data collection and elegant Wimbledon-inspired UI.

![Dashboard Preview](docs/dashboard-preview.png)

## 📋 Project Overview

This project centralizes tennis club information across the GTA, tracking 9 key data fields:

1. **Club Name**
2. **Location**
3. **Email**
4. **Club Type** (Private/Community/Public)
5. **Membership Status** (Open/Waitlist/Full)
6. **Current Waitlist Length**
7. **Number of Courts**
8. **Court Surface** (Hard/Clay/Grass/Indoor)
9. **Operating Season** (Year-round/Seasonal)

### Problem Statement

Tennis club information is scattered across hundreds of individual websites with inconsistent formats. This makes it difficult to:
- Find clubs with open memberships
- Compare waitlist lengths
- Identify clubs by specific criteria (court type, location, season)

### Solution

A centralized database with:
- **Automated web scraping** for baseline data
- **AI-powered extraction** using Claude for complex parsing
- **Email monitoring system** for membership status updates
- **Professional web dashboard** for data visualization and export

## 🎨 Features

### Dashboard (Wimbledon Theme)
- **Live Statistics**: Real-time progress tracking (306 total, 80 processed, 226 remaining)
- **Four Main Views**:
  - Overview with quick actions
  - Processed clubs table with search
  - Remaining clubs list
  - Data quality report with completion metrics
- **Batch Scraping**: Click-to-copy URLs for AI-assisted extraction
- **CSV Export**: One-click data download
- **Responsive Design**: Works on desktop and mobile

### Data Collection Methods
1. **Tennis Ontario Directory**: Official structured data (primary source)
2. **Individual Club Websites**: AI-powered extraction via Claude
3. **Email Campaigns**: Manual outreach for sensitive data (waitlist, membership)

### Technologies
- **Backend**: Flask (Python)
- **Data Processing**: Pandas, OpenPyXL
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **AI Assistant**: Anthropic Claude (via API for scraping)
- **Data Storage**: Excel (.xlsx) with dual-sheet structure

## 🚀 Quick Start

### Prerequisites
```bash
python 3.8+
pip (Python package manager)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist.git
cd GTA-tennis-clubs-waitlist
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Verify data file**
Ensure `data/GTA_Tennis_clubs_data_.xlsx` exists with two sheets:
- `data`: All 306 clubs (Club Name, Website URL)
- `run`: Processed clubs with complete data

4. **Run the application**
```bash
python app.py
```

5. **Access dashboard**
Open your browser to: **http://localhost:5001**

## 📊 Data Structure

### Excel File Structure
**Sheet: `data`**
| Club Name | Website URL |
|-----------|-------------|
| 10XTO | https://www.10xto.com/tennis |
| A Love of Tennis | http://www.aloveoftennis.org/ |
| ... | ... |

**Sheet: `run`**
| Club Name | Location | Email | Club Type | Membership Status | Waitlist Length | Number of Courts | Court Surface | Operating Season | Website URL | Date Scraped | URL Status |
|-----------|----------|-------|-----------|-------------------|-----------------|------------------|---------------|------------------|-------------|--------------|------------|

### Success Metrics (Current)
- **Total Clubs**: 306
- **Processed**: 80 (26.1%)
- **Data Completeness**:
  - Location: 67.5%
  - Email: 33.8%
  - Club Type: 45.0%
  - Court Surface: 28.7%
  - Membership Status: 33.8%

## 🔧 Usage

### Scraping Workflow

1. **Click "Get Next 10 Clubs"** in the dashboard
2. **Copy a club URL** using the copy button
3. **Ask Claude** to scrape it:
   ```
   Please scrape this club: http://www.clubname.ca/
   ```
4. Claude extracts all 9 fields automatically
5. Data is added to your spreadsheet
6. Refresh dashboard to see updates

### Manual Data Entry

For clubs requiring phone calls or email outreach:
1. Contact the club directly
2. Collect the 9 required fields
3. Manually update the Excel file
4. Refresh dashboard

### Export Data

Click **"Export CSV"** in the dashboard to download current data in CSV format.

## 📁 Project Structure

```
GTA-tennis-clubs-waitlist/
├── app.py                          # Flask application
├── templates/
│   └── dashboard.html              # Wimbledon-themed dashboard
├── data/
│   └── GTA_Tennis_clubs_data_.xlsx # Main database
├── docs/
│   ├── SETUP.md                    # Detailed setup instructions
│   ├── API.md                      # API documentation
│   └── SCRAPING_GUIDE.md          # Web scraping methodology
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore file
└── README.md                       # This file
```

## 🎯 Roadmap

### Phase 1: Foundation (✅ Complete)
- [x] Database schema design
- [x] Excel file structure
- [x] Basic web dashboard
- [x] Manual scraping workflow

### Phase 2: Automation (In Progress)
- [x] Wimbledon-themed UI redesign
- [x] Batch scraping system
- [ ] Claude API integration for automated scraping
- [ ] Gmail monitoring for email responses
- [ ] Automated Tennis Ontario directory scraping

### Phase 3: Enhancement (Planned)
- [ ] Database migration to PostgreSQL
- [ ] User authentication system
- [ ] Public search interface
- [ ] Email campaign management
- [ ] Automated reminder system for stale data
- [ ] Mobile app (React Native)

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tennis Ontario** for official club directory
- **Anthropic Claude** for AI-powered data extraction
- **Wimbledon** for design inspiration
- All GTA tennis clubs for their public information

## 📧 Contact

**Ophelia Chen**
- GitHub: [@YFC-ophey](https://github.com/YFC-ophey)
- Project Link: [https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist](https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist)

---

⭐ **Star this repo** if you find it useful!
