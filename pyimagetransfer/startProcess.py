import socket
import signal
import os
import logging
import time

from TCPSender import TCP_STATE
from TCPSender import TCPSender
from TCPReceiver import TCPReceiver

_localIP = "10.132.0.2"  # receive UDP broadcast by using '' as address
_localTCPPort = 8084
_bufferSize = 1024
_DEBUG = True

def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception:
        my_print(f"extract_ip : Exception : {Exception}")
        IP = socket.gethostbyname(socket.gethostname())
    finally:
        st.close()
    return IP


def receiveSignal(signalNumber, frame):
    # output current process id
    my_print(f"receiveSignal @ PID : {os.getpid()}")
    my_print(f"receiveSignal : {signalNumber}")
    return

def my_print(str):
    if(_DEBUG):
        print(str)

##### our entry point of the program #######
if __name__ == '__main__':

    _localIP = extract_ip()
    my_print(f"host ip = {_localIP}")

    if (_DEBUG):
        my_print(f"__main__ @ PID : {os.getpid()}")
        # signal listener
        # register the signals to be caught
        #signal.signal(signal.SIGCHLD, receiveSignal)
        #signal.signal(signal.SIGHUP, receiveSignal)
        #signal.signal(signal.SIGINT, receiveSignal)
        #signal.signal(signal.SIGQUIT, receiveSignal)
        #signal.signal(signal.SIGILL, receiveSignal)
        #signal.signal(signal.SIGTRAP, receiveSignal)
        #signal.signal(signal.SIGABRT, receiveSignal)
        #signal.signal(signal.SIGBUS, receiveSignal)
        #signal.signal(signal.SIGFPE, receiveSignal)
        #signal.signal(signal.SIGKILL, receiveSignal)
        #signal.signal(signal.SIGUSR1, receiveSignal)
        #signal.signal(signal.SIGSEGV, receiveSignal)
        #signal.signal(signal.SIGUSR2, receiveSignal)
        #signal.signal(signal.SIGPIPE, receiveSignal)
        #signal.signal(signal.SIGALRM, receiveSignal)
        #signal.signal(signal.SIGTERM, receiveSignal)

    logging.info(f"Main    : starting  @ {_localIP}:{_localTCPPort}")
    myTCPReceiver = TCPReceiver(_localIP, _localTCPPort)
    if (myTCPReceiver.tcpState.value == int(TCP_STATE.DOWN) or myTCPReceiver.tcpState.value == int(TCP_STATE.CLOSED)):
        my_print(f"No TCPReceiver server was not running. Starting a new process")
        try:
            myTCPReceiver.create_TCPProcess()
        except BaseException as err:
            print("create_TCPProcess() failed")
            print(f"Error: {err}, {type(err)}")
            my_print(f"KILL TCPReceiver server peocess.")
            myTCPReceiver.terminate_TCPProcess()
    else:
        my_print(f"TCP server is already listenning for connection")
    
    time.sleep(5)
    
    myTCPSender = TCPSender()
    myTCPSender.create_TCPProcess(_localIP, _localTCPPort)
    
    # process is spawned. no need for this to stay alive
    #while(True):
        #time.sleep(60) # Sleep for 1 minute