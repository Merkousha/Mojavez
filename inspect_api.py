"""
اسکریپت ساده برای بررسی GraphQL API
این اسکریپت بدون نیاز به Selenium کار می‌کند
"""

import requests
import json


def inspect_endpoint(endpoint_url: str):
    """
    بررسی یک GraphQL endpoint
    
    Args:
        endpoint_url: آدرس endpoint
    """
    print(f"\n{'='*60}")
    print(f"بررسی: {endpoint_url}")
    print('='*60)
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # تست 1: ساده‌ترین query
    print("\n1. تست query ساده...")
    simple_query = "{ __typename }"
    payload = {'query': simple_query}
    
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ پاسخ دریافت شد!")
            print(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"   ❌ خطا: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ خطا در اتصال: {e}")
        return False


def test_introspection(endpoint_url: str):
    """
    تست introspection query
    
    Args:
        endpoint_url: آدرس endpoint
    """
    print("\n2. تست Introspection Query...")
    
    introspection_query = """
    {
      __schema {
        queryType {
          name
          fields {
            name
            description
          }
        }
      }
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    payload = {'query': introspection_query}
    
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'errors' in result:
                print(f"   ⚠️ خطا در introspection: {result['errors']}")
            else:
                print(f"   ✅ Introspection موفق!")
                
                # ذخیره schema
                with open('schema_partial.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"   💾 Schema در schema_partial.json ذخیره شد")
                
                # نمایش query types
                if 'data' in result and '__schema' in result['data']:
                    query_type = result['data']['__schema'].get('queryType', {})
                    fields = query_type.get('fields', [])
                    if fields:
                        print(f"\n   Query Types موجود:")
                        for field in fields[:10]:  # نمایش 10 تای اول
                            print(f"     - {field.get('name')}")
                        if len(fields) > 10:
                            print(f"     ... و {len(fields) - 10} مورد دیگر")
                
                return True
        else:
            print(f"   ❌ Status Code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        return False


def main():
    """تابع اصلی"""
    print("\n" + "="*60)
    print("بررسی GraphQL API برای qr.mojavez.ir")
    print("="*60)
    
    # لیست endpointهای احتمالی
    endpoints = [
        "https://qr.mojavez.ir/graphql",
        "https://qr.mojavez.ir/api/graphql",
        "https://qr.mojavez.ir/v1/graphql",
        "https://api.qr.mojavez.ir/graphql",
        "https://qr.mojavez.ir/graphql/v1",
    ]
    
    valid_endpoint = None
    
    for endpoint in endpoints:
        if inspect_endpoint(endpoint):
            valid_endpoint = endpoint
            print(f"\n✅ Endpoint معتبر پیدا شد: {endpoint}")
            
            # تست introspection
            test_introspection(endpoint)
            break
    
    if not valid_endpoint:
        print("\n" + "="*60)
        print("⚠️ هیچ endpoint معتبری پیدا نشد!")
        print("="*60)
        print("\nراهنمایی:")
        print("1. سایت https://qr.mojavez.ir را در مرورگر باز کنید")
        print("2. F12 را بزنید و Developer Tools را باز کنید")
        print("3. به Network tab بروید")
        print("4. یک جستجو انجام دهید")
        print("5. درخواست‌های GraphQL را پیدا کنید")
        print("6. URL endpoint را کپی کنید")
        print("7. endpoint را در crawler.py تنظیم کنید")
        print("\nیا endpoint را به صورت دستی وارد کنید:")
        custom_endpoint = input("Endpoint URL: ").strip()
        if custom_endpoint:
            inspect_endpoint(custom_endpoint)
            test_introspection(custom_endpoint)


if __name__ == "__main__":
    main()
