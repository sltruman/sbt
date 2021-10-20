import sys
sys.path.append('..')
import robot.plc
import time

truss = robot.plc.Truss('192.168.1.105',dbs=[27,28],
    area_x=(-3400,3200),area_y=(20,8000),area_z=(0,600))

truss.a_magnetic_dot(
    [224,19,
    255,15,
    192,7],False)
    