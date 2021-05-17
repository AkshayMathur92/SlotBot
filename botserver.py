from dbserver import SlotBotDB, SlotBotException
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import requests
import sys
import re

BOT_TOKEN = "1874197080:AAGs1mRqG_OJOqbJlXeISLfpRDrcm6jq3VE"
regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$"; 
pincode_regex = re.compile(regex)

db = SlotBotDB()

class SimpleServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    # def do_GET(self):
    #     logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
    #     self._set_response()
    #     self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        # logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                # str(self.path), str(self.headers), post_data.decode('utf-8'))
        parseUpdate(post_data.decode('utf-8'))
        self._set_response()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleServer, port=8443 ):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

def parseUpdate(update):
    try:
        updateDict = json.loads(update)
        isCommand = updateDict["message"]["entities"][0]["type"]
        if(isCommand == "bot_command"):
            command_text = updateDict["message"]["text"]
            user = updateDict["message"]["from"]["id"]
            commands = command_text.split()
            if(len(commands) > 1):
                pincode = commands[1]
                verifyPinCode(pincode)
                getCommand(commands[0])( user, commands[1])
            else:
                if(commands[0] == '/addme'):
                    raise SlotBotException("addme requires pincode , usage /addme 302020")
                getCommand(commands[0])(user)
    except SlotBotException as ex:
        sendMessage(user, str(ex))
    except:
        logging.error('Something went wrong', sys.exc_info()[0])

def getCommand(command):
    return {
        '/start': start_message,
        '/momo' : love_message,
        '/addme': add_pincode,
        '/reset': remove_user,
        '/notify': notify_available
    }[command]

def verifyPinCode(pincode):
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

def remove_user(user):
    try:
        db.deleteUser(user)
        sendMessage(user, "use /addme <pincode> to get notified for vaccine slot")
    except SlotBotException as ex:
        sendMessage(user, str(ex))

def start_message(user):
    sendMessage(user, "Hello, I will help you notify when a covid vaccine slot is available at your pincode. To suscribe please reply with /addme <pincode>")

def love_message(user):
    sendMessage(user, "Love you Momo, LOLO XOXO, \u2764\ufe0f \u2764\ufe0f ")

def add_pincode(user, pincode):
    try:
        db.addUser(user,pincode)
        sendMessage(user, "You are now subscribed to notifications for {}. We will notify you once a slot is available".format(pincode))
    except SlotBotException as ex:
        sendMessage(user, str(ex))
        return
    

def sendMessage(user, text):
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(BOT_TOKEN)
    body = {'chat_id': user, 'text' : text}
    requests.post(url, data = body)
    # logging.info(response.json())

def check_availability(pincode):
    logging.info("checking for pincode {}".format(pincode))
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={}&date=17-05-2021".format(pincode)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    response = requests.get(url, headers=headers)
    sessions = response.json()
    avail_centre = []
    if(len(sessions) > 0):
        for session in sessions["sessions"]:
            avail_centre.append(session["name"])
    return avail_centre

def notify_available(ignored):
    pincodes = db.getPinCodes()
    for pincode in pincodes:
        centres_avail = check_availability(pincode)
        if(len(centres_avail) > 0):
            users = db.getUsersWithPincode(pincode)
            for user in users:
                sendMessage(user, "Hey slots are available @" + ', '.join([str(elem) for elem in centres_avail]) + ". Register here --> https://selfregistration.cowin.gov.in/")

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()