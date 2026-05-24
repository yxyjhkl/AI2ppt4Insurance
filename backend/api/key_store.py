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

    key_b64 = os.environ.get(KEY_ENV_VAR)
    if key_b64:
        try:
            _encryption_key = base64.urlsafe_b64decode(key_b64.encode())
            return _encryption_key
        except Exception:
            logger.warning("Failed to decode encryption key from environment variable")

    key_file = _get_store_path().parent / "encryption_key.key"
    if key_file.exists():
        try:
            with open(key_file, "rb") as f:
                _encryption_key = f.read()
            return _encryption_key
        except Exception:
            logger.warning("Failed to read existing encryption key file")

    try:
        from cryptography.fernet import Fernet
        _encryption_key = Fernet.generate_key()
    except ImportError:
        logger.error(
            "cryptography package is REQUIRED for API key encryption. "
            "Install with: pip install cryptography"
        )
        raise RuntimeError(
            "cryptography package is required for API key storage security. "
            "Install with: pip install cryptography"
        )

    try:
        with open(key_file, "wb") as f:
            f.write(_encryption_key)
        if os.name != "nt":
            os.chmod(key_file, 0o600)
    except Exception as e:
        logger.error(f"Failed to write encryption key file: {e}")
        raise

    return _encryption_key


def _encrypt_data(data: str) -> str:
    """Encrypt data using the encryption key."""
    from cryptography.fernet import Fernet
    key = _get_or_create_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def _decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using the encryption key."""
    from cryptography.fernet import Fernet
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    except Exception:
        logger.warning("Failed to decode encrypted data from base64")
        return ""

    key = _get_or_create_key()
    try:
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception:
        logger.warning("Failed to decrypt data - key may have changed or data is corrupted")
        return ""


def _save_store():
    """Save the API key store to encrypted file."""
    try:
        data_json = json.dumps(_api_key_store)
        encrypted = _encrypt_data(data_json)
        store_path = _get_store_path()

        with open(store_path, "w", encoding="utf-8") as f:
            f.write(encrypted)

        if os.name != "nt":
            os.chmod(store_path, 0o600)
    except Exception as e:
        logger.error(f"Failed to save encrypted API key store: {e}")


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
        if not decrypted:
            logger.warning("Decrypted store is empty - encryption key may have changed")
            return

        loaded = json.loads(decrypted)

        if isinstance(loaded, dict):
            _api_key_store = loaded
        else:
            logger.warning(f"Loaded store is not a dict: {type(loaded)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API key store JSON: {e}")
    except Exception as e:
        logger.error(f"Failed to load API key store: {e}")


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
