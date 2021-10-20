import re
from struct import unpack,pack
import time
import ctypes
from typing import Tuple, Optional, Callable, Any
import asyncio

import snap7
import snap7.types
from snap7.common import check_error, load_library, ipv4

import numpy as np
from functools import partial

from speedbotlib.common.cache import dson
from copy import deepcopy
                
def rotate(origin_pos,pos,degree):
    from math import pi,cos,sin
    a = pi / 180 * degree
    x2 = (pos[0] - origin_pos[0]) * cos(a) - (pos[1] - origin_pos[1]) * sin(a) + origin_pos[0]
    y2 = (pos[1] - origin_pos[1]) * cos(a) + (pos[0] - origin_pos[0]) * sin(a) + origin_pos[1]
    z2 = pos[2]
    return x2,y2,z2

class Truss():
    def __init__(self,view,name,db_dir,db_indices,port,area_x,area_y,area_z,interference_area_x,reset_x):
        self.area_x,self.area_y,self.area_z = area_x,area_y,area_z
        self.plate_dir = f'{db_dir}/plates_sorting'
        self.status_file = f'{db_dir}/status/{name}.json'
        self.params_file = f'{db_dir}/params/{name}.json'

        self.server = snap7.server.Server()
        self.dbs = dict()
        self.db0 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * 200)()
        self.server.register_area(snap7.types.srvAreaDB, db_indices[0], self.db0)
        self.server.start(tcpport=port)

        self.name = name
        self.view = view
        self.db_indices = db_indices
        
        self.loop = asyncio.get_event_loop()
        pass
    def __del__(self):
        pass
    def power_on(self):
        self.db0[0] = 88 
        self.db0[1] = 88 
        self.db1[34] = 0b00000010 
        self.db1[35] = 0b00000000 

        self.x = deepcopy(self.reset_x)
        self.y = [self.area_y[0],self.area_y[0]]
        self.z = [self.area_z[1],self.area_z[1]]
        self.r = [0,0]
        
        self.db1[2],self.db1[3],self.db1[4],self.db1[5] = pack('!f',self.x[0])
        self.db1[6],self.db1[7],self.db1[8],self.db1[9] = pack('!f',self.y[0])
        self.db1[10],self.db1[11],self.db1[12],self.db1[13] = pack('!f',self.z[0])
        self.db1[18],self.db1[19],self.db1[20],self.db1[21] = pack('!f',self.x[1])
        self.db1[22],self.db1[23],self.db1[24],self.db1[25] = pack('!f',self.y[1])
        self.db1[26],self.db1[27],self.db1[28],self.db1[29] = pack('!f',self.z[1])
        pass
    def emergency_stop(self):
        self.db0[0] = 0 
        self.db0[1] = 0 
        pass
    def pause(self):
        pass
    def reset(self):
        pass
    def manual(self):
        pass
    async def moving_x(self,index):
        if index == 0:
            x_end = unpack('!f',pack('4b',self.db0[38],self.db0[39],self.db0[40],self.db0[41]))[0]
            x_start = unpack('!f',pack('4b',self.db1[2],self.db1[3],self.db1[4],self.db1[5]))[0]
        elif index == 1:
            x_end = unpack('!f',pack('4b',self.db0[70],self.db0[71],self.db0[72],self.db0[73]))[0]
            x_start = unpack('!f',pack('4b',self.db1[18],self.db1[19],self.db1[20],self.db1[21]))[0]

        for interval in np.linspace(x_start,x_end,int(abs(x_start - x_end) / 200)):
            if index == 0: self.db1[2],self.db1[3],self.db1[4],self.db1[5] = pack('!f',interval)
            elif index == 1: self.db1[18],self.db1[19],self.db1[20],self.db1[21] = pack('!f',interval)
            self.x[index] = interval
            await asyncio.sleep(0.01)

        if self.db_indices[0] == 27 and index == 0 or self.db_indices[0] == 13 and index == 1:
            if self.interference_area_x[0] <= x_end and x_end <= self.interference_area_x[1]: 
                self.db1[35] = self.db1[35] | 0b00000010
            else: 
                self.db1[35] = self.db1[35] & 0b11111101
        pass
    async def moving_y(self,index):
        if index == 0:
            end = unpack('!f',pack('4b',self.db0[42],self.db0[43],self.db0[44],self.db0[45]))[0]
            start = unpack('!f',pack('4b',self.db1[6],self.db1[7],self.db1[8],self.db1[9]))[0]
        elif index == 1:
            end = unpack('!f',pack('4b',self.db0[74],self.db0[75],self.db0[76],self.db0[77]))[0]
            start = unpack('!f',pack('4b',self.db1[22],self.db1[23],self.db1[24],self.db1[25]))[0]
        for interval in np.linspace(start,end,int(abs(start - end) / 200)):
            if index == 0: self.db1[6],self.db1[7],self.db1[8],self.db1[9] = pack('!f',interval)
            elif index == 1: self.db1[22],self.db1[23],self.db1[24],self.db1[25] = pack('!f',interval)
            self.y[index] = interval
            await asyncio.sleep(0.01)
        pass
    async def moving_z(self,index):
        if index == 0:
            end = unpack('!f',pack('4b',self.db0[46],self.db0[47],self.db0[48],self.db0[49]))[0]
            start = unpack('!f',pack('4b',self.db1[10],self.db1[11],self.db1[12],self.db1[13]))[0]
        elif index == 1:
            end = unpack('!f',pack('4b',self.db0[78],self.db0[79],self.db0[80],self.db0[81]))[0]
            start = unpack('!f',pack('4b',self.db1[26],self.db1[27],self.db1[28],self.db1[29]))[0]
        for interval in np.linspace(start,end,int(abs(start - end) / 100)):
            if index == 0: self.db1[10],self.db1[11],self.db1[12],self.db1[13] = pack('!f',interval)
            elif index == 1: self.db1[26],self.db1[27],self.db1[28],self.db1[29] = pack('!f',interval)
            self.z[index] = interval
            await asyncio.sleep(0.01)
    async def moving_r(self,index):
        if index == 0:
            end = unpack('!f',pack('4b',self.db0[50],self.db0[51],self.db0[52],self.db0[53]))[0]
            start = unpack('!f',pack('4b',self.db1[14],self.db1[15],self.db1[16],self.db1[17]))[0]
        elif index == 1:
            end = unpack('!f',pack('4b',self.db0[82],self.db0[83],self.db0[84],self.db0[85]))[0]
            start = unpack('!f',pack('4b',self.db1[30],self.db1[31],self.db1[32],self.db1[33]))[0]
        for interval in np.linspace(start,end,int(abs(start - end) / 50)):
            if index == 0: self.db1[14],self.db1[15],self.db1[16],self.db1[17] = pack('!f',interval)
            elif index == 1: self.db1[30],self.db1[31],self.db1[32],self.db1[33] = pack('!f',interval)
            self.r[index] = interval
            await asyncio.sleep(0.01)
    async def picking(self,index,synced,index2):
        if index == 0:
            x_start = unpack('!f',pack('4b',self.db1[2],self.db1[3],self.db1[4],self.db1[5]))[0]
            y_start = unpack('!f',pack('4b',self.db1[6],self.db1[7],self.db1[8],self.db1[9]))[0]
            z_start = unpack('!f',pack('4b',self.db1[10],self.db1[11],self.db1[12],self.db1[13]))[0]
            r_start = unpack('!f',pack('4b',self.db1[14],self.db1[15],self.db1[16],self.db1[17]))[0]
            x_end = unpack('!f',pack('4b',self.db0[38],self.db0[39],self.db0[40],self.db0[41]))[0]
            y_end = unpack('!f',pack('4b',self.db0[42],self.db0[43],self.db0[44],self.db0[45]))[0]
            z_end = unpack('!f',pack('4b',self.db0[46],self.db0[47],self.db0[48],self.db0[49]))[0]
            r_end = unpack('!f',pack('4b',self.db0[50],self.db0[51],self.db0[52],self.db0[53]))[0]
            x2_end = unpack('!f',pack('4b',self.db0[54],self.db0[55],self.db0[56],self.db0[57]))[0]
            y2_end = unpack('!f',pack('4b',self.db0[58],self.db0[59],self.db0[60],self.db0[61]))[0]
            z2_end = unpack('!f',pack('4b',self.db0[62],self.db0[63],self.db0[64],self.db0[65]))[0]
            r2_end = unpack('!f',pack('4b',self.db0[66],self.db0[67],self.db0[68],self.db0[69]))[0]
        elif index == 1:
            x_start = unpack('!f',pack('4b',self.db1[18],self.db1[19],self.db1[20],self.db1[21]))[0]
            y_start = unpack('!f',pack('4b',self.db1[22],self.db1[23],self.db1[24],self.db1[25]))[0]
            z_start = unpack('!f',pack('4b',self.db1[26],self.db1[27],self.db1[28],self.db1[29]))[0]
            r_start = unpack('!f',pack('4b',self.db1[30],self.db1[31],self.db1[32],self.db1[33]))[0]
            x_end = unpack('!f',pack('4b',self.db0[70],self.db0[71],self.db0[72],self.db0[73]))[0]
            y_end = unpack('!f',pack('4b',self.db0[74],self.db0[75],self.db0[76],self.db0[77]))[0]
            z_end = unpack('!f',pack('4b',self.db0[78],self.db0[79],self.db0[80],self.db0[81]))[0]
            r_end = unpack('!f',pack('4b',self.db0[82],self.db0[83],self.db0[84],self.db0[85]))[0]
            x2_end = unpack('!f',pack('4b',self.db0[86],self.db0[87],self.db0[88],self.db0[89]))[0]
            y2_end = unpack('!f',pack('4b',self.db0[90],self.db0[91],self.db0[92],self.db0[93]))[0]
            z2_end = unpack('!f',pack('4b',self.db0[94],self.db0[95],self.db0[96],self.db0[97]))[0]
            r2_end = unpack('!f',pack('4b',self.db0[98],self.db0[99],self.db0[100],self.db0[101]))[0]

        async def x(self,start,end):
            for interval in np.linspace(start,end,int(abs(start - end) / 200)+1):
                if index == 0: self.db1[2],self.db1[3],self.db1[4],self.db1[5] = pack('!f',interval)
                elif index == 1: self.db1[18],self.db1[19],self.db1[20],self.db1[21] = pack('!f',interval)
                self.x[index] = interval
                await asyncio.sleep(0.01)
        async def y(self,start,end):
            for interval in np.linspace(start,end,int(abs(start - end) / 200)+1):
                if index == 0: self.db1[6],self.db1[7],self.db1[8],self.db1[9] = pack('!f',interval)
                elif index == 1: self.db1[22],self.db1[23],self.db1[24],self.db1[25] = pack('!f',interval)
                self.y[index] = interval
                await asyncio.sleep(0.01)
        async def z(self,start,end):
            for interval in np.linspace(start,end,int(abs(start - end) / 100)+1):
                if index == 0: self.db1[10],self.db1[11],self.db1[12],self.db1[13] = pack('!f',interval)
                elif index == 1: self.db1[26],self.db1[27],self.db1[28],self.db1[29] = pack('!f',interval)
                self.z[index] = interval
                await asyncio.sleep(0.01)
        async def r(self,start,end):
            for interval in np.linspace(start,end,int(abs(start - end) / 50)+1):
                if index == 0: self.db1[14],self.db1[15],self.db1[16],self.db1[17] = pack('!f',interval)
                elif index == 1: self.db1[30],self.db1[31],self.db1[32],self.db1[33] = pack('!f',interval)
                self.r[index] = interval
                await asyncio.sleep(0.01)

        if self.db_indices[0] == 27 and index == 0 or self.db_indices[0] == 13 and index == 1:
            if self.interference_area_x[0] <= x_end and x_end <= self.interference_area_x[1]: 
                self.db1[35] = self.db1[35] | 0b00000010
            else: 
                self.db1[35] = self.db1[35] & 0b11111101

        await self.loop.create_task(asyncio.wait([x(self,x_start,x_end),y(self,y_start,y_end),r(self,r_start,r_end)]))
        if synced: 
            synced[index] = 1
            while synced[index] > synced[index2]: await asyncio.sleep(0.01)
        await self.loop.create_task(z(self,z_start,z_end))
        if synced: 
            synced[index] = 2
            while synced[index] > synced[index2]: await asyncio.sleep(0.01)
        await self.loop.create_task(z(self,z_end,self.area_z[1]))
        if synced: 
            synced[index]= 3
            while synced[index] > synced[index2]: await asyncio.sleep(0.01)

        if self.db_indices[0] == 27 and index == 0 or self.db_indices[0] == 13 and index == 1:
            if self.interference_area_x[0] <= x2_end and x2_end <= self.interference_area_x[1]: 
                self.db1[35] = self.db1[35] | 0b00000010
            else: 
                self.db1[35] = self.db1[35] & 0b11111101

        await self.loop.create_task(asyncio.wait([x(self,x_end,x2_end),y(self,y_end,y2_end),r(self,r_end,r2_end)]))
        if synced: 
            synced[index] = 4
            while synced[index] > synced[index2]: await asyncio.sleep(0.01)
        await self.loop.create_task(z(self,self.area_z[1],z2_end))
        if synced: 
            synced[index] = 5
            while synced[index] > synced[index2]: await asyncio.sleep(0.01)
        await self.loop.create_task(z(self,z2_end,self.area_z[1]))
        if synced: 
            synced[index] = 6
            while synced[index] > synced[index2]: await asyncio.sleep(0.01)
        pass
    async def update(self):
        while True:
            event = self.server.pick_event()
            if not event: break
            request = self.server.event_text(event)
            
            m = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2} \[[\d]+\.[\d]+\.[\d]+.[\d]+\] (\w+) request, Area : DB(\d+), Start : (\d+), Size : (\d+) --> OK',request)
            if not m: continue
            command = m.group(1)
            area = int(m.group(2))
            index = int(m.group(3))
            size = int(m.group(4))
            action = self.db0[index]
            
            if command != 'Write': continue
            
            if index == 64 or index == 65:
                def finish(db,index,f):
                    db[index] = 88

                # if action == 1:
                #     print('单臂抓取指令')
                #     self.loop.create_task(self.picking(index,None,None)).add_done_callback(partial(finish,self.db0,index))
                #     pass
                # elif action == 2:
                #     print('双臂抓取指令')
                #     synced = [0,0]
                #     self.loop.create_task(self.picking(0,synced,1)).add_done_callback(partial(finish,self.db0,0))
                #     self.loop.create_task(self.picking(1,synced,0)).add_done_callback(partial(finish,self.db0,1))
                #     pass
                elif action & 0b00000100:
                    print('平移指令')
                    self.loop.create_task(
                        asyncio.wait([
                                self.loop.create_task(self.moving_x(index)),
                                self.loop.create_task(self.moving_y(index)),
                                self.loop.create_task(self.moving_z(index)),
                                self.loop.create_task(self.moving_r(index))
                            ])).add_done_callback(partial(finish,self.db0,index))
                    pass
                else:
                pass

            self.status = dson(self.status_file)
            self.params = dson(self.params_file)
            if 'plate_name' not in self.status: continue
            plate_name = self.status['plate_name']
            self.plate = dson(f'{self.plate_dir}/{plate_name}.json')

        self.view.cla()

        #区域
        self.view.text(self.area_x[1],0,0,'+X')
        self.view.text(0,self.area_y[1],0,'+Y')
        self.view.text(0,0,self.area_z[0],'-Z')
        self.view.plot([self.area_x[0]-750,self.area_x[1]+750],[0,0],[0,0],linewidth=1,linestyle='--')
        self.view.plot([0,0],self.area_y,[0,0],linewidth=1,linestyle='--')
        self.view.plot([0,0],[0,0],[self.area_z[0],self.area_z[1]],linewidth=1,linestyle='--')

        try:
            #画钢板
            plate_corner,plate_degree = self.status['corner']
            
            plate_size = self.plate['size']
            self.plate_right,self.plate_top = plate_corner
            self.plate_left = self.plate_right - plate_size[0]
            self.plate_bottom = self.plate_top - plate_size[1]
            self.grab_z = self.params['sorting.grab_z'] + plate_size[2]
            
            plate_p0 = rotate(plate_corner,(self.plate_left,self.plate_top,self.grab_z),plate_degree)
            plate_p1 = [plate_corner[0],plate_corner[1],self.grab_z]
            plate_p2 = rotate(plate_corner,(self.plate_right,self.plate_bottom,self.grab_z),plate_degree)
            plate_p3 = rotate(plate_corner,(self.plate_left,self.plate_bottom,self.grab_z),plate_degree)
            
            self.rectangle(plate_p0,plate_p1,plate_p2,plate_p3)
            self.view.scatter(plate_p1[0],plate_p1[1],plate_p1[2])
            self.view.text(plate_p1[0],plate_p1[1],plate_p1[2],f'{plate_p1} {plate_degree}°')

            #画托盘
            drop_pos = self.params['sorting.pallet_pos']
            pallet_size = self.params['sorting.pallet_size']
            
            p0 = drop_pos
            p1 = drop_pos[0], drop_pos[1] + pallet_size[1], drop_pos[2]
            p2 = drop_pos[0] + pallet_size[0], drop_pos[1] + pallet_size[1], drop_pos[2]
            p3 = drop_pos[0] + pallet_size[0], drop_pos[1], drop_pos[2]
            self.rectangle(p0,p1,p2,p3)
            self.view.text(p3[0],p3[1],p3[2],s=str(drop_pos))

            if self.plate['finished']:
                drop_positions = self.plate['tiling']
            else:
                drop_positions = self.plate['tiling']

            for part in self.plate['parts']:
                from copy import deepcopy
                part = deepcopy(part)
                id = part['id']
                handle = part['handle']
                center = part['center']
                part_size = part['size']
                part_degree = part['degree']

                if 'a_grab_pos' in part: a_grab_pos = part['a_grab_pos']
                if 'a_grab_degree' in part: a_grab_degree = part['a_grab_degree']
                if 'a_drop_pos_offset' in part: a_drop_pos_offset = part['a_drop_pos_offset']
                if 'a_drop_degree' in part: a_drop_degree = part['a_drop_degree']
                if 'a_magnetic_dots' in part: a_magnetic_dots = part['a_magnetic_dots']
        
                if 'b_grab_pos' in part: b_grab_pos = part['b_grab_pos']
                if 'b_grab_degree' in part: b_grab_degree = part['b_grab_degree']
                if 'b_drop_pos_offset' in part: b_drop_pos_offset = part['b_drop_pos_offset']
                if 'b_drop_degree' in part: b_drop_degree = part['b_drop_degree']
                if 'b_magnetic_dots' in part: b_magnetic_dots = part['b_magnetic_dots']

                box_center = self.plate_left + center[0],self.plate_bottom + center[1]
                box_left = box_center[0] - part_size[0] / 2
                box_top = box_center[1] - part_size[1] / 2
                box_right = box_left + part_size[0]
                box_bottom = box_top + part_size[1]
                
                # 叠加偏移，以右下角作为原点
                p0 = rotate(box_center,(box_left,box_top,self.grab_z),-part_degree)
                p1 = rotate(box_center,(box_right,box_top,self.grab_z),-part_degree)
                p2 = rotate(box_center,(box_right,box_bottom,self.grab_z),-part_degree)
                p3 = rotate(box_center,(box_left,box_bottom,self.grab_z),-part_degree)
                p0 = rotate(plate_corner,p0,plate_degree)
                p1 = rotate(plate_corner,p1,plate_degree)
                p2 = rotate(plate_corner,p2,plate_degree)
                p3 = rotate(plate_corner,p3,plate_degree)

                #可视化：包围盒
                self.rectangle(p0, p1, p2, p3)

                #叠加钢板角度
                if 'a_grab_degree' in part: a_grab_degree -= plate_degree
                if 'b_grab_degree' in part: b_grab_degree -= plate_degree

                if 'a_grab_pos' in part:
                    a_grab_pos[0] += self.plate_left
                    a_grab_pos[1] += self.plate_bottom
                    a_grab_pos[2] = self.grab_z

                if 'b_grab_pos' in part:
                    b_grab_pos[0] += self.plate_left
                    b_grab_pos[1] += self.plate_bottom
                    b_grab_pos[2] = self.grab_z

                if id not in drop_positions:continue
                if not part['picked']: continue

                drop_pos,pallet_name = drop_positions[id]
                drop_pos_offset = self.params['sorting.pallet_pos']
                drop_pos = drop_pos_offset[0] + drop_pos[0],drop_pos_offset[1] + drop_pos[1],drop_pos_offset[2] + drop_pos[2]

                if 0 == handle:
                    a_grab_pos = rotate(plate_corner,a_grab_pos,plate_degree)
                    self.view.scatter(a_grab_pos[0],a_grab_pos[1],a_grab_pos[2],s=3)
                    drop_x = drop_pos[0] + a_drop_pos_offset[0]
                    drop_y = drop_pos[1] + a_drop_pos_offset[1]
                    drop_z = drop_pos[2] + part_size[2]
                    self.view.scatter(drop_x,drop_y,drop_z,s=3)
                    
                    box_left = drop_pos[0] - part_size[0] / 2  
                    box_top = drop_pos[1] - part_size[1] / 2
                    box_right = box_left + part_size[0]
                    box_bottom = box_top + part_size[1]
                    p0 = box_left,box_top,drop_z
                    p1 = box_right,box_top,drop_z
                    p2 = box_right,box_bottom,drop_z
                    p3 = box_left,box_bottom,drop_z
                    self.rectangle(p0, p1, p2, p3)
                elif 1 == handle:
                    b_grab_pos = rotate(plate_corner,b_grab_pos,plate_degree)
                    self.view.scatter(b_grab_pos[0],b_grab_pos[1],b_grab_pos[2],s=3)
                    drop_x = drop_pos[0] + b_drop_pos_offset[0]
                    drop_y = drop_pos[1] + b_drop_pos_offset[1]
                    drop_z = drop_pos[2] + part_size[2]
                    self.view.scatter(drop_x,drop_y,drop_z,s=3)

                    box_left = drop_pos[0] - part_size[0] / 2  
                    box_top = drop_pos[1] - part_size[1] / 2
                    box_right = box_left + part_size[0]
                    box_bottom = box_top + part_size[1]
                    p0 = box_left,box_top,drop_z
                    p1 = box_right,box_top,drop_z
                    p2 = box_right,box_bottom,drop_z
                    p3 = box_left,box_bottom,drop_z
                    self.rectangle(p0, p1, p2, p3)
                else:
                    a_grab_pos = rotate(plate_corner,a_grab_pos,plate_degree)
                    self.view.scatter(a_grab_pos[0],a_grab_pos[1],a_grab_pos[2],s=3)
                    a_drop_x = drop_pos[0] + a_drop_pos_offset[0]
                    a_drop_y = drop_pos[1] + a_drop_pos_offset[1]
                    a_drop_z = drop_pos[2]
                    self.view.scatter(a_drop_x,a_drop_y,a_drop_z,s=3)

                    b_grab_pos = rotate(plate_corner,b_grab_pos,plate_degree)
                    self.view.scatter(b_grab_pos[0],b_grab_pos[1],b_grab_pos[2],s=3)
                    b_drop_x = drop_pos[0] + b_drop_pos_offset[0]
                    b_drop_y = drop_pos[1] + b_drop_pos_offset[1]
                    b_drop_z = drop_pos[2]
                    self.view.scatter(b_drop_x,b_drop_y,b_drop_z,s=3)

                    box_left = drop_pos[0] - part_size[0] / 2  
                    box_top = drop_pos[1] - part_size[1] / 2
                    box_right = box_left + part_size[0]
                    box_bottom = box_top + part_size[1]
                    p0 = [box_left,box_top,drop_pos[2]] 
                    p1 = [box_right,box_top,drop_pos[2]] 
                    p2 = [box_right,box_bottom,drop_pos[2]] 
                    p3 = [box_left,box_bottom,drop_pos[2]]
                    
                    self.rectangle(p0, p1, p2, p3)
        except:pass
                    
        self.view.plot([self.x[0],self.x[0]],[self.area_y[0],self.area_y[1]],[self.area_z[1],self.area_z[1]],c='red',linewidth=1)
        self.view.plot([self.x[1],self.x[1]],[self.area_y[0],self.area_y[1]],[self.area_z[1],self.area_z[1]],c='red',linewidth=1)
        self.view.plot([self.x[0],self.x[0]],[self.y[0],self.y[0]],[self.z[0],self.area_z[1]],c='red',linewidth=1)
        self.view.plot([self.x[1],self.x[1]],[self.y[1],self.y[1]],[self.z[1],self.area_z[1]],c='red',linewidth=1)
        
        x0,y0,_=rotate([self.x[0],self.y[0],0],[self.x[0]-750,self.y[0],0],-self.r[0])
        x1,y1,_=rotate([self.x[0],self.y[0],0],[self.x[0]+750,self.y[0],0],-self.r[0])
        self.view.plot([x0,x1],[y0,y1],[self.z[0],self.z[0]],c='blue',linewidth=1)

        x0,y0,_=rotate([self.x[1],self.y[1],0],[self.x[1]-750,self.y[1],0],-self.r[1])
        x1,y1,_=rotate([self.x[1],self.y[1],0],[self.x[1]+750,self.y[1],0],-self.r[1])
        self.view.plot([x0,x1],[y0,y1],[self.z[1],self.z[1]],c='blue',linewidth=1)

        self.view.text(self.x[0],self.y[0],self.z[0],str([int(self.x[0]),int(self.y[0]),int(self.z[0]),int(self.r[0])]))
        self.view.text(self.x[1],self.y[1],self.z[1],str([int(self.x[1]),int(self.y[1]),int(self.z[1]),int(self.r[1])]))
    def rectangle(self,p0,p1,p2,p3,c=None,s=''):
        self.view.plot(
            [p0[0],p1[0],p2[0],p3[0],p0[0]],
            [p0[1],p1[1],p2[1],p3[1],p0[1]],
            [p0[2],p1[2],p2[2],p3[2],p0[2]],linewidth=.5)
        if c: self.view.text(c[0],c[1],c[2],s=s)
    def show(self):
        self.loop.create_task(self.update())
        self.loop.run_forever()
        pass
