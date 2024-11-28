from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from typing import Dict, List, Any
from rich.console import Console

console = Console()

class EmailAlerter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('email_alert', {})
        self.recipients = self.config.get('recipients', [])
        self.smtp_config = self.config.get('smtp', {})
        self.whitelist = self.config.get('whitelist', [])
        self.alert_threshold = self.config.get('alert_threshold', 60)  # 默认60天
        
        # 加载邮件模板
        template_path = os.path.join(os.path.dirname(__file__), 'templates/email_template.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = Template(f.read())

    def should_alert(self, domain_info: Dict[str, Any]) -> bool:
        """判断是否需要发送报警"""
        if domain_info['domain'] in self.whitelist:
            return False
        return domain_info['days_until_expiry'] <= self.alert_threshold

    def send_alert(self, domains: List[Dict[str, Any]]) -> bool:
        """发送邮件报警"""
        if not domains or not self.recipients:
            return False

        # 对域名按照过期时间排序
        domains = sorted(domains, key=lambda x: x['days_until_expiry'])

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Domain Expiration Alert - {datetime.now().strftime("%Y-%m-%d")}'
            msg['From'] = self.smtp_config.get('username')
            msg['To'] = ', '.join(self.recipients)

            # 为每个域名添加状态标记
            for domain in domains:
                days = domain['days_until_expiry']
                if days <= 30:
                    domain['status'] = 'critical'
                elif days <= 60:
                    domain['status'] = 'warning'
                else:
                    domain['status'] = 'normal'

            html_content = self.template.render(domains=domains)
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            console.print("[green]Email alert sent successfully![/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to send email alert: {str(e)}[/red]")
            return False