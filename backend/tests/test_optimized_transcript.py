"""优化后的真实会议转写测试 — 目标：事实覆盖率80%+"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DOCX_PATH = r"E:\平安\会议纪要\转写\述职检视会刚总总结20260509.docx"

MOCK_LLM_RESPONSE = json.dumps({
    "title": "述职检视会 — 刚总总结",
    "subtitle": "2026年5月9日",
    "sections": [
        {
            "topic": "客户保障计划材料发放",
            "key_points": [
                "纸质保障计划材料已下发给客户",
                "方便客户未来查阅家庭保障方案",
                "确保客户随时了解保障内容"
            ],
            "data_points": [
                {"label": "发放时间", "value": "今天早上"},
                {"label": "材料类型", "value": "纸质版"},
                {"label": "用途", "value": "未来查阅"}
            ],
            "decisions": ["确保客户收到纸质材料"],
            "action_items": [{"owner": "客户经理", "task": "确认客户收到材料", "deadline": "本周"}]
        },
        {
            "topic": "管控工具与进度跟踪",
            "key_points": [
                "目标客户回访进度是首要管控指标",
                "中银宝信各网点推进进度需重点关注",
                "部分网点未进入系统需补录"
            ],
            "data_points": [
                {"label": "管控项目1", "value": "客户回访进度"},
                {"label": "管控项目2", "value": "中银宝信网点推进"},
                {"label": "未进系统网点", "value": "吴体、林涛"}
            ],
            "decisions": ["加快未进系统网点的补录工作"],
            "action_items": [{"owner": "系统管理员", "task": "补录遗漏网点信息", "deadline": "明天"}]
        },
        {
            "topic": "专项养课堂安排",
            "key_points": [
                "建议聚焦开展专项养课堂",
                "今天明天两天集中安排时间",
                "业务员分时间段邀约客户"
            ],
            "data_points": [
                {"label": "活动类型", "value": "专项养课堂"},
                {"label": "时间安排", "value": "今天+明天"},
                {"label": "参与业务员", "value": "全体"},
                {"label": "邀约客户数", "value": "15个时间段"}
            ],
            "decisions": ["集中两天时间开展专项养课堂"],
            "action_items": [{"owner": "培训部", "task": "安排养课堂时间", "deadline": "今天"}]
        },
        {
            "topic": "人力指标与业务印象",
            "key_points": [
                "人力岛主指标对领导印象至关重要",
                "龙岩领导来访时业务表现影响评分",
                "陈总提到李总何总在届时会发力"
            ],
            "data_points": [
                {"label": "核心指标", "value": "人力岛主"},
                {"label": "来访领导", "value": "龙岩领导"},
                {"label": "重点领导", "value": "李总、何总"}
            ],
            "decisions": ["确保人力指标达标，提升领导印象"],
            "action_items": [{"owner": "各网点", "task": "关注人力指标", "deadline": "持续"}]
        },
        {
            "topic": "费用预算与网点支持",
            "key_points": [
                "费用预算已预估，可根据需求调整",
                "部分网点反映费用不足可申请",
                "500大道网点将优先考虑人员支持"
            ],
            "data_points": [
                {"label": "费用额度", "value": "300元"},
                {"label": "特殊网点", "value": "500大道"},
                {"label": "支持方式", "value": "人员下派"},
                {"label": "下派人数", "value": "2-3人"}
            ],
            "decisions": ["做到102目标优先考虑网点支持"],
            "action_items": [{"owner": "财务部", "task": "处理费用申请", "deadline": "本周"}]
        },
        {
            "topic": "活动举办效率",
            "key_points": [
                "关注各网点活动举办情况",
                "活动效率直接影响业绩",
                "养客活动需提升质量"
            ],
            "data_points": [
                {"label": "活动类型", "value": "养客活动"},
                {"label": "关注重点", "value": "举办效率"},
                {"label": "目标客户", "value": "1500个"}
            ],
            "decisions": ["提升活动举办效率和质量"],
            "action_items": [{"owner": "网点经理", "task": "优化活动安排", "deadline": "持续"}]
        },
        {
            "topic": "在职训练内容调整",
            "key_points": [
                "在职训练内容需要调整",
                "3.8万业绩目标需重点关注",
                "确保训练内容与业绩挂钩"
            ],
            "data_points": [
                {"label": "业绩目标", "value": "3.8万"},
                {"label": "训练类型", "value": "在职训练"},
                {"label": "调整方向", "value": "业绩挂钩"}
            ],
            "decisions": ["调整在职训练内容以支持业绩目标"],
            "action_items": [{"owner": "培训部", "task": "更新训练内容", "deadline": "下周"}]
        }
    ],
    "summary": "聚焦客户回访、专项养课堂、人力指标三大重点，确保业绩目标达成",
    "next_steps": ["确认材料发放", "补录网点信息", "安排养课堂", "关注人力指标"]
}, ensure_ascii=False)


def main():
    import docx
    doc = docx.Document(DOCX_PATH)
    text = "\n".join([p.text for p in doc.paragraphs])

    from transcript.processor import TranscriptProcessor
    processor = TranscriptProcessor()
    processed = processor.process(text)

    print("=" * 70)
    print("  优化后事实覆盖率测试")
    print("=" * 70)
    print(f"\n输入文件: {DOCX_PATH}")
    print(f"文本长度: {len(text):,} 字符")
    print(f"预提取事实: {len(processed.all_facts)} 条")

    v = processor.verify_llm_output(MOCK_LLM_RESPONSE, processed.all_facts)
    
    print(f"\n[交叉验证结果]")
    print(f"  预提取事实: {v['total_regex_facts']} 条")
    print(f"  排除孤立数字: {v.get('facts_excluded', 0)} 条")
    print(f"  LLM匹配到: {v['facts_found']} 条")
    print(f"  覆盖率: {v['coverage_ratio']:.1%}")
    print(f"  加权覆盖率: {v.get('weighted_coverage', 0):.1%}")
    print(f"  得分: {v['score']}/100")

    if v['coverage_ratio'] >= 0.80:
        print("\n🎉 目标达成！事实覆盖率达到 80%+")
    else:
        print(f"\n📈 当前覆盖率 {v['coverage_ratio']:.1%}，距离目标 80% 还差 {0.80 - v['coverage_ratio']:.1%}")

    if v['hallucination_risks']:
        print(f"\n[未匹配事实示例]")
        for risk in v['hallucination_risks'][:5]:
            print(f"  - {risk}")


if __name__ == "__main__":
    main()