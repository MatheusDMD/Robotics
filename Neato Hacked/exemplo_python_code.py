#!/usr/bin/env python
# -*- coding:utf-8 -*-

import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from math import fabs
from sensor_msgs.msg import LaserScan


velocidade_objetivo = Twist();
pub = rospy.Publisher('/cmd_vel', Twist, queue_size=3)

def notificacao(data):
    global velocidade_objetivo
    """
        Codigo de notificacao executado sempre que chega uma leitura da odometria

        Esta leitura chega na variavel data e e'  um objeto do tipo odometria
    """
    # Todo: a partir de uma leitura da odometria faça
    # um publish na velocidade até que o robô tenha andado 2 metros
    velocidade_x = data.ranges[0]
    if velocidade_x <= 0.35:
        velocidade_x = 0
    # print(velocidade_x)
    print("callback ")
    velocidade_objetivo = Twist()
    velocidade_objetivo.linear.x = velocidade_x / 4
    velocidade_objetivo.linear.y = 0
    velocidade_objetivo.linear.z = 0
    # print "A velocidade objetivo bla bla", velocidade_objetivo.linear.x






def controle():
    """
        Função inicial do programa
    """
    rospy.init_node('Exemplo_Python')
    rospy.Subscriber('/stable_scan', LaserScan, notificacao)
    # Initial movement.
    pub.publish(velocidade_objetivo)
    print("bla")
    while not rospy.is_shutdown():  # Faz um loop infinito para o ROS nao retornar
        rospy.sleep(0.2)
        print velocidade_objetivo.linear.x
        pub.publish(velocidade_objetivo)



if __name__ == '__main__':
    try:
        controle()
    except rospy.ROSInterruptException:
        pass
