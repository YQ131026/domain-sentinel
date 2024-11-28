# Domain Expiration Monitor

A robust Python-based system for monitoring domain expiration dates and sending automated alerts.

## Features

- **Multi-Registrar Support**: Primary support for GoDaddy domains with WHOIS fallback
- **Special Domain Handling**: Custom support for special TLDs (e.g., .ai domains)
- **Flexible Configuration**: JSON-based configuration for easy maintenance
- **Email Alerts**: Automated notifications with configurable thresholds
- **Error Handling**: Robust error recovery and retry mechanisms
- **Color-Coded Status**: Visual indicators for domain status in both console and email outputs

## Requirements

- Python 3.12
- Required packages (see `requirements.txt`)
- SMTP server for email alerts
- GoDaddy API credentials (optional)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `config.json.example` to `config.json` and update with your settings

## Configuration

The `config.json` file contains all necessary settings:

```json
{
    "accounts": [
        {
            "name": "Example",
            "api_key": "your_godaddy_api_key",
            "api_secret": "your_godaddy_api_secret"
        }
    ],
    "godaddy": {
        "api_url": "https://api.godaddy.com/v1/domains",
        "page_size": 100
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
        }
    }
}
```

### Configuration Sections

- **accounts**: GoDaddy API credentials
- **godaddy**: GoDaddy API settings
- **domains**: List of domains to monitor
- **special_domains**: Custom handling for specific TLDs
- **email_alert**: Email notification settings
  - `alert_threshold`: Days before expiration to send alerts
  - `recipients`: List of email addresses to notify
  - `smtp`: Email server configuration

## Usage

Run the monitor:
```bash
python app.py
```

The script will:
1. Check all configured domains
2. Display status in the console
3. Send email alerts for domains nearing expiration

## Error Handling

The system includes:
- Multiple retry attempts for failed queries
- Timeout handling for WHOIS queries
- Special handling for different domain formats
- Fallback mechanisms for data extraction

## Security Notes

- Store sensitive information (API keys, passwords) securely
- Use environment variables when possible
- Enable TLS for SMTP connections
- Regularly update dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License