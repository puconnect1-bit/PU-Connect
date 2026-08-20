"""Async helpers to make Channels channel-layer operations resilient to the
intermittent ``redis.exceptions.ConnectionError`` ("Connection closed by
server") observed when the Redis-backed channel layer drops a connection.

Rather than letting a single transient failure reject a WebSocket handshake
immediately, these helpers retry a few times with a short backoff.
"""

import asyncio

try:
    from redis.exceptions import ConnectionError as RedisConnectionError
except ImportError:  # pragma: no cover - redis is required in practice
    redis = None
    RedisConnectionError = ConnectionError


# Number of attempts (including the first). A brief Redis blip usually recovers
# after 1-2 retries; if Redis is genuinely down we fail fast after the final
# attempt so the consumer can reject cleanly rather than hang.
CHANNEL_RETRIES = 4
# Backoff base in seconds: 0.5s, 1s, 2s, then the final attempt.
CHANNEL_BASE_DELAY = 0.5


async def retry_channel_op(coro_factory, label="channel op"):
    """Run ``coro_factory()`` with retry on Redis ConnectionError.

    ``coro_factory`` must be a zero-arg callable returning the awaitable to
    execute (e.g. ``lambda: layer.group_add(...)``). Returns the successful
    result, or raises the last exception once attempts are exhausted.
    """
    last_err = None
    for attempt in range(1, CHANNEL_RETRIES + 1):
        try:
            return await coro_factory()
        except RedisConnectionError as e:
            last_err = e
            if attempt == CHANNEL_RETRIES:
                break
            delay = CHANNEL_BASE_DELAY * attempt
            print(f"{label} failed (Redis {e}); retrying in {delay}s ({attempt}/{CHANNEL_RETRIES - 1})")
            await asyncio.sleep(delay)
    raise last_err


async def group_add_retry(channel_layer, group, channel, label="group_add"):
    return await retry_channel_op(
        lambda: channel_layer.group_add(group, channel), label=label
    )


async def group_discard_retry(channel_layer, group, channel, label="group_discard"):
    return await retry_channel_op(
        lambda: channel_layer.group_discard(group, channel), label=label
    )


async def group_send_retry(channel_layer, group, event, label="group_send"):
    return await retry_channel_op(
        lambda: channel_layer.group_send(group, event), label=label
    )
