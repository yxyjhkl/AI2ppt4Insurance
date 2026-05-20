import asyncio
import functools
import sys

if sys.version_info >= (3, 9):
    to_thread = asyncio.to_thread
else:
    async def to_thread(func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        func_call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)