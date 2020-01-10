# encoding: utf-8
import xxtea, requests, serial, time, sys

#---------- VARS --------------
url = "https://cpefiresimulation.azurewebsites.net/get"

SERIALPORT = "/dev/ttyUSB0"
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
        
        try:
            ser.open()
            print ("Starting Up Serial Monitor")
        except serial.SerialException:
            print("Serial {} port not available".format(SERIALPORT))
            exit()
    elif state == 'close':
        ser.close()

def sendUARTMessage(msg):
    ser.write(msg)

def formatList(lst):
    lst = lst[1:-1]                             # On enlève les [] de debut/fin
    lst = lst.replace('[', '').replace(']', '') # on enlèce tous les autres []
    lst = lst.split('"')                        # on split selon les ""
    lst = list(filter(None, lst))               # supressions des valeurs null
    while (',' in lst):                         # suppressions des virgules
        lst.remove(",")
    return lst

def encryptData(text):
    encrypted = xxtea.encrypt(text, key)
    return encrypted

def formatDataToSend(triplet):
    ret = triplet
    length = len(triplet)
    for i in range(52-length):
        ret += "x"
    return ret

def formatToList(myRequest):
    formattedStr = ""
    data = myRequest.text

    data = formatList(data)
    count = 1
    for x in range(len(data)):
        if(count%4 != 0):
            formattedStr += data[x] + ','
        else:
            formattedStr += data[x] + ';'
        count += 1
    listSplittedPointVirgule = formattedStr.split(';')
    listSplittedPointVirgule.pop()  # pour enlever le dernier element (qui est vide)
    data = ""
    return listSplittedPointVirgule


def main():
    myRequest = requests.get(url)
    if myRequest.status_code == 200:
        listSplittedPointVirgule = formatToList(myRequest)
        myData = ""
        hasMyData = False
        for triplet in listSplittedPointVirgule:
            if hasMyData :
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"+myData+"!!!")
                hasMyData = False
            new = triplet.split(',')
            trip = new[0] + ',' + new[3] + ';'
            if (len(myData) + len(trip)) <= 52:
                myData += trip
            else:
                dataToSend = formatDataToSend(myData)
                encryptedData = encryptData(dataToSend)
                print("envois de: " + dataToSend)
                print(len(encryptedData))
                sendUARTMessage(bytes(encryptedData))
                myData = ""
                myData += trip
                hasMyData = True
            time.sleep(0.05)
        if len(myData) != 0:
            dataToSend = formatDataToSend(myData)
            encryptedData = encryptData(dataToSend)
            print("envois de: " + dataToSend)
            print(len(encryptedData))
            sendUARTMessage(bytes(encryptedData))
        '''dataToSend = formatDataToSend(myData)
        encryptedData = encryptData(dataToSend)
        print("envois de: " + dataToSend)
        print(len(encryptedData))
        sendUARTMessage(bytes(encryptedData))'''
    else:
        print("HTTP request failed, error code: " + str(myRequest.status_code))

#-------- WHILE TRUE ---------
initUART('open')
while(1):
    try:
        main()
    except KeyboardInterrupt:
        initUART('close')
        sys.exit()

