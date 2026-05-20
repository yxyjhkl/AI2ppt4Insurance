from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import asyncio

router = APIRouter()


class ConfigureKeyRequest(BaseModel):
    model_id: str
    api_key: str
    base_url: str = ""


class ConfigureKeyResponse(BaseModel):
    ok: bool
    message: str


@router.post("/configure", response_model=ConfigureKeyResponse)
async def configure_api_key(payload: ConfigureKeyRequest):
    from api.key_store import set_api_key
    if not payload.api_key:
        return ConfigureKeyResponse(ok=False, message="API Key 不能为空")
    set_api_key(payload.model_id, payload.api_key, payload.base_url)
    return ConfigureKeyResponse(ok=True, message=f"模型 {payload.model_id} 的 API Key 已安全存储")


class CheckOllamaResponse(BaseModel):
    available: bool
    models: List[str] = []


class ProviderListResponse(BaseModel):
    providers: list


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers():
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-opus-4", "claude-sonnet-4", "claude-haiku-3.5"]},
            {"id": "gemini", "name": "Google Gemini", "models": ["gemini-2.5-pro", "gemini-2.5-flash"]},
            {"id": "deepseek", "name": "DeepSeek", "models": ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"]},
            {"id": "qwen", "name": "Qwen (Tongyi)", "models": ["qwen-max", "qwen-plus", "qwen-turbo"]},
            {"id": "doubao", "name": "Doubao (火山引擎)", "models": ["doubao-seed-1-6-251015", "doubao-pro-32k", "doubao-lite-32k"]},
            {"id": "zhipu", "name": "Zhipu GLM", "models": ["glm-4-plus", "glm-4-air"]},
            {"id": "ollama", "name": "Ollama (Local)", "models": []},
            {"id": "custom", "name": "Custom OpenAI-compatible", "models": []},
        ]
    }


@router.get("/check-ollama", response_model=CheckOllamaResponse)
async def check_ollama():
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=3.0)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                return {"available": True, "models": models}
    except ImportError:
        return {"available": False, "models": [], "error": "httpx not installed"}
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Ollama check failed: {e}")
    return {"available": False, "models": []}


class PromptListResponse(BaseModel):
    scenes: Dict[str, List[dict]]


import logging

logger = logging.getLogger(__name__)


class ConnectivityTestRequest(BaseModel):
    provider_id: str
    model: str
    base_url: str
    api_key: str = ""


class ConnectivityTestResponse(BaseModel):
    ok: bool
    message: str


