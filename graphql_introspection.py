"""
اجرای GraphQL Introspection و ذخیره schema
"""

import argparse
import json
import sys
import io
from typing import Dict, Any, Optional

import requests

# تنظیم encoding برای Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DEFAULT_ENDPOINT = "https://qr.mojavez.ir/graphql"
DEFAULT_OUTPUT = "graphql_introspection.json"

# Standard GraphQL Introspection Query (based on GraphQL spec)
INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description
      locations
      args {
        ...InputValue
      }
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
      }
    }
  }
}
"""


def run_introspection(
    endpoint: str,
    output_path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    اجرای introspection و ذخیره خروجی در فایل JSON
    """
    req_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    payload = {
        "query": INTROSPECTION_QUERY,
        "variables": {},
    }

    response = requests.post(endpoint, json=payload, headers=req_headers, timeout=timeout)
    response.raise_for_status()
    result = response.json()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def parse_headers(raw_headers: Optional[str]) -> Dict[str, str]:
    """
    پارس هدرها از فرم key:value,key:value
    """
    if not raw_headers:
        return {}

    headers: Dict[str, str] = {}
    parts = [part.strip() for part in raw_headers.split(",") if part.strip()]
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GraphQL introspection برای استخراج schema"
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="آدرس GraphQL endpoint",
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUTPUT,
        help="مسیر خروجی JSON",
    )
    parser.add_argument(
        "--headers",
        default="",
        help="هدرهای اضافی به صورت key:value,key:value",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="timeout بر حسب ثانیه",
    )

    args = parser.parse_args()
    extra_headers = parse_headers(args.headers)

    print(f"در حال اجرای introspection روی {args.endpoint}...")
    try:
        result = run_introspection(
            endpoint=args.endpoint,
            output_path=args.out,
            headers=extra_headers,
            timeout=args.timeout,
        )
    except requests.exceptions.RequestException as exc:
        print(f"❌ خطا در درخواست: {exc}")
        raise SystemExit(1) from exc

    if "errors" in result:
        print("⚠️ پاسخ دارای خطا بود. جزئیات در فایل خروجی ذخیره شد.")
    else:
        print("✅ introspection موفق بود.")

    print(f"💾 خروجی در {args.out} ذخیره شد")


if __name__ == "__main__":
    main()
