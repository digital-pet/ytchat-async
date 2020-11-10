## ytchat-async/exceptions.py
#
#   Contains exceptions removed from ytchat.py
#

class YoutubeLiveChatError(Exception):

    def __init__(self, message, code=None, errors=None):
        Exception.__init__(self, message)
        self.code = code
        self.errors = errors