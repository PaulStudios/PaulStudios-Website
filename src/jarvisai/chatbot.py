"""
Chatbot functions
"""
import datetime
import ChatbotAPI

import PaulStudios

brainid = PaulStudios.settings.BRAINID
brainkey = PaulStudios.settings.BRAINKEY

def wish_me():
    """Wish the user"""
    hour = datetime.datetime.now().hour
    if 12 > hour >= 0:
        return "Hello, Good Morning"
    if 18 > hour >= 12:
        return "Hello, Good Afternoon"
    return "Hello,Good Evening"


class Bot:
    """ChatBot"""

    def __init__(self):
        self.reply: str = "No response has been generated yet..."
        self.Chatbot: ChatbotAPI.ChatBot = ChatbotAPI.ChatBot(
            brainid,
            brainkey,
            history=True,
            debug=True)

    def userset(self, name: str):
        """Set username"""
        self.Chatbot.changename(name=name)

    def process(self, msg):
        """Get response from bot"""

        if 'time' in msg:
            date_and_time_now = datetime.datetime.now().strftime("%H:%M:%S")
            resp = f"The current time is {date_and_time_now}"
        else:
            resp = self.Chatbot.sendmsg(msg)
        self.reply = resp
        return resp
