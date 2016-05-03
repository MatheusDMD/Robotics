'''
Atividade Inicial de Robótica Computacional

*Objetivo - Seguir um objeto à uma distancia de 600mm até 1400mm mantendo uma distância de 600mm

*Link Vídeo Ilustrativo:
    https://www.youtube.com/watch?v=okXnH_KqIEk
'''


#!/usr/bin/env python

#!/usr/bin/env python

# Execute sudo pkill -HUP -f tcp_serial_redirect0.py antes de executar este programa
# Para desbloquear a serial



import sys
import os
import time
import signal
import threading
import socket
import codecs
import serial
from os import system

ser = None

def connect_to_serial():
    global ser
    # connect to serial port
    possible_ports = ['/dev/ttyUSB0','/dev/ttyUSB1']
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.parity   = 'N'
    ser.rtscts   = False
    #ser.xonxoff  = options.xonxoff
    ser.timeout  = 1     # required so that the reader thread can exit
    for p in possible_ports:
        ser.port = p
        try:
            ser.open()
            print "Connected on port: " + p
            return ser
        except:
            time.sleep(1)

def read():
    n = ser.inWaiting()
    data = ser.read(n)
    return data

def read_bump():
    n = ser.GetDigitalSensors()
    data = ser.read(n)
    time.sleep(1)
    return data


def ana(valor,dist):
    x = (valor*2.111)
    print "X", x
    ser.write("SetMotor -{0} {0} 150\n".format(x))
    time.sleep(5)
    y = (dist-600)
    ser.write("SetMotor {0} {0} 150\n".format(y))
    time.sleep(3)
    data = read()


def main():

    print("Starting connection to Neato on ports")

    ser = connect_to_serial()

    ser.write("TestMode On\n")

    while True:
        dist=[]
        ang =0
        time.sleep(1)
        ser.write("SetLDSRotation On\n")
        time.sleep(3)
        ser.write("GetLDSScan\n")
        time.sleep(5)
        data = read()
        time.sleep(5)
        d2 = read()
        data = data+d2
        time.sleep(4)
        data = data.split(',')
        time.sleep(4)

        for distancia in range(4,len(data)-1,3):
            #print(distancia)
            #print(data[distancia])
            if int(data[distancia]) != 0 and int(data[distancia]) > 700 and int(data[distancia]) < 1400:
                dist = int(data[distancia])
                ang = distancia/3
                print("ANG:", ang)
                print('objeto encontrado a {0} mm, no angulo de {1}'.format(data[distancia], distancia/3))

        ana(ang,dist)
        ser.write("SetLDSRotation Off\n")
        #data = read()
        print(data)
        time.sleep(4)

    print('Voce Chegou')
    ser.close()


if __name__ == "__main__":
    main()
