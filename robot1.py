'''
Atividade Inicial de Robótica Computacional

*Objetivo - Seguir uma parede próximo ao robô e parar ao alcançar a fita magnética.

*Link Vídeo Ilustrativo:
    https://www.youtube.com/watch?v=ZsNgBFPWu8I
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


def ana(valor):
    ser.write("SetMotor -{0} {0} 150\n".format(int(valor*2.1)))
    time.sleep(5)



def main():

    print("Starting connection to Neato on ports")

    ser = connect_to_serial()

    ser.write("TestMode On\n")

    time.sleep(2)
    ser.write("SetLDSRotation On\n")
    data = read()
    time.sleep(5)
    dist=[]
    ang =[0]
    while True:
        time.sleep(1)
        ser.write("GetLDSScan\n")
        data = read()
        data = data.split(',')
        time.sleep(1)

        for distancia in range(4,len(data)-1,3):
            if int(data[distancia]) > 0 and int(data[distancia]) < 1000:
                dist = int(data[distancia])
                ang = distancia/3
                print('objeto encontrado a {0} m, no angulo de {1}'.format(data[distancia], distancia/3))


        ana(ang)

        print(data)


    print('Voce Chegou')
    ser.close()


if __name__ == "__main__":
    main()
