"""测试详细日志输出功能"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcript.processor import TranscriptProcessor

TEST_TEXT = """今天的业务复盘会主要讨论Q2的业绩情况。
武平网点完成了128%的目标，长汀完成95%，连城完成88%。
上半年问责的压力很大，特别是长汀和必新两个网点。
我们需要在接下来的两个月里，借助惠银保和加一提费政策，把进度赶上来。
1025人力目标是我们的重中之重，每个网点至少要新增2个钻石人力。
下周三之前，各网点经理要提交增员计划。"""

TEST_LLM_RESPONSE = json.dumps({
    "title": "Q2业务复盘会",
    "sections": [
        {"topic": "Q2业绩回顾", "data_points": [
            {"label": "武平完成率", "value": "128%"},
            {"label": "长汀完成率", "value": "95%"},
            {"label": "连城完成率", "value": "88%"}
        ]},
        {"topic": "问责压力分析", "data_points": [
            {"label": "重点关注网点", "value": "长汀、必新"},
            {"label": "时间窗口", "value": "2个月"}
        ]},
        {"topic": "人力目标", "data_points": [
            {"label": "1025目标", "value": "每个网点2个钻石人力"},
            {"label": "计划提交", "value": "下周三"}
        ]}
    ]
}, ensure_ascii=False)


def test_verbose_logging():
    print("=" * 70)
    print("  详细日志输出测试")
    print("=" * 70)
    print()
    
    processor = TranscriptProcessor()
    processed = processor.process(TEST_TEXT)
    
    print("【文本预处理结果】")
    print(f"原始长度: {len(TEST_TEXT)} 字符")
    print(f"清洗后长度: {len(processed.cleaned_text)} 字符")
    print(f"预提取事实: {len(processed.all_facts)} 条")
    print()
    
    print("【事实分类统计】")
    fact_counts = {}
    for f in processed.all_facts:
        fact_counts[f.fact_type] = fact_counts.get(f.fact_type, 0) + 1
    for ft, cnt in fact_counts.items():
        print(f"  {ft}: {cnt} 条")
    print()
    
    print("=" * 70)
    print("  详细匹配过程")
    print("=" * 70)
    
    verification = processor.verify_llm_output(TEST_LLM_RESPONSE, processed.all_facts, verbose=True)
    
    print("\n" + "=" * 70)
    print("  匹配结果汇总")
    print("=" * 70)
    print(f"\n预提取事实: {verification['total_regex_facts']} 条")
    print(f"排除: {verification['facts_excluded']} 条")
    print(f"匹配: {verification['facts_found']} 条")
    print(f"遗漏: {verification['facts_missing']} 条")
    print(f"覆盖率: {verification['coverage_ratio']:.1%}")
    print(f"得分: {verification['score']}/100")
    
    if verification['hallucination_risks']:
        print("\n【未匹配事实】")
        for risk in verification['hallucination_risks']:
            print(f"  - {risk}")


if __name__ == "__main__":
    test_verbose_logging()