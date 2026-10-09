import asyncio
import json

from app.core import cache


class MemoryPubSub:
    def __init__(self, redis):
        self.redis = redis
        self.queue = asyncio.Queue()

    async def subscribe(self, channel):
        self.redis.subscribers.setdefault(channel, []).append(self)

    async def get_message(self, ignore_subscribe_messages=True, timeout=0):
        return await asyncio.wait_for(self.queue.get(), timeout=timeout)


class MemoryRedis:
    def __init__(self):
        self.lists = {}
        self.subscribers = {}

    def rpush(self, key, value):
        self.lists.setdefault(key, []).append(value)

    def ltrim(self, key, start, end):
        self.lists[key] = self.lists.get(key, [])[-50:]

    def expire(self, key, seconds):
        return True

    def publish(self, channel, value):
        subscribers = self.subscribers.get(channel, [])
        for subscriber in subscribers:
            subscriber.queue.put_nowait({"type": "message", "data": value})
        return len(subscribers)

    def pubsub(self):
        return MemoryPubSub(self)


def test_publish_fans_out_and_limits_reconnect_backlog(monkeypatch):
    redis = MemoryRedis()
    monkeypatch.setattr(cache, "redis_client", redis)

    async def scenario():
        first = redis.pubsub()
        second = redis.pubsub()
        await first.subscribe("events:user-1")
        await second.subscribe("events:user-1")
        cache.publish_event("user-1", {"type": "reflection.ready"})
        first_event, second_event = await asyncio.gather(
            first.get_message(timeout=0.1), second.get_message(timeout=0.1)
        )
        assert first_event["data"] == second_event["data"]
        assert json.loads(first_event["data"])["id"]

    asyncio.run(scenario())
    for index in range(55):
        cache.publish_event("user-1", {"type": "notification.new", "payload": index})
    backlog = redis.lists["events_backlog:user-1"]
    assert len(backlog) == 50


def test_publish_still_swallows_invalid_event(monkeypatch):
    redis = MemoryRedis()
    monkeypatch.setattr(cache, "redis_client", redis)
    cache.publish_event("user-1", None)
    assert redis.lists == {}
