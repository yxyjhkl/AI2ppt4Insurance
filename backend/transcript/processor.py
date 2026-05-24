"""Transcript Preprocessor — cleans and chunks unstructured meeting transcripts.

Architecture:
  Layer 1: Clean (filler words, merge fragments, extract speakers)
  Layer 2: Pre-extract (regex-based fact extraction before LLM)
  Layer 3: Chunk (overlapping chunks for LLM processing)
  Layer 4a: Score (confidence scoring for extracted data points)
  Layer 4b: Verify (cross-validation of LLM output against pre-extracted facts)
"""
from __future__ import annotations
import re
from typing import Optional
from dataclasses import dataclass, field


FILLER_WORDS_ZH = [
    "嗯", "啊", "哦", "呃", "这个", "那个", "就是说", "然后呢",
    "对吧", "是不是", "那个那个", "这个这个",
]

SPEAKER_PATTERN = re.compile(
    r"(?:^|\n)(说话人[0-9]+|Speaker\s*\d+|([A-Z][a-z]+):|([\u4e00-\u9fa5]{2,4})\s*[:：])"
)

IMPLICIT_SPEAKER_RE = re.compile(
    r'([\u4e00-\u9fa5]{1,2}(?:总|经理|总监|主管|主任|老师|工|哥|姐|董|长))'
    r'(?:说|讲|提到|指出|强调|总结|建议|觉得|认为|要求|特别|表示|'
    r'这边|那边|刚刚|刚才|前面|前面|最后|补充|发言)'
)


@dataclass
class ExtractedFact:
    text: str
    fact_type: str  # "number", "date", "decision", "action_item", "person", "metric"
    value: Optional[str] = None
    context_before: str = ""
    context_after: str = ""
    confidence: float = 1.0
    source: str = "regex"  # "regex" or "llm"
    char_start: int = -1  # original character position in source text
    char_end: int = -1


@dataclass
class TranscriptChunk:
    index: int
    text: str
    start_char: int
    end_char: int
    speaker: str = ""
    topic_hint: str = ""
    pre_extracted_facts: list[ExtractedFact] = field(default_factory=list)


@dataclass
class ProcessedTranscript:
    original_length: int
    cleaned_text: str
    chunks: list[TranscriptChunk]
    all_facts: list[ExtractedFact]
    speakers: list[str]
    estimated_duration_min: int
    meeting_type_hint: str = ""


