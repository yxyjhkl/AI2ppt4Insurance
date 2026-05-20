"""Test script: verify all 10 layout types render correctly in PPTX and SVG."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from slide_builder.generator import PPTXGenerator
from slide_builder.svg_filler import SVGFiller
from rule_engine.engine import OfflineRuleEngine
from utils.theme_utils import load_theme

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
os.makedirs(OUT_DIR, exist_ok=True)

TEMPLATE_ID = "professional-blue"
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "built-in", TEMPLATE_ID)
theme = load_theme(template_dir) if os.path.exists(template_dir) else \
    {"colors": {"primary": "#1e40af", "accent": "#f59e0b", "text": "#1f2937", "background": "#ffffff", "surface": "#f8fafc"}}

slides = [
    {
        "layout_type": "cover",
        "title": "2025 年度业务技术总结",
        "subtitle": "产品中心 · 2026年1月 · 机密",
        "body_items": [],
        "page_number": 1,
        "notes": "开场：感谢各位领导参加本次年度总结会",
    },
    {
        "layout_type": "content",
        "title": "执行摘要",
        "subtitle": "三大核心成果",
        "body_items": [
            {"type": "list_item", "text": "全年营收突破 12.8 亿，同比增长 34%", "level": 0},
            {"type": "list_item", "text": "用户数达到 580 万，DAU 突破 120 万", "level": 0},
            {"type": "list_item", "text": "发布 3 款新产品，NPS 评分提升至 72 分", "level": 0},
            {"type": "list_item", "text": "团队从 45 人扩展至 120 人，核心人才留存率 94%", "level": 0},
            {"type": "list_item", "text": "获评 Gartner Cool Vendor，行业影响力显著提升", "level": 0},
        ],
        "page_number": 2,
    },
    {
        "layout_type": "chapter",
        "title": "Part 1",
        "subtitle": "业务数据深度分析",
        "body_items": [],
        "page_number": 3,
    },
    {
        "layout_type": "content_table",
        "title": "各业务线核心指标对比",
        "subtitle": "Q4 vs Q3 环比数据",
        "tables": [
            {
                "markdown": (
                    "| 业务线 | Q3营收(万) | Q4营收(万) | 环比增长 | 状态 |\n"
                    "|---|---|---|---|---|\n"
                    "| SaaS平台 | 3,200 | 4,150 | +29.7% | ✅ 达标 |\n"
                    "| 企业定制 | 2,100 | 2,850 | +35.7% | ✅ 达标 |\n"
                    "| 数据服务 | 1,600 | 1,420 | -11.3% | 🟡 关注 |\n"
                    "| 技术咨询 | 800 | 650 | -18.8% | 🔴 未达标 |\n"
                    "| 培训认证 | 450 | 580 | +28.9% | ✅ 达标 |\n"
                )
            }
        ],
        "body_items": [],
        "page_number": 4,
    },
    {
        "layout_type": "content_two_col",
        "title": "SaaS平台 vs 企业定制 对比分析",
        "body_items": [
            {"type": "list_item", "text": "ARR 同比增长 52%，续费率 96%", "level": 0, "column": "left"},
            {"type": "list_item", "text": "客单价 ¥38,000/年，获客成本降低 18%", "level": 0, "column": "left"},
            {"type": "list_item", "text": "新增功能 47 个，用户满意度 4.8/5", "level": 0, "column": "left"},
            {"type": "list_item", "text": "项目交付周期缩短至 45 天（原 90 天）", "level": 0, "column": "right"},
            {"type": "list_item", "text": "客单价 ¥280,000/年，毛利率 62%", "level": 0, "column": "right"},
            {"type": "list_item", "text": "中标率提升至 38%（行业平均 22%）", "level": 0, "column": "right"},
        ],
        "page_number": 5,
    },
    {
        "layout_type": "content_table",
        "title": "季度KPI达成情况矩阵",
        "subtitle": "红黄绿灯评估体系",
        "tables": [
            {
                "markdown": (
                    "| KPI指标 | 目标值 | 实际值 | 达成率 | 评级 |\n"
                    "|---|---|---|---|---|\n"
                    "| 营收增长率 | 25% | 34% | 136% | 🟢 优秀 |\n"
                    "| 用户增长 | 400万 | 580万 | 145% | 🟢 优秀 |\n"
                    "| 客户满意度 | 4.5 | 4.6 | 102% | 🟢 达标 |\n"
                    "| 技术债务清理 | 60% | 45% | 75% | 🟡 预警 |\n"
                    "| 人才密度 | 80% | 72% | 90% | 🟡 预警 |\n"
                )
            }
        ],
        "body_items": [],
        "page_number": 6,
    },
    {
        "layout_type": "chapter",
        "title": "Part 2",
        "subtitle": "技术架构与代码成果",
        "body_items": [],
        "page_number": 7,
    },
    {
        "layout_type": "content_code",
        "title": "核心API网关配置示例",
        "code_block": (
            "apiVersion: gateway.example.com/v1\n"
            "kind: Gateway\n"
            "metadata:\n"
            "  name: production-gateway\n"
            "  namespace: prod-infra\n"
            "spec:\n"
            "  replicas: 6\n"
            "  resources:\n"
            "    cpu: 4000m\n"
            "    memory: 8Gi\n"
            "  rateLimit:\n"
            "    maxQPS: 50000\n"
            "    burst: 10000\n"
            "  observability:\n"
            "    tracing: enabled\n"
            "    metricsExport: prometheus\n"
            "    logLevel: info\n"
            "  security:\n"
            "    mtlsEnabled: true\n"
            "    jwtValidation: RS256\n"
            "    certificateIssuer: cert-manager-v2"
        ),
        "body_items": [],
        "page_number": 8,
    },
    {
        "layout_type": "content_quote",
        "title": "行业评价",
        "body_items": [
            {"type": "paragraph", "text": "该公司在过去12个月内完成了令人瞩目的技术转型，其API网关架构已成为行业最佳实践参考"},
            {"type": "paragraph", "text": "— Gartner Magic Quadrant Report, 2025"},
        ],
        "page_number": 9,
    },
    {
        "layout_type": "content_compare",
        "title": "技术债务清理：Before vs After",
        "body_items": [
            {"type": "list_item", "text": "🔴 单体应用 23万行代码，部署周期 2周", "level": 0, "column": "left"},
            {"type": "list_item", "text": "🔴 测试覆盖率 23%，线上事故月均 7次", "level": 0, "column": "left"},
            {"type": "list_item", "text": "🔴 接口平均响应时间 850ms，P99 达 3.2s", "level": 0, "column": "left"},
            {"type": "list_item", "text": "✅ 拆分为 47 个微服务，CI/CD 全自动化", "level": 0, "column": "right"},
            {"type": "list_item", "text": "✅ 测试覆盖率 82%，线上事故降至月均 1.3次", "level": 0, "column": "right"},
            {"type": "list_item", "text": "✅ 接口平均响应时间 120ms，P99 降至 380ms", "level": 0, "column": "right"},
        ],
        "page_number": 10,
    },
    {
        "layout_type": "content_three_col",
        "title": "2026 年三大战略方向",
        "body_items": [
            {"type": "list_item", "text": "【AI 赋能】\n· 发布 AI Copilot 功能\n· 智能数据分析引擎\n· 自动化测试覆盖率提升至 95%", "level": 0, "column": "left"},
            {"type": "list_item", "text": "【生态建设】\n· 开放平台 API 增至 200+\n· 合作伙伴达到 50 家\n· 开发者社区突破 10 万人", "level": 0, "column": "center"},
            {"type": "list_item", "text": "【国际化】\n· 拓展东南亚市场\n· 产品多语言支持\n· 海外营收占比提升至 20%", "level": 0, "column": "right"},
        ],
        "page_number": 11,
    },
    {
        "layout_type": "content",
        "title": "关键风险与应对措施",
        "body_items": [
            {"type": "list_item", "text": "🔴【高风险】技术人才竞争加剧 — 应对：启动股权激励计划，与3所高校建立联合实验室", "level": 0},
            {"type": "list_item", "text": "🟡【中风险】海外市场合规成本超预期 — 应对：聘请当地法务顾问，分阶段进入", "level": 0},
            {"type": "list_item", "text": "🟡【中风险】AI技术迭代速度不及预期 — 应对：与2家AI初创建立技术合作", "level": 0},
            {"type": "list_item", "text": "🟢【低风险】数据安全审计 — 应对：已通过 ISO 27001 认证，定期渗透测试", "level": 0},
        ],
        "page_number": 12,
    },
    {
        "layout_type": "ending",
        "title": "感谢聆听",
        "subtitle": "2026 年目标：营收突破 20 亿，用户突破 1000 万",
        "body_items": [
            {"type": "paragraph", "text": "联系人：产品中心负责人"},
            {"type": "paragraph", "text": "邮箱：product@example.com"},
            {"type": "paragraph", "text": "手机：138-0000-0000"},
        ],
        "page_number": 13,
    },
]

print("=" * 60)
print("🔨 生成 PPTX 文件...")
gen = PPTXGenerator(template_id=TEMPLATE_ID, theme=theme, canvas_format="16:9")
pptx_bytes = gen.generate_from_slide_data(slides)
pptx_path = os.path.join(OUT_DIR, "test_all_layouts.pptx")
with open(pptx_path, "wb") as f:
    f.write(pptx_bytes)
print(f"✅ PPTX 已保存: {pptx_path}")
print(f"   文件大小: {len(pptx_bytes) / 1024:.1f} KB")
print(f"   幻灯片数: {len(slides)}")

print()
print("=" * 60)
print("🔨 生成 SVG 预览...")

filler = SVGFiller(template_dir, theme)
engine = OfflineRuleEngine()

for i, slide in enumerate(slides):
    layout_type = slide["layout_type"]
    svg_filename = engine.LAYOUT_MAP.get(layout_type, "03_content.svg")
    svg_path = os.path.join(template_dir, svg_filename)

    if not os.path.exists(svg_path):
        print(f"  ⚠️  Slide {i+1} ({layout_type}): SVG 模板不存在 {svg_filename}，使用 fallback")
        filled = SVGFiller._fallback_svg(SVGFiller(template_dir, theme), slide)
    else:
        filled = filler.fill(svg_path, slide, i + 1)

    out_svg = os.path.join(OUT_DIR, f"slide_{i+1:02d}_{layout_type}.svg")
    with open(out_svg, "w", encoding="utf-8") as f:
        f.write(filled)
    print(f"  ✅ Slide {i+1:2d} ({layout_type:20s}) -> {out_svg}")

print()
print("=" * 60)
print("📊 测试汇总:")
layout_counts = {}
for s in slides:
    lt = s["layout_type"]
    layout_counts[lt] = layout_counts.get(lt, 0) + 1
for lt, cnt in layout_counts.items():
    print(f"  {lt:20s} × {cnt}")

print()
print(f"🎯 全部测试文件已输出到: {OUT_DIR}")
print(f"   - PPTX:  {pptx_path}")
for f in sorted(os.listdir(OUT_DIR)):
    if f.endswith(".svg"):
        print(f"   - SVG:   {os.path.join(OUT_DIR, f)}")