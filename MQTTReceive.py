import time
import paho.mqtt.client as paho
from paho import mqtt
import hashlib
from datetime import datetime

## Server config
server = "a50f52ba5eb6490bbfb6bcd53bd555ae.s1.eu.hivemq.cloud"
port = 8883

## User config
username = "otauser"
password = "OTApassword2022"

## Device config
topic = "dev/1"
qos = 1

# Defines
inHashFunc = hashlib.md5()
filename = b""
fileData = b""
file = None

def send_pong(client):
    pongmsg="pong"+",,"+str(datetime.now())
    pongmsg=bytearray(pongmsg,"utf-8")
    client.publish(topic, pongmsg, qos)


# Message processing function
def process_message(client, msg):
    global filename, fileData, file

    msg_in=msg.decode("utf-8")
    msg_in=msg_in.split(",,")
    if msg_in[0] == "ping":
        send_pong(client)
    elif msg_in[0] == "header":
        filename = msg_in[1]
        print("Opening file: " + filename)
        file = open(filename, "wb")
    elif msg_in[0] == "end":
        inHashFunc.update(fileData)
        in_hash_final=inHashFunc.hexdigest()
        if in_hash_final==msg_in[2]: 
            print("File copied OK -valid hash  ",in_hash_final)
            file.write(fileData)
        else:
            print("Bad file receive   ",in_hash_final)
        file.close()
        filename = b""
        fileData = b""
        file = None
    else:
        if file is not None:
            fileData += msg

# Message receive callback
def on_message(client, userdata, message):
    process_message(client, message.payload)

# Main function
def main():
    client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
    
    client.on_message = on_message

    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    client.username_pw_set(username, password)
    client.connect(server, port)
    
    client.subscribe(topic, qos)

    client.loop_forever()

if __name__ == "__main__":
    main()
