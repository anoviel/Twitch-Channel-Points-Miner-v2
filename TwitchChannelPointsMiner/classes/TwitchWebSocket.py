import json
import logging
import time

from websocket import WebSocketApp

from TwitchChannelPointsMiner.utils import create_nonce

logger = logging.getLogger(__name__)


class TwitchWebSocket(WebSocketApp):
    def listen(self, topic, auth_token=None):
        data = {"topics": [str(topic)]}
        if topic.is_user_topic() and auth_token is not None:
            data["auth_token"] = auth_token

        nonce = create_nonce()
        self.send({"type": "LISTEN", "nonce": nonce, "data": data})

    def ping(self):
        self.send({"type": "PING"})
        self.last_ping = time.time()

    def send(self, request):
        request_str = json.dumps(request, separators=(",", ":"))
        logger.debug(f"Send: {request_str}")
        super().send(request_str)

    def reset(self, parent_pool):
        self.parent_pool = parent_pool
        self.keep_running = True
        self.is_closed = False
        self.is_opened = False
        self.is_reconneting = False

        # Custom attribute
        self.topics = []
        self.pending_topics = []

        self.twitch = parent_pool.twitch
        self.browser = parent_pool.browser
        self.streamers = parent_pool.streamers
        self.events_predictions = parent_pool.events_predictions

        self.last_message_timestamp = None
        self.last_message_type_channel = None

        self.last_pong = time.time()
        self.last_ping = time.time()

    def elapsed_last_pong(self):
        return (time.time() - self.last_pong) // 60

    def elapsed_last_ping(self):
        return (time.time() - self.last_ping) // 60
