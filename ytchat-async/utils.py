## ytchat-async/utils.py
#
#   Contains utility functions removed from ytchat.py
#

from .exceptions import *

import cgi
import aiohttp

def _json_request(http, url, method='GET', headers=None, body=None):
    
    #async with aiohttp.ClientSession() as session:
    #    async with session.post(url, json=json)
    # argument json is a dict
    
    resp, content = http.request(url, method, headers=headers, body=body)
    content_type, content_type_params = cgi.parse_header(resp.get('content-type', 'application/json; charset=UTF-8'))
    charset = content_type_params.get('charset', 'UTF-8')
    data = loads(content.decode(charset))
    if 'error' in data:
        error = data['error']
        raise YoutubeLiveChatError(error['message'], error.get('code'), error.get('errors'))
    return resp, data


def get_datetime_from_string(datestr):
    dt = dateutil.parser.parse(datestr)
    return dt

def get_top_stream_chat_ids(credential_file):
    playlist_id = "PLiCvVJzBupKmEehQ3hnNbbfBjLUyvGlqx"
    storage = Storage(credential_file)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    url = "https://www.googleapis.com/youtube/v3/playlistItems?"
    params = {'part': 'contentDetails','playlistId':playlist_id}
    params = urlencode(params)
    resp, data = _json_request(http, url + params)
    chatids = []
    for item in data['items']:
        videoid = item['contentDetails']['videoId']
        url = "https://www.googleapis.com/youtube/v3/videos?"
        params = {'part': 'liveStreamingDetails','id': videoid}
        params = urlencode(params)
        response_obj, video_data = _json_request(http, url + params)
        chatId = video_data['items'][0]['liveStreamingDetails']['activeLiveChatId']
        chatids.append(chatId)

    return chatids

def get_live_chat_id_for_stream_now(credential_file):
    storage = Storage(credential_file)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?"
    params = {'part': 'snippet', 'default': 'true'}
    params = urlencode(params)
    resp, data = _json_request(http, url + params)
    return data['items'][0]['snippet']['liveChatId']


def get_live_chat_id_for_broadcast_id(broadcastId, credential_file):
    storage = Storage(credential_file)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?"
    params = {'part': 'snippet', 'id': broadcastId}
    params = urlencode(params)
    resp, data = _json_request(http, url + params)
    return data['items'][0]['snippet']['liveChatId']


def channelid_to_name(channelId, http):
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&id={0}".format(channelId)
    response, data = _json_request(http, url)
    return data['items'][0]['snippet']['title']