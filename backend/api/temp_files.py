"""Temporary file management for PPTX downloads."""
from __future__ import annotations
import os
import time
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from fastapi import HTTPException


# 全局临时文件存储
_temp_files: dict[str, dict] = {}
_temp_dir: Optional[Path] = None


def get_temp_dir() -> Path:
    """Get or create the temporary directory for generated files."""
    global _temp_dir
    if _temp_dir is not None and _temp_dir.exists():
        return _temp_dir
    
    # 尝试在多个位置创建临时目录
    candidates = []
    
    # 1. 应用数据目录
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.name == "darwin":  # macOS
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    candidates.append(base / "InsurDeck" / "temp")
    
    # 2. 系统临时目录
    candidates.append(Path(tempfile.gettempdir()) / "InsurDeck")
    
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            # 测试写入权限
            test_file = candidate / ".test"
            test_file.touch()
            test_file.unlink()
            _temp_dir = candidate
            return _temp_dir
        except Exception:
            continue
    
    raise RuntimeError("Could not create temporary directory")


def store_temp_file(data: bytes, filename: str = "output.pptx") -> str:
    """
    Store binary data as a temporary file and return a file ID.
    
    Args:
        data: Binary file content
        filename: Suggested filename for download
        
    Returns:
        File ID for retrieval
    """
    cleanup_old_files()
    
    file_id = str(uuid.uuid4())
    temp_dir = get_temp_dir()
    file_path = temp_dir / file_id
    
    with open(file_path, "wb") as f:
        f.write(data)
    
    _temp_files[file_id] = {
        "path": file_path,
        "filename": filename,
        "created_at": time.time(),
        "accessed_at": time.time()
    }
    
    return file_id


def get_temp_file(file_id: str) -> tuple[Path, str]:
    """
    Retrieve a temporary file by ID.
    
    Args:
        file_id: The file ID returned from store_temp_file
        
    Returns:
        Tuple of (file_path, original_filename)
        
    Raises:
        HTTPException: If file not found
    """
    if file_id not in _temp_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = _temp_files[file_id]
    file_path = file_info["path"]
    
    if not file_path.exists():
        del _temp_files[file_id]
        raise HTTPException(status_code=404, detail="File not found")
    
    # 更新访问时间
    file_info["accessed_at"] = time.time()
    
    return file_path, file_info["filename"]


def delete_temp_file(file_id: str):
    """Delete a temporary file by ID."""
    if file_id in _temp_files:
        file_info = _temp_files[file_id]
        try:
            Path(file_info["path"]).unlink(missing_ok=True)
        except Exception:
            pass
        del _temp_files[file_id]


def cleanup_old_files(max_age_seconds: float = 3600):
    """Clean up temporary files older than max_age_seconds (default 1 hour)."""
    current_time = time.time()
    expired_ids = []
    
    for file_id, file_info in _temp_files.items():
        if current_time - file_info["created_at"] > max_age_seconds:
            expired_ids.append(file_id)
    
    for file_id in expired_ids:
        delete_temp_file(file_id)
    
    # 也检查磁盘上的孤立文件
    try:
        temp_dir = get_temp_dir()
        for item in temp_dir.iterdir():
            if item.is_file() and item.name not in _temp_files:
                # 检查文件年龄
                if current_time - item.stat().st_mtime > max_age_seconds:
                    try:
                        item.unlink()
                    except Exception:
                        pass
    except Exception:
        pass


# 启动时进行一次清理
try:
    cleanup_old_files()
except Exception:
    pass
