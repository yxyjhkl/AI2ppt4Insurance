import requests

try:
    response = requests.get('http://localhost:8000/api/v1/templates')
    if response.ok:
        data = response.json()
        print('返回的模板数据:')
        for tpl in data[:10]:  # 显示前10个
            cat = tpl.get('category')
            print(f"  id: {tpl.get('id')}, category: {repr(cat)}, 小写: {repr(cat.lower() if cat else None)}")
        print(f'总模板数: {len(data)}')
    else:
        print(f'请求失败: {response.status_code}')
except Exception as e:
    print(f'请求异常: {e}')
