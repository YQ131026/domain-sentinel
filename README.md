# Domain Expiration Monitor

A robust Python-based system for monitoring domain expiration dates and sending automated alerts.

## Features

- **Multi-Registrar Support**: Primary support for GoDaddy domains with WHOIS fallback
- **Special Domain Handling**: Custom support for special TLDs (e.g., .ai domains)
- **Flexible Configuration**: JSON-based configuration for easy maintenance
- **Email Alerts**: Automated notifications with configurable thresholds
- **Error Handling**: Robust error recovery and retry mechanisms
- **Color-Coded Status**: Visual indicators for domain status in both console and email outputs
- **Rate Limiting**: Automatic handling of GoDaddy API rate limits
- **Progress Tracking**: Real-time progress updates with estimated completion time

## Requirements

- Python 3.12
- Required packages (see `requirements.txt`)
- SMTP server for email alerts
- GoDaddy API credentials (optional)

## Installation

### Using Docker
1. Build the Docker image:
   ```bash
   docker build -t domain-sentinel .
   ```

2. Prepare your configuration:
   - Copy `config.json.example` to a new directory (e.g., `./config`):
     ```bash
     mkdir -p ./config
     cp config.json.example ./config/config.json
     ```
   - Edit `./config/config.json` with your settings:
     - GoDaddy API credentials
     - API settings and limits
     - Domain list
     - Email alert settings
     - Other configurations

3. Run the container:
   ```bash
   # Basic usage
   docker run -v $(pwd)/config:/app/config domain-sentinel

   # With logs and automatic restart
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

4. Container Management:
   ```bash
   # View logs
   docker logs domain-sentinel
   docker logs -f domain-sentinel  # Follow log output

   # Stop container
   docker stop domain-sentinel

   # Start container
   docker start domain-sentinel

   # Remove container
   docker rm domain-sentinel

   # View container status
   docker ps -a | grep domain-sentinel
   ```

5. Volumes:
   - `/app/config`: Configuration files (required)
   - `/app/logs`: Application logs (optional)

6. Notes:
   - All settings are managed through `config.json`
   - The container runs with non-root user for security
   - Logs are rotated automatically when using json-file driver
   - Container will restart automatically with `--restart unless-stopped`

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