class TranscriptProcessor:
    MAX_CHUNK_CHARS = 2000
    CHUNK_OVERLAP_CHARS = 200
    MAX_CHUNKS = 20

    NUMBER_PATTERN = re.compile(
        r'([\d,]+\.?\d*)\s*(%|万|亿|元|美元|美金|人|个|件|笔|万元|亿元|百分点)?'
    )
    DATE_PATTERN = re.compile(
        r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?|\d{4}\.\d{1,2}\.\d{1,2}|'
        r'[上下前后]?[一二三四五六七八九十]?[季度月周]|[今明去]年[初中末]?)'
    )
    ACTION_PATTERN = re.compile(
        r'(需要|必须|应该|要|得|计划|安排|落实|推进|完成|负责|由|请)'
        r'[\u4e00-\u9fa5]{3,30}(?:。|，|；|！|\n|$)'
    )
    DECISION_PATTERN = re.compile(
        r'(决定|确定|决议|一致通过|表决|结论是|最终方案)[\u4e00-\u9fa5，、；。！？]{5,60}'
    )

    MEETING_TYPE_HINTS = {
        "复盘": "review",
        "对标": "benchmark",
        "启动": "launch",
        "培训": "training",
        "表彰": "celebration",
        "研讨": "seminar",
        "决策": "decision",
        "周报": "weekly",
        "月度": "monthly",
        "季度": "quarterly",
        "年度": "annual",
        "评审": "assessment",
    }

    def process(self, raw_text: str) -> ProcessedTranscript:
        if not raw_text or not raw_text.strip():
            return ProcessedTranscript(
                original_length=0, cleaned_text="", chunks=[],
                all_facts=[], speakers=[], estimated_duration_min=0,
            )

        original_length = len(raw_text)
        cleaned = self._clean_text(raw_text)
        speakers = self._extract_speakers(raw_text)
        pre_facts = self._regex_extract_facts(cleaned)
        chunks = self._chunk_text(cleaned, pre_facts)
        duration = self._estimate_duration(cleaned)
        meeting_type = self._detect_meeting_type(cleaned)

        return ProcessedTranscript(
            original_length=original_length,
            cleaned_text=cleaned,
            chunks=chunks,
            all_facts=pre_facts,
            speakers=speakers,
            estimated_duration_min=duration,
            meeting_type_hint=meeting_type,
        )

    def _clean_text(self, text: str) -> str:
        for fw in FILLER_WORDS_ZH:
            text = text.replace(fw, "")
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'[。，]{2,}', lambda m: m.group()[0], text)
        text = re.sub(r'([。！？；])([^\n])', r'\1\n\2', text)
        return text.strip()

    def _extract_speakers(self, text: str) -> list[str]:
        speakers = []
        seen = set()
        for line in text.split("\n"):
            m = SPEAKER_PATTERN.match(line.strip())
            if m:
                name = (m.group(1) or m.group(2) or m.group(3) or "").strip().rstrip(":：")
                if name and name not in seen:
                    speakers.append(name)
                    seen.add(name)

        if len(speakers) < 2:
            for m in IMPLICIT_SPEAKER_RE.finditer(text):
                name = m.group(1).strip()
                if name and name not in seen:
                    if not self._is_false_speaker(name):
                        speakers.append(name)
                        seen.add(name)

        unique_names = []
        name_seen = set()
        for s in speakers:
            base = s.rstrip("总经理总监主任工哥姐董长").strip()
            if base not in name_seen:
                unique_names.append(s)
                name_seen.add(base)

        return unique_names[:20]

    @staticmethod
    def _is_false_speaker(name: str) -> bool:
        false_words = ["个", "的", "是", "各", "某", "这", "那", "哪",
                       "该", "本", "前", "后", "上", "下", "大", "小"]
        for fw in false_words:
            if name.startswith(fw):
                return True
        if len(name) > 5:
            return True
        return False

    def _regex_extract_facts(self, text: str) -> list[ExtractedFact]:
        facts: list[ExtractedFact] = []
        seen_actions = set()

        for m in self.NUMBER_PATTERN.finditer(text):
            val = m.group(1)
            unit = m.group(2) or ""
            full = val + unit
            context_before = text[max(0, m.start() - 30):m.start()]
            context_after = text[m.end():min(len(text), m.end() + 30)]
            combined_ctx = context_before + context_after
            
            digits_only = val.replace(',', '').replace('.', '')
            
            if len(digits_only) <= 2 and not unit:
                has_context = any(c in combined_ctx for c in "%%万亿美元元人个股笔年金月周天度期场次")
                if not has_context and len(combined_ctx) < 8:
                    continue
            
            if len(digits_only) <= 1:
                continue
            
            if len(digits_only) >= 3:
                if len(combined_ctx) < 5:
                    continue
            
            facts.append(ExtractedFact(
                text=full, fact_type="metric" if unit else "number",
                value=val, context_before=context_before,
                context_after=context_after,
                confidence=1.0, source="regex",
                char_start=m.start(), char_end=m.end(),
            ))

        for m in self.DATE_PATTERN.finditer(text):
            context_before = text[max(0, m.start() - 20):m.start()]
            context_after = text[m.end():min(len(text), m.end() + 20)]
            facts.append(ExtractedFact(
                text=m.group(0), fact_type="date",
                value=m.group(0), 
                context_before=context_before,
                context_after=context_after,
                confidence=1.0, source="regex",
                char_start=m.start(), char_end=m.end(),
            ))

        for m in self.ACTION_PATTERN.finditer(text):
            action_text = m.group(0).rstrip("。，；！").strip()
            
            if len(action_text) < 8:
                continue
            
            if action_text in seen_actions:
                continue
            seen_actions.add(action_text)
            
            context_before = text[max(0, m.start() - 20):m.start()]
            
            invalid_patterns = ["得这", "要么", "我觉", "我也", "其实", "因为"]
            if any(p in action_text[:4] for p in invalid_patterns):
                continue
            
            if len(action_text) <= 12 and action_text.count(" ") == 0:
                continue
            
            facts.append(ExtractedFact(
                text=action_text, fact_type="action_item",
                context_before=context_before,
                confidence=1.0, source="regex",
                char_start=m.start(), char_end=m.end(),
            ))

        for m in self.DECISION_PATTERN.finditer(text):
            context_before = text[max(0, m.start() - 20):m.start()]
            facts.append(ExtractedFact(
                text=m.group(0), fact_type="decision",
                context_before=context_before,
                confidence=1.0, source="regex",
                char_start=m.start(), char_end=m.end(),
            ))

        return facts

    def _chunk_text(self, text: str, pre_facts: list[ExtractedFact]) -> list[TranscriptChunk]:
        chunks: list[TranscriptChunk] = []
        start = 0
        idx = 0

        while start < len(text) and idx < self.MAX_CHUNKS:
            end = min(start + self.MAX_CHUNK_CHARS, len(text))
            if end < len(text):
                period_pos = text.rfind("。", start, end)
                if period_pos > start + self.MAX_CHUNK_CHARS // 2:
                    end = period_pos + 1
                else:
                    newline_pos = text.rfind("\n", start, end)
                    if newline_pos > start + self.MAX_CHUNK_CHARS // 2:
                        end = newline_pos + 1

            chunk_text = text[start:end].strip()
            chunk_facts = [f for f in pre_facts if self._fact_in_range(f, start, end)]

            chunks.append(TranscriptChunk(
                index=idx, text=chunk_text,
                start_char=start, end_char=end,
                pre_extracted_facts=chunk_facts,
            ))

            start = max(start, end - self.CHUNK_OVERLAP_CHARS)
            idx += 1

        return chunks

    @staticmethod
    def _fact_in_range(fact: ExtractedFact, start: int, end: int) -> bool:
        if fact.char_start >= 0 and fact.char_end >= 0:
            # Fact has known position: check if overlap with [start, end]
            return fact.char_start < end and fact.char_end > start
        # Fallback for facts without position info: conservative inclusion
        return True

    def _estimate_duration(self, text: str) -> int:
        char_count = len(text)
        chars_per_min = 200
        return max(1, char_count // chars_per_min)

    def _detect_meeting_type(self, text: str) -> str:
        search_text = text[:3000]
        for keyword, mtype in self.MEETING_TYPE_HINTS.items():
            if keyword in search_text:
                return mtype
        return "general"

    def verify_llm_output(self, llm_output: str,
                           pre_facts: list[ExtractedFact],
                           verbose: bool = False) -> dict:
        results = {
            "facts_found": 0,
            "facts_missing": 0,
            "facts_excluded": 0,
            "total_regex_facts": len(pre_facts),
            "coverage_ratio": 0.0,
            "hallucination_risks": [],
            "score": 100,
            "match_details": {},
        }

        llm_lower = llm_output.lower()
        llm_normalized = self._normalize_for_match(llm_lower)

        fact_type_weights = {
            "metric": 3.0,
            "decision": 2.5,
            "action_item": 2.0,
            "date": 1.5,
            "number": 0.5,
        }

        weighted_found = 0.0
        weighted_total = 0.0

        if verbose:
            print(f"\n=== 交叉验证开始 ===")
            print(f"预提取事实总数: {len(pre_facts)}")
            print(f"LLM输出长度: {len(llm_output)} 字符")
            print()

        for i, fact in enumerate(pre_facts):
            ft = fact.fact_type
            weight = fact_type_weights.get(ft, 1.0)

            if ft == "number" and not fact.context_before.strip():
                results["facts_excluded"] += 1
                if verbose:
                    print(f"  [排除 {i+1}] [{ft}] '{self._shorten(fact.text, 20)}' - 无上下文")
                continue

            if self._is_isolated_number(fact):
                results["facts_excluded"] += 1
                if verbose:
                    print(f"  [排除 {i+1}] [{ft}] '{self._shorten(fact.text, 20)}' - 孤立数字")
                continue

            weighted_total += weight

            if verbose:
                print(f"\n  [事实 {i+1}] [{ft}] '{self._shorten(fact.text, 30)}'")
                print(f"     值: '{fact.value or ''}'")
                print(f"     上下文前: '{self._shorten(fact.context_before, 30)}'")
                print(f"     匹配过程:")

            if self._fact_matches(fact, llm_lower, llm_normalized, verbose=verbose):
                results["facts_found"] += 1
                weighted_found += weight
            else:
                results["facts_missing"] += 1
                if results["facts_missing"] <= 8:
                    results["hallucination_risks"].append(
                        f"Missing fact: '{self._shorten(fact.text, 30)}' "
                        f"(type={ft}, ctx={self._shorten(fact.context_before, 20)})"
                    )

        effective_total = results["total_regex_facts"] - results["facts_excluded"]
        if effective_total > 0:
            results["coverage_ratio"] = results["facts_found"] / effective_total
        if weighted_total > 0:
            results["weighted_coverage"] = weighted_found / weighted_total

        coverage = results["coverage_ratio"]
        weighted_cov = results.get("weighted_coverage", coverage)

        if coverage < 0.40:
            results["score"] -= 35
            results["hallucination_risks"].append(
                f"Critical: only {coverage:.0%} of facts found in LLM output"
            )
        elif coverage < 0.55:
            results["score"] -= 20
        elif coverage < 0.70:
            results["score"] -= 10

        if weighted_cov and weighted_cov >= 0.80:
            results["score"] = min(100, results["score"] + 5)

        return results

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        import re
        text = re.sub(r'\s+', '', text)
        text = text.replace(',', '').replace('，', '')
        return text

    @staticmethod
    def _is_isolated_number(fact: ExtractedFact) -> bool:
        if fact.fact_type != "number":
            return False
        ctx = (fact.context_before + fact.context_after).strip()
        if len(ctx) < 5:
            return True
        if not any(c in ctx for c in "%%万亿美元元人个股笔年金月周天度期"):
            if len(fact.text.replace(',', '').replace('.', '')) <= 2:
                return True
        return False

    def _fact_matches(self, fact: ExtractedFact,
                       llm_lower: str, llm_normalized: str,
                       verbose: bool = False) -> bool:
        text_lower = fact.text.lower()
        text_normalized = self._normalize_for_match(text_lower)
        value = (fact.value or "").lower()
        fact_str = f"[{fact.fact_type}] '{self._shorten(fact.text, 20)}'"

        if fact.fact_type in ("metric",):
            if value and value in llm_lower:
                if verbose:
                    print(f"  ✅ {fact_str} → 精确匹配 (value='{value}')")
                return True
            if value and self._num_in_range(value, llm_normalized, tolerance=0):
                if verbose:
                    print(f"  ✅ {fact_str} → 数值范围匹配 (value='{value}')")
                return True
            if verbose:
                print(f"  ❌ {fact_str} → metric匹配失败")

        if fact.fact_type == "number":
            if value:
                if value in llm_lower:
                    if verbose:
                        print(f"  ✅ {fact_str} → 数字精确匹配 (value='{value}')")
                    return True
                
                digits_only = value.replace(',', '').replace('.', '').replace('，', '')
                if len(digits_only) >= 2:
                    if self._match_number_range(value, llm_normalized):
                        if verbose:
                            print(f"  ✅ {fact_str} → 数字区间匹配 (±20%)")
                        return True
                
                if digits_only in llm_normalized:
                    if verbose:
                        print(f"  ✅ {fact_str} → 纯数字匹配 ('{digits_only}')")
                    return True
                
                text_clean = text_lower.replace(',', '').replace('，', '').replace('.', '')
                if text_clean in llm_normalized:
                    if verbose:
                        print(f"  ✅ {fact_str} → 清理后匹配 ('{text_clean}')")
                    return True
            
            if text_lower in llm_lower:
                if verbose:
                    print(f"  ✅ {fact_str} → 文本直接匹配")
                return True
            
            if verbose:
                print(f"  ❌ {fact_str} → number匹配失败")
            return False

        if fact.fact_type == "date":
            if text_lower in llm_lower:
                if verbose:
                    print(f"  ✅ {fact_str} → 日期精确匹配")
                return True
            if value and value in llm_lower:
                if verbose:
                    print(f"  ✅ {fact_str} → 日期值匹配 ('{value}')")
                return True
            
            parts = re.findall(r'\d+', text_lower)
            if parts:
                for p in parts:
                    if p in llm_normalized:
                        if verbose:
                            print(f"  ✅ {fact_str} → 日期数字匹配 ('{p}')")
                        return True
            
            if self._match_date_semantics(text_lower, llm_lower):
                if verbose:
                    print(f"  ✅ {fact_str} → 日期语义匹配")
                return True
            
            if verbose:
                print(f"  ❌ {fact_str} → date匹配失败")
            return False

        if fact.fact_type in ("decision", "action_item"):
            keywords = fact.text[:8] if len(fact.text) > 8 else fact.text
            if keywords.lower() in llm_lower:
                if verbose:
                    print(f"  ✅ {fact_str} → 关键词匹配 ('{keywords}')")
                return True
            if len(fact.text) >= 6:
                for i in range(0, len(fact.text) - 5, 3):
                    chunk = fact.text[i:i + 6]
                    if chunk.lower() in llm_lower:
                        if verbose:
                            print(f"  ✅ {fact_str} → 片段匹配 ('{chunk}')")
                        return True
            
            clean_text = self._clean_action_text(fact.text)
            if clean_text and clean_text.lower() in llm_lower:
                if verbose:
                    print(f"  ✅ {fact_str} → 清理后行动项匹配 ('{clean_text}')")
                return True
            
            ctx_keywords = self._extract_context_keywords(fact.context_before)
            if ctx_keywords:
                for kw in ctx_keywords[:3]:
                    if kw.lower() in llm_lower:
                        if verbose:
                            print(f"  ✅ {fact_str} → 上下文关键词匹配 ('{kw}')")
                        return True
            
            if verbose:
                print(f"  ❌ {fact_str} → action_item/decision匹配失败")
            return False

        if text_lower in llm_lower:
            if verbose:
                print(f"  ✅ {fact_str} → 默认文本匹配")
            return True
        if verbose:
            print(f"  ❌ {fact_str} → 所有规则均未匹配")
        return False

    @staticmethod
    def _num_in_range(value: str, target: str, tolerance: int = 0) -> bool:
        try:
            v = float(value.replace(',', '').replace('，', ''))
        except ValueError:
            return False
        for m in re.finditer(r'[\d,]+\.?\d*', target):
            try:
                t = float(m.group().replace(',', '').replace('，', ''))
                if abs(v - t) <= tolerance * max(1, v / 100):
                    return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _shorten(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len - 2] + ".."

    @staticmethod
    def _match_date_semantics(date_text: str, llm_text: str) -> bool:
        date_mappings = {
            "一周": ["本周", "这周", "这一周", "7天", "七天", "本星期"],
            "下一周": ["下周", "下星期", "下个星期", "下周", "下周开始"],
            "明天": ["明日", "明天", "明日开始"],
            "今天": ["今日", "今天", "今日开始"],
            "昨天": ["昨日", "昨天", "昨日"],
            "本月": ["这个月", "本月", "当月", "本月底"],
            "下月": ["下个月", "下月", "下月", "下月初"],
            "今年": ["本年度", "今年", "今年", "本年度内"],
            "明年": ["下年度", "明年", "明年", "下年度内"],
            "上半年": ["上半年度", "上半年", "1-6月"],
            "下半年": ["下半年度", "下半年", "7-12月"],
            "上旬": ["上半月", "月初", "1-10日"],
            "中旬": ["月中", "11-20日"],
            "下旬": ["下半月", "月末", "21-31日"],
        }
        
        for original, alternatives in date_mappings.items():
            if original in date_text:
                for alt in alternatives:
                    if alt in llm_text:
                        return True
        
        week_patterns = ["一周", "星期", "礼拜", "周"]
        week_found_in_date = any(p in date_text for p in week_patterns)
        week_found_in_llm = any(p in llm_text for p in week_patterns)
        if week_found_in_date and week_found_in_llm:
            return True
        
        month_patterns = ["月", "月份"]
        month_found_in_date = any(p in date_text for p in month_patterns)
        month_found_in_llm = any(p in llm_text for p in month_patterns)
        if month_found_in_date and month_found_in_llm:
            return True
        
        date_nums = re.findall(r'\d+', date_text)
        for num in date_nums:
            if num in llm_text:
                return True
        
        return False

    @staticmethod
    def _match_number_range(fact_value: str, llm_normalized: str) -> bool:
        try:
            val = float(fact_value.replace(',', '').replace('，', ''))
        except ValueError:
            return False
        
        for m in re.finditer(r'[\d,]+(?:\.\d+)?', llm_normalized):
            try:
                llm_num = float(m.group().replace(',', '').replace('，', ''))
                tolerance = 0.2
                if abs(val - llm_num) / max(1, abs(val)) <= tolerance:
                    return True
            except ValueError:
                continue
        
        if val >= 100:
            for m in re.finditer(r'[\d,]+', llm_normalized):
                try:
                    llm_num = float(m.group().replace(',', ''))
                    if abs(val - llm_num) <= 50:
                        return True
                except ValueError:
                    continue
        
        return False

    @staticmethod
    def _clean_action_text(text: str) -> str:
        text = text.replace("要", "").replace("需要", "").replace("得", "")
        text = text.replace("一下", "").replace("一下下", "")
        text = text.replace("做", "").replace("进行", "").replace("实施", "")
        text = text.replace("评估", "").replace("优化", "").replace("改进", "")
        text = text.replace("。", "").replace("，", "").replace("；", "")
        text = text.replace("的", "").strip()
        return text if len(text) >= 3 else ""

    @staticmethod
    def _extract_context_keywords(context: str) -> list[str]:
        if not context:
            return []
        keywords = []
        important_words = ["网点", "经理", "总监", "总", "客户", "产品",
                          "业绩", "目标", "任务", "指标", "会议", "活动",
                          "增员", "人力", "问责", "进度", "推动", "策略"]
        for word in important_words:
            if word in context:
                keywords.append(word)
        return keywords

    def build_llm_prompt(self, transcript: ProcessedTranscript) -> str:
        facts_summary = []
        by_type: dict[str, list[str]] = {}
        for f in transcript.all_facts[:30]:
            by_type.setdefault(f.fact_type, []).append(f.text)

        for ftype, items in by_type.items():
            label = {
                "number": "数据点", "metric": "指标", "date": "时间",
                "action_item": "待办事项", "decision": "决策",
            }.get(ftype, ftype)
            facts_summary.append(f"**{label}**: " + ", ".join(items[:8]))

        chunks_text = "\n\n---\n\n".join(
            f"## 段落 {ch.index + 1}\n{ch.text}"
            for ch in transcript.chunks
        )

        prompt = f"""<task>
你是一位专业的会议记录分析师。请从以下会议转录文字中提取结构化内容。
会议时长约 {transcript.estimated_duration_min} 分钟，共有 {len(transcript.speakers)} 位发言人。

<pre_extracted_facts>
系统已从原文中预提取了以下关键信息（置信度100%），请务必在输出中引用这些数据：
{chr(10).join(facts_summary) if facts_summary else "（未预提取到数据点）"}
</pre_extracted_facts>

<transcript>
{chunks_text[:6000]}
</transcript>

<output_format>
请严格按照以下JSON格式输出，不要输出其他内容：
{{
  "title": "会议主题（15字以内）",
  "subtitle": "副标题/日期",
  "sections": [
    {{
      "topic": "议题名称",
      "key_points": ["核心观点1", "核心观点2"],
      "data_points": [{{"label": "指标名", "value": "数值"}}],
      "decisions": ["决策1"],
      "action_items": [{{"owner": "负责人", "task": "任务描述", "deadline": "截止时间"}}],
      "suggested_layout": "content|content_kpi|content_table|content_compare"
    }}
  ],
  "summary": "一句话总结（30字以内）",
  "next_steps": ["下一步1", "下一步2"]
}}
</output_format>

<guidelines>
1. 优先使用 <pre_extracted_facts> 中的数据，不要编造新数据
2. 每个 section 的 key_points 不超过 3 条
3. suggested_layout: 有≥3个数据点→content_kpi，有数值对比→content_compare，纯列表→content_two_col，其他→content
4. 保持语言简洁，会议主题级别的内容
</guidelines>
</task>"""
        return prompt