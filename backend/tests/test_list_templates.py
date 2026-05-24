"""测试模板列表功能"""
from api.routes.templates import _list_templates_sync

templates = _list_templates_sync()
print(f"\n总模板数: {len(templates)}")

built_in = [t for t in templates if t.get('source') == 'built-in']
custom = [t for t in templates if t.get('source') == 'custom']

print(f"内置模板: {len(built_in)}")
print(f"自定义模板: {len(custom)}")

if custom:
    print("\n自定义模板列表:")
    for t in custom:
        print(f"  - {t['id']}")
