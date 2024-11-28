import os
import json
import requests
from typing import List, Dict, Any
import whois
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn
import time
import socket
from dateutil.parser import parse
from alerts import EmailAlerter

# Load environment variables
load_dotenv()

# Initialize rich console
console = Console()

class GoDaddyAccount:
    """GoDaddy account configuration"""
    def __init__(self, api_key: str, api_secret: str, name: str = "Default"):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.name = name
        self.api_url = 'https://api.godaddy.com/v1/domains'
        self.page_size = 100  # Number of domains per page

class DomainMonitor:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.accounts = []
        self.domains = []
        self.godaddy_config = {}
        self._load_config()
        
    def _load_config(self):
        """Load account and domain configuration from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                
                # Load GoDaddy configuration
                self.godaddy_config = self.config.get('godaddy', {})
                
                # Load accounts
                for account_config in self.config.get('accounts', []):
                    api_key = account_config.get('api_key')
                    api_secret = account_config.get('api_secret')
                    name = account_config.get('name', 'Default')
                    
                    if api_key and api_secret:
                        account = GoDaddyAccount(api_key, api_secret, name)
                        # Override default GoDaddy settings if configured
                        if self.godaddy_config:
                            account.api_url = self.godaddy_config.get('api_url', account.api_url)
                            account.page_size = self.godaddy_config.get('page_size', account.page_size)
                        self.accounts.append(account)
                
                # Load domain list
                self.domains = self.config.get('domains', [])
            
            # If no config file or config is empty, try to load from environment variables
            if not self.accounts:
                api_key = os.getenv('GODADDY_API_KEY')
                api_secret = os.getenv('GODADDY_API_SECRET')
                name = os.getenv('GODADDY_ACCOUNT_NAME', 'Default')
                
                if api_key and api_secret:
                    self.accounts.append(GoDaddyAccount(api_key, api_secret, name))
        
        except Exception as e:
            console.print(f"[red]Error loading config: {str(e)}[/red]")
            # Try to load from environment variables
            api_key = os.getenv('GODADDY_API_KEY')
            api_secret = os.getenv('GODADDY_API_SECRET')
            name = os.getenv('GODADDY_ACCOUNT_NAME', 'Default')
            
            if api_key and api_secret:
                self.accounts.append(GoDaddyAccount(api_key, api_secret, name))
        
        if not self.accounts:
            raise ValueError("No GoDaddy accounts configured. Please check your config.json or .env file.")

    def _get_all_domains(self, account: GoDaddyAccount) -> List[Dict]:
        """Get all domains under the account"""
        domains = []
        headers = {
            'Authorization': f'sso-key {account.api_key}:{account.api_secret}',
            'Accept': 'application/json'
        }
        
        params = {
            'limit': account.page_size,
            'statuses': 'ACTIVE,AWAITING_DOCUMENT_UPLOAD'
        }
        
        try:
            url = account.api_url
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code in [200, 203]:
                data = response.json()
                if isinstance(data, list):
                    with Progress() as progress:
                        task = progress.add_task(f"[cyan]Getting domains from {account.name} account...[/cyan]", total=len(data))
                        for domain_data in data:
                            domain_info = self.check_specific_domain(domain_data['domain'], account)
                            if domain_info:
                                domains.append(domain_info)
                            progress.advance(task)
                    return domains
            elif response.status_code == 403:
                console.print(f"[red]Access denied for account {account.name}[/red]")
            else:
                console.print(f"[red]Error fetching domains from {account.name}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
        
        return []

    def check_specific_domain(self, domain: str, account: GoDaddyAccount) -> Dict:
        """Check specific domain information"""
        headers = {
            'Authorization': f'sso-key {account.api_key}:{account.api_secret}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"{account.api_url}/{domain}"
            response = requests.get(url, headers=headers)
            
            if response.status_code in [200, 203]:
                data = response.json()
                expiry_date = datetime.strptime(data['expires'], '%Y-%m-%dT%H:%M:%S.%fZ')
                days_until_expiry = (expiry_date - datetime.now()).days
                
                status = data.get('status', 'UNKNOWN')
                if status == 'AWAITING_DOCUMENT_UPLOAD':
                    status_display = '📄 Document Upload Pending'
                elif status == 'ACTIVE':
                    status_display = '✅ Active'
                else:
                    status_display = f'❓ {status}'
                
                if days_until_expiry <= 30:
                    status_display = '⚠️ ' + status_display
                elif days_until_expiry <= 90:
                    status_display = '⚡ ' + status_display
                
                return {
                    'domain': domain,
                    'account_name': account.name,
                    'expiry_date': expiry_date,
                    'days_until_expiry': days_until_expiry,
                    'registrar': 'GoDaddy',
                    'status': status,
                    'status_display': status_display,
                    'created_at': datetime.strptime(data['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                    'nameServers': data.get('nameServers', []),
                    'privacy': data.get('privacy', False)
                }
            elif response.status_code == 404:
                return None
            elif response.status_code == 403:
                return None
            else:
                console.print(f"[red]Error checking {domain}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error checking {domain}: {str(e)}[/red]")
            return None
    
    def check_domain_without_auth(self, domain: str) -> Dict:
        """Check domain information without authentication"""
        # Check if it's a special .ai domain first
        if domain.endswith('.ai'):
            ai_domains = self.config.get('special_domains', {}).get('ai', {})
            if domain in ai_domains:
                domain_info = ai_domains[domain]
                try:
                    expiry_date = datetime.strptime(domain_info['expiry_date'], '%Y-%m-%d')
                    return {
                        'domain': domain,
                        'account_name': 'Manual',
                        'expiry_date': expiry_date,
                        'days_until_expiry': (expiry_date - datetime.now()).days,
                        'registrar': domain_info.get('registrar', 'Anguilla NIC'),
                        'status': 'ACTIVE',
                        'status_display': '✅ Active',
                        'created_at': None,  # We don't track creation date for .ai domains
                        'nameServers': [],  # We don't track nameservers for .ai domains
                        'privacy': None
                    }
                except Exception as e:
                    console.print(f"[red]Error processing .ai domain {domain}: {str(e)}[/red]")
                    return None

        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Use socket with a timeout for the initial connection
                socket.setdefaulttimeout(10)
                w = whois.whois(domain)
                
                # Reset timeout to default
                socket.setdefaulttimeout(None)
                
                # Handle case where whois query returns None or empty
                if not w or (not hasattr(w, 'domain_name') and not hasattr(w, 'expiration_date')):
                    if attempt < max_retries - 1:
                        console.print(f"[yellow]No data returned for {domain}, retrying...[/yellow]")
                        time.sleep(retry_delay)
                        continue
                    else:
                        console.print(f"[red]No WHOIS data available for {domain}[/red]")
                        return None

                # Handle domain name verification
                domain_name = None
                if hasattr(w, 'domain_name'):
                    if isinstance(w.domain_name, list):
                        domain_name = next((d.lower() for d in w.domain_name if d), None)
                    else:
                        domain_name = w.domain_name.lower() if w.domain_name else None
                
                # Special handling for .au domains
                if domain.endswith('.au') and not domain_name:
                    domain_name = domain.lower()
                
                # Verify domain name if available
                if domain_name and domain.lower() not in domain_name:
                    if attempt < max_retries - 1:
                        console.print(f"[yellow]Domain name mismatch for {domain}, retrying...[/yellow]")
                        time.sleep(retry_delay)
                        continue
                
                # Handle expiration date with multiple fallbacks
                expiry_date = None
                if hasattr(w, 'expiration_date'):
                    try:
                        if isinstance(w.expiration_date, list):
                            valid_dates = [d for d in w.expiration_date if d is not None]
                            if valid_dates:
                                expiry_date = sorted(valid_dates)[0]
                        elif isinstance(w.expiration_date, (str, datetime)):
                            expiry_date = parse(str(w.expiration_date)) if isinstance(w.expiration_date, str) else w.expiration_date
                    except Exception as e:
                        console.print(f"[yellow]Error parsing expiration date for {domain}: {str(e)}[/yellow]")
                
                # If no expiration date found, try alternative fields
                if not expiry_date and hasattr(w, 'registry_expiry_date'):
                    try:
                        expiry_date = parse(str(w.registry_expiry_date))
                    except:
                        pass
                
                if not expiry_date:
                    console.print(f"[red]Could not determine expiration date for {domain}[/red]")
                    return None
                
                # Handle registrar with fallbacks
                registrar = None
                if hasattr(w, 'registrar'):
                    if isinstance(w.registrar, list):
                        registrar = next((r for r in w.registrar if r), None)
                    else:
                        registrar = w.registrar
                
                if not registrar and hasattr(w, 'registrant'):
                    registrar = w.registrant
                
                registrar = registrar if registrar else 'Unknown'
                
                # Process creation date
                creation_date = None
                if hasattr(w, 'creation_date'):
                    try:
                        if isinstance(w.creation_date, list):
                            valid_dates = [d for d in w.creation_date if d is not None]
                            if valid_dates:
                                creation_date = sorted(valid_dates)[0]
                        elif isinstance(w.creation_date, (str, datetime)):
                            creation_date = parse(str(w.creation_date)) if isinstance(w.creation_date, str) else w.creation_date
                    except:
                        pass
                
                # Get nameservers with better error handling
                nameservers = []
                if hasattr(w, 'name_servers') and w.name_servers:
                    if isinstance(w.name_servers, list):
                        nameservers = [ns.lower() for ns in w.name_servers if ns and isinstance(ns, str)]
                    elif isinstance(w.name_servers, str):
                        nameservers = [w.name_servers.lower()]
                
                return {
                    'domain': domain,
                    'account_name': 'Manual',
                    'expiry_date': expiry_date,
                    'days_until_expiry': (expiry_date - datetime.now()).days if expiry_date else None,
                    'registrar': registrar,
                    'status': 'ACTIVE',
                    'status_display': '✅ Active',
                    'created_at': creation_date,
                    'nameServers': nameservers,
                    'privacy': None
                }
                    
            except (socket.timeout, socket.error) as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]Connection timeout for {domain}, retrying in {retry_delay} seconds... ({str(e)})[/yellow]")
                    time.sleep(retry_delay)
                    continue
                else:
                    console.print(f"[red]Failed to check {domain} after {max_retries} attempts: {str(e)}[/red]")
                    return None
            except whois.parser.PywhoisError as e:
                if "No match for domain" in str(e):
                    console.print(f"[red]Domain {domain} does not exist[/red]")
                else:
                    console.print(f"[red]WHOIS query failed for {domain}: {str(e)}[/red]")
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"[yellow]Error checking {domain}, retrying: {str(e)}[/yellow]")
                    time.sleep(retry_delay)
                    continue
                else:
                    console.print(f"[red]Error checking domain {domain}: {str(e)}[/red]")
                    return None
        
        return None

    def check_domains(self) -> List[Dict]:
        """Check all domains"""
        results = []
        
        # 1. Get all domains under the default account (SK)
        default_account = next((acc for acc in self.accounts if acc.name == "SK"), None)
        if default_account:
            console.print("[cyan]Retrieving domains from SK account...[/cyan]")
            results.extend(self._get_all_domains(default_account))
        
        # 2. Check configured domains
        configured_domains = set(self.domains)
        existing_domains = {d['domain'] for d in results}
        domains_to_check = configured_domains - existing_domains
        
        if domains_to_check:
            with Progress() as progress:
                task = progress.add_task("[cyan]Checking other domains...", total=len(domains_to_check))
                for domain in domains_to_check:
                    domain_info = self.check_domain_without_auth(domain)
                    
                    if domain_info:
                        results.append(domain_info)
                    
                    progress.advance(task)
        
        # Send email alert
        alerter = EmailAlerter(self.config)
        expiring_domains = [d for d in results if alerter.should_alert(d)]
        if expiring_domains:
            console.print(f"\nFound {len(expiring_domains)} domains that need attention, sending email alert...")
            alerter.send_alert(expiring_domains)
        
        return results

def display_results(results: List[Dict[str, Any]]):
    """Display domain check results"""
    if not results:
        console.print("[red]No domain information found or errors occurred during check.[/red]")
        return

    # Create table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
        title="Domain Expiration Information",
        caption="Last Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Add columns
    table.add_column("Status", justify="center", style="cyan", no_wrap=True)
    table.add_column("Account", justify="left", style="cyan")
    table.add_column("Domain", justify="left", style="white")
    table.add_column("Creation Date", justify="center", style="cyan")
    table.add_column("Expiry Date", justify="center", style="cyan")
    table.add_column("Days Left", justify="right")
    table.add_column("Nameservers", style="dim", max_width=30)
    table.add_column("Privacy", justify="center")

    # Sort results by days until expiry
    results.sort(key=lambda x: x['days_until_expiry'])

    # Display sorted domain information
    for result in results:
        days = result['days_until_expiry']
        color, icon = get_expiry_style(days)
        
        # Handle domain name servers display
        nameservers = result.get('nameServers', [])
        if len(nameservers) > 2:
            ns_display = f"{nameservers[0]}\n{nameservers[1]}\n..."
        else:
            ns_display = "\n".join(nameservers) if nameservers else "N/A"
        
        # Format date display
        expiry_date = format_date(result['expiry_date'])
        created_date = format_date(result['created_at']) if result['created_at'] else 'N/A'
        
        # Add row
        table.add_row(
            result['status_display'],
            result['account_name'],
            result['domain'],
            created_date,
            expiry_date,
            f"[{color}]{days} days[/{color}]",
            ns_display,
            "🔒" if result.get('privacy', False) else "🔓"
        )

    # Print table
    console.print()
    console.print(table)
    console.print()

    # Print statistics
    expiring_soon = len([r for r in results if r['days_until_expiry'] <= 30])
    expiring_soon_90 = len([r for r in results if 30 < r['days_until_expiry'] <= 90])
    
    stats = Table.grid(padding=1)
    stats.add_column(style="cyan")
    stats.add_row(f"[green]✓[/green] Successfully processed: [cyan]{len(results)}[/cyan] domains")
    if expiring_soon > 0:
        stats.add_row(f"[red]⚠️[/red] [red]{expiring_soon}[/red] domains will expire within 30 days")
    if expiring_soon_90 > 0:
        stats.add_row(f"[yellow]⚡[/yellow] [yellow]{expiring_soon_90}[/yellow] domains will expire within 90 days")
    
    console.print(stats)
    console.print()

    # Print legend
    legend = Table.grid(padding=1)
    legend.add_column(style="cyan")
    legend.add_row("[red]⚠️ Expiring within 30 days[/red]")
    legend.add_row("[yellow]⚡ Expiring within 90 days[/yellow]")
    legend.add_row("[green]✅ Expiring after 90 days[/green]")
    legend.add_row("🔒 Privacy protection enabled")
    legend.add_row("🔓 Privacy protection disabled")
    
    console.print(Panel(legend, title="Legend", border_style="cyan"))

def format_date(date):
    """Format date display"""
    return date.strftime('%Y-%m-%d %H:%M:%S')

def get_expiry_style(days):
    """Get style based on days until expiry"""
    if days <= 30:
        return "red", "⚠️"
    elif days <= 90:
        return "yellow", "⚡"
    else:
        return "green", "✅"

def main():
    """Main function"""
    # Load configuration
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Initialize domain monitor
    monitor = DomainMonitor()
    
    # Check all domains
    results = monitor.check_domains()
    
    display_results(results)

if __name__ == "__main__":
    main()