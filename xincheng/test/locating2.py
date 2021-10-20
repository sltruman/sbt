import sys
sys.path.append('..')
import robot.plc
from socket import *

truss = robot.plc.Truss('192.168.1.105',dbs=[13,14],
    name='7',area_x=(-3400,3200),area_y=(20,8000),area_z=(0,1000.99))

print(truss.locate2('192.168.10.15',30002,
    [-1449.29, 6206.12, 926.52,90],
    [3016.31, 6241.10, 1000.00,90]))