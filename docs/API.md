# API Documentation

Base URL: `http://localhost:5001`

## Endpoints

### GET `/`
**Description**: Renders the main dashboard

**Response**: HTML page

---

### GET `/api/stats`
**Description**: Get database statistics and completeness metrics

**Response**:
```json
{
  "total": 306,
  "processed": 80,
  "remaining": 226,
  "completion_rate": 26.1,
  "completeness": {
    "Location": {
      "complete": 54,
      "total": 80,
      "percentage": 67.5
    },
    "Email": {
      "complete": 27,
      "total": 80,
      "percentage": 33.8
    },
    "Club Type": {
      "complete": 36,
      "total": 80,
      "percentage": 45.0
    },
    "Membership Status": {
      "complete": 27,
      "total": 80,
      "percentage": 33.8
    },
    "Waitlist Length": {
      "complete": 0,
      "total": 80,
      "percentage": 0.0
    },
    "Number of Courts": {
      "complete": 44,
      "total": 80,
      "percentage": 55.0
    },
    "Court Surface": {
      "complete": 23,
      "total": 80,
      "percentage": 28.7
    },
    "Operating Season": {
      "complete": 0,
      "total": 80,
      "percentage": 0.0
    }
  }
}
```

---

### GET `/api/processed`
**Description**: Get list of all processed clubs with complete data

**Response**:
```json
[
  {
    "Club Name": "10XTO",
    "Location": "Toronto, ON",
    "Email": "info@10xto.com",
    "Club Type": "Private",
    "Membership Status": "Waitlist",
    "Waitlist Length": "Not Found",
    "Number of Courts": 8,
    "Court Surface": "Hard",
    "Operating Season": "Year-round",
    "Website URL": "https://www.10xto.com/tennis",
    "Date Scraped": "2024-11-15",
    "URL Status": "Success"
  },
  ...
]
```

---

### GET `/api/remaining`
**Description**: Get list of clubs not yet processed

**Response**:
```json
[
  {
    "Club Name": "Beaches Tennis Club",
    "Website URL": "http://www.beachestennis.ca/"
  },
  ...
]
```

---

### POST `/api/scrape/start`
**Description**: Get next batch of clubs to scrape

**Request Body**:
```json
{
  "batch_size": 10
}
```

**Response**:
```json
{
  "status": "ready",
  "batch_size": 10,
  "total_remaining": 226,
  "clubs": [
    {
      "Club Name": "Beaches Tennis Club",
      "Website URL": "http://www.beachestennis.ca/"
    },
    ...
  ]
}
```

---

### GET `/api/export`
**Description**: Export processed data as CSV

**Response**: CSV file download
- Filename: `gta_tennis_clubs.csv`
- Content-Type: `text/csv`

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message description"
}
```

**HTTP Status Codes**:
- `200`: Success
- `500`: Server error

---

## Usage Examples

### JavaScript (Fetch API)

**Get Statistics**:
```javascript
fetch('http://localhost:5001/api/stats')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Start Scraping Batch**:
```javascript
fetch('http://localhost:5001/api/scrape/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ batch_size: 10 })
})
  .then(response => response.json())
  .then(data => console.log(data.clubs));
```

### Python (requests)

```python
import requests

# Get stats
response = requests.get('http://localhost:5001/api/stats')
stats = response.json()

# Start scraping
response = requests.post(
    'http://localhost:5001/api/scrape/start',
    json={'batch_size': 10}
)
clubs = response.json()['clubs']
```

### cURL

```bash
# Get stats
curl http://localhost:5001/api/stats

# Get next batch
curl -X POST http://localhost:5001/api/scrape/start \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10}'

# Export CSV
curl http://localhost:5001/api/export -o tennis_clubs.csv
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider adding rate limiting to prevent abuse.

## Authentication

Currently no authentication is required. For production deployment with sensitive data, implement authentication (JWT, OAuth, etc.).
