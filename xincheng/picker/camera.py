from socket import *
import traceback
from snap7 import exceptions
import os
class LocatingError(Exception):pass

def locate5_calculating_offset(name,host,port,corner,edge):
    try:
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host,port))
        sock.send(f'pick;1;{corner[0]};{corner[1]};{edge[0]};{edge[1]};\n'.encode())
        val = sock.recv(1024).decode().split(';')
        print(val)

        if val[0] == 'pick':
            return [float(val[1]),float(val[2])],float(val[3])
        else:
            raise Exception
    finally:
        sock.close()
    pass


def locate5_take_edge(name,host,port,point_A):
    try:
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host,port))

        sock.send(f'takepic;0;{point_A[0]};{point_A[1]};\n'.encode())
        val = sock.recv(1024).decode().split(';')
        print('拍边',val)

        if val[0] != 'ok':
            raise Exception
    except:
        pass
    finally:
        sock.close()


def locate5_take_corner(name,host,port,point_B):
    try:
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host,port))

        sock.send(f'takepic;1;{point_B[0]};{point_B[1]};\n'.encode())
        val = sock.recv(1024).decode().split(';')
        print('拍角',val)

        if val[0] != 'ok':
            raise Exception
    except:
        pass
    finally:
        sock.close()

def locate5(name,host,port,plate_png_path):
    os.system(f'cp data{plate_png_path} db/vision/{name}/template/templ.png')
    
    try:
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(60)
        sock.connect((host,port))

        sock.send(f'pick;0;\n'.encode())
        val = sock.recv(1024).decode().split(';')
        print(val)
        
        if val[0] == 'pick':
            return [float(val[1]),float(val[2])],float(val[3])
        else:
            raise Exception
    finally:
        sock.close()
    pass

import robot.truss
from snap7.exceptions import Snap7Exception
from copy import deepcopy

def take_photos(name,params):
    plc = params['plc']
    plc2_port = params['plc2.port']
    plc_areas = params['plc.areas']
    plc_dbs = params['plc.dbs']
    point_A,point_B = deepcopy(params['locating.points.A']),deepcopy(params['locating.points.B'])
    point_A[0] = plc_areas[0][0] if point_A[0] <= plc_areas[0][0] else point_A[0]
    point_B[0] = plc_areas[0][1] if point_B[0] >= plc_areas[0][1] else point_B[0]

    try:
        truss = robot.truss.Truss(name,plc[0],plc[1],plc[2],plc[3],plc2_port,plc_dbs,plc_areas[0],plc_areas[1],plc_areas[2],plc_areas[3],plc_areas[4])
        truss.a_join()
        truss.b_join()

        try:
            host,port = params['locating']
            if params['locating.version'] == 8:
                truss.b_move(point_B)
                truss.b_join()
                locate5_take_corner(name,host, port, point_B)
                truss.b_move(point_A)
                truss.b_join()
                locate5_take_edge(name,host, port, point_A)
            else:
                raise Exception
        except:
            traceback.print_exc()
            raise Exception('拍照失败，桁架没有移动到拍照点或相机服务异常！')
    except:
        traceback.print_exc()
        raise Exception('拍照失败，桁架没有移动到拍照点或相机服务异常！')
    finally:
        if truss:
            truss.a_reset()
            truss.b_reset()
            
def calculating_offset(name,params,x0,y0,x1,y1):
    host,port = params['locating']
    point_B = params['locating.points.B']

    try:
        if params['locating.version'] == 8:
            corner,degree = locate5_calculating_offset(name,host, port, (x0,y0), (x1,y1))
        else:
            raise Exception
    except:
        traceback.print_exc()
        raise Exception('定位异常，计算失败！')

    return corner,degree

