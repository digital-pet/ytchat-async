## ytchat-async/ytchat.py
#
#   Contains main YoutubeLiveChat class
#

import cgi
import logging

from datetime import datetime, timedelta
from json import dumps, loads
from pprint import pformat

import dateutil.parser

#replaces threading, time
import asyncio
import async_timeout

#replaces httplib2
import aiohttp

#replaces oauth2client
import google_auth
#maybe not necessary? Will read the code more to determine
import aiohttp_google_auth_backend

from .utils import *
from .exceptions import *
from .types import *


from urllib.parse import urlencode


#depreciated and will be replaced
#from oauth2client.file import Storage
#import httplib2

#replaced with asyncio
#import threading
#import time
#from queue import Queue

#Never used
#import sys

class YoutubeLiveChat:

    def __init__(self, credential_filename, livechatIds):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.chat_subscribers = []
        #self.thread = threading.Thread(target=self.run)
        self.livechatIds = {}
        self.message_queue = Queue()

        storage = Storage(credential_filename)
        credentials = storage.get()
        self.http = credentials.authorize(httplib2.Http())
        self.livechat_api = LiveChatApi(self.http)

        #!!!move this out of init!!!
        for chat_id in livechatIds:
            self.livechatIds[chat_id] = {'nextPoll': datetime.now(), 'msg_ids': set(), 'pageToken': None}
            result = self.livechat_api.live_chat_messages_list(chat_id)
            while result['items']:
                pollingIntervalMillis = result['pollingIntervalMillis']
                self.livechatIds[chat_id]['msg_ids'].update(msg['id'] for msg in result['items'])
                self.livechatIds[chat_id]['nextPoll'] = datetime.now() + timedelta(seconds=pollingIntervalMillis / 1000)
                if result['pageInfo']['totalResults'] > result['pageInfo']['resultsPerPage']:
                    self.livechatIds[chat_id]['pageToken'] = result['nextPageToken']
                    time.sleep(result['pollingIntervalMillis'] / 1000)
                    result = self.livechat_api.live_chat_messages_list(chat_id,
                                                                       pageToken=self.livechatIds[chat_id]['pageToken'])
                else:
                    break
        #!!!end move this out of init!!!
        
        self.logger.debug("Initalized")

    def start(self):
        #self.running = True
        #self.thread = threading.Thread(target=self.run)
        #self.thread.daemon = True
        #self.thread.start()
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.run())
        loop.run_forever()
    
    def stop(self):
        self.running = False
        loop = asyncio.get_event_loop()
        loop.stop()

    async def _read_loop(self):
        """
        
        """
        while self.running:
            pass
        pass
        
    async def _write_loop(self):
        """
        
        """
        while self.running:
            to_send = await self.message_queue.get()
            self._send_message(to_send[0],to_send[1])
            self.message_queue.task_done()        

        
        
    def run(self):
        while self.running:
        
            #
            # send a queued messages
            #if not self.message_queue.empty():
            #    to_send = self.message_queue.get()
            #    self._send_message(to_send[0], to_send[1])
            # check for messages
            
            for chat_id in self.livechatIds:
                if self.livechatIds[chat_id]['nextPoll'] < datetime.now():
                    msgcache = self.livechatIds[chat_id]['msg_ids']
                    result = None
                    try:
                        result = self.livechat_api.live_chat_messages_list(
                            chat_id,
                            pageToken=self.livechatIds[chat_id]['pageToken'])
                    except Exception as e:
                        self.logger.warning(e)
                        self.logger.warning("Exception while trying to get yt api")
                    if result:
                        if 'pollingIntervalMillis' not in result:
                            self.logger.warning("Empty result")
                            self.logger.warning(pformat(result))
                            continue
                        pollingIntervalMillis = result['pollingIntervalMillis']
                        while result['items']:
                            latest_messages = {msg['id'] for msg in result['items']}
                            if msgcache:
                                new_messages = latest_messages.difference(msgcache)
                            else:
                                new_messages = latest_messages
                            new_msg_objs = [LiveChatMessage(self.http, json)
                                            for json in result['items'] if json['id'] in new_messages]

                            self.livechatIds[chat_id]['msg_ids'].update(new_messages)
                            nextPoll = datetime.now() + timedelta(seconds=pollingIntervalMillis / 1000)
                            self.livechatIds[chat_id]['nextPoll'] = nextPoll
                            if new_msg_objs:
                                self.logger.debug("New chat messages")
                                self.logger.debug(new_msg_objs)
                                for callback in self.chat_subscribers:
                                    try:
                                        callback(new_msg_objs, chat_id)
                                    except:
                                        msg = "Exception during callback to {0}".format(callback)
                                        self.logger.exception(msg)

                            if result['pageInfo']['totalResults'] > result['pageInfo']['resultsPerPage']:
                                self.livechatIds[chat_id]['pageToken'] = result['nextPageToken']
                                time.sleep(result['pollingIntervalMillis'] / 1000)
                                result = self.livechat_api.live_chat_messages_list(
                                    chat_id,
                                    pageToken=self.livechatIds[chat_id]['pageToken'])
                            else:
                                break

            time.sleep(1)

    def get_moderators(self, livechatId):
        result = self.livechat_api.live_chat_moderators_list(livechatId)
        if result['items']:
            mods = result['items']
            if result['pageInfo']['totalResults'] > result['pageInfo']['resultsPerPage']:
                while result['items']:
                    result = self.livechat_api.live_chat_moderators_list(livechatId, pageToken=result['nextPageToken'])
                    if result['items']:
                        mods.extend(result['items'])
                    else:
                        break
                    if 'nextPageToken' not in result:
                        break
            moderator_objs = [LiveChatModerator(self.http, json) for json in mods]
            return moderator_objs

    def set_moderator(self, livechatId, moderator_channelid):
        message = {u'snippet': {u'liveChatId': livechatId, "moderatorDetails": {"channelId": moderator_channelid}}}
        jsondump = dumps(message)
        return self.livechat_api.live_chat_moderators_insert(jsondump)

    def send_message(self, text, livechatId):
        self.message_queue.put((text, livechatId))

    def _send_message(self, text, livechatId):
        message = {
            u'snippet': {
                u'liveChatId': livechatId,
                "textMessageDetails": {
                    "messageText": text
                },
                "type": "textMessageEvent"
            }
        }

        jsondump = dumps(message)
        response = self.livechat_api.live_chat_messages_insert(jsondump)
        self.logger.debug(pformat(response))
        self.livechatIds[livechatId]['msg_ids'].add(response['id'])

    def subscribe_chat_message(self, callback):
        self.chat_subscribers.append(callback)


