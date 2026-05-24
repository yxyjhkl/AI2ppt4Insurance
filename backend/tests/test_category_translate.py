"""测试分类转换"""
from api.routes.templates import _list_templates_sync

templates = _list_templates_sync()

category_counts = {}
for t in templates:
    cat = t.get('category', '其他')
    category_counts[cat] = category_counts.get(cat, 0) + 1

print("分类统计:")
for cat, count in category_counts.items():
    print(f"  {cat}: {count} 个模板")
