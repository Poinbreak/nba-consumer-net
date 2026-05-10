import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LiveGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'

        # Join game room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to live updates for game {self.game_id}'
        }))

    async def disconnect(self, close_code):
        # Leave game room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def game_update(self, event):
        update_data = event['data']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'data': update_data
        }))
