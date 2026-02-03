"""
دریافت schema کامل برای searchLicenses و filterLicenses
"""

import requests
import json
import sys
import io

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_full_schema(endpoint_url: str):
    """دریافت schema کامل با جزئیات arguments و return types"""
    
    full_introspection = """
    query FullIntrospection {
      __schema {
        queryType {
          name
          fields {
            name
            description
            args {
              name
              description
              type {
                name
                kind
                ofType {
                  name
                  kind
                  ofType {
                    name
                    kind
                  }
                }
              }
              defaultValue
            }
            type {
              name
              kind
              ofType {
                name
                kind
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
        }
        types {
          name
          kind
          description
          fields {
            name
            description
            type {
              name
              kind
              ofType {
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
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    payload = {'query': full_introspection}
    
    print("در حال دریافت schema کامل...")
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        if 'errors' in result:
            print(f"❌ خطا: {result['errors']}")
            return None
        
        # ذخیره schema کامل
        with open('graphql_full_schema.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("✅ Schema کامل در graphql_full_schema.json ذخیره شد")
        
        # نمایش جزئیات searchLicenses و filterLicenses
        if 'data' in result and '__schema' in result['data']:
            query_type = result['data']['__schema'].get('queryType', {})
            fields = query_type.get('fields', [])
            
            for field in fields:
                if field['name'] in ['searchLicenses', 'filterLicenses', 'countFilteredLicenses']:
                    print(f"\n{'='*60}")
                    print(f"📋 {field['name']}")
                    print('='*60)
                    print(f"Description: {field.get('description', 'N/A')}")
                    
                    # Arguments
                    args = field.get('args', [])
                    if args:
                        print(f"\nArguments:")
                        for arg in args:
                            arg_type = arg.get('type', {})
                            type_name = arg_type.get('name') or arg_type.get('ofType', {}).get('name', 'Unknown')
                            print(f"  - {arg['name']}: {type_name}")
                            if arg.get('description'):
                                print(f"    {arg['description']}")
                    
                    # Return type
                    return_type = field.get('type', {})
                    if return_type.get('ofType'):
                        return_type_name = return_type['ofType'].get('name', 'Unknown')
                        print(f"\nReturn Type: {return_type_name}")
                        
                        # اگر return type یک object است، فیلدهایش را نمایش بده
                        if return_type['ofType'].get('kind') == 'OBJECT':
                            # پیدا کردن type definition
                            all_types = result['data']['__schema'].get('types', [])
                            for t in all_types:
                                if t.get('name') == return_type_name:
                                    type_fields = t.get('fields', [])
                                    if type_fields:
                                        print(f"\nFields:")
                                        for tf in type_fields[:20]:  # نمایش 20 تای اول
                                            tf_type = tf.get('type', {})
                                            tf_type_name = tf_type.get('name') or tf_type.get('ofType', {}).get('name', 'Unknown')
                                            print(f"  - {tf['name']}: {tf_type_name}")
                                        if len(type_fields) > 20:
                                            print(f"  ... و {len(type_fields) - 20} مورد دیگر")
                                    break
        
        return result
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None


if __name__ == "__main__":
    endpoint = "https://qr.mojavez.ir/graphql"
    get_full_schema(endpoint)
