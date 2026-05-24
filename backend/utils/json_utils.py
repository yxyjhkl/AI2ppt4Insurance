"""Shared JSON & viewport utilities used across the backend."""

import logging

logger = logging.getLogger(__name__)

CANVAS_VIEWBOX = {
    "16:9": (1280, 720),
    "4:3": (960, 720),
    "3:4": (720, 960),
    "1:1": (720, 720),
}

CANVAS_INCHES = {
    "16:9": (13.333, 7.5),
    "4:3": (10.0, 7.5),
    "3:4": (7.5, 10.0),
    "1:1": (8.0, 8.0),
}


def extract_json(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return ""
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return ""


def estimate_slide_count(text: str) -> int:
    char_count = len(text)
    if char_count < 200:
        return 5
    if char_count < 500:
        return 7
    if char_count < 1500:
        return 10
    if char_count < 4000:
        return 14
    if char_count < 8000:
        return 18
    return min(30, max(5, char_count // 400))
