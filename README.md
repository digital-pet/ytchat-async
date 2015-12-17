# Synopsis

A python module aimed to wrap the youtube live chat api and provide easy event based access to it.

# Usage

Run `python get_oauth_token.py` and follow the instructions to generate your credentials file.

```python
from time import sleep

from youtubechat import YoutubeLiveChat, get_live_chat_id_for_stream_now

livechat_id = get_live_chat_id_for_stream_now("oauth_creds")
chat_obj = YoutubeLiveChat("oauth_creds", [livechat_id])


def respond(msgs, chatid):
    for msg in msgs:
        msg.delete()
        chat_obj.send_message("RESPONSE!", chatid)


try:
    chat_obj.start()
    chat_obj.subscribe_chat_message(respond)
    while True:
        sleep(0.1)
finally:
    chat_obj.stop()
```

# Future Work

- Moderator control
- Banlist control
