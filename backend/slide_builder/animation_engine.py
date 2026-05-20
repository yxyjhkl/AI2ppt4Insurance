"""OOXML Animation Engine - adds entrance effects and slide transitions to PPTX.

Supports 22 entrance effects and 7 page transitions by manipulating
the underlying PPTX XML directly via lxml.
"""
from __future__ import annotations
import copy
from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn
from typing import Optional

p = "http://schemas.openxmlformats.org/presentationml/2006/main"
a = "http://schemas.openxmlformats.org/drawingml/2006/main"
r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


ENTRANCE_EFFECTS = {
    "fade":        ("fade", "entrance"),
    "flyInBottom": ("flyIn", "entrance", {"from": "b"}),
    "flyInTop":    ("flyIn", "entrance", {"from": "t"}),
    "flyInLeft":   ("flyIn", "entrance", {"from": "l"}),
    "flyInRight":  ("flyIn", "entrance", {"from": "r"}),
    "wipeBottom":  ("wipe", "entrance", {"dir": "b"}),
    "wipeTop":     ("wipe", "entrance", {"dir": "t"}),
    "wipeLeft":    ("wipe", "entrance", {"dir": "l"}),
    "wipeRight":   ("wipe", "entrance", {"dir": "r"}),
    "zoomIn":      ("zoom", "entrance", {"zoomType": "inCenter"}),
    "zoomOut":     ("zoom", "entrance", {"zoomType": "outCenter"}),
    "splitVertIn": ("split", "entrance", {"dir": "verticalIn", "orient": "vertical"}),
    "splitHorizIn":("split", "entrance", {"dir": "horizontalIn", "orient": "horizontal"}),
    "dissolve":    ("dissolve", "entrance"),
    "blindsHoriz": ("blinds", "entrance", {"dir": "horizontal"}),
    "blindsVert":  ("blinds", "entrance", {"dir": "vertical"}),
    "checkerboardAcross": ("checkerboard", "entrance", {"dir": "across"}),
    "checkerboardDown":   ("checkerboard", "entrance", {"dir": "down"}),
    "crawlLeft":   ("crawl", "entrance", {"dir": "l"}),
    "crawlRight":  ("crawl", "entrance", {"dir": "r"}),
    "flashOnce":   ("flashOnce", "entrance"),
    "lightSpeed":  ("lightSpeed", "entrance"),
    "randomBarsHoriz": ("randomBars", "entrance", {"dir": "horizontal"}),
    "randomBarsVert":  ("randomBars", "entrance", {"dir": "vertical"}),
    "shimmer":     ("shimmer", "entrance"),
    "swirl":       ("swirl", "entrance"),
    "wedge":       ("wedge", "entrance"),
    "wheel1":      ("wheel", "entrance", {"spokes": "1"}),
    "wheel4":      ("wheel", "entrance", {"spokes": "4"}),
    "wheel8":      ("wheel", "entrance", {"spokes": "8"}),
    "bounce":      ("bounce", "entrance"),
    "stretch":     ("stretch", "entrance"),
    "curveUp":     ("curveUp", "entrance"),
    "flip":        ("flip", "entrance"),
    "float":       ("float", "entrance"),
    "unfold":      ("unfold", "entrance"),
}

