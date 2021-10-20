import sys
sys.path.append('..')
import robot.plc

truss = robot.plc.Truss('192.168.1.105',area_x=(-3400,3200),area_y=(20,3800),area_z=(0,600))

print('a pos:',truss.a_pos())
print('a pos:',truss.b_pos())