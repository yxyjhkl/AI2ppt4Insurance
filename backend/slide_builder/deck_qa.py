"""整份演示文稿质量检查 —— P0-P3 四级检查体系

检查流程：check_all() 对每页执行单页检查，再对整份文档执行跨页检查
  单页检查（逐页）：P0空页/布局冲突 → P1重复标题/溢出 → P2标题过长/缺备注/低密度 → P3格式建议
  跨页检查（全局）：P1缺封面/结尾 → P1布局多样性 → P1内容节奏

P0（阻断）—— 导出的硬伤，必须修复：
  - 完全空白的幻灯片 → 要么填内容要么删除
  - 仅标题无正文（第2页起） → 可能遗漏了内容
  - 布局与数据不匹配（如表格布局无表格数据、数据布局无数字） → 数据页必须有效数据

P1（严重）—— 导出但带警告：
  - 重复标题 → 观众困惑
  - 单页内容超限（>10项 或 >2000字符） → 文字堆砌
  - 缺少封面/结束页 → 结构不完整
  - 纯文本布局占比>65% → 视觉单调
  - 连续3+页使用content布局 → 节奏疲劳

P2（建议）—— 优化建议：
  - 标题>120字符 → 建议精简
  - 有内容但无演讲备注 → 后续修改困难
  - 内容<30字符的正文页 → 补充数据或案例

P3（润色）—— 锦上添花：
  - 建议使用🟢🟡🔴状态标记或【标签】结构化标注
"""
from __future__ import annotations
import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class QAReport:
    severity: str
    level: str  # P0, P1, P2, P3
    category: str
    slide: int
    message: str
    detail: Optional[str] = None


