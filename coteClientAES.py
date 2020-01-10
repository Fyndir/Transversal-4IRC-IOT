# encoding: utf-8
import xxtea, requests, serial, time, sys
#from influxdb_client import InfluxDBClient
import multiprocessing as mp



#---------- VARS --------------
url = "https://emergencymanager.azurewebsites.net/fire/send"

SERIALPORT = "/dev/ttyUSB1"
BAUDRATE = 115200
ser = serial.Serial()

with open("keyFile.pem", "r") as fk:
    key = fk.readline()
    fk.close()

#---------- FUNCTIONS --------------
def initUART(state):
    if state == 'open':
        # ser = serial.Serial(SERIALPORT, BAUDRATE)
        ser.port = SERIALPORT
        ser.baudrate = BAUDRATE
        ser.bytesize = serial.EIGHTBITS  # number of bits per bytes
        ser.parity = serial.PARITY_NONE  # set parity check: no parity
        ser.stopbits = serial.STOPBITS_ONE  # number of stop bits
        ser.timeout = None  # block read

        # ser.timeout = 0             #non-block read
        # ser.timeout = 2              #timeout block read
        ser.xonxoff = False  # disable software flow control
        ser.rtscts = False  # disable hardware (RTS/CTS) flow control
        ser.dsrdtr = False  # disable hardware (DSR/DTR) flow control
        # ser.writeTimeout = 0     #timeout for write
        print ("Starting Up Serial Monitor")
        try:
            ser.open()
        except serial.SerialException:
            print("Serial {} port not available".format(SERIALPORT))
            exit()
    elif state == 'close':
        ser.close()

def readUARTMessage():
    ret = ser.read(56) # lis X octets
    return ret    # on enleve le caractere de retour a la ligne pour decrypter 

def parseX(myStr):
    return myStr.replace("x", "")

def sendHttp(buffer):
    while(1):
        try:       
            requests.post(url, data=str(buffer.get()))
            #print('p2 : '+ req.text)        
        except:
            print("error")

it = 0
myStr = ""

def main():
    global myStr, it
    print('debut')
    print('Attente de message')
    encryptedData = bytes(readUARTMessage())
    print('decryptage du message : '+encryptedData)
    decrypted = xxtea.decrypt(encryptedData, key)
    print('message decrypte : '+decrypted)
    finalRet = parseX(str(decrypted))
    print('enleve les x : '+finalRet)
    if(len(finalRet) != 0):
        print('ajout dans le buffer de '+ str(finalRet))
        myStr += str(finalRet)
        for sep in str(finalRet):
            if sep == ';':
                it += 1
        print('nb données dans buffer :'+str(it))
    if it >= 50:
        print('envoie dans la queue de P2 : ' + myStr)
        bufferPost.put(myStr)
        myStr = ""
        it = 0
        #print(finalRet)
        #bufferPost.put(str(finalRet))


#---------- WHILE TRUE --------------
initUART('open')
bufferPost = mp.Queue(600)
verrou = mp.Lock()
procPost = mp.Process(target=sendHttp, args=(bufferPost,))
procPost.start()

while(1):
    try:
        main()
    except KeyboardInterrupt:
        initUART('close')
        procPost.terminate()
        sys.exit()