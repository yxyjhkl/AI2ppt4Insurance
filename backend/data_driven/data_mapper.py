"""Column name fuzzy matching and data type conversion engine."""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import yaml
import os
import logging

try:
    from rapidfuzz import fuzz, process
    HAS_FUZZ = True
except ImportError:
    HAS_FUZZ = False

from .excel_parser import ExcelData, SheetData


logger = logging.getLogger(__name__)


@dataclass
class MappedField:
    field_name: str
    label: str
    column_name: str
    column_index: int
    confidence: float
    data_type: str
    mapped_data: Dict[str, Any] = field(default_factory=dict)
    raw_rows: List[Any] = field(default_factory=list)


class DataMapper:
    TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "data_templates")
    SIMILARITY_THRESHOLD = 65

    def __init__(self):
        self._cache: Dict[str, dict] = {}

    def load_template(self, meeting_type: str) -> dict:
        if meeting_type in self._cache:
            return self._cache[meeting_type]
        path = os.path.join(self.TEMPLATE_DIR, f"insurance_{meeting_type}.yaml")
        if not os.path.exists(path):
            msg = f"未找到「{meeting_type}」类型的数据模板。已支持的会议类型: business_review, leadership_instruction, business_launch, product_seminar, entrepreneur_seminar, service_rights, operation_review, business_report, product_training, underperformer_review"
            logger.warning(msg)
            raise ValueError(msg)
        with open(path, "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)
        self._cache[meeting_type] = template
        return template

    def match(self, excel_data: ExcelData, meeting_type: str) -> Tuple[str, Dict[str, MappedField], List[str]]:
        template = self.load_template(meeting_type)
        requirements = template.get("data_requirements", [])
        summary = f"模板: {template.get('label', meeting_type)}, 需要 {len(requirements)} 个字段"

        all_headers = []
        header_map: Dict[str, Tuple[str, int]] = {}
        for sheet in excel_data.sheets:
            for ci, header in enumerate(sheet.headers):
                h_key = f"{sheet.name}:{header}"
                all_headers.append(h_key)
                header_map[h_key] = (header, ci)

        mapped: Dict[str, MappedField] = {}
        warnings: List[str] = []

        for req in requirements:
            field_name = req["field"]
            aliases = req.get("aliases", [req.get("label", field_name)])
            required = req.get("required", False)

            best_match = None
            best_score = 0
            best_h_key = ""

            for h_key in all_headers:
                col_name = header_map[h_key][0]
                if HAS_FUZZ:
                    scores = [fuzz.partial_ratio(alias.lower(), col_name.lower()) for alias in aliases]
                    score = max(scores) if scores else 0
                else:
                    col_lower = col_name.lower()
                    score = 100 if any(alias.lower() in col_lower or col_lower in alias.lower() for alias in aliases) else 0

                if score > best_score:
                    best_score = score
                    best_match = header_map[h_key]
                    best_h_key = h_key

            if best_match and best_score >= self.SIMILARITY_THRESHOLD:
                col_name, col_idx = best_match
                mapped[field_name] = MappedField(
                    field_name=field_name,
                    label=req.get("label", field_name),
                    column_name=col_name,
                    column_index=col_idx,
                    confidence=best_score / 100.0,
                    data_type=req.get("type", "text"),
                )
            elif required and best_match and best_score >= 40:
                col_name, col_idx = best_match
                mapped[field_name] = MappedField(
                    field_name=field_name,
                    label=req.get("label", field_name),
                    column_name=col_name,
                    column_index=col_idx,
                    confidence=best_score / 100.0,
                    data_type=req.get("type", "text"),
                )
                warnings.append(f"低置信度匹配: '{req.get('label', field_name)}' → '{col_name}' (置信度 {best_score}%)")
            elif required:
                warnings.append(f"缺少必填字段: '{req.get('label', field_name)}' (候选列名: {aliases[:3]})")

        return summary, mapped, warnings

    def extract_data(self, excel_data: ExcelData, mapped: Dict[str, MappedField], meeting_type: str = "") -> Dict[str, MappedField]:
        primary_sheet = excel_data.sheets[0] if excel_data.sheets else None
        if not primary_sheet:
            return mapped

        template = self._cache.get(meeting_type, {}) if meeting_type else {}
        if not template and self._cache:
            template = next(iter(self._cache.values()), {})

        for field_name, mf in mapped.items():
            raw_rows = []
            ci = mf.column_index
            for row in primary_sheet.rows:
                if ci < len(row):
                    raw_rows.append(row[ci])
                else:
                    raw_rows.append(None)
            mf.raw_rows = raw_rows

            req = next((r for r in template.get("data_requirements", []) if r["field"] == field_name), {}) if template else {}
            mf.mapped_data = {
                "type": req.get("type", "text"),
                "unit": req.get("unit", ""),
                "maps_to_slide": req.get("maps_to_slide", ""),
                "status_thresholds": req.get("status_thresholds", {}),
            }

            values = [v for v in raw_rows if v is not None and str(v).strip()]
            if mf.data_type in ("currency", "number"):
                parsed = [self._parse_number(v) for v in values]
                mf.mapped_data["numeric_values"] = [p for p in parsed if p is not None]
                if mf.mapped_data["numeric_values"]:
                    nums = mf.mapped_data["numeric_values"]
                    mf.mapped_data["min"] = min(nums)
                    mf.mapped_data["max"] = max(nums)
                    mf.mapped_data["avg"] = round(sum(nums) / len(nums), 2)
            elif mf.data_type == "percent":
                parsed = [self._parse_percent(v) for v in values]
                mf.mapped_data["numeric_values"] = [p for p in parsed if p is not None]
            elif mf.data_type == "integer":
                parsed = [self._parse_number(v) for v in values]
                mf.mapped_data["numeric_values"] = [int(p) for p in parsed if p is not None]

        return mapped

    def build_data_table(self, mapped: Dict[str, MappedField], fields: List[str]) -> str:
        primary_sheet_rows = max((len(mf.raw_rows) for mf in mapped.values()), default=0)
        if primary_sheet_rows == 0:
            return ""

        headers = []
        for field_name in fields:
            mf = mapped.get(field_name)
            headers.append(mf.label if mf else field_name)

        rows_md = []
        for ri in range(primary_sheet_rows):
            row_vals = []
            for field_name in fields:
                mf = mapped.get(field_name)
                if mf and ri < len(mf.raw_rows):
                    val = mf.raw_rows[ri]
                    row_vals.append(str(val) if val is not None else "")
                else:
                    row_vals.append("")
            if any(v.strip() for v in row_vals):
                rows_md.append(row_vals)

        md = "| " + " | ".join(headers) + " |\n"
        md += "|" + "|".join("---" for _ in headers) + "|\n"
        for row in rows_md[:20]:
            md += "| " + " | ".join(row) + " |\n"

        return md

    def _parse_number(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            s = str(val).strip().replace(",", "").replace("，", "").replace(" ", "")
            return float(s)
        except (ValueError, TypeError):
            return None

    def _parse_percent(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            s = str(val).strip().rstrip("%")
            return float(s.replace(",", "").replace("，", ""))
        except (ValueError, TypeError):
            return None