TRANSITION_EFFECTS = {
    "fade":             "fade",
    "pushLeft":         ("push", {"dir": "l"}),
    "pushRight":        ("push", {"dir": "r"}),
    "pushUp":           ("push", {"dir": "u"}),
    "pushDown":         ("push", {"dir": "d"}),
    "wipeLeft":         ("wipe", {"dir": "l"}),
    "wipeRight":        ("wipe", {"dir": "r"}),
    "wipeUp":           ("wipe", {"dir": "u"}),
    "wipeDown":         ("wipe", {"dir": "d"}),
    "splitVertIn":      ("split", {"orient": "vert", "dir": "in"}),
    "splitVertOut":     ("split", {"orient": "vert", "dir": "out"}),
    "splitHorizIn":     ("split", {"orient": "horz", "dir": "in"}),
    "splitHorizOut":    ("split", {"orient": "horz", "dir": "out"}),
    "uncoverLeft":      ("uncover", {"dir": "l"}),
    "uncoverRight":     ("uncover", {"dir": "r"}),
    "uncoverUp":        ("uncover", {"dir": "u"}),
    "uncoverDown":      ("uncover", {"dir": "d"}),
    "coverLeft":        ("cover", {"dir": "l"}),
    "coverRight":       ("cover", {"dir": "r"}),
    "coverUp":          ("cover", {"dir": "u"}),
    "coverDown":        ("cover", {"dir": "d"}),
    "dissolve":         "dissolve",
    "zoomIn":           "zoom",
    "zoomOut":          ("zoom", {"dir": "out"}),
    "fanZoom":          ("zoom", {"dir": "in", "spd": "slow"}),
    "wheel1":           ("wheel", {"spokes": "1"}),
    "wheel4":           ("wheel", {"spokes": "4"}),
    "wheel8":           ("wheel", {"spokes": "8"}),
    "checkerboardAcross": ("checkerboard", {"dir": "across"}),
    "checkerboardDown":   ("checkerboard", {"dir": "down"}),
    "blindsHoriz":      ("blinds", {"dir": "horz"}),
    "blindsVert":       ("blinds", {"dir": "vert"}),
    "diamond":          "diamond",
    "plus":             "plus",
    "wedge":            "wedge",
    "circle":           "circle",
    "ripple":           "ripple",
    "glitterLeft":      ("glitter", {"dir": "l"}),
    "glitterRight":     ("glitter", {"dir": "r"}),
    "glitterTop":       ("glitter", {"dir": "t"}),
    "glitterBottom":    ("glitter", {"dir": "b"}),
    "honeycomb":        "honeycomb",
    "prism":            "prism",
    "doors":            "doors",
    "window":           "window",
    "ferris":           "ferris",
    "gallery":          "gallery",
    "conveyor":         "conveyor",
    "rotate":           "rotate",
    "orbital":          "orbital",
    "flythrough":       "flythrough",
    "shred":            "shred",
    "switch":           "switch",
    "flip":             "flip",
    "morph":            "morph",
    "boomrang":         "boomrang",
    "sparkle":          "sparkle",
    "vortex":           "vortex",
    "origami":          "origami",
    "pan":              "pan",
}


