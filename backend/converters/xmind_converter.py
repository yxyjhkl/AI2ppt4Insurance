"""XMind to Markdown converter - extracts mind map structure from .xmind files."""
import zipfile
import json
import os

MAX_XMIND_SIZE = 50 * 1024 * 1024  # 50MB
MAX_DECOMPRESSED_SIZE = 100 * 1024 * 1024  # 100MB


def _safe_zip_read(zf: zipfile.ZipFile, name: str) -> bytes:
    """Read a zip member safely, checking size to prevent ZIP bombs."""
    info = zf.getinfo(name)
    if info.file_size > MAX_DECOMPRESSED_SIZE:
        raise ValueError(f"XMind content too large: {info.file_size} bytes (max {MAX_DECOMPRESSED_SIZE})")
    return zf.read(name)


def _check_file_size(filepath: str) -> None:
    if os.path.getsize(filepath) > MAX_XMIND_SIZE:
        raise ValueError(f"XMind file too large: {os.path.getsize(filepath)} bytes (max {MAX_XMIND_SIZE})")


def xmind_to_markdown(filepath: str) -> str:
    """Convert XMind file to markdown outline format."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    _check_file_size(filepath)

    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            if 'content.json' in zf.namelist():
                content = json.loads(_safe_zip_read(zf, 'content.json'))
                return _parse_json_content(content)
            # Try content.xml (older XMind 8)
            if 'content.xml' in zf.namelist():
                return _parse_xml_content(_safe_zip_read(zf, 'content.xml'))
            raise ValueError("Unsupported XMind format: no content.json or content.xml found")
    except zipfile.BadZipFile:
        raise ValueError("Invalid XMind file: not a valid ZIP archive")


def _parse_json_content(data) -> str:
    """Parse XMind JSON content format."""
    lines = []
    root = data[0] if isinstance(data, list) else data
    root_topic = root.get('rootTopic', {})
    
    title = root_topic.get('title', '未命名')
    lines.append(f"# {title}")
    
    children = root_topic.get('children', {})
    if isinstance(children, dict):
        attached = children.get('attached', [])
        for child in attached:
            _extract_topic(child, lines, level=2)
    
    return "\n".join(lines)


def _extract_topic(topic: dict, lines: list, level: int):
    """Recursively extract topic hierarchy."""
    title = topic.get('title', '')
    if not title:
        return
    
    prefix = '#' * min(level, 6)
    lines.append(f"{prefix} {title}")
    
    children = topic.get('children', {})
    if isinstance(children, dict):
        attached = children.get('attached', [])
        for child in attached:
            _extract_topic(child, lines, level + 1)


def _parse_xml_content(xml_bytes: bytes) -> str:
    """Parse older XMind XML format."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_bytes)
    except ImportError:
        return "XML parsing requires elementtree module"
    
    lines = []
    ns = {'xmap': 'urn:xmind:xmap:xmlns:content:2.0'}
    
    sheet = root.find('.//xmap:sheet', ns) or root.find('.//sheet')
    if sheet is None:
        return "No sheet found in XMind XML"
    
    title_elem = sheet.find('.//xmap:title', ns) or sheet.find('.//title')
    title = title_elem.text if title_elem is not None and title_elem.text else '未命名'
    lines.append(f"# {title}")
    
    topic = sheet.find('.//xmap:topic', ns) or sheet.find('.//topic')
    if topic is not None:
        _extract_xml_topics(topic, lines, level=2, ns=ns)
    
    return "\n".join(lines)


def _extract_xml_topics(topic, lines: list, level: int, ns: dict):
    """Recursively extract XML topic hierarchy."""
    title_elem = topic.find('xmap:title', ns) or topic.find('title')
    if title_elem is not None and title_elem.text:
        prefix = '#' * min(level, 6)
        lines.append(f"{prefix} {title_elem.text.strip()}")
    
    children = topic.find('xmap:children', ns) or topic.find('children')
    if children is not None:
        topics = children.findall('xmap:topics', ns) or children.findall('topics')
        for topics_elem in topics:
            for child in topics_elem.findall('xmap:topic', ns) or topics_elem.findall('topic'):
                _extract_xml_topics(child, lines, level + 1, ns)
