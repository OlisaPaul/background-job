import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JobStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('job_status', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('job_status', self.channel_name)

    async def job_status_update(self, event):
        # Send the job update to the WebSocket
        await self.send(text_data=json.dumps(event['data']))
