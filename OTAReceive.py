from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
from subprocess import call, PIPE
import time
 
# path to the folder with the temporarily stored file
datapath = b"./"
 
 
class MyHandler(BaseHTTPRequestHandler):    
 
    def do_POST(client):
        if client.path == "/postArduinoCode":
            # a new file for Arduino is coming
            length = client.headers['content-length']
            data = client.rfile.read(int(length))
            contentType = client.headers.get('Content-Type')
            filename = (client.headers.get('filename')).encode()
            file = open(datapath + filename, 'wb')
            file.write(data)
            file.close()
            cmd = b"/usr/share/arduino/hardware/tools/avrdude -C /usr/share/arduino/hardware/tools/avrdude.conf -v -p atmega328p -c arduino -P /dev/ttyACM0 -b 115200 -D -Uflash:w:" + datapath + filename + b":i"
            print(cmd)
            proc = subprocess.Popen(cmd, stderr=PIPE, shell = True)
            print("Done")
            res = read_stderr(proc)
            client.send_response(200)
            client.send_header(b'Content-type', 'text/html')
            client.end_headers();
            client.wfile.write(res) 
 
def read_stderr(proc):
    res = b""
    for line in proc.stderr:
        res += line
    return res          
             
         
def main():
    try:
        # Start webserver
        server = HTTPServer(('',8080), MyHandler)
        print('started httpserver on port 8080 ...')
        print('stop with pressing Ctrl+C')
        server.serve_forever()
  
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()
 
if __name__ == '__main__':
    main()
