import sys
sys.path.append('..')
import robot.plc

truss = robot.plc.Truss('192.168.1.12')

input('按任意键，进行下一步：')
print('a pos:',truss.a_pos())
truss.a_move([0,3000,0])
