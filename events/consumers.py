import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

class EventConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            return await self.close()

        self.broadcast_group = "events_broadcast"
        self.user_group = f"user_{user.id}"

        await self.accept()
        await self.channel_layer.group_add(self.broadcast_group, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        logger.info(f"WebSocket CONNECTED: user={user.id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.broadcast_group, self.channel_name)
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        logger.info(f"WebSocket DISCONNECTED: code={close_code}")

    async def event_message(self, event):
        payload = {"type": event["event_type"], "data": event["data"]}
        try:
            await self.send_json(payload)
        except Exception as e:
            logger.exception("Failed to send WS payload %r: %s", payload, e)
