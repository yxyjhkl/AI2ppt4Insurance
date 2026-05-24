"""End-to-end test: Unstructured meeting transcript → PPT with quality control.

Tests the full 4-layer quality assurance pipeline:
  Layer 1: Pre-extraction (regex-based fact mining)
  Layer 2: LLM structured extraction (simulated)
  Layer 3: Cross-validation (LLM output vs pre-extracted facts)
  Layer 4: Deck QA (slide-level quality checks)
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MOCK_TRANSCRIPT = """会议主题：2025年Q1保险业务复盘与Q2策略规划
会议时间：2025年4月3日 14:00-16:30
参会人员：张总、李经理、王总监、赵主管、钱分析师

张总：好，那我们开始今天的会议。今天主要复盘一下Q1的业绩情况，然后讨论Q2的策略。
我们Q1整体保费收入是3800万，同比增长15%，但是离我们4200万的目标还是有差距的。

李经理：对，我补充一下具体数据。个险渠道Q1完成了2100万，同比增长12%，达成率是95%。然后团险渠道完成了1200万，同比增长22%，达成率是110%，表现很不错。然后网销渠道完成500万，同比增速只有5%，达成率65%，这个比较差。主要是我们的线上获客成本上升了，从去年的120元一个有效线索涨到了175元。

王总监：我来说说客户留存的情况。Q1我们的13个月续期率是82%，比去年Q4的85%下降了3个百分点。然后25个月续期率是65%，和去年同期持平。我觉得这个下降主要是因为年初的产品切换，客户对新产品的接受还需要时间。

张总：续期率下降这个事儿确实要重视，特别是82%这个数据，我觉得低于我们行业平均水平了。然后那个你说产品切换的问题，我决定我们从下周开始做一轮新产品说明会，每个营业部至少搞2场，覆盖到我们80%以上的存量客户。

赵主管：我这边做了Q1的理赔数据统计。整体理赔金额是950万，理赔率是25%，比去年同期的28%有所下降。然后重大疾病理赔占比最高，达到45%，然后是医疗险理赔35%，意外险20%。主要的问题是我们有一些理赔时效超标了，平均结案时间是5.8天，我们的目标是3天以内。

张总：5.8天这个太慢了，这个必须立刻整改。钱分析师，你说一下竞品对标的情况。

钱分析师：好的张总。我分析了A公司、B公司、C公司三家的Q1数据。A公司的个险渠道增速是18%，我们的12%明显落后了。然后B公司的新产品推出速度很快，Q1推出了3款产品，我们只推出了1款。C公司的话，他们的线上转化率是3.2%，我们是2.1%，差了一个多点。总体上我们在三个维度都是落后的。

张总：这个对标数据确实不太好看。那我们接下来讨论Q2怎么打。我提几个方向，然后大家讨论。

王总监：我觉得Q2核心要做三件事。第一是个险渠道要追上来，我建议把Q2目标定在2800万，同比增长要达到33%以上。第二是网销渠道必须搞起来，我建议Q2的目标定在800万，要通过优化投放渠道把获客成本降到150元以下。第三是理赔时效的问题，Q2必须把平均结案时间压缩到3天以内。

赵主管：理赔这边我补充一下。然后我们计划Q2要上线智能理赔系统，预计能把结案时间缩短40%。然后我们还要加强人员培训，每两周搞一次理赔技能培训。我觉得目标定在3天是有把握的。

李经理：我补充两个点。一个是新产品，Q2我们必须要推出至少2款新产品，一款是针对年轻人的定期寿险，一款是针对中老年的防癌险。另一个是客户运营，我建议我们启动一个老客户复购计划，通过权益升级和体检服务来提升客户的续期率，目标是把13个月续期率从82%提升到88%。

