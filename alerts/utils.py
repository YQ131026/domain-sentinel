from datetime import datetime
from typing import Dict, Optional, Any

def format_date(date_obj: Optional[datetime]) -> str:
    """格式化日期显示"""
    if not date_obj:
        return 'N/A'
    return date_obj.strftime('%Y-%m-%d')

def get_expiry_style(days: int) -> str:
    """获取到期状态的样式"""
    if days <= 30:
        return 'days-critical'
    elif days <= 60:
        return 'days-warning'
    return 'days-normal'

def format_domain_info(domain_info: Dict[str, Any]) -> Dict[str, Any]:
    """格式化域名信息用于显示"""
    return {
        'domain': domain_info['domain'],
        'expiry_date': format_date(domain_info['expiry_date']),
        'days_until_expiry': domain_info['days_until_expiry'],
        'registrar': domain_info.get('registrar', 'Unknown'),
        'status_class': get_expiry_style(domain_info['days_until_expiry'])
    }