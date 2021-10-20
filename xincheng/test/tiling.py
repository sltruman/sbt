import sys
sys.path.append('..')
from socket import *

def tile(host,port,xyz,size,source):
    '''
    放置点计算
    '''
    print(f'tiling {host} {port} {xyz} {size} {source}')
    
    try:
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(20)
        sock.connect((host,port))
        sock.sendall(f'ResizePallet {size[0]} {size[1]}\n'.encode())
        buffer = sock.recv(1024)
        sock.sendall(source.encode())
        buffer = sock.recv(1024)
        vals = []
        val = {}
        for row in buffer.decode().split("\n"):
            columns = row.split(' ')
            if len(columns) < 4 or row == '0 0.000000 0.000000 0.000000 0 0 0': 
                vals.append(val)
                val = {}
                continue

            n = columns[0]
            #将放置点偏移到xyz
            x = xyz[0] + float(columns[1])
            y = xyz[1] + float(columns[2])
            z = xyz[2] + float(columns[3])

            val[n] = (x,y,z)
    finally:
        sock.close()
    print(f'tiled {vals}')
    return val


tiling_source = [
    'a 1 50 50\n',
    'b 1 50 50\n',
    'c 1 50 50\n',
    'd 1 50 50\n'
]

s = ''
for i in tiling_source:
    s += i

tile('localhost',9898,(0,0,0),(510,510),s)