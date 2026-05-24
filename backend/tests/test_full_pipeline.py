"""端到端测试：真实会议转写 → PPT生成完整流程"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slide_builder.pipeline import GenerationPipeline
from transcript.processor import TranscriptProcessor


def test_full_pipeline():
    print("=" * 70)
    print("  端到端测试：会议转写 → PPT生成")
    print("=" * 70)
    
    DOCX_PATH = r"E:\平安\会议纪要\转写\刚总会议总结20260505.docx"
    
    try:
        import docx
        doc = docx.Document(DOCX_PATH)
        raw_text = "\n".join([p.text for p in doc.paragraphs])
        print(f"\n【输入文件】{DOCX_PATH}")
        print(f"文本长度: {len(raw_text):,} 字符")
        print(f"预览: {raw_text[:100]}...")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    print("\n" + "-" * 70)
    print("Step 1: 文本预处理")
    print("-" * 70)
    
    processor = TranscriptProcessor()
    processed = processor.process(raw_text)
    
    print(f"✓ 清洗完成: {len(raw_text):,} → {len(processed.cleaned_text):,} 字符")
    print(f"✓ 分块: {len(processed.chunks)} 块")
    print(f"✓ 预提取事实: {len(processed.all_facts)} 条")
    print(f"✓ 识别发言人: {processed.speakers}")
    print(f"✓ 会议类型: {processed.meeting_type_hint}")
    
    print("\n" + "-" * 70)
    print("Step 2: 构建LLM提示词")
    print("-" * 70)
    
    prompt = processor.build_llm_prompt(processed)
    print(f"✓ 提示词长度: {len(prompt):,} 字符")
    print(f"✓ 包含预提取事实: {'pre_extracted_facts' in prompt}")
    
    print("\n" + "-" * 70)
    print("Step 3: 模拟LLM结构化输出")
    print("-" * 70)
    
    import json
    llm_response = json.dumps({
        "title": "5月业务推进会 — 刚总总结",
        "subtitle": "2025年5月6日",
        "sections": [
            {
                "topic": "心梗筛查邀约流程优化",
                "key_points": ["心梗筛查作为获客手段可行，但不能混入促成环节",
                              "国安办了两场，人多但转化效果未达预期",
                              "建议将心梗筛查定位为获客养客"],
                "data_points": [{"label": "国安已办场次", "value": "2场"},
                               {"label": "邀约模式评估", "value": "需优化"}],
                "decisions": ["不要以心梗筛查名义直接邀约促成客户"],
                "action_items": [{"owner": "汇总/组训", "task": "研究促成端优化方案", "deadline": "本周"}],
                "suggested_layout": "content_compare"
            },
            {
                "topic": "增员主体推进与1025人力目标",
                "key_points": ["增员主体必须本周参加增员活动",
                              "8号后召开述职检测会",
                              "1025目标：1个主管上岗+2个钻石人力"],
                "data_points": [{"label": "连城现有人力", "value": "6人"},
                               {"label": "1025目标", "value": "1+2"},
                               {"label": "时间节点", "value": "5月8日"}],
                "decisions": ["各网点提前推增员，不等下周"],
                "action_items": [{"owner": "各网点经理", "task": "本周内安排增员活动", "deadline": "5月8日前"}],
                "suggested_layout": "content_kpi"
            },
            {
                "topic": "惠银保产品推动与网点业绩",
                "key_points": ["武平上月惠银保卖得好，但年进度低于中支均值3个点",
                              "长汀、永定需借助惠银保+加一提费赶进度"],
                "data_points": [{"label": "武平年进度差距", "value": "低于均值3个百分点"},
                               {"label": "惠银保推动力", "value": "加一提费政策"}],
                "decisions": ["有惠银保基础的网点要借势多推"],
                "action_items": [{"owner": "武平/长汀/永定", "task": "加大惠银保推动力度", "deadline": "5-6月"}],
                "suggested_layout": "content_compare"
            },
            {
                "topic": "半年问责风险预警",
                "key_points": ["问责压力排序：长汀 > 必新 > 连城 > 克林",
                              "二部4个网点达成率低于均值"],
                "data_points": [{"label": "问责风险第一", "value": "长汀"},
                               {"label": "问责风险第二", "value": "必新"},
                               {"label": "二部低于均值网点", "value": "4个"}],
                "decisions": ["半年问责只看达成率，不可调整"],
                "action_items": [{"owner": "长汀网点", "task": "重点研究追赶方案", "deadline": "5月底"}],
                "suggested_layout": "content_table"
            },
            {
                "topic": "目标客户与签单策略",
                "key_points": ["聚焦稳利宝+惠银保+加一提费产品体系",
                              "以1025为导向，20%做钻石人力"],
                "data_points": [{"label": "核心产品", "value": "稳利宝+惠银保"},
                               {"label": "人员覆盖", "value": "百分百已面谈"}],
                "decisions": ["圈定主力人群，借助8分钟面谈强化意愿"],
                "action_items": [{"owner": "各网点", "task": "梳理目标客户名单", "deadline": "本周"}],
                "suggested_layout": "content"
            }
        ],
        "summary": "聚焦1025人力目标+惠银保产品推动，抓住5-6月窗口赶半年进度",
        "next_steps": ["梳理增员名单", "加大惠银保推动", "优化邀约流程"]
    }, ensure_ascii=False)
    
    print("✓ 模拟LLM输出: 5个议题，14个数据点")
    
    print("\n" + "-" * 70)
    print("Step 4: 交叉验证")
    print("-" * 70)
    
    verification = processor.verify_llm_output(llm_response, processed.all_facts)
    print(f"✓ 事实覆盖率: {verification['coverage_ratio']:.1%}")
    print(f"✓ 匹配事实: {verification['facts_found']}/{verification['total_regex_facts']}")
    print(f"✓ 得分: {verification['score']}/100")
    
    if verification['hallucination_risks']:
        print(f"⚠️ 幻觉风险: {len(verification['hallucination_risks'])} 条")
    else:
        print("✓ 无幻觉风险")
    
    print("\n" + "-" * 70)
    print("Step 5: PPT生成")
    print("-" * 70)
    
    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )
    
    structured = json.loads(llm_response)
    sections = structured.get("sections", [])
    slides_data = pipeline._transcript_sections_to_slides(structured, sections)
    
    print(f"✓ 生成幻灯片: {len(slides_data)} 页")
    
    from slide_builder.generator import PPTXGenerator
    gen = PPTXGenerator("professional-blue", pipeline.theme, "16:9")
    
    from dataclasses import asdict
    pptx_bytes = gen.generate_from_slide_data([asdict(s) for s in slides_data])
    
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "刚总会议总结_正式测试.pptx")
    
    with open(output_path, "wb") as f:
        f.write(pptx_bytes)
    
    print(f"✓ PPTX已生成: {output_path}")
    print(f"✓ 文件大小: {len(pptx_bytes):,} 字节 ({len(pptx_bytes)/1024:.1f} KB)")
    
    print("\n" + "-" * 70)
    print("Step 6: Deck QA")
    print("-" * 70)
    
    from slide_builder.deck_qa import DeckQA
    qa = DeckQA()
    results = qa.check_all(slides_data)
    
    errors = [r for r in results if r["severity"] == "error"]
    warnings = [r for r in results if r["severity"] == "warning"]
    
    print(f"✓ QA检查完成")
    print(f"  错误: {len(errors)} 条")
    print(f"  警告: {len(warnings)} 条")
    
    if errors:
        for e in errors:
            print(f"    🔴 {e['message']}")
    
    print("\n" + "=" * 70)
    print("  ✅ 端到端测试完成")
    print("=" * 70)
    print(f"\n输出文件: {output_path}")
    print(f"幻灯片数: {len(slides_data)} 页")
    print(f"事实覆盖率: {verification['coverage_ratio']:.1%}")
    print(f"综合质量: {'优秀' if verification['score'] >= 80 else '良好'}")


if __name__ == "__main__":
    test_full_pipeline()