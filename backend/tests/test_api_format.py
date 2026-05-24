"""测试API返回数据格式"""
from api.routes.templates import _list_templates_sync
import json

templates = _list_templates_sync()

print(f"总模板数: {len(templates)}")
print("\n--- 第一个模板数据 ---")
if templates:
    print(json.dumps(templates[0], ensure_ascii=False, indent=2))
