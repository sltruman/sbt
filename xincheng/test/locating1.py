import sys
sys.path.append('..')
from socket import *
import snap7
from time import sleep

host,port = '192.168.10.60',30002
name = 7

plc = snap7.client.Client()
plc.connect('192.168.1.11', 0, 1)

print('locating {} {}  ...'.format(host, port))
plc.db_write(51,0,(1).to_bytes(1,'big'))
plc.db_write(51,1,(1).to_bytes(1,'big'))
plc.db_write(51,2,(300).to_bytes(2,'little')) #offset
plc.db_write(51,4,(300).to_bytes(2,'little')) #offset

sleep(10)

try:
    sock = socket(AF_INET,SOCK_STREAM)
    sock.settimeout(60)
    sock.connect((host,port))
    
    errc = 0
    for c in '710@7@0@0@0@0@0@0@0'.encode():
        errc += c
    
    sock.send('710@7@0@0@0@0@0@0@0@{}@0'.format(errc).encode())
    val = sock.recv(1024).decode().split('@')
    print(val)
    if 1 != int(val[10]): raise ValueError
    corner = (float(val[6]),float(val[7]))
    degree = (float(val[8]) + 90)
finally:
    sock.close()
    plc.db_write(51,0,(2).to_bytes(1,'big'))
    plc.db_write(51,1,(2).to_bytes(1,'big'))
    plc.db_write(51,2,(0).to_bytes(2,'little')) #offset
    plc.db_write(51,4,(0).to_bytes(2,'little')) #offset.
    plc.disconnect()
    sleep(4)
print('located {} {}'.format(corner,degree))