class LiveChatApi:

    def __init__(self, http):
        self.http = http
        self.logger = logging.getLogger("liveChat_api")

    def get_all_messages(self, livechatId):
        data = self.LiveChatMessages_list(livechatId, maxResults=2000)
        total_items = data['pageInfo']['totalResults']
        pageToken = data['nextPageToken']
        if len(data['items']) < total_items:
            time.sleep(data['pollingIntervalMillis'] / 1000)
            while len(data['items']) < total_items:
                other_data = self.LiveChatMessages_list(livechatId, maxResults=2000, pageToken=pageToken)
                if not other_data['items']:
                    break
                else:
                    data['items'].extend(other_data['items'])
                    pageToken = other_data['nextPageToken']
                    time.sleep(other_data['pollingIntervalMillis'] / 1000)
        return data

    def live_chat_moderators_list(self, livechatId, part='snippet', maxResults=5, pageToken=None):
        url = 'https://www.googleapis.com/youtube/v3/liveChat/moderators'
        url = url + '?liveChatId={0}'.format(livechatId)
        if pageToken:
            url = url + '&pageToken={0}'.format(pageToken)
        url = url + '&part={0}'.format(part)
        url = url + '&maxResults={0}'.format(maxResults)
        resp, data = _json_request(self.http, url)
        resp, content = self.http.request(url, 'GET')
        data = loads(content.decode("UTF-8"))
        return data

    def live_chat_moderators_insert(self, liveChatId, liveChatModerator):
        url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
        url = url + '?part=snippet'
        resp, data = _json_request(self.http,
                                   url,
                                   'POST',
                                   headers={'Content-Type': 'application/json; charset=UTF-8'},
                                   body=liveChatModerator)
        return data

    def live_chat_messages_list(self,
                                livechatId,
                                part='snippet,authorDetails',
                                maxResults=200,
                                pageToken=None,
                                profileImageSize=None):
        url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
        url = url + '?liveChatId={0}'.format(livechatId)
        if pageToken:
            url = url + '&pageToken={0}'.format(pageToken)
        if profileImageSize:
            url = url + '&profileImageSize={0}'.format(profileImageSize)
        url = url + '&part={0}'.format(part)
        url = url + '&maxResults={0}'.format(maxResults)
        resp, data = _json_request(self.http, url)
        return data

    def live_chat_messages_insert(self, liveChatMessage):
        url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
        url = url + '?part=snippet'
        resp, data = _json_request(self.http,
                                   url,
                                   'POST',
                                   headers={'Content-Type': 'application/json; charset=UTF-8'},
                                   body=liveChatMessage)
        self.logger.debug(pformat(resp))
        return data

    def live_chat_message_delete(self, idstring):
        "DELETE https://www.googleapis.com/youtube/v3/liveChat/messages"
