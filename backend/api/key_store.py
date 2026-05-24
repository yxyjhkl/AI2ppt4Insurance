"""Server-side secure API key store (never logged, never sent to frontend)."""
from __future__ import annotations
import os
import json
import base64
import logging
from pathlib import Path
from typing import Optional

# Import config loader
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_api_keys_from_config
except ImportError:
    get_api_keys_from_config = lambda: {}

logger = logging.getLogger(__name__)

# 优先使用环境变量中的密钥，否则生成并存储
KEY_ENV_VAR = "InsurDeck_ENCRYPTION_KEY"
STORE_FILENAME = "api_keys.enc"

_encryption_key: Optional[bytes] = None
_api_key_store: dict[str, dict[str, str]] = {}


def _get_store_path() -> Path:
    """Get the path to the encrypted storage file."""
    # 尝试找到用户数据目录
    if os.name == "nt":  # Windows
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.name == "darwin":  # macOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux
        base_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    
    store_dir = base_dir / "InsurDeck"
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir / STORE_FILENAME


def _get_or_create_key() -> bytes:
    """Get encryption key from env or generate and store a new one."""
    global _encryption_key
    
    if _encryption_key is not None:
        return _encryption_key
    
    # 尝试从环境变量获取
    key_b64 = os.environ.get(KEY_ENV_VAR)
    if key_b64:
        try:
            _encryption_key = base64.urlsafe_b64decode(key_b64.encode())
            return _encryption_key
        except Exception:
            pass
    
    # 尝试从密钥文件加载
    key_file = _get_store_path().parent / "encryption_key.key"
    if key_file.exists():
        try:
            with open(key_file, "rb") as f:
                _encryption_key = f.read()
            return _encryption_key
        except Exception:
            pass
    
    # 生成新密钥
    try:
        from cryptography.fernet import Fernet
        _encryption_key = Fernet.generate_key()
    except ImportError:
        # Fallback: use simple base64 encoding (not secure, but better than nothing)
        import secrets
        _encryption_key = secrets.token_urlsafe(32).encode()
        logger.warning(
            "cryptography package not installed - API keys will use weak XOR obfuscation. "
            "Install with: pip install cryptography"
        )
    
    # 保存密钥
    try:
        with open(key_file, "wb") as f:
            f.write(_encryption_key)
        # 限制文件权限
        if os.name != "nt":
            os.chmod(key_file, 0o600)
    except Exception:
        pass
    
    return _encryption_key


def _encrypt_data(data: str) -> str:
    """Encrypt data using the encryption key."""
    key = _get_or_create_key()
    
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except ImportError:
        # Fallback: simple XOR encoding (not secure, but better than plaintext)
        key_bytes = key[:32] if len(key) >= 32 else key.ljust(32, b'\0')
        data_bytes = data.encode()
        encrypted = bytes([a ^ b for a, b in zip(data_bytes, key_bytes * (len(data_bytes) // 32 + 1))])
        return base64.urlsafe_b64encode(encrypted).decode()


def _decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using the encryption key."""
    key = _get_or_create_key()
    
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    except Exception:
        return ""
    
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except ImportError:
        # Fallback: simple XOR decoding
        key_bytes = key[:32] if len(key) >= 32 else key.ljust(32, b'\0')
        decrypted = bytes([a ^ b for a, b in zip(encrypted_bytes, key_bytes * (len(encrypted_bytes) // 32 + 1))])
        try:
            return decrypted.decode()
        except Exception:
            return ""


def _save_store():
    """Save the API key store to encrypted file."""
    try:
        data_json = json.dumps(_api_key_store)
        encrypted = _encrypt_data(data_json)
        store_path = _get_store_path()
        
        with open(store_path, "w", encoding="utf-8") as f:
            f.write(encrypted)
        
        # 限制文件权限
        if os.name != "nt":
            os.chmod(store_path, 0o600)
    except Exception:
        pass


def _load_store():
    """Load the API key store from encrypted file."""
    global _api_key_store
    
    try:
        store_path = _get_store_path()
        if not store_path.exists():
            return
        
        with open(store_path, "r", encoding="utf-8") as f:
            encrypted = f.read()
        
        decrypted = _decrypt_data(encrypted)
        loaded = json.loads(decrypted)
        
        if isinstance(loaded, dict):
            _api_key_store = loaded
    except Exception:
        pass


def _merge_config_keys():
    """Merge API keys from config file into store (only if not already present)."""
    try:
        config_keys = get_api_keys_from_config()
        if config_keys:
            for model_id, key_info in config_keys.items():
                if model_id not in _api_key_store:
                    # Only add if not already in encrypted store
                    _api_key_store[model_id] = key_info
                    logger.debug(f"Loaded default API key for {model_id} from config")
    except Exception as e:
        logger.debug(f"Failed to load config keys: {e}")


# 初始化时加载存储
_load_store()
_merge_config_keys()


def set_api_key(model_id: str, api_key: str, base_url: str | None = None):
    _api_key_store[model_id] = {"api_key": api_key, "base_url": base_url or ""}
    _save_store()


def get_api_key(model_id: str) -> dict[str, str]:
    return _api_key_store.get(model_id, {"api_key": "", "base_url": ""})


def delete_api_key(model_id: str) -> bool:
    if model_id in _api_key_store:
        del _api_key_store[model_id]
        _save_store()
        return True
    return False


def list_model_ids() -> list[str]:
    return list(_api_key_store.keys())
