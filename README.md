# Domain Expiration Monitor

A robust Python-based system for monitoring domain expiration dates and sending automated alerts.

## Features

- **Multi-Registrar Support**: Primary support for GoDaddy domains with WHOIS fallback
- **Special Domain Handling**: Custom support for special TLDs (e.g., .ai domains)
- **Flexible Configuration**: JSON-based configuration for easy maintenance
- **Email Alerts**: Automated notifications with configurable thresholds
- **Error Handling**: Robust error recovery with 5 retries and configurable delays
- **Color-Coded Status**: Visual indicators for domain status in both console and email outputs
- **Rate Limiting**: Automatic handling of GoDaddy API rate limits (60 requests/minute)
- **Progress Tracking**: Real-time progress updates with estimated completion time

## Project Structure

```
domain-sentinel/
├── app.py                 # Main application file
├── config.json.example    # Example configuration file
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
├── alerts/              # Alert system module
│   ├── __init__.py      # Module initialization
│   ├── email_alerter.py # Email notification system
│   ├── utils.py         # Utility functions
│   └── templates/       # Email templates
└── config/              # Configuration directory (created on setup)
    └── config.json      # Your configuration file
```

## Requirements

- Python 3.12
- Required packages (see `requirements.txt`):
  - requests==2.31.0: HTTP client for API calls
  - rich==13.7.0: Terminal formatting and progress bars
  - python-whois==0.8.0: WHOIS lookups for non-GoDaddy domains
  - python-dotenv==1.0.0: Environment variable management
  - python-dateutil==2.8.2: Date parsing utilities
  - jinja2==3.1.2: Template engine for email alerts
- SMTP server for email alerts
- GoDaddy API credentials (optional)

## Installation

### Using Docker (Recommended)

Our Docker setup includes:
- Base: miniconda3 for reliable Python environment
- Security: Non-root user (appuser) for container execution
- Health Checks: 30-second intervals with 3 retries
- Volume Management: Separate config and logs volumes
- Resource Monitoring: Process health verification

1. Build the image:
   ```bash
   docker build -t domain-sentinel .
   ```

2. Prepare configuration:
   ```bash
   mkdir -p ./config
   cp config.json.example ./config/config.json
   # Edit ./config/config.json with your settings
   ```

3. Run the container:
   ```bash
   # Basic usage
   docker run -v $(pwd)/config:/app/config domain-sentinel

   # Production setup with logging
   docker run -d \
     -v $(pwd)/config:/app/config \
     -v $(pwd)/logs:/app/logs \
     --restart unless-stopped \
     --log-driver json-file \
     --log-opt max-size=10m \
     --log-opt max-file=3 \
     --name domain-sentinel \
     domain-sentinel
   ```

### Using pip
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Using conda
1. Create and activate conda environment:
   ```bash
   conda create -n domain-sentinel python=3.12 -y
   conda activate domain-sentinel
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `config.json.example` to `config.json` and update with your settings

## GoDaddy API Limitations

The system automatically handles the following GoDaddy API limitations:

1. **Rate Limits**:
   - Maximum 60 requests per minute
   - Automatic waiting and continuation when limit is reached
   - Progress tracking with estimated completion time

2. **Account Requirements**:
   - Availability API: Limited to accounts with 50 or more domains
   - Management and DNS APIs: Limited to accounts with 10 or more domains and/or an active Discount Domain Club – Premier Membership plan

For more information about the GoDaddy API, visit: https://developer.godaddy.com/getstarted

## Configuration

The `config.json` file supports:

```json
{
    "accounts": [
        {
            "name": "Example",
            "api_key": "your_godaddy_api_key",
            "api_secret": "your_godaddy_api_secret",
            "api_url": "https://api.godaddy.com/v1/domains"  # Optional override
        }
    ],
    "godaddy": {
        "api_url": "https://api.godaddy.com/v1/domains",
        "page_size": 100,
        "rate_limit": {
            "requests_per_minute": 60,
            "domain_limits": {
                "availability": 50,
                "management": 10,
                "dns": 10
            }
        }
    },
    "domains": [
        "example.com"
    ],
    "special_domains": {
        "ai": {
            "example.ai": {
                "expiry_date": "2024-12-31",
                "registrar": "Example Registrar"
            }
        }
    },
    "email_alert": {
        "alert_threshold": 60,
        "recipients": ["admin@example.com"],
        "smtp": {
            "host": "smtp.example.com",
            "port": 587,
            "username": "user",
            "password": "pass",
            "use_tls": true
        },
        "whitelist": []  # Optional domain whitelist
    }
}
```

### Configuration Details

- **accounts**: Multiple GoDaddy account support
  - `name`: Account identifier
  - `api_key`, `api_secret`: GoDaddy API credentials
  - `api_url`: Optional per-account API URL override

- **godaddy**: Global GoDaddy settings
  - `api_url`: Default API endpoint
  - `page_size`: Domains per page (default: 100)
  - `rate_limit`: API request limiting
    - `requests_per_minute`: Maximum API calls
    - `domain_limits`: Minimum domain requirements

- **domains**: Additional domains to monitor (non-GoDaddy)

- **special_domains**: Custom TLD handling
  - Currently supports .ai domains
  - Manual expiry date management

- **email_alert**: Notification settings
  - `alert_threshold`: Days before expiry
  - `recipients`: Alert recipients
  - `smtp`: Email server configuration
  - `whitelist`: Optional domain filtering

## Error Handling

The system includes:
- **Retry Logic**: 5 attempts for failed queries with 2-second delays
- **Rate Limiting**: Automatic request throttling
- **Timeout Handling**: 10-second timeout for WHOIS queries
- **Special TLD Support**: Custom handling for .ai domains
- **Fallback Mechanisms**: WHOIS fallback for non-GoDaddy domains

## Security Best Practices

- Container runs as non-root user
- Sensitive data stored in mounted config volume
- TLS support for SMTP connections
- Environment variable support for credentials
- Regular dependency updates recommended
- Log rotation and size limits
- Health monitoring with automatic recovery

## Monitoring and Maintenance

### Health Checks
- 30-second intervals
- 10-second timeout
- 5-second startup grace period
- 3 retries before failure

### Log Management
- JSON format logging
- 10MB per file limit
- 3 file rotation
- Automatic cleanup

## Usage

Run the monitor:
```bash
python app.py
```

The script will:
1. Check all configured domains
2. Display status in the console
3. Send email alerts for domains nearing expiration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License