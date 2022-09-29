from abc import ABC, abstractmethod
from operator import pos
from string import Template

import requests
from dbserver import SlotBotException
import re
import json

pin_regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$"; 
pincode_regex = re.compile(pin_regex)
age_regex = "^@mathur_vaccine_slot_bot ([1-9][0-9])$"
age_matcher = re.compile(age_regex)

class BotState(ABC):
    @abstractmethod
    def instruction(self, chatId) -> str:
        pass

    @abstractmethod
    def parse(self, message) -> None:
        if message["from"]["is_bot"]:
           raise SlotBotException("This bot does not serve other bots.") 
        pass

    @abstractmethod
    def process(self, user, db) -> None:
        pass

    @abstractmethod
    def reply(self) -> str:
        pass

class Start(BotState):
    userName = None
    def instruction(self, chatId) -> str:
        return Template("""{
            "chat_id": "${chat_id}",
            "text": "Hello, I will help you notify when a covid vaccine slot is available at your pincode."
        }""").substitute(chat_id = chatId)

    def parse(self, message):
        if not message["text"] == "/start" :
           raise SlotBotException("Incorrect Command. Reply with /start to start.")
        if message["chat"]["first_name"] :
            self.userName = message["chat"]["first_name"]
        else:
            self.userName = "NOT_FOUND"
    
    def process(self, user, db):
        if db.isUserRegistered(user):
            raise SlotBotException("User is already registerd, use /reset to start again")
        db.addUserWithState(user, self.userName)
    
    def reply(self):
        return "You are now registered !"

class AskPincode(BotState):
    pincode = None
    postOffice = None
    def instruction(self, chatId) -> str:
        return Template("""{
            "chat_id": "${chat_id}",
            "text": "Please reply with you area pincode."
        }""").substitute(chat_id = chatId)

    def parse(self, message) -> None:
        pincode = message["text"]
        postOffice = None
        if (pincode == ''):
            raise SlotBotException("Pincode seem to be incorrect")
        # Pattern class contains matcher() method
        # to find matching between given pin code
        # and regular expression.
        m = re.match(pincode_regex, pincode)
        # Return True if the pin code
        # matched the ReGex else False
        if m is None:
            raise SlotBotException("Pincode seems to be incorrect")
        str_response = requests.get("https://api.postalpincode.in/pincode/{}".format(pincode))
        if str_response.status_code / 100 == 2:
            response = json.loads(str_response.text)
            if response[0]["Status"] == "Success":
                postOffice = response[0]["PostOffice"][0]["Name"]
            else:
                raise SlotBotException("Pincode not found in India, are you sure ?")
        else:
            raise SlotBotException("Pincode seems to be incorrect")
        self.pincode = pincode
        self.postOffice = postOffice
    
    def process(self, user, db) -> None:
        if self.pincode:
            db.updatePincode(user, self.pincode)
    
    def reply(self) -> str:
        return "Pincode added, We will now notify you for " + self.pincode +  " area " + self.postOffice + " Reply back if you want to add age."

class AskAditionalInfo(BotState):
    def instruction(self, chatId) -> str:
        t = Template ("""{
        "chat_id": "${chat_id}",
        "text": "Select an age group",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "18 - 45",
                        "switch_inline_query_current_chat": "18"
                    },
                    {
                        "text": "45 +",
                        "switch_inline_query_current_chat": "45"
                    }
                ]
            ]
        }
        }""").substitute(chat_id = chatId)
        return t

    def parse(self, message) -> None:
        self.age = -1
        if(len(message["entities"]) > 0 and message["entities"][0]["type"] == "mention"):
            m = re.match(age_matcher, message["text"])
            if m is None:
                raise SlotBotException("Does not understand you, try again")
            self.age = int(m.group(1))
        else:
            raise SlotBotException("Does not understand you, try again")
    
    def process(self, user, db) -> None:
        db.saveAge(user, self.age)
    
    def reply(self) -> str:
        if self.age <= 45:
            return "You are now subscribed to 18 - 45 group."
        else:
            return "You are now subscribed to 45+ group."