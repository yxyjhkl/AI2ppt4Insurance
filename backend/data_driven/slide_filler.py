"""Mechanical slide filler - maps data to slide JSON structures without LLM for numerical data.
Only uses LLM for analytical/narrative text generation."""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import os
import yaml

from .data_mapper import DataMapper, MappedField
from .excel_parser import ExcelData

logger = logging.getLogger(__name__)


@dataclass
class FilledSlide:
    layout_type: str
    title: str
    subtitle: Optional[str] = None
    body_items: List[Dict[str, Any]] = None
    tables: List[Dict[str, str]] = None
    notes: str = ""
    page_number: int = 0

    def __post_init__(self):
        if self.body_items is None:
            self.body_items = []
        if self.tables is None:
            self.tables = []


class SlideFiller:
    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir or os.path.join(os.path.dirname(__file__), "data_templates")
        self._template_cache: Dict[str, dict] = {}

    def _load_template(self, meeting_type: str) -> dict:
        if meeting_type in self._template_cache:
            return self._template_cache[meeting_type]
        path = os.path.join(self.template_dir, f"insurance_{meeting_type}.yaml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"数据模板不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)
        self._template_cache[meeting_type] = template
        return template

    def build_slides(
        self,
        meeting_type: str,
        mapped: Dict[str, MappedField],
        excel_data: ExcelData,
        ai_text: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[FilledSlide], Dict[str, Any]]:
        template = self._load_template(meeting_type)
        ai_text = ai_text or {}
        slides: List[FilledSlide] = []
        page = 1

        primary_data = self._get_primary_row(mapped)
        table_data = self._build_table_data(mapped)

        cover = self._build_cover(template, primary_data, page)
        if cover:
            slides.append(cover)
            page += 1

        agenda = self._build_agenda(template, primary_data, page)
        if agenda:
            slides.append(agenda)
            page += 1

        table_slides_cfg = template.get("table_slides", {})
        for ts_key, ts_cfg in table_slides_cfg.items():
            ts = self._build_table_slide(ts_cfg, mapped, table_data, primary_data, page)
            if ts:
                slides.append(ts)
                page += 1

        text_content_fields = [
            f for f in template.get("data_requirements", [])
            if f.get("maps_to_slide", "").startswith("content")
            and f["field"] not in {k for cfg in table_slides_cfg.values() for k in cfg.get("fields", [])}
        ]

        for req in text_content_fields:
            field_name = req["field"]
            slide_layout = req.get("maps_to_slide", "content")
            ai_text_content = ai_text.get(field_name, "")
            raw_value = primary_data.get(field_name, "")

            if ai_text_content or raw_value:
                slides.append(FilledSlide(
                    layout_type=slide_layout if slide_layout.startswith("content") else "content",
                    title=req.get("label", field_name),
                    body_items=[
                        {"type": "list_item", "text": item.strip(), "level": 0}
                        for item in str(ai_text_content or raw_value).split("\n")
                        if item.strip()
                    ][:7],
                    notes="",
                    page_number=page,
                ))
                page += 1

        compare_slides_cfg = template.get("compare_slides", {})
        for cs_key, cs_cfg in compare_slides_cfg.items():
            cs = self._build_compare_slide(cs_cfg, mapped, primary_data, page)
            if cs:
                slides.append(cs)
                page += 1

        ending = self._build_ending(template, primary_data, page)
        if ending:
            slides.append(ending)
            page += 1

        for i, s in enumerate(slides):
            s.page_number = i + 1

        extra_context = {
            "template_label": template.get("label", meeting_type),
            "template_description": template.get("description", ""),
            "table_data": table_data,
            "primary_data": primary_data,
            "fields_with_analysis_needed": [f["field"] for f in text_content_fields],
        }

        return slides, extra_context

    def _get_primary_row(self, mapped: Dict[str, MappedField]) -> Dict[str, Any]:
        primary = {}
        for field_name, mf in mapped.items():
            raw_rows = mf.raw_rows
            primary[field_name] = raw_rows[0] if raw_rows else None
            if mf.data_type in ("currency", "number", "integer", "percent"):
                primary[f"{field_name}_numeric"] = mf.mapped_data.get("numeric_values", [None])[0] if mf.mapped_data.get("numeric_values") else None
                primary[f"{field_name}_min"] = mf.mapped_data.get("min")
                primary[f"{field_name}_max"] = mf.mapped_data.get("max")
                primary[f"{field_name}_avg"] = mf.mapped_data.get("avg")
                primary[f"{field_name}_unit"] = mf.mapped_data.get("unit", "")
        return primary

    def _build_table_data(self, mapped: Dict[str, MappedField]) -> List[Dict[str, Any]]:
        max_rows = max((len(mf.raw_rows) for mf in mapped.values()), default=0)
        rows = []
        for ri in range(max_rows):
            row = {}
            for field_name, mf in mapped.items():
                if ri < len(mf.raw_rows):
                    row[field_name] = mf.raw_rows[ri]
                    row[f"{field_name}_label"] = mf.label
                else:
                    row[field_name] = None
                    row[f"{field_name}_label"] = mf.label
            rows.append(row)
        return rows

    def _build_cover(self, template: dict, primary: dict, page: int) -> Optional[FilledSlide]:
        label = template.get("label", "")
        cover_fields = [f for f in template.get("data_requirements", []) if f.get("maps_to_slide") == "cover"]
        text_parts = []
        for cf in cover_fields:
            val = primary.get(cf["field"])
            if val:
                text_parts.append(f"{cf['label']}: {val}")

        return FilledSlide(
            layout_type="cover",
            title=label,
            subtitle=" | ".join(text_parts) if text_parts else template.get("description", ""),
            page_number=page,
        )

    def _build_agenda(self, template: dict, primary: dict, page: int) -> Optional[FilledSlide]:
        table_slides = template.get("table_slides", {})
        compare_slides = template.get("compare_slides", {})
        items = []
        idx = 1
        for ts_cfg in table_slides.values():
            items.append({"type": "list_item", "text": f"{idx}. {ts_cfg.get('title', '')}", "level": 0})
            idx += 1
        for cs_cfg in compare_slides.values():
            items.append({"type": "list_item", "text": f"{idx}. {cs_cfg.get('title', '')}", "level": 0})
            idx += 1
        if not items:
            return None
        return FilledSlide(
            layout_type="chapter",
            title="会议议程",
            body_items=items,
            page_number=page,
        )

    def _build_table_slide(
        self, cfg: dict, mapped: Dict[str, MappedField],
        table_data: List[Dict[str, Any]], primary: dict, page: int
    ) -> Optional[FilledSlide]:
        fields = cfg.get("fields", [])
        if not fields or not mapped:
            return None

        headers = []
        for fn in fields:
            mf = mapped.get(fn)
            headers.append(mf.label if mf else fn)

        md_rows = []
        for row_data in table_data[:20]:
            row_vals = []
            for fn in fields:
                val = row_data.get(fn)
                if val is not None:
                    mf = mapped.get(fn)
                    if mf and mf.data_type in ("currency", "number") and isinstance(val, (int, float)):
                        row_vals.append(f"{val:,.2f}")
                    elif mf and mf.data_type == "percent" and isinstance(val, (int, float)):
                        row_vals.append(f"{val:.1f}%")
                    else:
                        row_vals.append(str(val))
                else:
                    row_vals.append("")
            if any(v.strip() for v in row_vals):
                rank_field = cfg.get("rank_field", "")
                if not rank_field:
                    for fn in fields:
                        mf = mapped.get(fn)
                        if mf and mf.data_type == "percent" and "_rate" in fn.lower():
                            rank_field = fn
                            break
                status_col = self._get_rank_status(row_data, rank_field)
                if status_col:
                    row_vals[0] = f"{status_col} {row_vals[0]}"
                md_rows.append(row_vals)

        if not md_rows:
            return None

        md = "| " + " | ".join(headers) + " |\n"
        md += "|" + "|".join("---" for _ in headers) + "|\n"
        for row in md_rows:
            md += "| " + " | ".join(row) + " |\n"

        return FilledSlide(
            layout_type="content_table",
            title=cfg.get("title", "数据表"),
            tables=[{"markdown": md}],
            page_number=page,
        )

    def _build_compare_slide(
        self, cfg: dict, mapped: Dict[str, MappedField], primary: dict, page: int
    ) -> Optional[FilledSlide]:
        left_fields = cfg.get("left_fields", [])
        right_fields = cfg.get("right_fields", [])
        left_label = cfg.get("left_label", "左")
        right_label = cfg.get("right_label", "右")

        left_items = []
        for fn in left_fields:
            mf = mapped.get(fn)
            val = primary.get(fn)
            if val:
                left_items.append({"type": "list_item", "text": str(val), "level": 0, "column": "left"})

        right_items = []
        for fn in right_fields:
            mf = mapped.get(fn)
            val = primary.get(fn)
            if val:
                right_items.append({"type": "list_item", "text": str(val), "level": 0, "column": "right"})

        if not left_items and not right_items:
            return None

        return FilledSlide(
            layout_type="content_two_col",
            title=cfg.get("title", "对比"),
            subtitle=f"{left_label} vs {right_label}",
            body_items=left_items + right_items,
            page_number=page,
        )

    def _build_ending(self, template: dict, primary: dict, page: int) -> Optional[FilledSlide]:
        return FilledSlide(
            layout_type="ending",
            title="总结与下一步",
            body_items=[
                {"type": "list_item", "text": "数据驱动决策，持续追踪改善", "level": 0},
                {"type": "list_item", "text": "明确改进方向，落实行动方案", "level": 0},
                {"type": "list_item", "text": "感谢聆听", "level": 0},
            ],
            page_number=page,
        )

    def _get_rank_status(self, row_data: dict, rank_field: str) -> str:
        if not rank_field:
            return ""
        value = row_data.get(rank_field)
        if value is None:
            return ""
        try:
            s = str(value).strip()
            is_pct = s.endswith("%")
            v = float(s.rstrip("%").replace(",", ""))
        except (ValueError, TypeError):
            return ""
        if is_pct:
            if v >= 100:
                return "🟢"
            elif v >= 80:
                return "🟡"
            else:
                return "🔴"
        else:
            if v >= 1000:
                return "🟢"
            elif v >= 500:
                return "🟡"
            else:
                return "🔴"

    def generate_analysis_prompt(self, meeting_type: str, mapped: Dict[str, MappedField],
                                  excel_data: ExcelData, extra_context: dict) -> str:
        template = self._load_template(meeting_type)
        label = template.get("label", meeting_type)
        description = template.get("description", "")

        data_summary_lines = []
        for field_name, mf in mapped.items():
            md = mf.mapped_data
            num_vals = md.get("numeric_values", [])
            if num_vals:
                stats = f"min={md.get('min', 'N/A')}, max={md.get('max', 'N/A')}, avg={md.get('avg', 'N/A')}"
                data_summary_lines.append(
                    f"- {mf.label}: {len(num_vals)}条, {stats} {md.get('unit', '')}"
                )
            else:
                raw_vals = [v for v in mf.raw_rows if v is not None and str(v).strip()][:3]
                data_summary_lines.append(f"- {mf.label}: {', '.join(str(v) for v in raw_vals)}")

        fields_needing_analysis = extra_context.get("fields_with_analysis_needed", [])
        req_map = {r["field"]: r for r in template.get("data_requirements", [])}

        analysis_fields_desc = []
        for fn in fields_needing_analysis:
            req = req_map.get(fn, {})
            analysis_fields_desc.append(f"- {req.get('label', fn)}: {req.get('type', 'text')}")

        prompt = f"""你是一位专业的保险行业数据分析师。请根据以下数据生成PPT中需要的分析性文字。

## 会议类型
{label} - {description}

## 数据概况
{chr(10).join(data_summary_lines)}

## 需要生成分析文字的部分
{chr(10).join(analysis_fields_desc)}

## 输出要求
请为每个需要分析的字段生成一段专业、简洁的分析文字（每段100-200字）。
使用以下JSON格式输出，不要包含```json标记：

{{
  "field_name_1": "分析文字...",
  "field_name_2": "分析文字..."
}}

注意：
1. 只输出分析性文字，不要重复数据表中的数值
2. 分析需要有洞察和观点，而非单纯描述
3. 使用保险行业专业术语
4. 如果数据中有排名信息，请结合排名进行分析
5. 对于问题诊断类字段，请给出根本原因分析和改进建议"""
        return prompt

    def get_fields_needing_llm(self, meeting_type: str) -> List[str]:
        template = self._load_template(meeting_type)
        requirements = template.get("data_requirements", [])
        table_slide_fields = set()
        for ts_cfg in template.get("table_slides", {}).values():
            for f in ts_cfg.get("fields", []):
                table_slide_fields.add(f)
        compare_slide_fields = set()
        for cs_cfg in template.get("compare_slides", {}).values():
            for f in cs_cfg.get("left_fields", []) + cs_cfg.get("right_fields", []):
                compare_slide_fields.add(f)

        llm_fields = []
        for req in requirements:
            fn = req["field"]
            maps_to = req.get("maps_to_slide", "")
            if fn in table_slide_fields or fn in compare_slide_fields:
                continue
            if maps_to.startswith("content"):
                llm_fields.append(fn)
            elif req.get("type") == "text" and not maps_to:
                llm_fields.append(fn)

        return llm_fields