## ytchat-async/types.py
#
#   Contains datatype objects removed from ytchat.py
#

from .utils import *
from json import dumps

class MessageAuthor:
    def __init__(self, json):
        self.is_verified = json['isVerified']
        self.channel_url = json['channelUrl']
        self.profile_image_url = json['profileImageUrl']
        self.channel_id = json['channelId']
        self.display_name = json['displayName']
        self.is_chat_owner = json['isChatOwner']
        self.is_chat_sponsor = json['isChatSponsor']
        self.is_chat_moderator = json['isChatModerator']

class LiveChatMessage:

    def __init__(self, http, json):
        self.http = http
        self.json = json
        self.etag = json['etag']
        self.id = json['id']
        snippet = json['snippet']
        self.type = snippet['type']
        self.message_text = snippet['textMessageDetails']['messageText']
        self.display_message = snippet['displayMessage']
        self.has_display_content = snippet['hasDisplayContent']
        self.live_chat_id = snippet['liveChatId']
        self.published_at = get_datetime_from_string(snippet['publishedAt'])
        self.author = MessageAuthor(json['authorDetails'])

    def delete(self):
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        url = url + '?id={0}'.format(self.id)
        resp, content = self.http.request(url, 'DELETE')

    def permaban(self):
        url = "https://www.googleapis.com/youtube/v3/liveChat/bans"
        message = {u'snippet': {u'liveChatId': self.live_chat_id, u'type': 'permanent', "bannedUserDetails": {"channelId": self.author.channel_id}}}
        jsondump = dumps(message)
        url = url + '?part=snippet'
        resp, data = _json_request(self.http,
                                   url,
                                   'POST',
                                   headers={'Content-Type': 'application/json; charset=UTF-8'},
                                   body=jsondump)
        jsonresponse = dumps(data)
        return data['id']

    def tempban(self, timee = 300):
        url = "https://www.googleapis.com/youtube/v3/liveChat/bans"
        message = {u'snippet': {u'liveChatId': self.live_chat_id, u'type': 'temporary', "banDurationSeconds": timee, "bannedUserDetails": {"channelId": self.author.channel_id}}}
        jsondump = dumps(message)
        url = url + '?part=snippet'
        resp, data = _json_request(self.http,
                                   url,
                                   'POST',
                                   headers={'Content-Type': 'application/json; charset=UTF-8'},
                                   body=jsondump)

    def unban(self, id):
        url = "https://www.googleapis.com/youtube/v3/liveChat/bans"
        url = url + '?id=' + id
        content = self.http.request(url, 'DELETE')

    def __repr__(self):
        return self.display_message


class LiveChatModerator:

    def __init__(self, http, json):
        self.http = http
        self.json = json
        self.etag = json['etag']
        self.id = json['id']
        snippet = json['snippet']
        self.channel_id = snippet['moderatorDetails']['channelId']
        self.channel_url = snippet['moderatorDetails']['channelUrl']
        self.display_name = snippet['moderatorDetails']['displayName']
        self.profile_image_url = snippet['moderatorDetails']['profileImageUrl']

    def delete(self):
        url = "https://www.googleapis.com/youtube/v3/liveChat/moderators"
        url = url + '?id={0}'.format(self.id)
        resp, content = self.http.request(url, 'DELETE')

    def __repr__(self):
        return self.display_name

