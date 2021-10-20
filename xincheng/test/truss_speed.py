import sys
sys.path.append('..')
import robot.plc

truss = robot.plc.Truss('192.168.1.105',dbs=[13,14],area_x=(-3400,3200),area_y=(20,3800),area_z=(0,600))

truss.a_speed([200,200,100,50])
truss.b_speed([200,200,100,50])