@router.post("/connectivity-test", response_model=ConnectivityTestResponse)
async def test_connectivity(payload: ConnectivityTestRequest):
    provider = payload.provider_id
    base = payload.base_url.rstrip("/")
    api_key = payload.api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")

    logger.info(f"[连通测试] ====== provider={provider} model={payload.model} base_url={base} ======")

    if not api_key:
        logger.warning(f"[连通测试] {provider}: API Key 未填写")
        return ConnectivityTestResponse(ok=False, message="API Key 未填写，请在设置中填入有效的 API Key")

    safe_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AIPPTXPLUS/1.0",
    }

    try:
        import httpx
        import time

        # 先做 TCP 级别连通性检查（DNS + 端口）
        from urllib.parse import urlparse
        parsed = urlparse(base)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        logger.info(f"[连通测试] 阶段1: TCP连通性检查 -> {host}:{port}")
        t0 = time.time()
        try:
            import asyncio
            _reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5.0)
            writer.close()
            logger.info(f"[连通测试] 阶段1 ✅ TCP可达，耗时 {time.time()-t0:.2f}s")
        except asyncio.TimeoutError:
            elapsed = time.time() - t0
            logger.error(f"[连通测试] 阶段1 ❌ TCP 连接超时 ({elapsed:.1f}s)，可能原因: 目标服务器不可达/防火墙拦截/代理问题")
            return ConnectivityTestResponse(
                ok=False,
                message=f"TCP 无法连接至 {host}:{port}，请检查: ①网络代理/VPN 设置 ②防火墙是否拦截 ③Base URL 域名是否正确"
            )
        except OSError as e:
            logger.error(f"[连通测试] 阶段1 ❌ TCP 连接失败: {e}")
            return ConnectivityTestResponse(
                ok=False,
                message=f"无法解析或连接至 {host}，请检查 DNS 或网络设置: {e}"
            )

        logger.info(f"[连通测试] 阶段2: 尝试 API 端点")

        candidates = [f"{base}/models"]
        if "/v1" not in base:
            candidates.append(f"{base}/v1/models")

        last_err = ""
        last_status = None
        last_body = ""
        for url in candidates:
            logger.info(f"[连通测试] 阶段2: GET {url}")
            t1 = time.time()
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=True) as client:
                    resp = await client.get(url, headers=headers)
                    elapsed = time.time() - t1
                    status = resp.status_code
                    text = resp.text[:500]
                    logger.info(f"[连通测试] 阶段2 {url} -> HTTP {status} ({elapsed:.1f}s)")
                    logger.debug(f"[连通测试] 阶段2 响应体: {text}")
                    last_status = status
                    last_body = text

                    if status == 200:
                        logger.info(f"[连通测试] ✅ {provider} 连接成功，响应: {text}")
                        return ConnectivityTestResponse(ok=True, message="连接成功")
                    elif status == 401:
                        logger.warning(f"[连通测试] ❌ {provider} 认证失败 (401)")
                        return ConnectivityTestResponse(ok=False, message="API Key 无效，请检查 Key 是否正确 (需以 sk- 开头)")
                    elif status == 402:
                        logger.warning(f"[连通测试] ❌ {provider} 账户余额不足 (402)")
                        return ConnectivityTestResponse(ok=False, message="账户余额不足，请充值后重试")
                    elif status == 403:
                        logger.warning(f"[连通测试] ❌ {provider} 权限不足 (403)")
                        return ConnectivityTestResponse(ok=False, message="API Key 无权限，请检查账户状态")
                    elif status == 429:
                        logger.warning(f"[连通测试] ❌ {provider} 请求频率限制 (429)")
                        return ConnectivityTestResponse(ok=False, message="请求过于频繁，请稍后重试")
                    else:
                        last_err = f"HTTP {status}: {text[:100]}"
            except httpx.ConnectError as e:
                elapsed = time.time() - t1
                logger.error(f"[连通测试] 阶段2 ❌ {url} 连接失败 ({elapsed:.1f}s): {e}")
                last_err = f"连接失败: {e}"
            except httpx.ReadTimeout:
                elapsed = time.time() - t1
                logger.error(f"[连通测试] 阶段2 ❌ {url} 读取超时 ({elapsed:.1f}s)")
                last_err = "服务器响应超时，请检查网络稳定性"
            except Exception as e:
                last_err = str(e)
                logger.warning(f"[连通测试] 阶段2 {url} 请求异常: {e}")

        logger.error(f"[连通测试] ❌ {provider} 所有路径均失败，最后状态: {last_status}, 错误: {last_err}, 响应: {last_body}")
        if last_status and last_body:
            return ConnectivityTestResponse(ok=False, message=f"API 返回 HTTP {last_status}: {last_body[:200]}")
        return ConnectivityTestResponse(ok=False, message=f"无法连接: {last_err}")
    except ImportError:
        logger.error("[连通测试] httpx 未安装")
        return ConnectivityTestResponse(ok=False, message="后端缺少 httpx 依赖，请执行: pip install httpx")
    except Exception as e:
        logger.error(f"[连通测试] 未知异常: {e}")
        return ConnectivityTestResponse(ok=False, message=str(e))


@router.get("/prompts", response_model=PromptListResponse)
async def list_prompts():
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "scenes")
    scenes = {}
    if not os.path.isdir(prompts_dir):
        return {"scenes": scenes}
    for fname in os.listdir(prompts_dir):
        if fname.endswith((".yaml", ".yml", ".json", ".md")):
            scene_id = os.path.splitext(fname)[0]
            scenes[scene_id] = []
    return {"scenes": scenes}
