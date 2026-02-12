"""
تست سریع دریافت جزئیات مجوز از GraphQL
"""

import argparse
import json
import sys
import io

from crawler import MojavezCrawler

# تنظیم encoding برای Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test license detail via GraphQL")
    parser.add_argument("request_number", help="کد رهگیری (request_number)")
    parser.add_argument(
        "--endpoint",
        default=None,
        help="در صورت نیاز endpoint را override کنید",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="چاپ JSON با فرمت خوانا",
    )

    args = parser.parse_args()

    crawler = MojavezCrawler(endpoint=args.endpoint)
    result = crawler.fetch_detail_via_graphql(args.request_number)

    if not result:
        print("❌ نتیجه‌ای از GraphQL دریافت نشد")
        raise SystemExit(1)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
