from time import sleep
from struct import pack,unpack
from socket import *
import os
from operator import eq
import snap7

class StopedError(Exception):pass
class OverrangeError(Exception):pass

class Truss():
    def __init__(self,name,server,port,rack,slot,port2,dbs,area_x,area_y,area_z,interference_area_x,reset_x):
        self.port = port
        self.port2 = port2

        self.area_x = area_x
        self.area_y = area_y
        self.area_z = area_z
        self.interference_area_x = interference_area_x
        self.reset_x = reset_x

        self.name = name
        self.dbs = dbs
        self.status = 88,1
        
        self.plc = snap7.client.Client()
        self.plc.connect(server, rack, slot, port)

        if port != port2:
            self.plc2 = snap7.client.Client()
            self.plc2.connect(server, rack, slot, port2)
        else:
            self.plc2 = self.plc

        locked1 = self.plc.db_read(self.dbs[1],35,1)[0]
        locked2 = self.plc2.db_read(self.dbs[2],35,1)[0]
        if locked1 & locked2 & 0b00000010: raise StopedError('桁架处于干涉区，先复位!')
        
        self.a_unlock()
        self.b_unlock()
    def __del__(self):
        if self.plc.get_connected():
            self.plc.disconnect()
            if self.port != self.port2:
                self.plc2.disconnect()
    def varify_pos(self,pos):
        if pos[0] < self.area_x[0] or pos[0] > self.area_x[1] or \
            pos[1] < self.area_y[0] or pos[1] > self.area_y[1] or \
            pos[2] < self.area_z[0] or pos[2] > self.area_z[1]:
            raise OverrangeError('坐标值超出桁架坐标范围！')
    def a_speed(self,vals=None):
        if vals:
            self.plc.db_write(self.dbs[0],6,pack('!f',vals[0])) #x
            self.plc.db_write(self.dbs[0],10,pack('!f',vals[1])) #y
            self.plc.db_write(self.dbs[0],14,pack('!f',vals[2])) #z
            self.plc.db_write(self.dbs[0],18,pack('!f',vals[3])) #r
        else:
            x = unpack('!f',self.plc.db_read(self.dbs[0],2,4))[0]
            y = unpack('!f',self.plc.db_read(self.dbs[0],6,4))[0]
            z = unpack('!f',self.plc.db_read(self.dbs[0],10,4))[0]
            r = unpack('!f',self.plc.db_read(self.dbs[0],14,4))[0]
            return x,y,z,r
    def b_speed(self,vals):
        if vals:
            self.plc.db_write(self.dbs[0],22,pack('!f',vals[0])) #x
            self.plc.db_write(self.dbs[0],26,pack('!f',vals[1])) #y
            self.plc.db_write(self.dbs[0],30,pack('!f',vals[2])) #z
            self.plc.db_write(self.dbs[0],34,pack('!f',vals[3])) #r 
        else:
            x = unpack('!f',self.plc.db_read(self.dbs[0],22,4))[0]
            y = unpack('!f',self.plc.db_read(self.dbs[0],26,4))[0]
            z = unpack('!f',self.plc.db_read(self.dbs[0],30,4))[0]
            r = unpack('!f',self.plc.db_read(self.dbs[0],34,4))[0]
            return x,y,z,r
    def a_reset(self):
        print('reset 0')
        self.plc.db_write(self.dbs[0],0,(3).to_bytes(1,'big'))
        self.a_unlock()
    def b_reset(self):
        print('reset 1')
        self.plc.db_write(self.dbs[0],1,(3).to_bytes(1,'big'))
        self.b_unlock()
    def a_pos(self):
        x = unpack('!f',self.plc.db_read(self.dbs[1],2,4))[0]
        y = unpack('!f',self.plc.db_read(self.dbs[1],6,4))[0]
        z = unpack('!f',self.plc.db_read(self.dbs[1],10,4))[0]
        r = unpack('!f',self.plc.db_read(self.dbs[1],14,4))[0]
        return x,y,z,r
    def b_pos(self):
        x = unpack('!f',self.plc.db_read(self.dbs[1],18,4))[0]
        y = unpack('!f',self.plc.db_read(self.dbs[1],22,4))[0]
        z = unpack('!f',self.plc.db_read(self.dbs[1],26,4))[0]
        r = unpack('!f',self.plc.db_read(self.dbs[1],30,4))[0]
        return x,y,z,r
    def a_move(self,pos):
        print(f'move 0 {pos}')
        self.varify_pos(pos)

        x,y,z,r = pos

        if self.interference_area_x[0] <= pos[0] and pos[0] <= self.interference_area_x[1]:
            self.a_lock()
        else:
            self.a_unlock()

        self.plc.db_write(self.dbs[0],38,pack('!f',x)) #x
        self.plc.db_write(self.dbs[0],42,pack('!f',y)) #y
        self.plc.db_write(self.dbs[0],46,pack('!f',z)) #z
        self.plc.db_write(self.dbs[0],50,pack('!f',r)) #r
        self.plc.db_write(self.dbs[0],0,(11).to_bytes(1,'big')) #移动xyr
        self.a_join()
        self.plc.db_write(self.dbs[0],0,(12).to_bytes(1,'big')) #移动z
    def b_move(self,pos):
        print(f'move 1 {pos}')
        self.varify_pos(pos)

        if self.interference_area_x[0] <= pos[0] and pos[0] <= self.interference_area_x[1]:
            self.b_lock()
        else:
            self.b_unlock()

        x,y,z,r = pos
        self.plc.db_write(self.dbs[0],70,pack('!f',x)) #x
        self.plc.db_write(self.dbs[0],74,pack('!f',y)) #y
        self.plc.db_write(self.dbs[0],78,pack('!f',z)) #z
        self.plc.db_write(self.dbs[0],82,pack('!f',r)) #r
        self.plc.db_write(self.dbs[0],1,(11).to_bytes(1,'big')) #移动xyr
        self.b_join()
        self.plc.db_write(self.dbs[0],1,(12).to_bytes(1,'big')) #移动z
    def ab_move(self,a_pos,b_pos):
        print(f'move 0 {a_pos}')
        print(f'move 1 {b_pos}')
        if b_pos[0] - a_pos[0] < 1900:
            raise OverrangeError('双臂距离过近！')

        self.varify_pos(a_pos)
        self.varify_pos(b_pos)

        if self.interference_area_x[0] <= a_pos[0] and a_pos[0] <= self.interference_area_x[1]:
            self.a_lock()
        else:
            self.b_unlock()

        if self.interference_area_x[0] <= b_pos[0] and b_pos[0] <= self.interference_area_x[1]:
            self.b_lock()
        else:
            self.b_unlock()

        self.plc.db_write(self.dbs[0],38,pack('!f',a_pos[0])) #A x
        self.plc.db_write(self.dbs[0],42,pack('!f',a_pos[1])) #A y
        self.plc.db_write(self.dbs[0],46,pack('!f',a_pos[2])) #A z
        self.plc.db_write(self.dbs[0],50,pack('!f',a_pos[3])) #A r

        self.plc.db_write(self.dbs[0],70,pack('!f',b_pos[0])) #B x
        self.plc.db_write(self.dbs[0],74,pack('!f',b_pos[1])) #B y
        self.plc.db_write(self.dbs[0],78,pack('!f',b_pos[2])) #B z
        self.plc.db_write(self.dbs[0],82,pack('!f',b_pos[3])) #B r
        
        self.plc.db_write(self.dbs[0],0,(11).to_bytes(1,'big')) #移动A xyr
        self.plc.db_write(self.dbs[0],1,(11).to_bytes(1,'big')) #移动B xyr
        self.a_join()
        self.b_join()
        self.plc.db_write(self.dbs[0],0,(12).to_bytes(1,'big')) #移动A z
        self.plc.db_write(self.dbs[0],1,(12).to_bytes(1,'big')) #移动B z
    def a_grab(self,grab_pos,grab_r,drop_pos,drop_r,a):
        print(f'pick 0 {list(grab_pos) + [grab_r]} {list(drop_pos) + [drop_r]} {a}')

        x,y,z = grab_pos
        r = grab_r
        rx,ry,rz = drop_pos
        rr = drop_r

        self.varify_pos(grab_pos)
        self.varify_pos(drop_pos)

        if self.interference_area_x[0] <= grab_pos[0] and grab_pos[0] <= self.interference_area_x[1] or \
           self.interference_area_x[0] <= drop_pos[0] and drop_pos[0] <= self.interference_area_x[1]:
            self.a_lock()
        else:
            self.a_unlock()

        self.plc.db_write(self.dbs[0],38,pack('!f',x)) #x
        self.plc.db_write(self.dbs[0],42,pack('!f',y)) #y
        self.plc.db_write(self.dbs[0],46,pack('!f',z)) #z
        self.plc.db_write(self.dbs[0],50,pack('!f',r)) #r
        self.plc.db_write(self.dbs[0],54,pack('!f',rx)) #rx
        self.plc.db_write(self.dbs[0],58,pack('!f',ry)) #ry
        self.plc.db_write(self.dbs[0],62,pack('!f',rz)) #rz
        self.plc.db_write(self.dbs[0],66,pack('!f',rr)) #rr
        self.plc.db_write(self.dbs[0],102,bytearray(a)) #absorp
        self.plc.db_write(self.dbs[0],0,(1).to_bytes(1,byteorder='big')) #xyzr抓取
    def b_grab(self,grab_pos,grab_r,drop_pos,drop_r,a):
        print(f'pick 1 {list(grab_pos) + [grab_r]} {list(drop_pos) + [drop_r]} {a}')
        
        x,y,z = grab_pos
        r = grab_r
        rx,ry,rz = drop_pos
        rr = drop_r

        self.varify_pos(grab_pos)
        self.varify_pos(drop_pos)

        if self.interference_area_x[0] <= grab_pos[0] and grab_pos[0] <= self.interference_area_x[1] or \
           self.interference_area_x[0] <= drop_pos[0] and drop_pos[0] <= self.interference_area_x[1]:
            self.b_lock()
        else:
            self.b_unlock()
        
        self.plc.db_write(self.dbs[0],70,pack('!f',x)) #x
        self.plc.db_write(self.dbs[0],74,pack('!f',y)) #y
        self.plc.db_write(self.dbs[0],78,pack('!f',z)) #z
        self.plc.db_write(self.dbs[0],82,pack('!f',r)) #r
        self.plc.db_write(self.dbs[0],86,pack('!f',rx)) #rx
        self.plc.db_write(self.dbs[0],90,pack('!f',ry)) #ry
        self.plc.db_write(self.dbs[0],94,pack('!f',rz)) #rz
        self.plc.db_write(self.dbs[0],98,pack('!f',rr)) #rr
        self.plc.db_write(self.dbs[0],108,bytearray(a)) #absorp
        self.plc.db_write(self.dbs[0],1,(1).to_bytes(1,byteorder='big')) #xyzr抓取
    def ab_grab(self,a_grab_pos,a_r,a_drop_pos,a_a,b_grab_pos,b_r,b_drop_pos,b_a):
        print(f'syncing-pick {list(a_grab_pos) + [a_r]} {a_drop_pos} {a_a} {list(b_grab_pos) + [b_r]} {b_drop_pos} {b_a}')

        if b_grab_pos[0] - a_grab_pos[0] < 1900:
            raise OverrangeError('双臂距离过近！')

        (a_x,a_y,a_z) = a_grab_pos
        (a_rx,a_ry,a_rz) = a_drop_pos
        (b_x,b_y,b_z) = b_grab_pos
        (b_rx,b_ry,b_rz) = b_drop_pos

        self.varify_pos(a_grab_pos)
        self.varify_pos(a_drop_pos)
        self.varify_pos(b_grab_pos)
        self.varify_pos(b_drop_pos)

        if self.interference_area_x[0] <= a_grab_pos[0] and a_grab_pos[0] <= self.interference_area_x[1] or \
           self.interference_area_x[0] <= a_drop_pos[0] and a_drop_pos[0] <= self.interference_area_x[1]:
            self.a_lock()
        else:
            self.a_unlock()

        if self.interference_area_x[0] <= b_grab_pos[0] and b_grab_pos[0] <= self.interference_area_x[1] or \
           self.interference_area_x[0] <= b_drop_pos[0] and b_drop_pos[0] <= self.interference_area_x[1]:
            self.b_lock()
        else:
            self.b_unlock()

        self.plc.db_write(self.dbs[0],38,pack('!f',a_x)) #x
        self.plc.db_write(self.dbs[0],42,pack('!f',a_y)) #y
        self.plc.db_write(self.dbs[0],46,pack('!f',a_z)) #z
        self.plc.db_write(self.dbs[0],50,pack('!f',a_r)) #r
        self.plc.db_write(self.dbs[0],54,pack('!f',a_rx)) #rx
        self.plc.db_write(self.dbs[0],58,pack('!f',a_ry)) #ry
        self.plc.db_write(self.dbs[0],62,pack('!f',a_rz)) #rz
        self.plc.db_write(self.dbs[0],66,pack('!f',a_r)) #rr

        self.plc.db_write(self.dbs[0],70,pack('!f',b_x)) #x
        self.plc.db_write(self.dbs[0],74,pack('!f',b_y)) #y
        self.plc.db_write(self.dbs[0],78,pack('!f',b_z)) #z
        self.plc.db_write(self.dbs[0],82,pack('!f',b_r)) #r
        self.plc.db_write(self.dbs[0],86,pack('!f',b_rx)) #rx
        self.plc.db_write(self.dbs[0],90,pack('!f',b_ry)) #rx
        self.plc.db_write(self.dbs[0],94,pack('!f',b_rz)) #rz
        self.plc.db_write(self.dbs[0],98,pack('!f',b_r)) #rr
        self.plc.db_write(self.dbs[0],102,bytearray(a_a + b_a)) #absorp
        self.plc.db_write(self.dbs[0],0,b'\x02\x02') #do it
    def a_idle(self):
        val = self.plc.db_read(self.dbs[0],0,1)[0]
        status = self.plc.db_read(self.dbs[1],34,1)[0]
        fault =     bool(status & 0b00000001)
        writeable = bool(status & 0b00000010)
        paused =    bool(status & 0b00000100)
        # safe_a =    bool(status & 0b00001000)
        # safe_b =    bool(status & 0b00010000)
        # finished_a =  bool(status & 0b00100000)
        # finished_b =  bool(status & 0b01000000)
        # synced =  bool(status & 0b10000000)
        status = val,fault,writeable,paused #,safe_a,safe_b,finished_a,finished_b,synced
        if not eq(status,self.status):
            self.status = status
            print(f'status 0')
            print('动作,故障,可写,暂停:',self.status)

        if val == 0: raise StopedError('桁架按下了急停!')
        if not writeable: raise StopedError('桁架切换到手动模式!')
        if fault: raise StopedError('桁架故障!')
        if paused: return False
        return val == 88
    def b_idle(self):
        val = self.plc.db_read(self.dbs[0],1,1)[0]
        status = self.plc.db_read(self.dbs[1],34,1)[0]
        fault =     bool(status & 0b00000001)
        writeable = bool(status & 0b00000010)
        paused =    bool(status & 0b00000100)
        # safe_a =    bool(status & 0b00001000)
        # safe_b =    bool(status & 0b00010000)
        # finished_a =  bool(status & 0b00100000)
        # finished_b =  bool(status & 0b01000000)
        # synced =  bool(status & 0b10000000)

        status = val,fault,writeable,paused #,safe_a,safe_b,finished_a,finished_b,synced
        if not eq(status,self.status):
            self.status = status
            print(f'status 1')
            print('动作,故障,可写,暂停:',self.status)

        if val == 0: raise StopedError('桁架按下了急停!')
        if not writeable: raise StopedError('桁架切换到手动模式!')
        if fault: raise StopedError('桁架故障!')
        if paused: return False
        return val == 88
    def a_lock(self):
        if self.dbs[0] != 27: return
        
        print(f'lock 0 {self.dbs[0]}')
        control = self.plc.db_read(self.dbs[0],2,1)[0]
        control =  control | 0b00010000
        self.plc.db_write(self.dbs[0],2,control.to_bytes(1,'big'))  #请求进入干涉区
        
        while not self.plc.db_read(self.dbs[1],35,1)[0] & 0b00000001:
            sleep(1)
            print('A等待干涉区解锁')
            self.a_idle()
    def a_unlock(self):
        if self.dbs[0] != 27: return
        control = self.plc.db_read(self.dbs[0],2,1)[0]
        control =  control & 0b11101111
        self.plc.db_write(self.dbs[0],2,control.to_bytes(1,'big'))  #解锁干涉区
    def b_lock(self):
        if self.dbs[0] != 13: return
        print(f'lock 1 {self.dbs[0]}')
        
        control = self.plc.db_read(self.dbs[0],2,1)[0]
        control =  control | 0b00010000
        self.plc.db_write(self.dbs[0],2,control.to_bytes(1,'big'))  #请求进入干涉区
            
        while not self.plc.db_read(self.dbs[1],35,1)[0] & 0b00000001:
            sleep(1)
            print('B等待干涉区解锁')
            self.b_idle()
    def b_unlock(self):
        if self.dbs[0] != 13: return
        control = self.plc.db_read(self.dbs[0],2,1)[0]
        control =  control & 0b11101111
        self.plc.db_write(self.dbs[0],2,control.to_bytes(1,'big'))  #解锁干涉区
    def a_join(self):
        while not self.a_idle(): sleep(0.2)
    def b_join(self):
        while not self.b_idle(): sleep(0.2)
    def a_magnetic_dot(self,a,enable = True):
        self.plc.db_write(self.dbs[0],102,bytearray(a))
        if enable: self.plc.db_write(self.dbs[0],0,(13).to_bytes(1,'big')) #移动z
        else: self.plc.db_write(self.dbs[0],0,(14).to_bytes(1,'big')) #移动z
    def b_magnetic_dot(self,a,enable = True):
        self.plc.db_write(self.dbs[0],108,bytearray(a))
        if enable: self.plc.db_write(self.dbs[0],1,(13).to_bytes(1,'big')) #移动z
        else: self.plc.db_write(self.dbs[0],1,(14).to_bytes(1,'big')) #移动z
    def plate_rfid(self):
        return 0
    def pallet_1_rfid(self):
        return 1
    def pallet_2_rfid(self):
        return 2