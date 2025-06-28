import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JobStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting job status updates to all connected clients.
    """
    async def connect(self):
        await self.channel_layer.group_add('job_status', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('job_status', self.channel_name)

    async def job_status_update(self, event):
        """Send the job update to the WebSocket client."""
        await self.send(text_data=json.dumps(event['data']))
