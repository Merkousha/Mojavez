"""
تست queryهای واقعی برای پیدا کردن ساختار دقیق
"""

import requests
import json
import sys
import io

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ENDPOINT = "https://qr.mojavez.ir/graphql"

def test_query(query_name: str, query: str, variables: dict = None):
    """تست یک query"""
    print(f"\n{'='*60}")
    print(f"تست: {query_name}")
    print('='*60)
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    payload = {
        'query': query,
        'variables': variables or {}
    }
    
    try:
        response = requests.post(ENDPOINT, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'errors' in result:
                print(f"❌ خطاها:")
                for error in result['errors']:
                    print(f"  - {error.get('message')}")
                    if 'locations' in error:
                        print(f"    Location: {error['locations']}")
            else:
                print(f"✅ موفق!")
                print(f"\nResponse structure:")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])  # نمایش 2000 کاراکتر اول
                return result
        else:
            print(f"❌ Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ خطا: {e}")
    
    return None


# تست 1: دریافت لیست استان‌ها
test_query(
    "Get Provinces",
    """
    query {
      provinceTownship {
        provinces {
          id
          name
        }
      }
    }
    """
)

# تست 2: دریافت شهرهای یک استان (مثال: تهران)
test_query(
    "Get Townships (Cities)",
    """
    query {
      provinceTownship {
        townships(provinceId: 1) {
          id
          name
        }
      }
    }
    """
)

# تست 3: جستجوی ساده مجوزها
test_query(
    "Search Licenses - Simple",
    """
    query SearchLicenses($input: SearchLicensesInput!) {
      searchLicenses(input: $input) {
        licenses {
          id
          licenseNumber
          issueDate
          expiryDate
        }
        totalCount
      }
    }
    """,
    {
        "input": {
            "page": 1,
            "pageSize": 10
        }
    }
)

# تست 4: فیلتر مجوزها با تاریخ
test_query(
    "Filter Licenses with Date",
    """
    query FilterLicenses($input: filterLicensesInput!) {
      filterLicenses(input: $input) {
        licenses {
          id
          licenseNumber
          issueDate
          expiryDate
        }
        totalCount
      }
    }
    """,
    {
        "input": {
            "page": 1,
            "pageSize": 10,
            "dateFrom": "2024-01-01",
            "dateTo": "2024-01-31"
        }
    }
)

# تست 5: تعداد مجوزهای فیلتر شده
test_query(
    "Count Filtered Licenses",
    """
    query CountFiltered($input: filterLicensesInput!) {
      countFilteredLicenses(input: $input) {
        count
      }
    }
    """,
    {
        "input": {
            "dateFrom": "2024-01-01",
            "dateTo": "2024-01-31"
        }
    }
)

print("\n" + "="*60)
print("تست‌ها تمام شد!")
print("="*60)
print("\nاگر queryها خطا داشتند، باید ساختار دقیق input را از Developer Tools")
print("مرورگر (Network tab) کپی کنید.")
