from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def send_real_time(event_type: str, recipient_group: str, data: dict):
    async_to_sync(get_channel_layer().group_send)(
        recipient_group,
        {
            "type": "event_message",   
            "event_type": event_type,
            "data": data,
        }
    )