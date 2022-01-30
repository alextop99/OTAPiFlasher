import requests
import sys, getopt
 
def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hu:f:",["url=","hexfile="])
    except getopt.GetoptError:
        print('GetoptError: OTASend -u <url> -f <hexfile>')
        sys.exit(2)
     
    # extract url and path from parameters
    for opt, arg in opts:
        if opt == '-h':
            print('OTASend -u <url> -f <hexfile>')
            sys.exit()
        elif opt in ("-u", "--url"):
            url = arg
        elif opt in ("-f", "--hexfile"):
            hexfile = arg.strip()
    print("url:" + str(url))
    print("hexfile:" + str(hexfile))
    print("uploading ...")
     
    # extract filename
    folders = hexfile.split("/")
    filename = folders[-1]
     
    #read file from filesystem
    data = open(hexfile, 'rb')
     
    # set header
    headers = {'filename': filename}
     
    # send file
    r = requests.post(url, data=data, headers=headers)
     
    print(r.text)
 
if __name__ == "__main__":
   main(sys.argv[1:])