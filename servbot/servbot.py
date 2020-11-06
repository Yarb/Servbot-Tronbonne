#!/usr/bin/env python

# Servbot, a WS server that obeys every whim of Tron Bonne (AKA clients).
# In short, incoming button presses are sent to all clients and sent as
# keypresses to the system.
# NOTE!
# This should be run in controlled environment as giving
# Internet access to limited virtual keyboard without decent security
# is not the best idea in the long run. You have been warned.

import asyncio
import json
import logging
import websockets
import random

import ssl
import pathlib
import argparse

import pyvjoy


joy1 = pyvjoy.VJoyDevice(1)
        
admin_enable = {"value": False}

USERS1 = set()
USERS2 = set()
ADMINS = set()

# Groups
PLAYERS = 1
ADMIN = 2

# Players
P1 = 0
P2 = 1

# Message actions 
ACTION_ADM_ENABLE = "Enable"
ACTION_ADM_DISABLE = "Disable"
ACTION_ADM_BTN_P1 = "btn1"
ACTION_ADM_BTN_P2 = "btn2"
ACTION_ADM_KILL = "KILL clients"

# Message fields
TYPE = "type"
TYPE_STATE = "state"
TYPE_USERS = "users"
TYPE_KEYSTATE = "keystate"
TYPE_TOKEN = "tokens"
TOKEN = "token"
VALUE = "value"
ID = "id"
ADM_BUTTON = "btn"
ACTION = "action"

# Tokens
token1 = ""
token2 = ""
admin_token = ""
token_length = 5

# Button configuration. Set value indicates the button number
BUTTONS = [{"up"   : 0, "down" : 1, "left" : 2, "right": 3, "A"    : 4, 
                "B"    : 5, "C"    : 6, "X"    : 7, "Y"    : 8, "Z"    : 9 },
               {"up"   : 10, "down" : 11, "left" : 12, "right": 13, "A"    : 14, 
                "B"    : 15, "C"    : 16, "X"    : 17, "Y"    : 18, "Z"    : 19}
              ]

IP = "localhost"
PORT = 6789
KEY_OUTPUT = 0
ssl_state = False           


def main():

    global IP, PORT, KEY_OUTPUT, ssl_state, token_length
    logging.basicConfig()

    parser = argparse.ArgumentParser(description='Servbot. WS server for accepting button presses from browsers')
    parser.add_argument('-a', dest='ip', required=True,
                        help='IP address of the server.')
    parser.add_argument('-p', type=int, default=6789, dest='port',
                        help='Server port (default 6789).')
    parser.add_argument('-k', action='store_const',const=1 , metavar='', dest='output',
                        help='Output keypresses.')
    parser.add_argument('-S', dest='base_filename',
                        help='Use SSL. Provide filename for .key and .crt files. Eg. "file" -> "file.crt" and "file.key".')
    parser.add_argument('-T', type = int, dest='keystrength',
                        help='Enable stronger token system with given keylength. Admin will always be keylength + 2')
    args = parser.parse_args()
    IP = args.ip
    PORT = args.port
    KEY_OUTPUT = args.output
    if args.keystrength:
        token_length = args.keystrength
    
    # SSL cert and key checking and loading
    if args.base_filename:
        fn = args.base_filename
        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            cert_pem = pathlib.Path(__file__).with_name(fn + ".crt")
            key = pathlib.Path(__file__).with_name(fn + ".key")
            ssl_context.load_cert_chain(cert_pem, keyfile=key)
            ssl_state = True
        except FileNotFoundError:
            print("SSL init error:")
            print(fn + ".key and/or " + fn + ".crt not found in the same directory")
            exit(-1)
        except ssl.SSLError:
            print("SSL init error: Bad .key or .crt?")
            exit(-1)
    
    if ssl_state:
        start_server = websockets.serve(server, IP, PORT, ssl=ssl_context)
    else:
        start_server = websockets.serve(server, IP, PORT)

    # Generate user tokens
    generate_tokens(False)
    print_settings()

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()        