class AnimationEngine:

    def __init__(self, prs: Presentation):
        self.prs = prs
        self.anim_id_counter = 2

    def apply_slide_transition(self, slide_index: int, effect_name: str = "fade",
                               duration: str = "medium", advance_on_click: bool = True,
                               advance_after_ms: Optional[int] = None):
        if slide_index < 0 or slide_index >= len(self.prs.slides):
            return
        slide = self.prs.slides[slide_index]
        sld_elem = slide._element
        nsmap = {"p": p, "a": a, "r": r}

        existing_trans = sld_elem.find(qn("p:transition"))
        if existing_trans is not None:
            sld_elem.remove(existing_trans)
        trans_elem = etree.SubElement(sld_elem, qn("p:transition"))
        trans_elem.set("spd", duration)
        trans_elem.set("advClick", "1" if advance_on_click else "0")
        if advance_after_ms is not None:
            trans_elem.set("advTm", str(advance_after_ms * 1000))

        trans_def = TRANSITION_EFFECTS.get(effect_name)
        if trans_def is None:
            effect_name = "fade"
            trans_def = TRANSITION_EFFECTS["fade"]

        if isinstance(trans_def, str):
            etree.SubElement(trans_elem, qn(f"p:{trans_def}"))
        elif isinstance(trans_def, tuple):
            tag_name = trans_def[0]
            attrs = trans_def[1]
            child = etree.SubElement(trans_elem, qn(f"p:{tag_name}"))
            for k, v in attrs.items():
                child.set(k, v)

    def apply_entrance_to_shape(self, slide_index: int, shape_name: str,
                                effect: str = "fade", duration_ms: int = 500,
                                delay_ms: int = 0):
        if slide_index < 0 or slide_index >= len(self.prs.slides):
            return
        slide = self.prs.slides[slide_index]
        shape_id = self._find_shape_id(slide, shape_name)
        if shape_id is None:
            return
        self._add_animation_to_slide(slide, shape_id, effect, duration_ms, delay_ms)

    def apply_entrance_to_all_shapes(self, slide_index: int, effect: str = "fade",
                                     duration_ms: int = 500, stagger_ms: int = 200):
        if slide_index < 0 or slide_index >= len(self.prs.slides):
            return
        slide = self.prs.slides[slide_index]
        shape_ids = self._get_all_shape_ids(slide)
        for i, sid in enumerate(shape_ids):
            self._add_animation_to_slide(slide, sid, effect, duration_ms, delay_ms=i * stagger_ms)

    def apply_transitions_to_all(self, effect: str = "fade", duration: str = "medium"):
        for i in range(len(self.prs.slides)):
            self.apply_slide_transition(i, effect, duration)

    def _find_shape_id(self, slide, shape_name: str) -> Optional[int]:
        sld_elem = slide._element
        for sp in sld_elem.iter(qn("p:sp")):
            nvsp = sp.find(qn("p:nvSpPr"))
            if nvsp is not None:
                cnv = nvsp.find(qn("p:cNvPr"))
                if cnv is not None and cnv.get("name") == shape_name:
                    nvsp_pr = nvsp.find(qn("p:nvPr"))
                    sp_id = cnv.get("id")
                    if sp_id:
                        return int(sp_id)
        for sp in sld_elem.iter(qn("p:pic")):
            nvpic = sp.find(qn("p:nvPicPr"))
            if nvpic is not None:
                cnv = nvpic.find(qn("p:cNvPr"))
                if cnv is not None and cnv.get("name") == shape_name:
                    sp_id = cnv.get("id")
                    if sp_id:
                        return int(sp_id)
        return None

    def _get_all_shape_ids(self, slide) -> list[int]:
        sld_elem = slide._element
        ids = []
        for tag in (qn("p:sp"), qn("p:pic"), qn("p:grpSp"), qn("p:oleObj"), qn("p:graphicFrame")):
            for elem in sld_elem.iter(tag):
                cnv = elem.find(qn("p:nvSpPr") if tag in (qn("p:sp"),) else qn("p:nvPicPr") if tag == qn("p:pic") else qn("p:nvGrpSpPr") if tag == qn("p:grpSp") else qn("p:nvGraphicFramePr"))
                if cnv is None:
                    continue
                cnv_pr = cnv.find(qn("p:cNvPr")) if cnv is not None else None
                if cnv_pr is not None:
                    sp_id = cnv_pr.get("id")
                    if sp_id:
                        ids.append(int(sp_id))
        return ids

    def _add_animation_to_slide(self, slide, shape_id: int, effect: str,
                                duration_ms: int, delay_ms: int):
        sld_elem = slide._element
        effect_def = ENTRANCE_EFFECTS.get(effect)
        if effect_def is None:
            effect_def = ENTRANCE_EFFECTS["fade"]

        timing = sld_elem.find(qn("p:timing"))
        if timing is None:
            timing = etree.SubElement(sld_elem, qn("p:timing"))
            tn_lst = etree.SubElement(timing, qn("p:tnLst"))
        else:
            tn_lst = timing.find(qn("p:tnLst"))

        if tn_lst is None:
            tn_lst = etree.SubElement(timing, qn("p:tnLst"))

        main_par = tn_lst.find(qn("p:par"))
        if main_par is None:
            main_par = etree.SubElement(tn_lst, qn("p:par"))
            main_ctn = etree.SubElement(main_par, qn("p:cTn"))
            main_ctn.set("id", "1")
            main_ctn.set("dur", str(duration_ms))
            main_ctn.set("fill", "hold")
            st_cond = etree.SubElement(main_ctn, qn("p:stCondLst"))
            cond = etree.SubElement(st_cond, qn("p:cond"))
            cond.set("delay", "0")
            child_tn = etree.SubElement(main_ctn, qn("p:childTnLst"))
        else:
            main_ctn = main_par.find(qn("p:cTn"))
            if main_ctn is None:
                main_ctn = etree.SubElement(main_par, qn("p:cTn"))
                main_ctn.set("id", "1")
                main_ctn.set("dur", str(duration_ms))
                main_ctn.set("fill", "hold")
                st_cond = etree.SubElement(main_ctn, qn("p:stCondLst"))
                cond = etree.SubElement(st_cond, qn("p:cond"))
                cond.set("delay", "0")
                child_tn = etree.SubElement(main_ctn, qn("p:childTnLst"))
            else:
                existing_dur = int(main_ctn.get("dur", "2000"))
                main_ctn.set("dur", str(max(existing_dur, duration_ms + delay_ms)))
                child_tn = main_ctn.find(qn("p:childTnLst"))
                if child_tn is None:
                    child_tn = etree.SubElement(main_ctn, qn("p:childTnLst"))

        anim_elem = etree.SubElement(child_tn, qn("p:anim"))
        anim_elem.set("effect", effect_def[0])
        anim_elem.set("prSet", effect_def[1])

        ctn = etree.SubElement(anim_elem, qn("p:cTn"))
        ctn_id = self.anim_id_counter
        self.anim_id_counter += 1
        ctn.set("id", str(ctn_id))
        ctn.set("dur", str(duration_ms))

        if delay_ms > 0:
            st_cond = etree.SubElement(ctn, qn("p:stCondLst"))
            cond = etree.SubElement(st_cond, qn("p:cond"))
            cond.set("delay", str(delay_ms))

        if len(effect_def) > 2:
            for k, v in effect_def[2].items():
                anim_elem.set(k, v)

        tgt_el = etree.SubElement(anim_elem, qn("p:tgtEl"))
        sp_tgt = etree.SubElement(tgt_el, qn("p:spTgt"))
        sp_tgt.set("spid", str(shape_id))

    def add_motion_path(self, slide_index: int, shape_name: str,
                        path_points: list[tuple[int, int]],
                        duration_ms: int = 2000, delay_ms: int = 0):
        if slide_index < 0 or slide_index >= len(self.prs.slides):
            return
        slide = self.prs.slides[slide_index]
        shape_id = self._find_shape_id(slide, shape_name)
        if shape_id is None:
            return

        sld_elem = slide._element
        timing = sld_elem.find(qn("p:timing"))
        if timing is None:
            timing = etree.SubElement(sld_elem, qn("p:timing"))

        tn_lst = timing.find(qn("p:tnLst"))
        if tn_lst is None:
            tn_lst = etree.SubElement(timing, qn("p:tnLst"))
        if len(tn_lst) == 0:
            main_par = etree.SubElement(tn_lst, qn("p:par"))
            main_ctn = etree.SubElement(main_par, qn("p:cTn"))
            main_ctn.set("id", "1")
            main_ctn.set("dur", str(duration_ms))
            main_ctn.set("fill", "hold")
            st_cond = etree.SubElement(main_ctn, qn("p:stCondLst"))
            cond = etree.SubElement(st_cond, qn("p:cond"))
            cond.set("delay", "0")
            child_tn = etree.SubElement(main_ctn, qn("p:childTnLst"))
        else:
            main_par = tn_lst[0]
            main_ctn = main_par.find(qn("p:cTn"))
            if main_ctn is None:
                return
            existing_dur = int(main_ctn.get("dur", "2000"))
            main_ctn.set("dur", str(max(existing_dur, duration_ms + delay_ms)))
            child_tn = main_ctn.find(qn("p:childTnLst"))
            if child_tn is None:
                child_tn = etree.SubElement(main_ctn, qn("p:childTnLst"))

        anim_motion = etree.SubElement(child_tn, qn("p:animMotion"))
        anim_motion.set("origin", "layout")
        anim_motion.set("path", "lines")
        anim_motion.set("ptType", "relative")

        motion_ctn = etree.SubElement(anim_motion, qn("p:cTn"))
        ctn_id = self.anim_id_counter
        self.anim_id_counter += 1
        motion_ctn.set("id", str(ctn_id))
        motion_ctn.set("dur", str(duration_ms))
        motion_ctn.set("fill", "hold")

        if delay_ms > 0:
            st_cond = etree.SubElement(motion_ctn, qn("p:stCondLst"))
            cond = etree.SubElement(st_cond, qn("p:cond"))
            cond.set("delay", str(delay_ms))

        tgt_el = etree.SubElement(anim_motion, qn("p:tgtEl"))
        sp_tgt = etree.SubElement(tgt_el, qn("p:spTgt"))
        sp_tgt.set("spid", str(shape_id))

        by_elem = etree.SubElement(anim_motion, qn("p:by"))
        by_elem.set("x", "100000")
        by_elem.set("y", "0")
