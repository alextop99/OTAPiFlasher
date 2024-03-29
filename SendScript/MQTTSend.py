import time, sys, hashlib, getopt
import paho.mqtt.client as paho
from paho import mqtt
from datetime import datetime
from config import settings

## Server config
server = settings.server
port = settings.port

## User config
username = settings.username
password = settings.password

## Device config
topic = settings.topic
qos = settings.qos

## Send config
BLOCK_SIZE=2000

## Pong message
pongReceived = False
pongTimestamp = None

resReceived = False

## RECEIVE FUNCTIONS FOR VALIDATION
inHashFunc = hashlib.md5()
outFileName = b""
fileData = b""
file = None

def process_message(msg):
    global outFileName, fileData, file, pongReceived, pongTimestamp, resReceived

    msg_in=msg.decode("utf-8")
    msg_in=msg_in.split(",,")

    if msg_in[0] == "pong":
        pongReceived = True
        pongTimestamp = msg_in[1]
    if msg_in[0] == "res":
        resReceived = True
        print(str(msg_in[1]))
    if msg_in[0] == "header":
        outFileName = "copy_" + msg_in[1]
        print("Opening file: " + outFileName)
        file = open(outFileName, "wb")
    elif msg_in[0] == "end":
        inHashFunc.update(fileData)
        in_hash_final=inHashFunc.hexdigest()
        if in_hash_final==msg_in[2]: 
            print("File copied OK -valid hash  ",in_hash_final)
            file.write(fileData)
        else:
            print("Bad file receive   ",in_hash_final)
        file.close()
        outFileName = b""
        fileData = b""
        file = None
    else:
        if file is not None:
            fileData += msg

def on_message(client, userdata, message):
    process_message(message.payload)

def on_publish(client, userdata, mid):
    client.mid_value=mid
    client.puback_flag=True  

## waitfor loop
def wait_for(client,msgType,period=0.25,wait_time=40,running_loop=False):
    client.running_loop=running_loop
    wcount=0

    while True:
        if msgType=="PUBACK":
            if client.on_publish:        
                if client.puback_flag:
                    return True
     
        if not client.running_loop:
            client.loop(.01) 

        time.sleep(period)
        wcount+=1
        if wcount>wait_time:
            print("return from wait loop taken too long")
            return False

def send_header(client, filename):
    header="header"+",,"+filename
    print("Sending header: " + header)
    header=bytearray(header,"utf-8")
    c_publish(client,topic,header,qos)

def send_ping(client, period=0.25, wait_time=40):
    pingmsg="ping"+",,"+str(datetime.now())
    pingmsg=bytearray(pingmsg,"utf-8")
    c_publish(client, topic, pingmsg, qos)

    wcount = 0
    while not pongReceived:
        time.sleep(period)
        wcount+=1
        if wcount>wait_time:
            print("Ping took too long, failing file send!!")
            return False
    return True

def send_file(client, filename):
    out_hash_md5 = hashlib.md5()
    fileToRead = open(filename, "rb")
    chunk = fileToRead.read(BLOCK_SIZE)
    while chunk:
        c_publish(client,topic,chunk,qos)
        out_hash_md5.update(chunk)
        chunk = fileToRead.read(BLOCK_SIZE)

    return out_hash_md5.hexdigest()

def send_end(client, filename, filehash):
    end="end"+",,"+filename+",,"+filehash
    print("Sending end: " + end)
    end=bytearray(end,"utf-8")
    c_publish(client,topic,end,qos)

def c_publish(client, topic, message, qos):
    res, mid=client.publish(topic, message, qos)
    if res==0:
        if wait_for(client,"PUBACK",running_loop=True):
            if mid==client.mid_value:
                client.puback_flag=False #reset flag
            else:
                print("quitting")
                raise SystemExit("not got correct puback mid so quitting")
        else:
            raise SystemExit("not got puback so quitting")

def waitForResult(period=0.25, wait_time=40):
    global resReceived

    wcount = 0
    while not resReceived:
        time.sleep(period)
        wcount+=1
        if wcount>wait_time:
            print("Result took too long, probably failed flash!!")
            return False
    return True

# Main function
def main(argv):
    filename = ""
    try:
        opts, args = getopt.getopt(argv,"hf:",["hexfile="])
    except getopt.GetoptError:
        print('GetoptError: MQTTSend -f <hexfile>')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('MQTTSend -f <hexfile>')
            sys.exit()
        elif opt in ("-f", "--hexfile"):
            filename = arg.strip()
    
    if filename == "":
        print('MQTTSend -f <hexfile>')
        sys.exit()
    
    client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)

    client.puback_flag=False
    client.mid_value=None
    client.on_message = on_message
    client.on_publish = on_publish

    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    client.username_pw_set(username, password)
    client.connect(server, port)

    client.loop_start()
    
    client.subscribe(topic, qos)

    if send_ping(client):
        send_header(client, filename)

        filehash = send_file(client, filename)

        send_end(client, filename, filehash)

        waitForResult()

    client.disconnect()
    client.loop_stop()

if __name__ == "__main__":
    main(sys.argv[1:])