# Simple random token generator
def random_token(value):

    a = ""
    for i in range(value):
        a += str(random.randint(0,9))
    return a

    
# Better random token generator
def random_token2(value):

    a = ""
    for i in range(value):
        if random.randint(0,1):
            a += str(random.randint(0,9))
        else:
            # 97 for lower, 65 for uppercase
            a += chr(65 + random.randint(0,25))
    return a    


def generate_tokens(reset):

    global token1, token2, admin_token
    token1 = random_token(token_length)
    token2 = random_token(token_length)
    if not reset:
        admin_token = random_token(token_length + 2)    


def keypresser(buttons, player):
    # Reverse the order of buttons so that numbers match with vJoy system.
    newbuttons = buttons.copy()
    newbuttons.reverse()
    
    newbuttons = "".join(newbuttons)
    if player == P1 or player == P2:
        joy1.data.lButtons = int(newbuttons, 2)
    else:
        return
    joy1.update()


        
# Generate JSON of all users in given list and 
# send notification to said users and to admins
async def notify_users(userlist):

    # Generate message
    if userlist is USERS1:
        id = P1
    elif userlist is USERS2:
        id = P2
    else: 
        id = ADMIN
    users = ["--"]
    if userlist:
        users = [i for h,i in userlist]
    message = json.dumps({TYPE: TYPE_USERS, VALUE: users, ID:id})
    
    if userlist:  # asyncio.wait doesn't accept an empty list
        for user, username in userlist:
            await user.send(message)
    if ADMINS:
        for user, username in ADMINS:
            await user.send(message)


# Notify given userlist of events, send monitoring data to admins and
# if key output is enabled, forward the buttons to be pressed.
async def notify_buttons(player, group, buttons):

    # Generate message
    if (KEY_OUTPUT and (admin_enable[VALUE] or group == ADMIN)):
        keypresser(buttons, player)
    if player:
        buttons = buttons[len(BUTTONS[P2]):]
    else:
        buttons = buttons[:len(BUTTONS[P1])]
    message =  json.dumps({TYPE: TYPE_STATE, VALUE: buttons, ID: player})
    
    if USERS1 and player == P1:  # asyncio.wait doesn't accept an empty list
        for user, username in USERS1:
            await user.send(message)
    
    if USERS2 and player == P2:  # asyncio.wait doesn't accept an empty list
        for user, username in USERS2:
            await user.send(message)
    
    if ADMINS:
        for user, username in ADMINS:
            await user.send(message)


# Send the virtual keyboard state to admins
async def notify_admin():

    if ADMINS:
        message = json.dumps({TYPE: TYPE_KEYSTATE, **admin_enable})
        for user, username in ADMINS:
            await user.send(message)


# Send the session tokens to admins        
async def send_admin_tokens():

    if ADMINS:
        message = json.dumps({TYPE: TYPE_TOKEN, VALUE: [token1, token2, admin_token]})
        for user, username in ADMINS:
            await user.send(message)


# Register websocket
async def register(websocket, user, userlist):

    userlist.add((websocket, user))
    await notify_users(userlist)


# Remove registered websocket
async def unregister(websocket, userlist):

    for client in userlist:
        if client[0] == websocket:
            userlist.remove(client)
            await notify_users(userlist)
            return True
    return False

            
# Check if websocket exists in given userlist
def check_client(websocket, userlist):

    for client in userlist:
        if client[0] == websocket:
            return True
    return False


# Restart the session. This removes all the users except for admins
# and generates new set of session tokens
async def restart_session():

    while USERS1:
        client = USERS1.pop()
        await client[0].close()
    await notify_users(USERS1)

    while USERS2:
        client = USERS2.pop()
        await client[0].close()
    await notify_users(USERS2)
    generate_tokens(True)


async def process_buttons(player, group, buttons, button, new_state):

    if button in BUTTONS[player]:
        if new_state:
            buttons[BUTTONS[player][button]] = "1"
        else:
            buttons[BUTTONS[player][button]] = "0"
        await notify_buttons(player, group, buttons)


