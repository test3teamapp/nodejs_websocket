import socket
from time import time
import cv2
#import io
import numpy as np
import threading
import logging
from multiprocessing import Process, Value, Array
from multiprocessing import Queue
import time
from enum import IntEnum
import os
# for converting cv2 image to PIL Image, to feed the detector
from PIL import Image

class TCP_STATE(IntEnum):
    DOWN = 1
    LISTENING = 2
    CONNECTED = 3
    CLOSED = 4

class TCPReceiver:
    """Class for spawning and controlling a process for openning a TCP connection for receiving images """

    # variables here are common to all instances of the class #


    def __init__(self, localIP, tcpPort): 
        self.localIP = localIP
        self.tcpPort = tcpPort

        self.startTCP = Value('B',0)
        self.tcpState = Value('i',int(TCP_STATE.DOWN))
        self.tcpProcess = Process()


    def setIPandPort(self,localIP, tcpPort):
        self.localIP = localIP
        self.tcpPort = tcpPort

# https://stackoverflow.com/questions/48024720/python-how-to-check-if-socket-is-still-connected
    def is_socket_closed(self,sock: socket.socket) -> bool:
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            logging.exception(
                "unexpected exception when checking if a socket is closed")
            return False
        return False

    def recvSome(self,sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf:
                return b'\x00'
            buf += newbuf
            count -= len(newbuf)
        return buf

    def process_TCPServer(self, ipaddr, port):

        logging.info(f"{os.getpid()} : TCPReceiver : starting @ {ipaddr}:{port} ")

        # If you run an interactive ipython session, and want to use highgui windows, do cv2.startWindowThread() first.
        # In detail: HighGUI is a simplified interface to display images and video from OpenCV code.
        #cv2.startWindowThread()
        #cv2.namedWindow("preview")
        #cv2.moveWindow("preview", 20, 20)

        # Use default library installation
        #jpeg = TurboJPEG()

        # TCP socket
        TCPServerSocket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM)
        try:
            TCPServerSocket.bind((self.localIP, self.tcpPort))
        except BaseException as err:
            print(f"{os.getpid()} : TCPReceiver : port binding failed")
            print(f"{os.getpid()} : TCPReceiver : Error: {err}, {type(err)}")
            return
        # wait
        print(f"{os.getpid()} : TCPReceiver : server up and listening")
        self.tcpState.value = int(TCP_STATE.LISTENING)        
        TCPServerSocket.listen()
        while(self.startTCP.value):
            # wait for connection
            if ( self.tcpState.value != int(TCP_STATE.CONNECTED)):
                print(f"{os.getpid()} : TCPReceiver : Waiting for connection")
                # accepts TCP connection
                TCPconnection, addr = TCPServerSocket.accept()
                print(f"{os.getpid()} : TCPReceiver : server accepted connection from {addr}")
                self.tcpState.value = int(TCP_STATE.CONNECTED)

        
            try:
                lengthAsBytes = self.recvSome(TCPconnection, 4)
                intLength = int.from_bytes(lengthAsBytes, "little")
                #print(f"image size in bytes: {intLength}")
                if (intLength > 0):
                    imageData = self.recvSome(TCPconnection, intLength)

                    # arbitrary logical number for a jpg image of resonalble size
                    if (len(imageData) > 1000):
                        # display image
                        #buffer = io.BytesIO(message)
                        # buffer.seek(0)
                        #inp = np.asarray(bytearray(message), dtype=np.uint8)
                        i = cv2.imdecode(np.frombuffer(
                            imageData, dtype=np.uint8), cv2.IMREAD_COLOR)
                        cv2.imwrite("frames/frame.jpg", i)
                        #i = jpeg.decode(message)
                        #cv2.imshow("preview", i)
                        # cv2.waitKey(0)
                         # WE NEED TO TRANSFORM THE CV2 image TO A PIL Image
                        #img = cv2.cvtColor(i, cv2.COLOR_BGR2RGB)
                        #im_pil = Image.fromarray(img)                       

                else:
                    # if length of image buffer is 0, check if connection is closed
                    if (self.is_socket_closed(TCPconnection)):
                        print(f"{os.getpid()} : TCPReceiver : Socket closed")                        
                        self.tcpState.value = int(TCP_STATE.CLOSED)                        
                        

            except BaseException as err:
                print(f"{os.getpid()} : TCPReceiver : Unexpected error {err}, {type(err)}")
                break

        TCPconnection.close()
        TCPServerSocket.close()
        self.startTCP.value = 0
        self.tcpState.value = int(TCP_STATE.DOWN)        
        logging.info(f"{os.getpid()} : TCPReceiver : finishing")
        print(f"{os.getpid()} : TCPReceiver : finishing")

    def create_TCPProcess(self):
        # check if TCP Process is running
        print(f"{os.getpid()} : TCPReceiver : create_TCPProcess : current state is : {self.tcpState.value}")
        if (self.tcpState.value == int(TCP_STATE.DOWN) or self.tcpState.value == int(TCP_STATE.CLOSED)):
            self.startTCP.value = 1
            self.tcpProcess = Process(
                target=self.process_TCPServer, args=(self.localIP, self.tcpPort))
            self.tcpProcess.start()

    def terminate_TCPProcess(self):
        self.startTCP.value = 0
        self.tcpState.value = int(TCP_STATE.DOWN)
        self.tcpProcess.terminate()
        self.tcpProcess.kill()