import sys
sys.path.append('..')
import robot.plc
from socket import *

plate_png_file = '/M210608Q345B8A05/large_first_result/plate.png'

truss = robot.plc.Truss('192.168.1.105',dbs=[13,14],
    name='7',area_x=(-3400,3200),area_y=(20,8000),area_z=(0,1000.99))
print(truss.locate3_calculating_offset('192.168.10.15',30002,
    [100,100],[100,100],
    plate_png_file))