# Main server loop
async def server(websocket, path):
    try:
        buttons_p1
        buttons_p2
    except NameError:
        buttons = ["0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0"]

    # register(websocket) sends user_event() to websocket
    try:
        async for message in websocket:
        
            # Load message and verify
            data = json.loads(message)
            valid_msg = 1

            if TOKEN in data:
                msg_token = data[TOKEN].upper()
            else:
                logging.error("Token error", data)
                valid_msg = 0
                
            if ACTION in data:
                msg_action = data[ACTION]
            else:    
                logging.error("Invalid message", data)
                valid_msg = 0
            if VALUE in data:
                msg_value = data[VALUE]
            

            #If valid, proceed
            if valid_msg:
                
                # If websocket registered - check commands
                if check_client(websocket, USERS1):
                    # check token and change state of pressed button
                    if msg_token == token1:
                        await process_buttons(P1, PLAYERS, buttons, msg_action, msg_value)

                elif check_client(websocket, USERS2):
                    # check token and change state of pressed button
                    if msg_token == token2:
                        await process_buttons(P2, PLAYERS, buttons, msg_action, msg_value)

                elif check_client(websocket, ADMINS):
                    if msg_token == admin_token:
                        # check command
                        if msg_action == ACTION_ADM_ENABLE:
                            admin_enable[VALUE] = True
                            await notify_admin()
                            
                        elif msg_action == ACTION_ADM_DISABLE:
                            admin_enable[VALUE] = False
                            await notify_admin()
                        elif msg_action == ACTION_ADM_BTN_P1:
                            await process_buttons(P1, ADMIN, buttons, data[ADM_BUTTON], msg_value)
                        
                        elif msg_action == ACTION_ADM_BTN_P2:
                            await process_buttons(P2, ADMIN, buttons, data[ADM_BUTTON], msg_value)
                        
                        elif msg_action == ACTION_ADM_KILL:
                            print("Servbot, restarting session:")
                            await restart_session()
                            await notify_admin()
                            await send_admin_tokens()
                            buttons_p1 = ["0","0","0","0","0","0","0","0","0","0"]
                            buttons_p2 = ["0","0","0","0","0","0","0","0","0","0"]
                            print_settings()
                # else check login 
                else:
                    # New websocket login
                    if msg_action == "login":
                        if msg_token == token1 and data["user"]:
                            await register(websocket, data["user"], USERS1)
                        elif msg_token == token2 and data["user"]:
                            await register(websocket, data["user"], USERS2)

                    # New admin login
                    elif msg_action == "ADMIN" and msg_token == admin_token:
                        await register(websocket, data["user"], ADMINS)
                        await notify_admin()
                        await send_admin_tokens()
                        await notify_users(USERS1)
                        await notify_users(USERS2)
                        
                    # Something else, report.
                    else:
                        logging.error("Token error or bad message", data)

    finally:
            # Go throught the lists one by one and try to unregister the websocket
            # This needs to be done in order, which is why it is done this way.
            if not await unregister(websocket, USERS1):
                if not await unregister(websocket, USERS2):
                    await unregister(websocket, ADMINS)


def print_settings():
    print("\n---\n")

    if (KEY_OUTPUT):
        print("Virtual keyboard mode is enabled. Use the admin interface to activate output")
    else:
        print("Connection testing mode. Virtual keyboard is DISABLED.")

    print("\nServbot running at: " )
    if ssl_state:
        print("wss://" + IP + ":" + str(PORT))
    else:
        print("ws://" + IP + ":" + str(PORT))
    print("---")
    print("ADMIN token is: " + admin_token)
    print("\n")
    print("Player 1 session token is: " + token1)
    print("Player 2 session token is: " + token2)
    print("\n")
    print("Token verification is case insensitive")
    print("\n---\n")

if __name__ == "__main__":
    main()