"""Numerical data validator - ensures data accuracy between Excel source and PPT output."""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import logging

from .data_mapper import MappedField

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    passed: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def to_qa_list(self) -> List[Dict[str, Any]]:
        qa = []
        for e in self.errors:
            qa.append({
                "severity": "error",
                "category": "data_validation",
                "slide": e.get("slide", 0),
                "message": e["message"],
                "detail": e.get("detail"),
            })
        for w in self.warnings:
            qa.append({
                "severity": "warning",
                "category": "data_validation",
                "slide": w.get("slide", 0),
                "message": w["message"],
                "detail": w.get("detail"),
            })
        return qa


def validate_numbers(
    mapped: Dict[str, MappedField],
    slides_data: List[Any],
    tolerance: float = 0.001,
) -> ValidationResult:
    result = ValidationResult()
    extracted = _extract_numbers_from_slides(slides_data)

    for field_name, mf in mapped.items():
        if mf.data_type not in ("currency", "number", "integer", "percent"):
            continue

        source_vals = mf.mapped_data.get("numeric_values", [])
        if not source_vals:
            continue

        source_text = _format_source_values(mf, source_vals)
        source_header = f"[Source Excel] {mf.label}"
        result.total_checks += 1

        found = False
        for slide_num, slide_text in extracted.items():
            if source_text and source_text in slide_text:
                found = True
                break

        if not found and source_vals:
            found_in_any = False
            for val in source_vals[:5]:
                if isinstance(val, (int, float)):
                    val_str = f"{val:,.2f}" if mf.data_type != "percent" else f"{val:.2f}%"
                    for slide_num, slide_text in extracted.items():
                        if val_str in slide_text:
                            found_in_any = True
                            break
                if found_in_any:
                    break

            if found_in_any:
                found = True

        if found:
            result.passed_checks += 1
        else:
            result.failed_checks += 1
            val_preview = ", ".join(str(v) for v in source_vals[:3])
            result.warnings.append({
                "slide": 0,
                "field": field_name,
                "message": f"数值 '{mf.label}' 未在PPT中找到匹配",
                "detail": f"源数据: {val_preview}... 请手动核对PPT中的 {mf.label} 数值。",
            })

    for field_name, mf in mapped.items():
        if mf.data_type not in ("currency", "number", "integer", "percent"):
            continue
        source_vals = mf.mapped_data.get("numeric_values", [])
        if not source_vals:
            continue

        ppt_vals = _find_numeric_match(extracted, mf.label, mf.data_type)
        if ppt_vals:
            result.total_checks += 1
            s_sorted = sorted(source_vals)
            p_sorted = sorted(ppt_vals)

            if len(s_sorted) == len(p_sorted):
                all_match = True
                for sv, pv in zip(s_sorted, p_sorted):
                    if abs(sv - pv) > tolerance * max(abs(sv), abs(pv), 1.0):
                        all_match = False
                        break
                if all_match:
                    result.passed_checks += 1
                else:
                    result.failed_checks += 1
                    result.errors.append({
                        "slide": 0,
                        "field": field_name,
                        "message": f"'{mf.label}' 的Excel数据与PPT数据不一致",
                        "detail": f"Excel: {s_sorted[:5]}, PPT: {p_sorted[:5]}",
                    })

    result.passed = result.failed_checks == 0
    return result


def _extract_numbers_from_slides(slides_data: List[Any]) -> Dict[int, str]:
    extracted: Dict[int, str] = {}
    for i, slide in enumerate(slides_data):
        page = getattr(slide, "page_number", i + 1) if hasattr(slide, "page_number") else i + 1
        if isinstance(slide, dict):
            page = slide.get("page_number", i + 1)
        extracted[page] = str(slide)
    return extracted


def _format_source_values(mf: MappedField, values: List[Any]) -> str:
    if not values:
        return ""
    if mf.data_type == "percent":
        return ", ".join(f"{v:.2f}%" for v in values[:3] if isinstance(v, (int, float)))
    elif mf.data_type == "integer":
        return ", ".join(str(int(v)) for v in values[:3] if isinstance(v, (int, float)))
    elif mf.data_type in ("currency", "number"):
        return ", ".join(f"{v:,.2f}" for v in values[:3] if isinstance(v, (int, float)))
    return str(values)


def _find_numeric_match(extracted: Dict[int, str], label: str, data_type: str) -> Optional[List[float]]:
    for slide_num, slide_text in extracted.items():
        pattern = rf"{re.escape(label)}.*?([\d,]+(?:\.\d+)?)"
        matches = re.findall(pattern, slide_text, re.IGNORECASE)
        if matches:
            nums = []
            for m in matches:
                try:
                    nums.append(float(m.replace(",", "")))
                except ValueError:
                    pass
            if nums:
                return nums
    return None