"""
WebSocket endpoint — streams live platform updates via Redis pub/sub.
"""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from shared.redis_client import get_async_redis
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/updates")
async def websocket_updates(websocket: WebSocket):
    """Accept WS connection, subscribe to Redis pub/sub, forward messages."""
    await websocket.accept()
    redis = get_async_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe("platform_updates")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message["type"] == "message":
                data = message["data"]
                # async redis with decode_responses=True returns str directly
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                await websocket.send_text(data)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected")
    except Exception as e:
        logger.error("ws_error", error=str(e))
    finally:
        await pubsub.unsubscribe("platform_updates")
        await pubsub.close()
        await redis.close()
