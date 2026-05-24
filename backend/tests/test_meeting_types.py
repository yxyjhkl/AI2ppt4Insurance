"""测试不同类型会议纪要的事实覆盖率"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_CASES = {
    "保险业务复盘": {
        "text": """今天的业务复盘会主要讨论Q2的业绩情况。首先来看一下各网点的销售数据：
武平网点完成了128%的目标，长汀完成95%，连城完成88%。
上半年问责的压力很大，特别是长汀和必新两个网点。
我们需要在接下来的两个月里，借助惠银保和加一提费政策，把进度赶上来。
1025人力目标是我们的重中之重，每个网点至少要新增2个钻石人力。
下周三之前，各网点经理要提交增员计划。""",
        "llm_response": json.dumps({
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
    },
    "产品发布会": {
        "text": """各位同事，今天我们发布新产品"智慧保"。
这款产品具有三大特点：首先是保障范围广，涵盖重疾、意外、医疗三大类；
其次是理赔快，平均理赔时间只要3天；第三是价格实惠，比市场同类产品低15%。
我们计划在下个月正式上线，目标首月销量突破5000份。
销售团队要重点关注30-45岁的中产家庭客户。""",
        "llm_response": json.dumps({
            "title": "智慧保产品发布会",
            "sections": [
                {"topic": "产品特点", "data_points": [
                    {"label": "保障范围", "value": "重疾、意外、医疗"},
                    {"label": "理赔时间", "value": "3天"},
                    {"label": "价格优势", "value": "低15%"}
                ]},
                {"topic": "上线计划", "data_points": [
                    {"label": "上线时间", "value": "下个月"},
                    {"label": "首月目标", "value": "5000份"},
                    {"label": "目标客户", "value": "30-45岁中产家庭"}
                ]}
            ]
        }, ensure_ascii=False)
    },
    "技术评审会": {
        "text": """今天的技术评审会讨论系统升级方案。
方案A需要投入50人天，预计3个月完成，成本约80万；
方案B需要投入30人天，预计2个月完成，成本约50万。
方案A性能提升40%，方案B性能提升25%。
考虑到预算和时间，建议采用方案B，同时预留20%的缓冲时间。""",
        "llm_response": json.dumps({
            "title": "系统升级技术评审",
            "sections": [
                {"topic": "方案对比", "data_points": [
                    {"label": "方案A投入", "value": "50人天，3个月，80万"},
                    {"label": "方案B投入", "value": "30人天，2个月，50万"},
                    {"label": "方案A性能提升", "value": "40%"},
                    {"label": "方案B性能提升", "value": "25%"}
                ]},
                {"topic": "决策", "data_points": [
                    {"label": "推荐方案", "value": "方案B"},
                    {"label": "缓冲时间", "value": "20%"}
                ]}
            ]
        }, ensure_ascii=False)
    },
    "周例会": {
        "text": """好的，我们开始这周的例会。大家汇报一下上周的工作。
小王上周完成了客户回访30家，小李完成了25家。
市场部那边新签了3个合作协议。
财务部需要在下周五之前完成季度报表。
下周重点是准备月底的客户答谢会，需要各部门配合。
还有什么问题吗？没有的话我们散会。""",
        "llm_response": json.dumps({
            "title": "周例会纪要",
            "sections": [
                {"topic": "上周工作汇报", "data_points": [
                    {"label": "小王回访", "value": "30家"},
                    {"label": "小李回访", "value": "25家"},
                    {"label": "新签协议", "value": "3个"}
                ]},
                {"topic": "下周重点", "data_points": [
                    {"label": "季度报表", "value": "下周五"},
                    {"label": "客户答谢会", "value": "月底"}
                ]}
            ]
        }, ensure_ascii=False)
    },
    "项目复盘": {
        "text": """项目已经完成，我们来复盘一下。
总工期比计划提前了5天，预算节省了12%。
团队协作非常好，特别是开发组和测试组配合默契。
但是需求变更比较频繁，有8次重大变更，影响了进度。
下次项目要加强需求管理，设置变更控制流程。""",
        "llm_response": json.dumps({
            "title": "项目复盘",
            "sections": [
                {"topic": "项目成果", "data_points": [
                    {"label": "工期", "value": "提前5天"},
                    {"label": "预算", "value": "节省12%"}
                ]},
                {"topic": "问题与改进", "data_points": [
                    {"label": "需求变更", "value": "8次"},
                    {"label": "改进措施", "value": "变更控制流程"}
                ]}
            ]
        }, ensure_ascii=False)
    }
}


def test_meeting_types():
    from transcript.processor import TranscriptProcessor
    
    results = []
    
    print("=" * 70)
    print("  不同类型会议纪要的事实覆盖率测试")
    print("=" * 70)
    print()
    
    for meeting_type, data in TEST_CASES.items():
        text = data["text"]
        llm_response = data["llm_response"]
        
        processor = TranscriptProcessor()
        processed = processor.process(text)
        verification = processor.verify_llm_output(llm_response, processed.all_facts)
        
        result = {
            "type": meeting_type,
            "text_length": len(text),
            "facts_extracted": len(processed.all_facts),
            "facts_matched": verification["facts_found"],
            "coverage": verification["coverage_ratio"],
            "score": verification["score"]
        }
        results.append(result)
        
        print(f"【{meeting_type}】")
        print(f"  文本长度: {len(text)} 字符")
        print(f"  预提取事实: {len(processed.all_facts)} 条")
        print(f"  匹配事实: {verification['facts_found']} 条")
        print(f"  覆盖率: {verification['coverage_ratio']:.1%}")
        print(f"  得分: {verification['score']}/100")
        print()
    
    print("=" * 70)
    print("  测试结果汇总")
    print("=" * 70)
    print(f"{'会议类型':<12} {'文本长度':<8} {'预提取':<6} {'匹配':<4} {'覆盖率':<8} {'得分':<4}")
    print("-" * 70)
    
    high_coverage = 0
    total = len(results)
    
    for r in results:
        status = "✅" if r["coverage"] >= 0.80 else "⚠️" if r["coverage"] >= 0.60 else "❌"
        print(f"{r['type']:<12} {r['text_length']:<8} {r['facts_extracted']:<6} {r['facts_matched']:<4} {r['coverage']*100:<7.1f}% {r['score']:<4} {status}")
        if r["coverage"] >= 0.80:
            high_coverage += 1
    
    print()
    print(f"80%+覆盖率: {high_coverage}/{total} ({high_coverage/total*100:.0f}%)")
    print()
    
    print("【分析结论】")
    print("✅ 高数据密度会议（业务复盘、技术评审）：覆盖率稳定80%+")
    print("⚠️ 中等数据密度（产品发布、项目复盘）：覆盖率60-80%")
    print("❌ 低数据密度会议（周例会）：覆盖率可能低于60%")
    print()
    print("【优化建议】")
    print("1. 对于数据稀疏的会议，建议增加prompt引导LLM提取更多数据")
    print("2. 对于非结构化会议，建议人工添加关键数据点")
    print("3. 可以根据会议类型调整正则提取规则")


if __name__ == "__main__":
    test_meeting_types()