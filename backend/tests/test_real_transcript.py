"""真实会议转写文本 → 4层质量保障体系 端到端测试 (文件输出版)"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DOCX_PATH = r"E:\平安\会议纪要\转写\刚总会议总结20260505.docx"
OUTPUT_LOG = os.path.join(os.path.dirname(__file__), "test_output", "real_transcript_report.txt")

lines = []

def log(msg: str = ""):
    lines.append(msg)
    print(msg, flush=True)


def load_transcript() -> str:
    import docx
    doc = docx.Document(DOCX_PATH)
    return "\n".join([p.text for p in doc.paragraphs])


MOCK_LLM_RESPONSE = json.dumps({
    "title": "5月业务推进会 — 刚总总结",
    "subtitle": "2025年5月6日",
    "sections": [
        {
            "topic": "心梗筛查邀约流程优化",
            "key_points": [
                "心梗筛查作为获客手段可行，但不能混入促成环节",
                "国安办了两场，人多但转化效果未达预期",
                "建议将心梗筛查定位为获客养客，促成环节单独设计"
            ],
            "data_points": [
                {"label": "国安已办场次", "value": "2场"},
                {"label": "邀约模式评估", "value": "需优化"}
            ],
            "decisions": [
                "不要以心梗筛查名义直接邀约促成客户",
                "优化流程：更多时间放在促成环节而非筛查环节"
            ],
            "action_items": [
                {"owner": "汇总/组训", "task": "研究促成端优化方案", "deadline": "本周"},
                {"owner": "各网点经理", "task": "评估心梗筛查邀约方式", "deadline": "持续"}
            ],
            "suggested_layout": "content_compare"
        },
        {
            "topic": "果爸课件及网点活动要求",
            "key_points": [
                "果爸课件已重新发到网点经理群",
                "郊县网点必须多办活动，不办活动压力会非常大",
                "建议每周安排1-2场促成场 + 2场客户活动场"
            ],
            "data_points": [
                {"label": "周促成场建议", "value": "1-2场"},
                {"label": "周活动场建议", "value": "2场"}
            ],
            "decisions": [
                "郊县网点一周至少4场活动"
            ],
            "action_items": [
                {"owner": "网点经理", "task": "查看果爸课件内容", "deadline": "本周"},
                {"owner": "郊县网点", "task": "增加活动频次", "deadline": "持续"}
            ],
            "suggested_layout": "content"
        },
        {
            "topic": "增员主体推进与1025人力目标",
            "key_points": [
                "增员主体必须本周参加增员活动或办创会",
                "8号后召开述职检测会，时间紧迫",
                "1025目标：1个主管上岗+2个钻石人力"
            ],
            "data_points": [
                {"label": "连城现有人力", "value": "6人"},
                {"label": "1025目标", "value": "1+2"},
                {"label": "时间节点", "value": "5月8日"}
            ],
            "decisions": [
                "各网点提前推增员，不等下周",
                "1025达成率严肃问责，百分百必须达成"
            ],
            "action_items": [
                {"owner": "各网点经理", "task": "本周内安排增员活动/创会", "deadline": "5月8日前"},
                {"owner": "桂总", "task": "确保增员主体参与活动", "deadline": "本周"}
            ],
            "suggested_layout": "content_kpi"
        },
        {
            "topic": "惠银保产品推动与网点业绩",
            "key_points": [
                "武平上月惠银保卖得好，但年进度低于中支均值3个点",
                "长汀、永定等网点需借助惠银保+加一提费赶进度",
                "武平问责预计全省中等偏下，必须借势拉高"
            ],
            "data_points": [
                {"label": "武平年进度差距", "value": "低于均值3个百分点"},
                {"label": "武平问责预估", "value": "全省中等偏下"},
                {"label": "惠银保推动力", "value": "加一提费政策"}
            ],
            "decisions": [
                "有惠银保基础的网点要借势多推",
                "半年问责只看结果，5-6月是关键窗口"
            ],
            "action_items": [
                {"owner": "武平/长汀/永定网点", "task": "加大惠银保推动力度", "deadline": "5-6月"},
                {"owner": "各网点", "task": "借助加一提费政策冲刺年进度", "deadline": "6月底"}
            ],
            "suggested_layout": "content_compare"
        },
        {
            "topic": "半年问责风险预警",
            "key_points": [
                "问责压力排序：长汀(最大) > 必新 > 连城 > 克林",
                "二部4个网点达成率低于中支/分公司均值",
                "浮动绩效直接挂钩问责结果，无法调整"
            ],
            "data_points": [
                {"label": "问责风险第一", "value": "长汀"},
                {"label": "问责风险第二", "value": "必新"},
                {"label": "问责风险第三", "value": "连城"},
                {"label": "问责风险第四", "value": "克林"},
                {"label": "二部低于均值网点", "value": "4个"}
            ],
            "decisions": [
                "半年问责只看达成率，不可调整",
                "抓住5-6月惠银保窗口赶进度"
            ],
            "action_items": [
                {"owner": "长汀网点", "task": "重点研究追赶方案", "deadline": "5月底"},
                {"owner": "各网点", "task": "明确问责压力，全力赶进度", "deadline": "6月底"}
            ],
            "suggested_layout": "content_table"
        },
        {
            "topic": "网点人员配置与激励机制",
            "key_points": [
                "中支超编人员将下派到网点担任内勤",
                "1025达标的网点优先配备额外内勤",
                "武平产能已接近上杭/二部水平，可考虑增配"
            ],
            "data_points": [
                {"label": "中支超编状态", "value": "超编"},
                {"label": "服务最久网点", "value": "克林/必新/涛亮(9年)"},
                {"label": "计划下派人数", "value": "2-3人"}
            ],
            "decisions": [
                "干的好的网点优先配额外内勤",
                "干不好的网点调配人员，不会给好岗位",
                "综合管理室、培训部人员培养后支持网点"
            ],
            "action_items": [
                {"owner": "刚总/沈总", "task": "排定网点巡视行事历", "deadline": "近期"},
                {"owner": "各网点", "task": "力争1025达标争取增配", "deadline": "持续"}
            ],
            "suggested_layout": "content_compare"
        },
        {
            "topic": "目标客户与签单策略",
            "key_points": [
                "聚焦稳利宝+惠银保+加一提费产品体系",
                "以1025为导向，20%做钻石人力",
                "VIP客户积分兑换是公司重点目标客户方向"
            ],
            "data_points": [
                {"label": "核心产品", "value": "稳利宝+惠银保"},
                {"label": "目标客户方向", "value": "VIP积分兑换"},
                {"label": "人员覆盖", "value": "百分百已面谈"}
            ],
            "decisions": [
                "圈定主力人群，借助8分钟面谈强化意愿",
                "名单清晰签单才容易，模糊则困难",
                "建新办客领会模式值得推广"
            ],
            "action_items": [
                {"owner": "各网点", "task": "梳理目标客户名单", "deadline": "本周"},
                {"owner": "各网点", "task": "聚焦VIP积分兑换客户群", "deadline": "持续"}
            ],
            "suggested_layout": "content"
        }
    ],
    "summary": "聚焦1025人力目标+惠银保产品推动，抓住5-6月窗口赶半年进度，问责结果直接挂钩浮动绩效",
    "next_steps": [
        "各网点梳理增员名单并安排增员活动",
        "加大惠银保+加一提费推动力度",
        "优化心梗筛查邀约流程",
        "郊县网点增加活动频次（每周≥4场）",
        "中支启动人员下派网点计划"
    ]
}, ensure_ascii=False)


def main():
    log("=" * 70)
    log("  真实会议转写文本 — 4层质量保障体系测试")
    log("=" * 70)
    log(f"  输入: {DOCX_PATH}")
    log()

    text = load_transcript()
    log(f"  文本: {len(text):,}字符, 口语化转写, 无分段结构")
    log(f"  预览: {text[:120]}...")
    log()

    # ── Layer 1 ──
    log("-" * 70)
    log("  Layer 1: 正则预提取（清洗 + 分块 + 事实挖掘）")
    log("-" * 70)

    from transcript.processor import TranscriptProcessor
    processor = TranscriptProcessor()
    processed = processor.process(text)

    log(f"  原始长度: {processed.original_length:,} 字符")
    log(f"  清洗后: {len(processed.cleaned_text):,} 字符")
    log(f"  分块: {len(processed.chunks)} 块")
    log(f"  预估时长: ~{processed.estimated_duration_min} min")
    log(f"  会议类型: {processed.meeting_type_hint}")
    log(f"  发言人: {processed.speakers}")

    fact_types = {}
    for f in processed.all_facts:
        fact_types[f.fact_type] = fact_types.get(f.fact_type, 0) + 1
    type_labels = {
        "number": "数字", "metric": "指标", "date": "时间",
        "action_item": "行动项", "decision": "决策",
    }
    log(f"  预提取事实: {len(processed.all_facts)} 条")
    for ft, c in sorted(fact_types.items(), key=lambda x: -x[1]):
        log(f"    {type_labels.get(ft, ft):8s} {c:4d} 条")

    log(f"\n  文本前3个chunk:")
    for ch in processed.chunks[:3]:
        p = ch.text[:80].replace("\n", " ")
        log(f"    #{ch.index + 1}: [{len(ch.text)}字] {p}...")

    log()

    # ── Layer 2 ──
    log("-" * 70)
    log("  Layer 2: LLM结构化抽取")
    log("-" * 70)

    structured = json.loads(MOCK_LLM_RESPONSE)
    sections = structured["sections"]
    log(f"  标题: {structured['title']}")
    log(f"  议题: {len(sections)} 个")

    td = sum(len(s.get("data_points", [])) for s in sections)
    tdc = sum(len(s.get("decisions", [])) for s in sections)
    ta = sum(len(s.get("action_items", [])) for s in sections)
    tk = sum(len(s.get("key_points", [])) for s in sections)

    for i, s in enumerate(sections):
        log(f"  {i + 1}. {s['topic']:28s} "
            f"| 要点{len(s.get('key_points',[]))} "
            f"数据{len(s.get('data_points',[]))} "
            f"决策{len(s.get('decisions',[]))} "
            f"行动{len(s.get('action_items',[]))}")

    log(f"  总计: {tk}观点, {td}数据点, {tdc}决策, {ta}行动项")
    log()

    # ── Layer 3 ──
    log("-" * 70)
    log("  Layer 3: 交叉验证（LLM vs 正则预提取）")
    log("-" * 70)

    v = processor.verify_llm_output(MOCK_LLM_RESPONSE, processed.all_facts)
    log(f"  预提取事实: {v['total_regex_facts']} 条")
    log(f"  已排除孤立数字: {v.get('facts_excluded', 0)} 条")
    log(f"  有效验证范围: {v['total_regex_facts'] - v.get('facts_excluded', 0)} 条")
    log(f"  LLM匹配到: {v['facts_found']} 条")
    log(f"  遗漏: {v['facts_missing']} 条")
    log(f"  覆盖率: {v['coverage_ratio']:.1%}")
    if 'weighted_coverage' in v:
        log(f"  加权覆盖率(指标×3/数字×0.5): {v['weighted_coverage']:.1%}")
    log(f"  得分: {v['score']}/100")

    if v['coverage_ratio'] >= 0.75:
        log(f"  评级: 优秀 (覆盖率 >= 75%)")
    elif v['coverage_ratio'] >= 0.50:
        log(f"  评级: 及格 (覆盖率 >= 50%)")
    else:
        log(f"  评级: 不合格 (覆盖率 < 50%)")

    if v['hallucination_risks']:
        log(f"  幻觉风险: {len(v['hallucination_risks'])} 条")
        for r in v['hallucination_risks'][:6]:
            log(f"    - {r}")
    log()

    # ── Layer 4 ──
    log("-" * 70)
    log("  Layer 4: SlideData 转换 + Deck QA")
    log("-" * 70)

    from slide_builder.pipeline import GenerationPipeline
    pipeline = GenerationPipeline(scene="insurance", template_id="professional-blue", ai_mode="offline")
    slides = pipeline._transcript_sections_to_slides(structured, sections)

    lt_count = {}
    for s in slides:
        lt_count[s.layout_type] = lt_count.get(s.layout_type, 0) + 1
    log(f"  {len(sections)}议题 -> {len(slides)}页幻灯片")
    for lt, c in lt_count.items():
        log(f"    {lt}: {c}页")
    log()

    from slide_builder.deck_qa import DeckQA
    qa = DeckQA()
    gr = qa.check_all(slides)
    tr = qa.check_transcript_deck(slides, len(sections), tdc, ta, td)

    all_qa = gr + [{"severity": r.get("severity","info"), "category": r.get("category",""),
                     "slide": r.get("slide",0), "message": r.get("message","")} for r in tr]

    errs = [r for r in all_qa if r["severity"] == "error"]
    warns = [r for r in all_qa if r["severity"] == "warning"]
    infos = [r for r in all_qa if r["severity"] == "info"]

    log(f"  QA结果: {len(all_qa)}条 ({len(errs)}错误, {len(warns)}警告, {len(infos)}信息)")
    for e in errs:
        log(f"    [ERROR] {e['message']}")
    for w in warns[:5]:
        log(f"    [WARN] {w['message']}")
    for i in infos[:5]:
        log(f"    [INFO] {i['message']}")
    log()

    # ── Layer 5 ──
    log("-" * 70)
    log("  Layer 5: PPTX 生成")
    log("-" * 70)

    from slide_builder.generator import PPTXGenerator
    from dataclasses import asdict
    gen = PPTXGenerator("professional-blue", pipeline.theme, "16:9")
    pptx = gen.generate_from_slide_data([asdict(s) for s in slides])

    import uuid
    out = os.path.join(os.path.dirname(__file__), "test_output",
                       f"刚总会议总结_PPT_{uuid.uuid4().hex[:6]}.pptx")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(pptx)

    log(f"  输出: {out}")
    log(f"  大小: {len(pptx):,} 字节 ({len(pptx)/1024:.1f} KB)")
    log(f"  页数: {len(slides)}")
    log()

    # ── 综合评估 ──
    log("=" * 70)
    log("  综合质量评估报告")
    log("=" * 70)

    score = 100
    items = []

    cov = v['coverage_ratio']
    wcov = v.get('weighted_coverage', cov)

    if cov >= 0.70:
        items.append(f"  + 事实覆盖率 {cov:.0%} — 优秀")
    elif cov >= 0.50:
        score -= 10
        items.append(f"  ~ 事实覆盖率 {cov:.0%} — 及格")
    else:
        score -= 20
        items.append(f"  ~ 事实覆盖率 {cov:.0%} — 偏低（语义提取差异）")

    if len(sections) >= 5:
        items.append(f"  + 议题数量 {len(sections)} — 充分")
    elif len(sections) >= 3:
        score -= 5
        items.append(f"  ~ 议题数量 {len(sections)} — 基本够用")

    if len(lt_count) >= 5:
        items.append(f"  + 布局类型 {len(lt_count)}种 — 丰富")
    elif len(lt_count) >= 3:
        items.append(f"  ~ 布局类型 {len(lt_count)}种 — 良好")

    if len(errs) == 0:
        items.append(f"  + 零质检错误")
    else:
        score -= len(errs) * 15
        items.append(f"  - {len(errs)}个质检错误")

    if 5 <= len(slides) <= 15:
        items.append(f"  + 页数 {len(slides)} — 适中")
    elif len(slides) > 20:
        score -= 5
        items.append(f"  ~ 页数 {len(slides)} — 偏多")

    score = max(0, min(100, score))

    for item in items:
        log(item)
    log(f"\n  综合得分: {score}/100")
    log(f"  输出PPTX: {out}")

    log()
    log("=" * 70)
    log("  测试完成")
    log("=" * 70)

    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"\n  报告已保存: {OUTPUT_LOG}")


if __name__ == "__main__":
    main()