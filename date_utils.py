"""
ابزارهای تبدیل تاریخ
"""

from datetime import datetime
from typing import Optional


def convert_date_format(date_str: str, from_format: str = "YYYY-MM-DD", to_format: str = "YYYY/M/D") -> str:
    """
    تبدیل فرمت تاریخ
    
    Args:
        date_str: رشته تاریخ
        from_format: فرمت ورودی (YYYY-MM-DD یا YYYY/M/D)
        to_format: فرمت خروجی (YYYY-MM-DD یا YYYY/M/D)
    
    Returns:
        رشته تاریخ با فرمت جدید
    """
    if from_format == "YYYY-MM-DD" and to_format == "YYYY/M/D":
        # تبدیل از YYYY-MM-DD به YYYY/M/D
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y/%m/%d").replace("/0", "/").replace("/0", "/")
        except:
            return date_str
    elif from_format == "YYYY/M/D" and to_format == "YYYY-MM-DD":
        # تبدیل از YYYY/M/D به YYYY-MM-DD
        try:
            # ممکن است فرمت‌های مختلفی داشته باشد: YYYY/M/D یا YYYY/MM/DD
            parts = date_str.split("/")
            if len(parts) == 3:
                year = parts[0]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                return f"{year}-{month}-{day}"
        except:
            pass
        return date_str
    
    return date_str


def format_date_for_api(date: datetime) -> str:
    """
    تبدیل datetime به فرمت مورد نیاز API (YYYY/M/D)
    
    Args:
        date: datetime object
    
    Returns:
        رشته تاریخ به فرمت YYYY/M/D
    """
    return date.strftime("%Y/%m/%d").replace("/0", "/").replace("/0", "/")


def parse_api_date(date_str: str) -> Optional[datetime]:
    """
    تبدیل رشته تاریخ API به datetime
    
    Args:
        date_str: رشته تاریخ به فرمت YYYY/M/D
    
    Returns:
        datetime object یا None در صورت خطا
    """
    try:
        # فرمت‌های مختلف را امتحان می‌کنیم
        formats = ["%Y/%m/%d", "%Y/%m/%d", "%Y/%#m/%#d"]  # # برای Windows
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # اگر هیچکدام کار نکرد، دستی parse می‌کنیم
        parts = date_str.split("/")
        if len(parts) == 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return datetime(year, month, day)
    except:
        pass
    
    return None