class DeckQA:
    MAX_TITLE_LENGTH = 120
    MAX_BODY_CHARS = 2000
    MAX_ITEMS_PER_SLIDE = 10
    CONTENT_RATIO_WARN = 0.65

    def check_all(self, slides: list) -> list[dict]:
        if not slides:
            return [{"severity": "error", "level": "P0", "category": "empty_deck",
                      "slide": 0, "message": "幻灯片组为空，无法生成"}]

        reports: list[QAReport] = []
        seen_titles: dict = {}

        for i, slide in enumerate(slides):
            page = i + 1
            self._check_p0_empty(slide, page, reports)
            self._check_p1_duplicate_title(slide, page, seen_titles, reports)
            self._check_p1_overflow(slide, page, reports)
            self._check_p2_title_length(slide, page, reports)
            self._check_p0_layout_conflict(slide, page, reports)
            self._check_p2_missing_notes(slide, page, reports)
            self._check_p2_low_density(slide, page, reports)
            self._check_p3_content_format(slide, page, reports)

        self._check_p1_deck_structure(slides, reports)
        self._check_p1_layout_diversity(slides, reports)
        self._check_p1_content_rhythm(slides, reports)

        return [r.__dict__ if hasattr(r, '__dict__') else r for r in reports]

    def get_p0_count(self, reports: list[dict]) -> int:
        return sum(1 for r in reports if r.get("level") == "P0")

    def get_p1_count(self, reports: list[dict]) -> int:
        return sum(1 for r in reports if r.get("level") == "P1")

    def all_p0_clear(self, reports: list[dict]) -> bool:
        return self.get_p0_count(reports) == 0

    @staticmethod
    def severity_label(level: str) -> str:
        return {"P0": "阻断", "P1": "警告", "P2": "建议", "P3": "优化"}.get(level, level)

    # ===== P0: BLOCKING =====

    def _check_p0_empty(self, slide, page: int, reports: list[QAReport]):
        title = self._safe(slide, "title")
        body = self._safe(slide, "body_items", [])
        img = self._safe(slide, "images", [])
        tbl = self._safe(slide, "tables", [])
        code = self._safe(slide, "code_block")
        has_content = bool(title or body or img or tbl or code)
        if not has_content:
            reports.append(QAReport("error", "P0", "empty_slide", page,
                                     f"第{page}页完全为空，必须删除或填充内容"))
        elif not body and not img and not tbl and not code and page > 1:
            reports.append(QAReport("warning", "P0", "title_only", page,
                                     f"第{page}页仅标题无内容，可能遗漏正文"))

    def _check_p0_layout_conflict(self, slide, page: int, reports: list[QAReport]):
        layout = self._safe(slide, "layout_type", "content")
        code = self._safe(slide, "code_block")
        tables = self._safe(slide, "tables", [])
        if layout == "content_table" and not tables:
            reports.append(QAReport("warning", "P0", "layout_mismatch", page,
                                     f"布局为表格但无表格数据——数据页不能空着"))
        if layout == "content_code" and not code:
            reports.append(QAReport("warning", "P0", "layout_mismatch", page,
                                     f"布局为代码但无代码块——要么填代码要么换布局"))
        if layout in ("content_kpi", "content_gauge", "content_waterfall", "content_ranking", "content_funnel"):
            body = self._safe(slide, "body_items", [])
            body_text = " ".join(self._safe(b, "text", "") for b in body)
            if not re.search(r'\d', body_text):
                reports.append(QAReport("warning", "P0", "missing_numbers", page,
                                         f"数据布局'{layout}'未检测到任何数字——数据页必须有数据"))

    # ===== P1: MAJOR =====

    def _check_p1_duplicate_title(self, slide, page: int, seen: dict, reports: list[QAReport]):
        title = self._safe(slide, "title").lower().strip()
        if not title:
            return
        if title in seen:
            reports.append(QAReport("warning", "P1", "duplicate_title", page,
                                     f"标题在第{seen[title]}页已出现——请区分标题"))
        seen[title] = page

    def _check_p1_overflow(self, slide, page: int, reports: list[QAReport]):
        body = self._safe(slide, "body_items", [])
        total_chars = sum(len(self._safe(b, "text", "")) for b in body)
        if len(body) > self.MAX_ITEMS_PER_SLIDE:
            reports.append(QAReport("warning", "P1", "overflow_items", page,
                                     f"{len(body)}项内容超过{self.MAX_ITEMS_PER_SLIDE}项上限——建议拆分或精简"))
        if total_chars > self.MAX_BODY_CHARS:
            reports.append(QAReport("warning", "P1", "overflow_chars", page,
                                     f"{total_chars}字符超过{self.MAX_BODY_CHARS}上限——文字堆砌影响阅读体验"))

    def _check_p1_deck_structure(self, slides, reports: list[QAReport]):
        if len(slides) < 3:
            reports.append(QAReport("warning", "P1", "too_few", 0,
                                     f"仅{len(slides)}页——演示文稿至少需要3页（封面+内容+结尾）"))
        has_cover = self._safe(slides[0], "layout_type") == "cover" if slides else False
        has_ending = self._safe(slides[-1], "layout_type") == "ending" if slides else False
        if not has_cover:
            reports.append(QAReport("warning", "P1", "missing_cover", 0,
                                     "缺少封面页——第一页应为cover布局"))
        if not has_ending and len(slides) > 2:
            reports.append(QAReport("warning", "P1", "missing_ending", len(slides),
                                     "缺少结束页——最后一页应为ending布局"))

    def _check_p1_layout_diversity(self, slides, reports: list[QAReport]):
        if len(slides) < 5:
            return
        layouts = [self._safe(s, "layout_type", "content") for s in slides]
        content_ratio = layouts.count("content") / len(layouts)
        if content_ratio > self.CONTENT_RATIO_WARN:
            reports.append(QAReport("warning", "P1", "low_diversity", 0,
                                     f"{int(content_ratio*100)}%的幻灯片使用纯文本布局——建议穿插表格/KPI/对比/矩阵丰富视觉"))

    def _check_p1_content_rhythm(self, slides, reports: list[QAReport]):
        layouts = [self._safe(s, "layout_type", "content") for s in slides]
        max_run = 0
        run = 0
        for lt in layouts:
            if lt == "content":
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
        if max_run >= 3:
            reports.append(QAReport("warning", "P1", "content_rhythm", 0,
                                     f"连续{max_run}页使用content布局——穿插其他布局打破视觉疲劳"))

    # ===== P2: MINOR =====

    def _check_p2_title_length(self, slide, page: int, reports: list[QAReport]):
        title = self._safe(slide, "title", "")
        if len(title) > self.MAX_TITLE_LENGTH:
            reports.append(QAReport("info", "P2", "long_title", page,
                                     f"标题{len(title)}字符，建议精简至{self.MAX_TITLE_LENGTH}以内"))

    def _check_p2_missing_notes(self, slide, page: int, reports: list[QAReport]):
        notes = self._safe(slide, "notes", "")
        body = self._safe(slide, "body_items", [])
        if not notes and len(body) >= 2:
            reports.append(QAReport("info", "P2", "missing_notes", page,
                                     "有内容但无演讲备注——添加备注有助于后续修改和讲者准备"))

    def _check_p2_low_density(self, slide, page: int, reports: list[QAReport]):
        body = self._safe(slide, "body_items", [])
        total_chars = sum(len(self._safe(b, "text", "")) for b in body)
        layout = self._safe(slide, "layout_type")
        if total_chars < 30 and len(body) > 0 and layout not in ("cover", "ending", "chapter"):
            reports.append(QAReport("info", "P2", "low_density", page,
                                     f"内容仅{total_chars}字符——建议补充数据或案例"))

    # ===== P3: POLISH =====

    def _check_p3_content_format(self, slide, page: int, reports: list[QAReport]):
        body = self._safe(slide, "body_items", [])
        has_status = any("🟢" in self._safe(b, "text", "") or "🔴" in self._safe(b, "text", "") for b in body)
        has_label = any("【" in self._safe(b, "text", "") and "】" in self._safe(b, "text", "") for b in body)
        if not has_status and not has_label and len(body) >= 3:
            reports.append(QAReport("info", "P3", "format_suggestion", page,
                                     "建议使用🟢🟡🔴状态标记或【标签】结构化标注，提升可读性"))

    @staticmethod
    def _safe(obj, attr, default=""):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
