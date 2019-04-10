import sys, os
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../calibration"))
from new_listen_tools import runCalibration, listen, stopListening
import socket
import threading
import json

LISTEN_SECONDS = 30

flowLock = threading.Lock()

DEVICE_NAME = "TurnUp 1"
SETTINGS_SERVER_PORT = 8144
BUFFER_SIZE = 1024

UDP_IP = '' # Empty to bind to any available interface
UDP_PORT = 8111

CLIENT_CONNECT_ADDRESS = None
CLIENT_CONNECT_PORT = None  # Client port to send device data back to

""" Basic TurnUp settings server flow:
        1. Listen for a UDP device discovery message that will be broadcasted by the user phone
            * discovery message will include a port number that the device can connect to in order to send important server data
        2. Send device data to the user phone using the port number included in the broadcast message
            * basically say to the phone "I am a turnup device, here's how to connect to me"
        3. Listen for TCP connections that the phone can now connect to
            * now the phone may connect and send user specified settings
"""

bypass_calibration = False

def UDPserver():
    while True:
        # UDP receive socket setup
        UDPsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDPsocket.bind((UDP_IP, UDP_PORT))
        # Listen for the UDP broadcast message from the user phone
        while True:
            flowLock.acquire()
            print("Starting UDP server to listen for discovery messages...")
            print("Listening on port %s\n" % (UDP_PORT))
            flowLock.release()
            data, address = UDPsocket.recvfrom(4096)
            try:
                stringData = data.decode("UTF-8")       # decode the character bytes to a string
                dataDict = json.loads(stringData)       # convert json string to a dictionary
                CLIENT_CONNECT_PORT = dataDict["port"]  # extract the port number from the received data
                CLIENT_CONNECT_ADDRESS = address[0]     # extract the client address from the socket data
                if (CLIENT_CONNECT_ADDRESS is not None):
                    flowLock.acquire()
                    print("Received discovery message from %s:%d\n" % (CLIENT_CONNECT_ADDRESS, address[1]))
                    flowLock.release()
                    break
            except:     # ignore the UDP message and continue listening for discovery message
                continue

        
        # create a response data dictionary
        responseData = {
            "name": DEVICE_NAME,
            "port": SETTINGS_SERVER_PORT
        }

        # convert the dictionary to a byte representation of a JSON string
        responseMessage = bytes(json.dumps(responseData), 'utf-8')

        flowLock.acquire()
        print("Constructed the following discovery response message: %s\n" % (responseMessage))
        flowLock.release()

        # Connect to the user phone using the recieved IP address and port
        # Send back device connection data (device name & port to connect to) to the phone
        responseSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      # open socket to send response data to phone
        responseSocket.connect((CLIENT_CONNECT_ADDRESS, CLIENT_CONNECT_PORT))   # connect socket to phone IP and port
        responseSocket.sendall(responseMessage)
        responseSocket.close()

        flowLock.acquire()
        print("Sent discovery response message to %s:%d" % (CLIENT_CONNECT_ADDRESS, CLIENT_CONNECT_PORT))
        print("Completed discovery phase!\n")
        flowLock.release()

        # if no current TCP thread, start one
        if len(threading.enumerate()) < 3:
            TCPthread = threading.Thread(target=TCPserver, args=())
            TCPthread.start()
        



def TCPserver():
    # sensitivity will be set by user later
    sensitivity = 0
    M = 0
    B = 0
    didCalibrate = False
    didReceiveUserSettings = False
    
    # declare listen thread
    listen_thread = None
    
    # Set up the main device server to receive user settings data from a user phone
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", SETTINGS_SERVER_PORT))  # open up a socket that anyone may connect to
    s.listen(1)
    flowLock.acquire()
    print("Starting TCP server to receive user commands")
    print("Listening on port %s\n" % (SETTINGS_SERVER_PORT))
    flowLock.release()
    # Always look for connections
    while 1:
        conn, addr = s.accept()
        flowLock.acquire()
        print("Connected to client with address:port pair %s:%s\n" % (addr[0], str(addr[1])))
        flowLock.release()
        while 1:
            # Receive the byte data
            byteData = conn.recv(BUFFER_SIZE)
            if not byteData:
                break
        
        
            stringData = byteData.decode("UTF-8")   # convert the byte data to a string
            userMessage = json.loads(stringData)   # convert the string into a dictionary
            
            # settings, discovery, calibrate
            
            
            # Two types of data to be sent... calibrate, or settings update
            if userMessage["type"] == "calibrate":
                # run calibration stage
                flowLock.acquire()
                print("Received CALIBRATE message from user\n")
                if bypass_calibration:
                    try:
                        with open('good_calibration_parameters.json') as parameterFile:
                            parameters = json.load(parameterFile)
                        M = parameters['M']
                        B = parameters['B']
                        print("Loaded the following parameters:")
                        print("\tM = " + str(M))
                        print("\tB = " + str(B))
                    except IOError as e:
                        print("Can't load parameters")
                else:
                    M,B = runCalibration()
                didCalibrate = True
                flowLock.release()
            elif userMessage["type"] == "load_calibrate":
                flowLock.acquire()
                print("Received LOAD_CALIBRATE message from user\n")
                
                calibration_load_success = False
                
                try:
                    with open('calibration_parameters.json') as parameterFile:
                        parameters = json.load(parameterFile)
                    M = parameters['M']
                    B = parameters['B']
                    print("Loaded the following parameters:")
                    print("\tM = " + str(M))
                    print("\tB = " + str(B))
                    calibration_load_success = True
                except IOError as e:
                    print("Can't load parameters")
                
                responseData = {
                    "calibration_load_success": calibration_load_success   
                }
                responseMessage = bytes(json.dumps(responseData), 'utf-8')
                conn.sendall(responseMessage)
                
                didCalibrate = True
                flowLock.release()
                
            elif userMessage["type"] == "settings":
                # extrapolate and store the user settings in the system
                flowLock.acquire()
                print("Recived SETTINGS message from user\n")
                print("Received the following settings:")
                print("\tSensitivity:\t%d\n" %(userMessage["sensitivity"]))
                if didCalibrate:
                    sensitivity = userMessage["sensitivity"]
                    didReceiveUserSettings = True
                else:
                    print("DID NOT PROPERLY CALIBRATE\n")
                flowLock.release()
            
            elif userMessage["type"] == "start_listening":
                flowLock.acquire()
                print("Received START LISTENING message from user\n")
                flowLock.release()
                if didReceiveUserSettings:
                    listen_thread = threading.Thread(target=listen, args=(M, B, sensitivity))
                    listen_thread.start()
                else:
                    flowLock.acquire()
                    print("DID NOT PROPERLY RECEIVE USER SETTINGS\n")
                    flowLock.release()
                
            elif userMessage["type"] == "stop_listening":
                flowLock.acquire()
                print("Received STOP LISTENING message from user")
                stopListening()
                listen_thread.join()
                print("Successfully stopped listening\n")
                flowLock.release()
                
            
            else:
                flowLock.acquire()
                print("Received invalid message from user (neither calibrate nor settings message\n)")
                flowLock.release()
                
        conn.close()


if __name__ == "__main__":
    
    UDPthread = threading.Thread(target=UDPserver, args=())
    UDPthread.start()

