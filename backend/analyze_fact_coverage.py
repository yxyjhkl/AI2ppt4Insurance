"""分析事实覆盖率问题：哪些事实被匹配？哪些没被匹配？为什么？"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DOCX_PATH = sys.argv[1] if len(sys.argv) > 1 else None

MOCK_LLM_RESPONSE = json.dumps({
    "title": "5月业务推进会 — 刚总总结",
    "subtitle": "2025年5月6日",
    "sections": [
        {"topic": "心梗筛查邀约流程优化",
         "key_points": ["心梗筛查作为获客手段可行，但不能混入促成环节",
                        "国安办了两场，人多但转化效果未达预期",
                        "建议将心梗筛查定位为获客养客，促成环节单独设计"],
         "data_points": [{"label": "国安已办场次", "value": "2场"},
                         {"label": "邀约模式评估", "value": "需优化"}],
         "decisions": ["不要以心梗筛查名义直接邀约促成客户",
                      "优化流程：更多时间放在促成环节而非筛查环节"],
         "action_items": [{"owner": "汇总/组训", "task": "研究促成端优化方案", "deadline": "本周"},
                         {"owner": "各网点经理", "task": "评估心梗筛查邀约方式", "deadline": "持续"}]},
        {"topic": "增员主体推进与1025人力目标",
         "key_points": ["增员主体必须本周参加增员活动或办创会",
                        "8号后召开述职检测会，时间紧迫",
                        "1025目标：1个主管上岗+2个钻石人力"],
         "data_points": [{"label": "连城现有人力", "value": "6人"},
                         {"label": "1025目标", "value": "1+2"},
                         {"label": "时间节点", "value": "5月8日"}],
         "decisions": ["各网点提前推增员，不等下周",
                      "1025达成率严肃问责，百分百必须达成"],
         "action_items": [{"owner": "各网点经理", "task": "本周内安排增员活动/创会", "deadline": "5月8日前"}]},
        {"topic": "惠银保产品推动与网点业绩",
         "key_points": ["武平上月惠银保卖得好，但年进度低于中支均值3个点",
                        "长汀、永定等网点需借助惠银保+加一提费赶进度"],
         "data_points": [{"label": "武平年进度差距", "value": "低于均值3个百分点"},
                         {"label": "惠银保推动力", "value": "加一提费政策"}],
         "decisions": ["有惠银保基础的网点要借势多推"]},
        {"topic": "半年问责风险预警",
         "key_points": ["问责压力排序：长汀(最大) > 必新 > 连城 > 克林",
                        "二部4个网点达成率低于中支/分公司均值"],
         "data_points": [{"label": "问责风险第一", "value": "长汀"},
                         {"label": "问责风险第二", "value": "必新"},
                         {"label": "问责风险第三", "value": "连城"},
                         {"label": "问责风险第四", "value": "克林"},
                         {"label": "二部低于均值网点", "value": "4个"}]},
        {"topic": "目标客户与签单策略",
         "key_points": ["聚焦稳利宝+惠银保+加一提费产品体系",
                        "以1025为导向，20%做钻石人力"],
         "data_points": [{"label": "核心产品", "value": "稳利宝+惠银保"},
                         {"label": "人员覆盖", "value": "百分百已面谈"}]}
    ]
}, ensure_ascii=False)


def main():
    if not DOCX_PATH:
        print("用法: python analyze_fact_coverage.py <docx_path>")
        print("示例: python analyze_fact_coverage.py ./test_optimized_transcript.docx")
        return

    from transcript.processor import TranscriptProcessor
    
    import docx
    doc = docx.Document(DOCX_PATH)
    text = "\n".join([p.text for p in doc.paragraphs])
    
    processor = TranscriptProcessor()
    processed = processor.process(text)
    
    print("=" * 75)
    print("  事实覆盖率深度分析报告")
    print("=" * 75)
    print(f"\n原始文本: {len(text):,}字符")
    print(f"预提取事实总数: {len(processed.all_facts)} 条")
    print()
    
    fact_type_counts = {}
    for f in processed.all_facts:
        fact_type_counts[f.fact_type] = fact_type_counts.get(f.fact_type, 0) + 1
    
    print("【事实类型分布】")
    for ft, cnt in sorted(fact_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {ft:12s} {cnt:3d} 条")
    print()
    
    llm_lower = MOCK_LLM_RESPONSE.lower()
    
    matched_facts = []
    unmatched_facts = []
    excluded_facts = []
    
    for fact in processed.all_facts:
        if fact.fact_type == "number":
            ctx = (fact.context_before + fact.context_after).strip()
            if len(ctx) < 5 or (not any(c in ctx for c in "%%万亿美元元人个股笔年金月周天度期") and len(fact.text.replace(',', '').replace('.', '')) <= 2):
                excluded_facts.append(fact)
                continue
        
        matched = False
        fact_text = fact.text.lower()
        fact_value = (fact.value or "").lower()
        
        if fact_value and fact_value in llm_lower:
            matched = True
        elif fact_text in llm_lower:
            matched = True
        
        if matched:
            matched_facts.append(fact)
        else:
            unmatched_facts.append(fact)
    
    print("【匹配情况统计】")
    print(f"  排除的孤立数字: {len(excluded_facts)} 条")
    print(f"  成功匹配: {len(matched_facts)} 条")
    print(f"  未匹配: {len(unmatched_facts)} 条")
    print(f"  实际覆盖率: {len(matched_facts)/(len(processed.all_facts)-len(excluded_facts)):.1%}")
    print()
    
    print("=" * 75)
    print("  未匹配事实详细分析")
    print("=" * 75)
    
    unmatched_by_type = {}
    for f in unmatched_facts:
        if f.fact_type not in unmatched_by_type:
            unmatched_by_type[f.fact_type] = []
        unmatched_by_type[f.fact_type].append(f)
    
    for ft, facts in unmatched_by_type.items():
        print(f"\n【{ft}】({len(facts)}条)")
        for i, f in enumerate(facts[:6]):
            ctx_b = f.context_before[-30:] if len(f.context_before) > 30 else f.context_before
            ctx_a = f.context_after[:30] if len(f.context_after) > 30 else f.context_after
            print(f"  {i+1}. [{f.text}]")
            print(f"     上下文: ...{ctx_b}[{f.text}]{ctx_a}...")
            if f.value:
                print(f"     值: {f.value}")
            print()
    
    print("=" * 75)
    print("  提升覆盖率的建议")
    print("=" * 75)
    print()
    print("【当前问题根因】")
    print("  1. 正则提取了大量孤立数字（如 '14'、'500'），但LLM做语义聚合")
    print("  2. 正则提取的时间词（如 '下一周'）在LLM输出中被具体化（如 '5月8日'）")
    print("  3. 部分事实是口语中的重复表述，LLM做了去重")
    print()
    print("【可改进方向】")
    print("  1. 优化正则：增加上下文要求，减少孤立数字提取")
    print("  2. 优化提示词：强制LLM引用原文中的具体数字")
    print("  3. 语义匹配：支持数字范围匹配、时间归一化匹配")
    print("  4. 增加LLM输出密度：要求每个议题包含更多数据点")
    print()
    
    return {
        "total": len(processed.all_facts),
        "matched": len(matched_facts),
        "unmatched": len(unmatched_facts),
        "excluded": len(excluded_facts),
        "coverage": len(matched_facts)/(len(processed.all_facts)-len(excluded_facts))
    }


if __name__ == "__main__":
    main()