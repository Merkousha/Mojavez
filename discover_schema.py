"""
اسکریپت برای شناسایی GraphQL endpoint و schema از سایت qr.mojavez.ir
این اسکریپت به شما کمک می‌کند تا queries واقعی سایت را پیدا کنید
"""

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time


def discover_graphql_endpoint():
    """
    شناسایی GraphQL endpoint با استفاده از Selenium
    """
    print("در حال باز کردن مرورگر...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # اجرا بدون نمایش مرورگر
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("در حال باز کردن سایت...")
        driver.get("https://qr.mojavez.ir/")
        
        # صبر برای لود شدن صفحه
        time.sleep(5)
        
        # بررسی Network requests
        print("\nدر حال بررسی Network requests...")
        print("لطفاً Developer Tools را باز کنید و به Network tab بروید")
        print("سپس یک جستجو انجام دهید و GraphQL requests را بررسی کنید")
        
        # می‌توانیم از Performance Logs استفاده کنیم
        driver.execute_script("console.log('Page loaded')")
        
        # صبر برای بررسی دستی
        input("پس از بررسی Network requests، Enter را بزنید...")
        
    finally:
        driver.quit()


def test_graphql_endpoint(endpoint_url: str, query: str, variables: dict = None):
    """
    تست یک GraphQL endpoint
    
    Args:
        endpoint_url: آدرس endpoint
        query: GraphQL query
        variables: متغیرهای query
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    payload = {
        'query': query,
        'variables': variables or {}
    }
    
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"\n✅ درخواست موفق!")
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\n❌ خطا در درخواست: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


def introspect_schema(endpoint_url: str):
    """
    دریافت GraphQL schema با استفاده از introspection query
    
    Args:
        endpoint_url: آدرس GraphQL endpoint
    """
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        queryType {
          name
          fields {
            name
            description
            args {
              name
              type {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
            }
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
        types {
          name
          kind
          description
          fields {
            name
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
      }
    }
    """
    
    print(f"\nدر حال دریافت schema از {endpoint_url}...")
    result = test_graphql_endpoint(endpoint_url, introspection_query)
    
    if result:
        # ذخیره schema
        with open('graphql_schema.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n✅ Schema در فایل graphql_schema.json ذخیره شد")
    
    return result


def main():
    """تابع اصلی"""
    print("=" * 60)
    print("شناسایی GraphQL Schema برای qr.mojavez.ir")
    print("=" * 60)
    
    # لیست endpointهای احتمالی
    possible_endpoints = [
        "https://qr.mojavez.ir/graphql",
        "https://qr.mojavez.ir/api/graphql",
        "https://qr.mojavez.ir/v1/graphql",
        "https://api.qr.mojavez.ir/graphql",
    ]
    
    print("\n1. تست endpointهای احتمالی...")
    for endpoint in possible_endpoints:
        print(f"\nتست {endpoint}...")
        test_query = "{ __typename }"  # ساده‌ترین query
        result = test_graphql_endpoint(endpoint, test_query)
        if result and 'errors' not in result:
            print(f"✅ Endpoint معتبر پیدا شد: {endpoint}")
            
            # تلاش برای دریافت schema
            print("\n2. دریافت schema...")
            introspect_schema(endpoint)
            break
    else:
        print("\n⚠️ هیچ endpoint معتبری پیدا نشد.")
        print("\nراهنمایی:")
        print("1. سایت را در مرورگر باز کنید")
        print("2. Developer Tools (F12) را باز کنید")
        print("3. به Network tab بروید")
        print("4. یک جستجو انجام دهید")
        print("5. GraphQL request را پیدا کنید و endpoint را کپی کنید")
        print("6. سپس endpoint را در crawler.py تنظیم کنید")
        
        # اجرای Selenium برای کمک به کاربر
        print("\n3. باز کردن مرورگر برای بررسی دستی...")
        discover_graphql_endpoint()


if __name__ == "__main__":
    main()
