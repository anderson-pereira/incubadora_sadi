import serial
import serial.tools.list_ports
import re
import queue
import threading, time

expressoesRegulares = list()
portaSerial = 0
queue = queue.Queue(20)
ExitThread = False

# TS:   Temperatura configurada em °C
# TR:   Temperatura real no momento da leitura em °C
# HM:   Umidade lida em %
# FAN:  Velocidade do FAN em %
# ALM1: Alarme 01 em HH:MM:SS
# ALM1: Alarme 02 em HH:MM:SS
# RTC:  Horário do RTC em HH:MM:SS
# PI:   Ganhos do controlador PI [Kp:Ki] (para debug)


regexList = [
    r'(TS):(\d{1,2}.\d{1,2})[\n\r]*$',
    r'(TR):(\d{1,2}.\d{1,2})[\n\r]*$',
    r'(HM):(\d{1,2}.\d{1,2})[\n\r]*$',
    r'(FAN_SPEED):(\d{1,3})[\n\r]*$',
    r'(FAN_STATUS):(\d{1})[\n\r]*$',   
    r'(ALM):(\d{1,2}:\d{1,2}:\d{1,2})[\n\r]*$', 
    r'(ALM_STATUS):(\d{1})[\n\r]*$',    
    r'(RTC):(\d{1,2}:\d{1,2}:\d{1,2})[\n\r]*$',
    r'(MOD_SEG):(\d{1})[\n\r]*$'
]


def getSerialPorts () :
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return ports


def serial_read(s):
    global portaSerial
    while not ExitThread:
        line = s.readline().decode()
        queue.put(line)


def initSerialCom (serialDevice) :
    global portaSerial, expressoesRegulares

    portaSerial = serial.Serial(serialDevice, 9600, timeout=5)
    
    for rgx in regexList:
        expressoesRegulares.append(re.compile(rgx))

    thread1 = threading.Thread(target=serial_read, args=(portaSerial,),).start()


def closeSerialCom () :
    global portaSerial 
    try:
        portaSerial.flush()
        portaSerial.flushInput()
        portaSerial.flushOutput()
        portaSerial.close()
        ExitThread = True
    except:
        pass



def readDataFromSerial () :
    rectMsg = list()
    try:
        
        if queue.empty() : return 0
        if queue.qsize() < len(expressoesRegulares) : return 0

        line = queue.get(True, 1)
        while "TS:" not in line :
            if queue.empty() : return 0
            line = queue.get(True, 1)

        rectMsg.append( line )    

        for _ in range(len(expressoesRegulares)-1) :
            if queue.empty() : return 0
            line = queue.get(True, 1)
            rectMsg.append( line )
            
    except Exception as err:
        print (err)
        portaSerial.flushInput()
        return 0
    portaSerial.flushInput()
    print (rectMsg)
    return rectMsg

def sendDataToSerial (data) :
    portaSerial.flushOutput()
    portaSerial.write((data).encode())

def dataParse (msgList) :
    checkedVals = dict()

    if len(msgList) != len(expressoesRegulares):
        return 0
    
    for i in range(len(msgList)):
        reSearch = expressoesRegulares[i].search(msgList[i])
        print(reSearch)
        if reSearch :
            checkedVals[reSearch.group(1)] = reSearch.group(2)
        else :
            return 0
    
    return checkedVals
