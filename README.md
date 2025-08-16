# DaimiData - ph.d.-analyse for Datalogisk Institut

Automatiseret analyse og visualisering af ph.d.-afhandlinger fra Datalogisk Institut ved Aarhus Universitet.

## 🎯 Features

- **Automated Data Collection**: Daily scraping of PhD data from AU CS website
- **Interactive Web Report**: Vue.js + Bulma CSS dashboard with 4 main sections:
  - 📅 **First 10 PhDs** (1975-1987 timeline)
  - 👨‍🏫 **Top 10 Supervisors** (by number of students)
  - 🔗 **Longest Supervision Chains** (up to 5 generations!)
  - 🌳 **Most Descendants** (academic family trees)
- **Data Cleaning**: Automatic correction of date errors and name variations
- **GitHub Pages Deployment**: Live site updated automatically

## 🔍 Key Findings

- **373 PhD dissertations** from 1975-2025
- **Longest academic chain**: 5 generations spanning 48 years
  - Arto Salomaa → Sven Skyum (1975) → Peter Bro Miltersen (1993) → Kristoffer Arnsfelt Hansen (2006) → Kasper Høgh (2023)
- **Most productive supervisor**: Kaj Grønbæk with 26 PhD students
- **Largest academic family**: Morten Kyng with 55 descendants

## 🚀 How It Works

### 1. Data Fetching (`fetch_data.py`)
```bash
python fetch_data.py
```
- Scrapes PhD data from https://cs.au.dk/education/phd/phds-produced/
- Fixes common date errors (e.g., "19-05-215" → "19-05-2015")
- Normalizes name variations for consistency
- Saves cleaned data to `data/phd_data.json`

### 2. Report Generation (`generate_html.py`)
```bash
python generate_html.py
```
- Analyzes supervision relationships and academic lineages
- Finds longest chains using depth-first search
- Calculates descendant counts for academic family trees
- Generates interactive HTML report in `docs/index.html`

### 3. Automated Updates (GitHub Actions)
- **Daily Schedule**: Runs at 06:00 UTC every day
- **Manual Trigger**: Can be run on-demand
- **Auto-deploy**: Updates GitHub Pages when data changes

## 📊 Data Structure

```json
{
  "number": 1,
  "name": "Sven Skyum",
  "supervisors": "Arto Salomaa",
  "date_raw": "19-03-1975",
  "date": "1975-03-19",
  "year": 1975,
  "title": "Parallelisme i definitioner af sprog"
}
```

## 🛠️ Technology Stack

- **Backend**: Python 3.11 + Beautiful Soup
- **Frontend**: Vue.js 3 + Bulma CSS
- **Deployment**: GitHub Actions + GitHub Pages
- **Data**: JSON storage with automatic backups

## 📈 Live Report

Visit the live interactive report: [GitHub Pages URL]

## 🔧 Local Development

1. Clone the repository
2. Install dependencies: `pip install requests beautifulsoup4`
3. Run data fetch: `python fetch_data.py`
4. Generate report: `python generate_html.py`
5. Open `docs/index.html` in browser

## 📝 Data Sources

- **Primary**: https://cs.au.dk/education/phd/phds-produced/
- **Update Frequency**: Daily automated checks
- **Data Quality**: Automated error correction and validation

## 🤝 Contributing

This project automatically maintains itself through GitHub Actions. Data corrections and feature improvements are welcome via pull requests.

## 📄 License

Data is publicly available from Aarhus University. Code is provided under MIT license.

---

*Last updated: Generated automatically by GitHub Actions*