import time, hashlib
from datetime import datetime

## Pong message
pongReceived = False
pongTimestamp = None

resReceived = False

## Send config
BLOCK_SIZE=2000

## RECEIVE FUNCTIONS FOR VALIDATION
inHashFunc = hashlib.md5()
outFileName = b""
fileData = b""
file = None

def process_message(msg, userdata):
    global outFileName, fileData, file, pongReceived, pongTimestamp, resReceived

    msg_in=msg.decode("utf-8")
    msg_in=msg_in.split(",,")

    if msg_in[0] == "pong":
        pongReceived = True
        pongTimestamp = msg_in[1]
    if msg_in[0] == "res":
        resReceived = True
        changeOutputText = userdata['changeOutputText']
        changeOutputText(str(msg_in[1]))
        #print(str(msg_in[1]))
    if msg_in[0] == "header":
        path = msg_in[1].split("/")
        outFileName = "copy_" + path[-1]
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
    process_message(message.payload, userdata)

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

def send_header(client, path, topic, qos):
    filename = path.split("/")[-1]
    header="header"+",,"+filename
    print("Sending header: " + header)
    header=bytearray(header,"utf-8")
    c_publish(client,topic,header,qos)

def send_ping(client, topic, qos, period=0.25, wait_time=40):
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

def send_file(client, path, topic, qos):
    out_hash_md5 = hashlib.md5()
    fileToRead = open(path, "rb")
    chunk = fileToRead.read(BLOCK_SIZE)
    while chunk:
        c_publish(client,topic,chunk,qos)
        out_hash_md5.update(chunk)
        chunk = fileToRead.read(BLOCK_SIZE)

    return out_hash_md5.hexdigest()

def send_end(client, path, filehash, topic, qos):
    filename = path.split("/")[-1]
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