import socket
import time
from datetime import datetime
import cv2
#import io
import numpy as np
import threading
import logging
from multiprocessing import Process, Value
from multiprocessing import Queue
import base64
from enum import IntEnum
import os

# for converting cv2 image to PIL Image, to feed the detector
from PIL import Image

_SHOULD_DETECT = False
_DEBUG = True

class TCP_STATE(IntEnum):
    DOWN = 1
    LISTENING = 2
    CONNECTED = 3
    CLOSED = 4

class TCPSender:
    """Class for spawning and controlling a process for openning a TCP connection for sending images """

    # variables here are common to all instances of the class #


    def __init__(self):
        self.remoteIP = ""
        self.tcpPort = -1
        # see https://docs.python.org/2/library/array.html#module-array
        # for ctypes available for Multiprocessing.Values
        self.startTCP = Value('B',0)
        self.tcpState = Value('i',int(TCP_STATE.DOWN))
        self.tcpProcess = Process()
        # created an unbounded queue for accessing the state variable from the new process
        #self.queue = Queue()
        #self.queue.put(self.tcpState)

    def setRemoteIPandPort(self,remoteIP, tcpPort):
        self.remoteIP = remoteIP
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

    def process_TCPServer(self, ipaddr, port):#, stateQueue):

        logging.info(f"{os.getpid()} : TCPSender : connecting @ %s:%s ", ipaddr, port)
        self.my_print(f"{os.getpid()} : TCPSender : connecting @ {ipaddr}:{port} ")

        # If you run an interactive ipython session, and want to use highgui windows, do cv2.startWindowThread() first.
        # In detail: HighGUI is a simplified interface to display images and video from OpenCV code.
        #cv2.startWindowThread()
        #cv2.namedWindow("preview")
        #cv2.moveWindow("preview", 20, 20)

        # TCP socket
        TCPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while (self.tcpState.value !=  int(TCP_STATE.CONNECTED)):
            try:
                TCPServerSocket.connect((ipaddr , port))
                self.my_print(f"{os.getpid()} : TCPSender : connection established @ {ipaddr}")
                self.tcpState.value = int(TCP_STATE.CONNECTED)
            except BaseException as err:
                print(f"{os.getpid()} : TCPSender : remote connection failed")
                print(f"{os.getpid()} : TCPSender : Error: {err}, {type(err)}")
                print(f"{os.getpid()} : TCPSender : trying again in 1 minute")
                time.sleep(60) 
                #return


        cap = cv2.VideoCapture("sample_640x360.mp4") # or camera id
        numOfFrames = 0
        start = time.time()

        while(self.startTCP.value):
            try:

                #############  --- capture and send image

                if cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    numOfFrames += 1
                    if (numOfFrames == 30):
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        fps = 30 / (time.time() - start)
                        self.my_print(f"camera fps={fps} / time = {current_time}")
                        start = time.time()
                        numOfFrames = 0

                    encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
                    result, imgencode = cv2.imencode('.jpg', frame, encode_param)
                    data = np.array(imgencode)
                    ba1 = bytearray(data.tobytes())
                    lengthInt = len(ba1)
                    #save lenght in a 4byte configuration
                    ba2 = bytearray(lengthInt.to_bytes(4, byteorder='little'))
                    #self.my_print(f"Sending length of image data : {lengthInt} and then data")
                    TCPServerSocket.sendall(ba2 + ba1)


            except BaseException as err:
                print(f"{os.getpid()} : TCPSender : Unexpected {err}, {type(err)}")
                self.startTCP.value = 0
                break


        #TCPconnection.close()
        cap.release()
        TCPServerSocket.close()
        self.startTCP.value = 0
        self.tcpState.value = int(TCP_STATE.DOWN)
        #stateQueue.put(self.tcpState)
        cv2.destroyAllWindows()
        logging.info(f"{os.getpid()} : TCPSender  : finishing")
        self.my_print(f"{os.getpid()} : TCPSender : finishing")

    def create_TCPProcess(self, remoteIP, tcpPort):
        self.remoteIP = remoteIP
        self.tcpPort = tcpPort
        # check if TCP Process is running

        # get the last item from the queue. the latest self.tcpState value
        #state = TCP_STATE.DOWN
        #while (not self.queue.empty()):
        #    state = self.queue.get()
        self.my_print(f"{os.getpid()} : TCPSender : create_TCPProcess : state = {self.tcpState.value}")
        if (self.tcpState.value == int(TCP_STATE.DOWN) or self.tcpState.value == int(TCP_STATE.CLOSED)):
            self.startTCP.value = 1
            self.tcpProcess = Process(
                target=self.process_TCPServer, args=(self.remoteIP, self.tcpPort))
            self.tcpProcess.start()

    def terminate_TCPProcess(self):
        self.startTCP.value = 0
        self.tcpProcess.terminate()
        self.tcpProcess.kill()
        self.tcpState.value = int(TCP_STATE.DOWN)

    def my_print(self,str):
        if(_DEBUG):
            print(str)
