"""会议类型配置参数 - 根据不同会议类型调整以保持高覆盖率"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TranscriptConfig:
    """转录处理配置"""
    
    # 正则提取参数
    min_action_length: int = 8           # 行动项最小长度
    min_number_context: int = 5          # 数字上下文最小长度
    allow_single_digit: bool = False     # 是否允许单数字
    
    # 匹配算法参数
    number_tolerance: float = 0.2        # 数字匹配容差 (±20%)
    date_synonym_enabled: bool = True    # 是否启用日期同义词
    fuzzy_match_enabled: bool = True     # 是否启用模糊匹配
    
    # 事实类型权重（影响加权覆盖率计算）
    fact_weights: Dict[str, float] = field(default_factory=lambda: {
        "metric": 3.0,
        "decision": 2.5,
        "action_item": 2.0,
        "date": 1.5,
        "number": 0.5,
    })
    
    # 覆盖率阈值
    coverage_threshold: float = 0.75     # 合格覆盖率阈值
    score_threshold: int = 60            # 合格分数阈值
    
    # 输出控制
    min_data_points_per_section: int = 3 # 每议题最少数据点
    max_slides: int = 25                # 最大幻灯片数
    min_slides: int = 3                 # 最小幻灯片数


MEETING_TYPE_CONFIGS: Dict[str, TranscriptConfig] = {
    "business_review": TranscriptConfig(
        min_action_length=8,
        min_number_context=5,
        allow_single_digit=False,
        number_tolerance=0.2,
        date_synonym_enabled=True,
        fuzzy_match_enabled=True,
        fact_weights={
            "metric": 3.0,
            "decision": 2.5,
            "action_item": 2.0,
            "date": 1.5,
            "number": 0.5,
        },
        coverage_threshold=0.75,
        min_data_points_per_section=3,
    ),
    
    "product_release": TranscriptConfig(
        min_action_length=6,
        min_number_context=3,
        allow_single_digit=False,
        number_tolerance=0.15,
        date_synonym_enabled=True,
        fuzzy_match_enabled=True,
        fact_weights={
            "metric": 4.0,
            "decision": 2.0,
            "action_item": 1.5,
            "date": 1.5,
            "number": 0.5,
        },
        coverage_threshold=0.80,
        min_data_points_per_section=4,
    ),
    
    "tech_review": TranscriptConfig(
        min_action_length=8,
        min_number_context=4,
        allow_single_digit=True,
        number_tolerance=0.10,
        date_synonym_enabled=True,
        fuzzy_match_enabled=True,
        fact_weights={
            "metric": 4.0,
            "decision": 2.5,
            "action_item": 2.0,
            "date": 1.0,
            "number": 1.0,
        },
        coverage_threshold=0.85,
        min_data_points_per_section=4,
    ),
    
    "weekly_meeting": TranscriptConfig(
        min_action_length=6,
        min_number_context=3,
        allow_single_digit=True,
        number_tolerance=0.25,
        date_synonym_enabled=True,
        fuzzy_match_enabled=True,
        fact_weights={
            "metric": 2.0,
            "decision": 3.0,
            "action_item": 2.5,
            "date": 1.5,
            "number": 0.5,
        },
        coverage_threshold=0.70,
        min_data_points_per_section=2,
    ),
    
    "project_review": TranscriptConfig(
        min_action_length=10,
        min_number_context=6,
        allow_single_digit=True,
        number_tolerance=0.30,
        date_synonym_enabled=True,
        fuzzy_match_enabled=True,
        fact_weights={
            "metric": 2.0,
            "decision": 3.0,
            "action_item": 3.0,
            "date": 1.5,
            "number": 0.5,
        },
        coverage_threshold=0.60,
        min_data_points_per_section=2,
    ),
    
    "general": TranscriptConfig(),
}


def get_config(meeting_type: str) -> TranscriptConfig:
    """根据会议类型获取配置"""
    return MEETING_TYPE_CONFIGS.get(meeting_type, MEETING_TYPE_CONFIGS["general"])


def adjust_config_for_low_coverage(config: TranscriptConfig) -> TranscriptConfig:
    """针对低覆盖率场景调整配置"""
    return TranscriptConfig(
        min_action_length=4,
        min_number_context=2,
        allow_single_digit=True,
        number_tolerance=0.30,
        date_synonym_enabled=True,
        fuzzy_match_enabled=True,
        fact_weights={
            "metric": 2.0,
            "decision": 2.0,
            "action_item": 2.0,
            "date": 1.5,
            "number": 1.0,
        },
        coverage_threshold=0.50,
        min_data_points_per_section=2,
    )


def get_optimization_tips(meeting_type: str) -> List[str]:
    """获取针对特定会议类型的优化建议"""
    tips = {
        "business_review": [
            "确保数据点包含具体数字（如百分比、金额）",
            "结构化输出决策和行动项",
            "使用表格展示对比数据",
        ],
        "product_release": [
            "重点提取产品特性和数据指标",
            "明确上线时间和目标",
            "强调差异化优势",
        ],
        "tech_review": [
            "提取技术指标和性能数据",
            "明确方案对比参数",
            "记录技术决策和风险",
        ],
        "weekly_meeting": [
            "关注任务分配和进度",
            "提取关键数字（如完成量）",
            "明确下周重点",
        ],
        "project_review": [
            "提取项目成果和问题",
            "记录经验教训",
            "明确改进措施",
        ],
    }
    return tips.get(meeting_type, ["提取关键决策和行动项"])