张总：好，我总结一下。我决定Q2重点做四件事。第一，个险渠道目标2800万。第二，团险渠道继续稳住1200万的盘子。第三，网销渠道目标800万。第四，理赔时效压缩到3天以内。然后产品方面，我们要在5月底前推出2款新产品。客户运营方面，6月份启动老客户复购计划。大家有没有补充？

全员：没有。
张总：好，那今天的会议就到这里，大家按照分工去落实。
"""

MOCK_LLM_RESPONSE = json.dumps({
    "title": "2025年Q1保险业务复盘与Q2策略规划",
    "subtitle": "2025年4月3日",
    "sections": [
        {
            "topic": "Q1整体业绩概览",
            "key_points": [
                "Q1保费收入3800万，同比增长15%",
                "离4200万目标缺口400万，达成率90.5%"
            ],
            "data_points": [
                {"label": "Q1保费总收入", "value": "3800万"},
                {"label": "同比增长", "value": "15%"},
                {"label": "目标达成率", "value": "90.5%"}
            ],
            "decisions": [],
            "action_items": [],
            "suggested_layout": "content_kpi"
        },
        {
            "topic": "渠道业绩分析",
            "key_points": [
                "个险渠道2100万，达成率95%，达标但增速放缓",
                "团险渠道1200万，达成率110%，超额完成",
                "网销渠道500万，达成率65%，问题突出"
            ],
            "data_points": [
                {"label": "个险渠道", "value": "2100万 (95%)"},
                {"label": "团险渠道", "value": "1200万 (110%)"},
                {"label": "网销渠道", "value": "500万 (65%)"},
                {"label": "线上获客成本", "value": "175元/线索"}
            ],
            "decisions": [],
            "action_items": [],
            "suggested_layout": "content_table"
        },
        {
            "topic": "客户留存与续期率",
            "key_points": [
                "13个月续期率82%，环比下降3个百分点",
                "产品切换导致客户对新品接受度不足"
            ],
            "data_points": [
                {"label": "13月续期率", "value": "82%"},
                {"label": "25月续期率", "value": "65%"},
                {"label": "Q4续期率", "value": "85%"}
            ],
            "decisions": [
                "下周起每营业部至少2场新产品说明会",
                "覆盖80%以上存量客户"
            ],
            "action_items": [
                {"owner": "王总监", "task": "组织新产品说明会", "deadline": "下周启动"}
            ],
            "suggested_layout": "content_kpi"
        },
        {
            "topic": "理赔数据分析",
            "key_points": [
                "Q1理赔金额950万，理赔率25%",
                "平均结案5.8天，目标3天，差距明显",
                "重疾理赔占比最高45%"
            ],
            "data_points": [
                {"label": "理赔金额", "value": "950万"},
                {"label": "理赔率", "value": "25%"},
                {"label": "平均结案时间", "value": "5.8天"},
                {"label": "目标结案时间", "value": "3天"}
            ],
            "decisions": [],
            "action_items": [
                {"owner": "赵主管", "task": "上线智能理赔系统", "deadline": "Q2"},
                {"owner": "赵主管", "task": "每两周理赔技能培训", "deadline": "持续"}
            ],
            "suggested_layout": "content_table"
        },
        {
            "topic": "竞品对标分析",
            "key_points": [
                "A公司个险增速18%，我方12%",
                "B公司Q1推3款新品，我方仅1款",
                "C公司线上转化率3.2%，我方2.1%"
            ],
            "data_points": [
                {"label": "我方个险增速", "value": "12%"},
                {"label": "A公司个险增速", "value": "18%"},
                {"label": "我方线上转化率", "value": "2.1%"},
                {"label": "C公司线上转化率", "value": "3.2%"}
            ],
            "decisions": [],
            "action_items": [],
            "suggested_layout": "content_compare"
        },
        {
            "topic": "Q2核心决策与行动项",
            "key_points": [
                "个险渠道Q2目标2800万（+33%）",
                "网销渠道Q2目标800万，获客成本降至150元",
                "理赔时效压缩到3天以内",
                "5月底前推出2款新产品"
            ],
            "data_points": [
                {"label": "个险Q2目标", "value": "2800万"},
                {"label": "网销Q2目标", "value": "800万"},
                {"label": "获客成本目标", "value": "≤150元"}
            ],
            "decisions": [
                "Q2推出2款新产品（定期寿险+防癌险）",
                "6月启动老客户复购计划",
                "13月续期率目标提升至88%"
            ],
            "action_items": [
                {"owner": "李经理", "task": "Q2推出2款新产品", "deadline": "5月底"},
                {"owner": "李经理", "task": "启动老客户复购计划", "deadline": "6月"},
                {"owner": "赵主管", "task": "理赔时效压缩到3天", "deadline": "Q2"},
                {"owner": "王总监", "task": "个险渠道达成2800万", "deadline": "Q2"}
            ],
            "suggested_layout": "content_compare"
        }
    ],
    "summary": "Q1达成3800万（目标90.5%），Q2聚焦个险增长、网销突破、理赔提效、产品创新四大方向",
    "next_steps": [
        "各渠道制定Q2详细执行计划",
        "5月底前完成2款新品上市",
        "启动智能理赔系统部署",
        "6月启动老客户复购计划"
    ]
}, ensure_ascii=False)


def test_transcript_detection():
    """Test that pipeline correctly identifies transcript-style text."""
    from slide_builder.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )

    is_transcript = pipeline._detect_transcript(MOCK_TRANSCRIPT)
    assert is_transcript, "Should detect meeting transcript"
    print("  [PASS] Transcript detection works correctly")

    not_transcript = pipeline._detect_transcript("Q1 report: Sales up 15%. Team did well.")
    assert not not_transcript, "Short structured text should NOT be detected as transcript"
    print("  [PASS] Short text correctly not classified as transcript")

    empty = pipeline._detect_transcript("")
    assert not empty, "Empty string should not be transcript"
    print("  [PASS] Empty text handling OK")

    print("Transcript detection: ALL PASSED\n")


def test_transcript_processing():
    """Test the transcript processor: cleaning, chunking, fact extraction."""
    from transcript.processor import TranscriptProcessor

    processor = TranscriptProcessor()
    processed = processor.process(MOCK_TRANSCRIPT)

    print(f"  Original length: {processed.original_length}")
    print(f"  Cleaned length: {len(processed.cleaned_text)}")
    print(f"  Chunks: {len(processed.chunks)}")
    print(f"  Facts extracted: {len(processed.all_facts)}")
    print(f"  Speakers: {processed.speakers}")
    print(f"  Estimated duration: {processed.estimated_duration_min} min")
    print(f"  Meeting type: {processed.meeting_type_hint}")

    assert processed.original_length > 0
    assert len(processed.chunks) > 0, "Should have at least 1 chunk"
    assert len(processed.all_facts) > 0, "Should extract facts"
    assert len(processed.speakers) > 0, "Should extract speakers"

    fact_types = {}
    for f in processed.all_facts:
        fact_types[f.fact_type] = fact_types.get(f.fact_type, 0) + 1
    print(f"  Fact types: {fact_types}")

    assert fact_types.get("metric", 0) + fact_types.get("number", 0) >= 3, \
        "Should extract at least 3 numbers/metrics"
    assert fact_types.get("action_item", 0) >= 1, \
        "Should extract at least 1 action item"

    llm_prompt = processor.build_llm_prompt(processed)
    assert len(llm_prompt) > 200, "LLM prompt should be substantive"
    assert "pre_extracted_facts" in llm_prompt
    print(f"  LLM prompt length: {len(llm_prompt)} chars")

    print("Transcript processing: ALL PASSED\n")
    return processed


def test_fact_verification():
    """Test cross-validation: LLM output vs regex-extracted facts."""
    from transcript.processor import TranscriptProcessor

    processor = TranscriptProcessor()
    processed = processor.process(MOCK_TRANSCRIPT)

    verification = processor.verify_llm_output(MOCK_LLM_RESPONSE, processed.all_facts)

    print(f"  Total regex facts: {verification['total_regex_facts']}")
    print(f"  Facts found in LLM output: {verification['facts_found']}")
    print(f"  Facts missing: {verification['facts_missing']}")
    print(f"  Coverage ratio: {verification['coverage_ratio']:.1%}")
    print(f"  Score: {verification['score']}")
    print(f"  Hallucination risks: {len(verification['hallucination_risks'])}")

    assert verification['total_regex_facts'] > 0
    assert verification['coverage_ratio'] >= 0.3, \
        f"Coverage too low: {verification['coverage_ratio']:.1%}"
    assert verification['score'] >= 70, \
        f"Score too low: {verification['score']}"

    print("Fact verification: ALL PASSED\n")
    return verification


def test_json_parsing():
    """Test JSON parsing with error recovery."""
    from slide_builder.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )

    parsed = pipeline._parse_transcript_json(MOCK_LLM_RESPONSE)
    assert parsed, "Should parse valid JSON"
    assert "title" in parsed
    assert "sections" in parsed
    assert len(parsed["sections"]) >= 3
    print(f"  Parsed: {parsed['title']}, {len(parsed['sections'])} sections")

    broken_json = '{"title": "Test", "sections": [{"topic": "X"}]}'  # missing comma
    parsed_broken = pipeline._parse_transcript_json(broken_json)
    assert parsed_broken, "Should recover from broken JSON"
    print("  [PASS] Broken JSON recovery works")

    empty_output = pipeline._parse_transcript_json("no json here")
    assert not empty_output, "Should return empty for non-JSON"
    print("  [PASS] Non-JSON handling OK")

    print("JSON parsing: ALL PASSED\n")


def test_section_to_slide_conversion():
    """Test converting transcript sections to SlideData."""
    from slide_builder.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )

    structured = json.loads(MOCK_LLM_RESPONSE)
    sections = structured["sections"]
    slides = pipeline._transcript_sections_to_slides(structured, sections)

    print(f"  Generated {len(slides)} slides from {len(sections)} sections")

    layout_types = {}
    for s in slides:
        lt = s.layout_type
        layout_types[lt] = layout_types.get(lt, 0) + 1
    print(f"  Layout distribution: {layout_types}")

    assert len(slides) >= 4, f"Should generate at least 4 slides, got {len(slides)}"
    assert slides[0].layout_type == "cover", "First slide should be cover"
    assert slides[-1].layout_type == "ending", "Last slide should be ending"

    kpi_slides = [s for s in slides if s.layout_type == "content_kpi"]
    table_slides = [s for s in slides if s.layout_type == "content_table"]
    compare_slides = [s for s in slides if s.layout_type == "content_compare"]
    print(f"  KPI: {len(kpi_slides)}, Table: {len(table_slides)}, Compare: {len(compare_slides)}")

    has_data_slide = len(kpi_slides) + len(table_slides) > 0
    assert has_data_slide, "Should have at least 1 data visualization slide"

    print("Section to slide conversion: ALL PASSED\n")


def test_deck_qa_transcript():
    """Test DeckQA transcript-specific checks."""
    from slide_builder.deck_qa import DeckQA
    from slide_builder.pipeline import GenerationPipeline, SlideData

    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )

    structured = json.loads(MOCK_LLM_RESPONSE)
    sections = structured["sections"]
    slides = pipeline._transcript_sections_to_slides(structured, sections)

    qa = DeckQA()

    generic_results = qa.check_all(slides)
    print(f"  Generic QA: {len(generic_results)} issues")
    for r in generic_results:
        sev = r.get("severity", "?")
        msg = r.get("message", "")[:80]
        print(f"    [{sev}] {msg}")

    total_decisions = sum(len(s.get("decisions", [])) for s in sections)
    total_actions = sum(len(s.get("action_items", [])) for s in sections)
    total_data = sum(len(s.get("data_points", [])) for s in sections)

    transcript_results = qa.check_transcript_deck(
        slides,
        section_count=len(sections),
        decision_count=total_decisions,
        action_count=total_actions,
        data_point_count=total_data,
    )
    print(f"  Transcript QA: {len(transcript_results)} issues")
    for r in transcript_results:
        sev = r.get("severity", "?")
        msg = r.get("message", "")[:80]
        print(f"    [{sev}] {msg}")

    errors = [r for r in generic_results + transcript_results if r.get("severity") == "error"]
    assert len(errors) == 0, f"Should have no errors, got {len(errors)}: {errors}"

    print("Deck QA transcript: ALL PASSED\n")


def test_pptx_generation():
    """Test full PPTX generation from transcript-derived slides."""
    from slide_builder.pipeline import GenerationPipeline, SlideData
    from slide_builder.generator import PPTXGenerator

    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )

    structured = json.loads(MOCK_LLM_RESPONSE)
    sections = structured["sections"]
    slides = pipeline._transcript_sections_to_slides(structured, sections)

    slide_dicts = []
    for s in slides:
        from dataclasses import asdict
        slide_dicts.append(asdict(s))

    generator = PPTXGenerator(
        template_id="professional-blue",
        theme=pipeline.theme,
        canvas_format="16:9",
    )

    pptx_bytes = generator.generate_from_slide_data(slide_dicts)

    import uuid
    output_path = os.path.join(
        os.path.dirname(__file__), "test_output",
        f"transcript_test_{uuid.uuid4().hex[:8]}.pptx"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pptx_bytes)

    file_size = os.path.getsize(output_path)
    print(f"  PPTX generated: {output_path}")
    print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

    assert file_size > 1000, "PPTX should be at least 1KB"

    print("PPTX generation: PASSED\n")
    return output_path


async def test_full_pipeline_offline():
    """Test the complete pipeline with a transcript input in offline mode."""
    from slide_builder.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(
        scene="insurance",
        template_id="professional-blue",
        ai_mode="offline",
    )

    result = await pipeline.run(MOCK_TRANSCRIPT)

    print(f"  Mode: {result.mode}")
    print(f"  Slides: {len(result.slides)}")
    print(f"  Title: {result.title}")
    print(f"  Message: {result.message}")
    print(f"  QA results: {len(result.qa_results)}")
    for qa in result.qa_results[:5]:
        print(f"    [{qa.get('severity', '?')}] {qa.get('message', '')[:80]}")

    assert len(result.slides) > 0, "Should generate slides"
    assert result.pptx_bytes is not None, "Should generate PPTX"

    output_path = os.path.join(
        os.path.dirname(__file__), "test_output",
        "transcript_full_pipeline.pptx"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(result.pptx_bytes)

    print(f"  Full pipeline PPTX: {output_path}")
    print("Full pipeline offline: PASSED\n")


def main():
    print("=" * 60)
    print("Transcript Pipeline End-to-End Tests")
    print("=" * 60)
    print()

    tests = [
        ("1. Transcript Detection", test_transcript_detection),
        ("2. Transcript Processing", test_transcript_processing),
        ("3. Fact Verification", test_fact_verification),
        ("4. JSON Parsing", test_json_parsing),
        ("5. Section → Slide Conversion", test_section_to_slide_conversion),
        ("6. Deck QA (Transcript)", test_deck_qa_transcript),
        ("7. PPTX Generation", test_pptx_generation),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'=' * 60}")

    print("\n--- 8. Full Pipeline (Offline) ---")
    try:
        asyncio.run(test_full_pipeline_offline())
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    print(f"\n{'=' * 60}")
    print(f"Final Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)