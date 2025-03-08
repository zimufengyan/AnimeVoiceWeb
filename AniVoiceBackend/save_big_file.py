import httpx
import aiofiles
import asyncio
from typing import Generator
from pathlib import Path
import logging


async def save_wav_stream(stream: Generator[bytes, None, None], file_path: Path) -> None:
    """异步保存流式WAV文件"""
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            async for chunk in stream:
                await f.write(chunk)
                # 立即刷新缓冲区确保实时写入
                await f.flush()
    except Exception as e:
        logging.error(f"Stream save failed: {str(e)}")
        await cleanup_file(file_path)
        raise


async def save_wav_bytes(data: bytes, file_path: Path) -> None:
    """异步保存完整WAV文件"""
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data)
    except Exception as e:
        logging.error(f"Bytes save failed: {str(e)}")
        await cleanup_file(file_path)
        raise


async def cleanup_file(file_path: Path) -> None:
    """清理未完整保存的文件"""
    try:
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
    except Exception as e:
        logging.error(f"Cleanup failed: {str(e)}")