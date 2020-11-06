# servbot-tronbonne
Simple WebSocket solution for sharing a controller(emulated keyboard) to multiple players over Internet.

This is a new version of the original Servbot-Tronbonne concept that utilizes vJoy virtual gamepad through pyvjoy. Main reason for the change is better compability (Pynput virtual keyboards had problems with several games). With virtual gamepad, the game support should be better.

Servbot:
-
The Websocket server that handles connections from Tronbonne-clients and connects them to virtual gamepad that can be used to control games. In order to work, the system requires pyvjoy library and vJoy virtual gamepad.

Tronbonne:
-
Simple website that contains necessary code to access the servbot and execute keypresses. Just like it's namesake, all Tronbonne clients have their strong opinions on what commands should be executed by the connected servbot. Thus every client can press any assigned button on the 'controller'. End result should resemble multiplayer gaming....or chaos.

Installation:
-
Requirements:
 * Python 3.6.1+
 * Python Websockets 8.1 (https://pypi.org/project/websockets/).
 * Pyvjoy (https://github.com/tidzo/pyvjoy)
 * vJoy (http://vjoystick.sourceforge.net/site/)

Modify the Tronbonne JS. scripts to contain correct address of the target Servbot and host the webpage. Note that as long as the client running the webpage has access to the Servbot address, everything should just work. This allows for flexibility in deployment.

Run the Servbot with:
`python3 servbot.py -a <ip-address>`

For additional commands, including enabling the virtual gamepad,  run:
`python3 servbot.py -h`

Upon running, the servbot generates and provides you with tokens that can be used to access the server.
Simply enter one of these tokens to Tronbonne along with a cool playername and you are good to go.
For deployment over Internet, modify the Tronbonne webpage to contain the correct address for the server.

There is also a admin interface used to remotely enable/disable the virtual gamepad output and to monitor activity.

Have fun - Johan Strandman

Acknowledgements:
-
 - OptimusDu at OpenGameArt.org for creating neat arcade button sprites.
 - Fellows at Triforce for providing inspiration.
 - Following composers for making background music for coding:
   - Ichinen Miura
   - Yasunori Iwasaki
   - Kohei Tanaka
   - Nakagawa Koutarou
   - Toshihiko Sahashi
