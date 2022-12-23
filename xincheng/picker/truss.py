from copy import deepcopy
from services.station import plate
from matplotlib.pyplot import fignum_exists
from transitions.core import MachineError
from transitions.extensions import AsyncMachine as Machine
import threading
import asyncio
import traceback
from socket import *
import time
import sys
import numpy as np
import math as m
import picker.pallet
import picker.camera
import robot.truss
from speedbotlib.common.cache import dson
import os
from pprint import pprint
import requests as http
from snap7.exceptions import Snap7Exception

class NothingToPick(Exception):pass
class WaitingToPick(Exception):pass
class TilingError(Exception):pass

def rotate(origin_pos,pos,degree):
    from math import pi,cos,sin
    a = pi / 180 * degree
    x2 = (pos[0] - origin_pos[0]) * cos(a) - (pos[1] - origin_pos[1]) * sin(a) + origin_pos[0]
    y2 = (pos[1] - origin_pos[1]) * cos(a) + (pos[0] - origin_pos[0]) * sin(a) + origin_pos[1]
    z2 = pos[2]
    return x2,y2,z2

class Truss():
    states = ['initial','opening','locating','placing','nexting','picking','interrupting','waiting','finishing','faulting']
    
    def __init__(self,params):
        os.makedirs('db/status',exist_ok=True)
        os.makedirs('db/params',exist_ok=True)
        os.makedirs('db/stacks',exist_ok=True)
        os.system('chmod ugo+rw db/status')
        os.system('chmod ugo+rw db/params')
        os.system('chmod ugo+rw db/stacks')

        self.params = params
        self.name = self.params['robot_name']
        status_path = f'db/status/{self.name}.json'
        if os.path.exists(status_path):
            self.status = dson(status_path)
        else:
            self.status = dson(status_path,**dict(
                step='initial',
                plate_name='',
                placeable=True,
                disabled=True,
                ignored_parts=[] # 抓不到的零件
            ))

        stacks_path = f'db/stacks/{self.name}.json'
        if os.path.exists(stacks_path):
            self.stacks = dson(stacks_path)
        else:
            self.stacks = dson(stacks_path,**dict(left=[],middle=[],right=[]))

        self.plate = None
        self.part = None
        self.plc = None

        self.machine = Machine(model=self,queued=True,states=Truss.states,ignore_invalid_triggers=True)
        self.machine.add_transition(trigger='idle', source=['initial','finishing','waiting'], dest='initial')
        self.machine.add_transition(trigger='wait', source=['waiting','interrupting','initial'], dest='waiting')
        self.machine.add_transition(trigger='open',source=['initial','waiting'], dest='opening')
        self.machine.add_transition(trigger='locate',source='opening', dest='locating')
        self.machine.add_transition(trigger='place',source=['locating','placing','picking'], dest='placing')
        self.machine.add_transition(trigger='pick', source=['picking','placing'], dest='picking')
        self.machine.add_transition(trigger='interrupt', source=['opening','locating','placing','picking','faulting'], dest='interrupting')
        self.machine.add_transition(trigger='finish', source=['initial','opening','locating','placing','picking','faulting','interrupting','waiting'], dest='finishing')
        self.machine.add_transition(trigger='fault', source=['opening','locating','placing','picking'], dest='faulting')
        
        self.loop = asyncio.new_event_loop()
        self.t = threading.Thread(target=self.run)
        self.t.start()

    def __del__(self):
        try:
            del self.truss
        except:
            pass

    def run(self):
        asyncio.set_event_loop(self.loop)

        while True:
            try:
                self.loop.run_until_complete(self.idle())
            except:
                traceback.print_exc()
                print('状态机异常停止！')
            else:
                print('状态机停止！')

        self.loop.close()
        
    def start(self,plate):
        plate_name = plate['name']
        print('钢板：',plate_name)

        self.plate = plate
        if self.status['plate_name'] != plate_name:
            print('清除上一张钢板的缓存。')
            del self.status['tiling']
            del self.status['corner']

        self.status['plate_name'] = plate_name
        
        if self.state == 'waiting':
            print('分拣恢复。')
            self.loop.create_task(self.open())

        del self.status['error_module']
        del self.status['error_message']
        del self.status['error_help']
        pass

    def pause(self):
        if not self.plate: 
            print('没有分拣任务！')
            return
        print('分拣暂停。')
        self.loop.create_task(self.interrupt())
        pass

    def stop(self):
        self.loop.create_task(self.finish())
        while self.state != 'initial' and self.state != 'waiting':
            time.sleep(2)
            print('等待桁架停止。')
        pass

    def close(self):
        self.loop.stop()
        pass


    def on_enter_initial(self):
        if self.status['step'] == 'waiting':
            self.loop.create_task(self.wait())
            self.status['disabled'] = False
            if self.plc and self.plc.get_connected(): self.plc.disconnect()
            self.plc = None
            return
        
        if self.status['step'] != 'initial': self.status['step'] = self.state
        
        if not self.plate:
            time.sleep(5)
            self.loop.create_task(self.idle())

            try:
                import snap7
                plc_dbs = self.params['plc.dbs']
                if not self.plc:
                    server,port,rack,slot = self.params['plc']
                    self.plc = snap7.client.Client()
                    self.plc.connect(server,rack,slot,port)

                val = self.plc.db_read(plc_dbs[0],0,1)[0]
                if val == 0: self.status['disabled'] = True
                else: self.status['disabled'] = False
            except:
                traceback.print_exc()
                self.status['disabled'] = True
                if self.plc and self.plc.get_connected(): self.plc.disconnect()
                self.plc = None

            return
        
        self.status['disabled'] = False
        if self.plc and self.plc.get_connected(): self.plc.disconnect()
        self.plc = None

        if not self.plate['parts']:
            self.plate['finished'] = True
            self.loop.create_task(self.finish())
        elif self.plate['finished']:
            self.plate = None
            self.loop.create_task(self.idle())
        else:
            self.loop.create_task(self.open())

    def on_enter_opening(self):
        self.status['step'] = self.state

        plc = self.params['plc']
        plc2_port = self.params['plc2.port']
        plc_areas = self.params['plc.areas']
        plc_dbs = self.params['plc.dbs']
        
        print(f'连接桁架：',plc,plc2_port,plc_areas,plc_dbs)
        
        try:
            self.truss = robot.truss.Truss(self.name,plc[0],plc[1],plc[2],plc[3],plc2_port,plc_dbs,plc_areas[0],plc_areas[1],plc_areas[2],plc_areas[3],plc_areas[4])
        except:
            traceback.print_exc()
            self.error_module = 1
            self.error_message = f'无法连接桁架！'
            self.error_help = f'确认桁架已经启动且各项状态正常。'
            self.loop.create_task(self.fault())
            return
        else:
            self.loop.create_task(self.locate())

    def on_enter_locating(self):
        self.status['step'] = self.state #状态补丁

        host,port = self.params['locating']
        point_A,point_B = deepcopy(self.params['locating.points.A']),deepcopy(self.params['locating.points.B'])
        plc_areas = self.params['plc.areas']
        plate_size = self.plate['size']
        plate_offset = self.plate['offset']
        point_B[0] = point_B[0] - plate_offset[0]
        point_A[0] = point_A[0] - plate_offset[0]
        point_A[1] = point_B[1] = point_B[1] - plate_offset[1]
        point_A[0] = plc_areas[0][0] if point_A[0] <= plc_areas[0][0] else point_A[0]
        point_B[0] = plc_areas[0][1] if point_B[0] >= plc_areas[0][1] else point_B[0]
        
        if 'corner' not in self.status:
            try:
                if self.params['locating.version'] == 4: #无寻边版本
                    print(f'人力寻边：{host,port,self.params["locating.points.A"],self.params["locating.points.B"],plate_offset}')
                    plate_corner,plate_degree = self.params['locating.value']
                else:
                    print(f'桁架寻边：{host,port,self.params["locating.points.A"],self.params["locating.points.B"],plate_offset}')

                    try:
                        self.truss.a_join()
                        self.truss.b_join()
                    except:
                        traceback.print_exc()
                        self.error_module = 1
                        self.error_message = f'无法连接桁架！'
                        self.error_help = f'确认桁架已经启动且各项状态正常。'
                        self.loop.create_task(self.fault())
                        return
                    else:
                        if self.params['locating.version'] == 5: #仿真寻板
                            self.truss.a_reset()
                            self.truss.b_move(point_B)
                            self.truss.b_join()
                            self.truss.b_move(point_A)
                            self.truss.b_join()
                            plate_corner,plate_degree = self.params['locating.value']
                        elif self.params['locating.version'] == 8: #新版寻板
                            self.truss.a_reset()
                            self.truss.b_move(point_B)
                            self.truss.b_join()
                            picker.camera.locate5_take_corner(self.name,host, port, point_B)
                            self.truss.b_move(point_A)
                            self.truss.b_join()
                            picker.camera.locate5_take_edge(self.name,host, port, point_A)
                            if plate_offset[0] + plate_offset[1] == 0:
                                print(f'没有混捡数据！')
                                raise Exception(f'没有混捡数据！')
                            plate_corner,plate_degree = picker.camera.locate5(self.name,host,port,self.plate['plate_png_path'])
                            #point_A[2] = 400 #防止碰撞
                            #self.truss.b_move(point_A)
                            self.truss.b_reset()
                        else:
                            print(f'没有找到对应的寻边版本！')
                            raise Exception(f'没有找到对应的寻边版本！')
            except:
                traceback.print_exc()
                self.error_module = 4
                self.error_message = f'寻边失败！'
                self.error_help = f'进行手动寻边。'
                self.loop.create_task(self.fault())
                return
            else: 
                self.status['corner'] = plate_corner,plate_degree #钢板右，钢板角度
                self.plate['corner'] = plate_corner,plate_degree
        else:
            plate_corner,plate_degree = self.status['corner'] #钢板右，钢板角度

        print(f'寻边：{plate_corner,plate_degree}')
        
        plate_size = self.plate['size']
        
        self.plate_right,self.plate_top = plate_corner
        self.plate_left = self.plate_right - plate_size[0]
        self.plate_bottom = self.plate_top - plate_size[1]
        self.grab_z = self.params['sorting.grab_z'] + plate_size[2]

        self.loop.create_task(self.place())

        #重新设置抓取零件的抓手
        plate_left = plate_corner[0] - plate_size[0]
        ignored_parts = []

        for part in [part for part in self.plate['parts'] if not part['picked']]:
            if part['level'] == 3:
                grab_pos_x = plate_left + part['a_grab_pos'][0]
                if grab_pos_x < self.truss.area_x[0] or grab_pos_x > self.truss.area_x[1]:
                    ignored_parts.append(part['id'])
                    continue

                grab_pos_x = plate_left + part['b_grab_pos'][0]
                if grab_pos_x < self.truss.area_x[0] or grab_pos_x > self.truss.area_x[1]:
                    ignored_parts.append(part['id'])
                    continue

            grab_pos_x = plate_left + (part['b_grab_pos'][0] if part['handle'] else part['a_grab_pos'][0])
            if grab_pos_x < self.truss.area_x[0] or grab_pos_x > self.truss.area_x[1]:
                ignored_parts.append(part['id'])
                continue

        self.status['ignored_parts'] = ignored_parts

    def on_enter_placing(self):
        self.status['step'] = self.state

        try:
            self.truss.a_join()
            self.truss.b_join()
        except:
            traceback.print_exc()
            self.error_module = 1
            self.error_message = f'无法连接桁架！'
            self.error_help = f'确认桁架已经启动且各项状态正常。'
            self.loop.create_task(self.fault())
            return

        picked_count = len([part for part in self.plate['parts'] if part['picked']])
        all_count = len(self.plate['parts'])
        ignored_count = len(self.status['ignored_parts'])
        print(f'已分拣{picked_count}/全部{all_count}/忽略{ignored_count}')

        if picked_count + ignored_count == all_count:
            if picked_count == all_count: self.plate['finished'] = True
            self.loop.create_task(self.finish())
            return

        if self.status['placeable']:
            drop_pos = self.params['placing.pallet_pos']
            pallet_size = self.params['placing.pallet_size']
            plate_name = self.plate['name']
            
            if not self.params['placing.no_wait']:
                try:
                    host,port = self.params['scheduler']
                    url = f'http://{host}:{port}/pallet/primary/ready' #查询能否放置，不然就等待
                    res = http.get(url,json=dict(name=self.name))
                    if not res.json()['val']:
                        self.truss.a_reset()
                        self.truss.b_reset()
                        raise Exception
                except:
                    self.loop.create_task(self.place())
                    time.sleep(2)
                    return

            if 'tiling' not in self.plate:
                print('平铺计算：',self.params['placing'])
                plate_parts = [part for part in self.plate['parts'] if not part['picked'] and part['id'] not in self.status['ignored_parts']]
                if 'tiling' in self.status: plate_parts = [part for part in plate_parts if part['id'] not in self.status['tiling']]
                
                try:
                    host,port = self.params['placing']
                    pallet_pos = self.params['placing.pallet_pos']
                    self.plate['tiling'] = self.tile(host,port,pallet_pos,pallet_size,plate_parts)[0] #计算放置点
                except:
                    traceback.print_exc()
                    self.error_module = 4
                    self.error_message = f'平铺计算失败！'
                    self.error_help = f'在WEB控制界面中点击强制移动或恢复分拣'
                    self.loop.create_task(self.fault())
                    return

            unpicked = [part for part in self.plate['parts'] if (not part['picked']) and (part['id'] in self.plate['tiling'])]
            if not unpicked:
                if not self.params['placing.no_wait']:
                    try:
                        host,port = self.params['scheduler']
                        url = f'http://{host}:{port}/pallet/primary/next' #流料
                        res = http.get(url,json=dict(name=self.name,plate=self.plate.value))
                        print('请求流料，成功')
                    except:
                        print('请求流料，失败')
                        pass

                self.loop.create_task(self.place())
                del self.plate['tiling']
                return

            self.drop_positions = self.plate['tiling'] 
            self.part = None
        else:
            if 'tiling' not in self.status:
                try:
                    plate_parts = [part for part in self.plate['parts'] if not part['picked'] and part['id'] not in self.status['ignored_parts']]
                    if 'tiling' in self.plate: plate_parts = [part for part in plate_parts if part['id'] not in self.plate['tiling']]
                    tiling = self.stack(plate_parts) #计算放置点
                    
                    if not tiling:
                        print('切换到平铺')
                        self.status['placeable'] = True #切换到平铺
                        self.loop.create_task(self.place())

                        pallet_names = []
                        for part in plate_parts:
                            if part['handle'] == 0:
                                if not self.params['placing.pallets.left.pos'] and self.params['placing.pallets.middle.pos']:
                                    pallet_names.append('middle')
                                elif self.params['placing.pallets.left.pos']:
                                    pallet_names.append('left')
                            if part['handle'] == 1:
                                if not self.params['placing.pallets.right.pos'] and self.params['placing.pallets.middle.pos']:
                                    pallet_names.append('middle')
                                elif self.params['placing.pallets.right.pos']:
                                    pallet_names.append('right')
                            if part['handle'] == 2:
                                if self.params['placing.pallets.middle.pos']:
                                    pallet_names.append('middle')
                            
                        for pallet_name in [n for n in ['left','middle','right'] if n in pallet_names]:
                            if not self.stacks[pallet_name]: continue #零件放不下，不报告料框已满

                            try:
                                host,port = self.params['scheduler']
                                url = f'http://{host}:{port}/report/full_mini_pallet'
                                http.put(url,json=dict(name=self.name,pallet_name=pallet_name,rfid=0,progress=100),timeout=5)
                            except:
                                print(f'{pallet_name}满框报告：失败')
                                traceback.print_exc()
                            else:
                                print(f'{pallet_name}满框报告：成功')
                        return

                    self.status['tiling'] = tiling 
                except:
                    traceback.print_exc()
                    self.error_module = 4
                    self.error_message = f'码垛计算失败！'
                    self.error_help = f'在WEB控制界面中点击强制移动或恢复分拣'
                    self.loop.create_task(self.fault())
                    return

            unpicked = [part for part in self.plate['parts'] if (not part['picked']) and (part['id'] in self.status['tiling'])]
            if not unpicked:
                self.loop.create_task(self.place())
                del self.status['tiling']
                return
            
            self.drop_positions = self.status['tiling']
            self.part = None

        self.loop.create_task(self.pick())
        

    def on_enter_picking(self):
        self.status['step'] = self.state

        #寻找可放置到当前托盘的零件
        def one_of_parts_to_pallet(pallet,parts):
            unpicked_parts = [part for part in parts if not part['picked'] and part['id'] in pallet and part['id'] not in self.status['ignored_parts']]
            return unpicked_parts[-1] if sorted(unpicked_parts,key=lambda x:x['center'][0]) else None
        
        parts = self.plate['parts']
        
        try:
            if not self.part: #如果检测到碰撞无法获得另一个零件，则单臂抓取，另一臂复位
                part = one_of_parts_to_pallet(self.drop_positions,parts) #得到一个可被放置的零件
                if not part:  raise NothingToPick #没有零件可放置
                handle = part['handle']
                
                if not self.idle_for_grabbing(handle): #如果机械臂忙碌，则等待
                    time.sleep(1)
                    raise WaitingToPick

                self.part = part
                self.wait_for_grabbing(handle) #等待单臂抓取结束

            handle = self.part['handle'] #分拣零件所使用的机械臂
            
            if not self.idle_for_grabbing(handle): #如果机械臂忙碌，则等待
                time.sleep(1)
                raise WaitingToPick

            part_id = self.part['id']
            print('分拣中：',part_id)

            try:
                a_drop_pos,b_drop_pos,pallet_pos,pallet_name = self.drop_positions[part_id]
                a_part_drop_pos = pallet_pos[0] + a_drop_pos[0], \
                                  pallet_pos[1] + a_drop_pos[1], \
                                  pallet_pos[2] + a_drop_pos[2]
                b_part_drop_pos = pallet_pos[0] + b_drop_pos[0], \
                                  pallet_pos[1] + b_drop_pos[1], \
                                  pallet_pos[2] + b_drop_pos[2]
                self.next(self.part,self.grab_z,a_part_drop_pos,b_part_drop_pos) #分拣一个，如果机械臂忙碌，则会阻塞
            except (robot.truss.OverrangeError):
                print(f'违规的零件：{part_id}')
                another_part = None
            else:
                report_part = self.part #待上报的零件
                handle_width = self.params['sorting.handle_width']
                another_part = self.another_one(parts,self.part,self.plate_left,self.drop_positions,handle_width) #得到另一个不会被碰撞的零件
            
            self.part['picked'] = True
            self.plate['parts'] = parts

            if another_part: print(' 另一个',another_part['id'])
            self.part = another_part #下一个待分拣零件
        except WaitingToPick:
            self.loop.create_task(self.pick())
        except NothingToPick:
            self.loop.create_task(self.place())
        except robot.truss.StopedError:
            self.error_module = 1
            self.error_message = f'无法连接桁架！'
            self.error_help = f'确认桁架已经启动且各项状态正常。'
            self.loop.create_task(self.fault())
        except Snap7Exception:
            self.error_module = 1
            self.error_message = f'无法连接桁架！'
            self.error_help = f'确认桁架已经启动且各项状态正常。'
            self.loop.create_task(self.fault())
        else:
            self.loop.create_task(self.pick())
            if 'report_part' in dir():
                try: #报告零件分拣状态
                    host,port = self.params['scheduler']
                    url = f'http://{host}:{port}/report/part'
                    http.put(url,json=dict(name=self.name,plate_name=self.plate['name'],part=report_part,pallet_name=pallet_name),timeout=4)
                except:
                    print(f'报告零件{report_part["id"]}失败！')
                else:
                    print(f'报告零件{report_part["id"]}成功。')

    def on_enter_interrupting(self):
        self.status['step'] = self.state
        if not self.plate: return # 没有分拣任务
        self.loop.create_task(self.wait())

        try: 
            print('桁架回到原点。')
            self.truss.a_join()
            self.truss.a_reset()
            self.truss.b_join()
            self.truss.b_reset()
            del self.truss
        except:
            traceback.print_exc()
        pass

    def on_enter_waiting(self):
        if self.status['step'] != 'waiting': self.status['step'] = self.state

        time.sleep(5)
        print('暂停中。')
        self.loop.create_task(self.wait())
        pass

    def on_enter_finishing(self):
        self.status['step'] = self.state

        self.loop.create_task(self.idle())
        if not self.plate: return # 没有分拣任务
        self.status['placeable'] = True #切换到平铺
        
        try: 
            print('桁架回到原点。')
            self.truss.a_join()
            self.truss.b_join()
            self.truss.a_reset()
            self.truss.b_reset()
            del self.truss
        except:
            traceback.print_exc()
            pass
        
        try:
            host,port = self.params['scheduler']
            url = f'http://{host}:{port}/report/finished' 
            http.put(url,json=dict(name=self.name,plate=self.plate.value)) #流料并报告分拣状态
        except:
            print('报告分拣状态：失败')
            traceback.print_exc()
        else:
            print('报告分拣状态：成功')

        if 'tiling' in self.plate:
            try:
                url = f'http://{host}:{port}/pallet/primary/next' #流料
                res = http.get(url,json=dict(name=self.name,plate=self.plate.value))
                print('请求流料，成功')
            except:
                print('请求流料，失败')
                pass

            del self.plate['tiling']
        del self.status['tiling']

        picked_count = len([part for part in self.plate['parts'] if part['picked']])
        all_count = len(self.plate['parts'])
        ignored_count = len(self.status['ignored_parts'])

        print(f'已分拣{picked_count}/全部{all_count}/忽略{ignored_count}')

        self.plate = None
        print('结束分拣。')
        pass

    def on_enter_faulting(self):
        self.status['step'] = self.state

        print('错误：',self.error_module,self.error_message,self.error_help)

        self.status.update_l(**dict(
            error_module = self.error_module,
            error_message = self.error_message,
            error_help = self.error_help
        ))
          
        self.loop.create_task(self.interrupt())
        
        try:
            host,port = self.params['scheduler']
            url = f'http://{host}:{port}/report/error'
            http.put(url,json=dict(name=self.name,message=self.error_message,module=self.error_module,solve=self.error_help,plate_name=self.plate['name']),timeout=4) 
        except:
            traceback.print_exc()
            print('上报错误失败！')
        else:
            print('上报错误成功！')
        pass

    def idle_for_grabbing(self,handle):
        if handle == 0:
            return self.truss.a_idle()
        elif handle == 1:
            return self.truss.b_idle()
        else:
            return self.truss.a_idle() and self.truss.b_idle()

    def wait_for_grabbing(self,handle):
        if handle == 0:
            self.truss.b_join()
            self.truss.b_reset()
        elif handle == 1:
            self.truss.a_join()
            self.truss.a_reset()

    def next(self,part,grab_z,a_drop_pos,b_drop_pos):
        from copy import deepcopy
        part = deepcopy(part)

        plate_corner,plate_degree = self.status['corner'] #钢板边缘，右下角

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
        
        #叠加钢板角度
        if 'a_grab_degree' in part: a_grab_degree -= plate_degree
        if 'b_grab_degree' in part: b_grab_degree -= plate_degree

        if 'a_grab_pos' in part:
            a_grab_pos[0] += self.plate_left
            a_grab_pos[1] += self.plate_bottom
            a_grab_pos[2] = grab_z

        if 'b_grab_pos' in part:
            b_grab_pos[0] += self.plate_left
            b_grab_pos[1] += self.plate_bottom
            b_grab_pos[2] = grab_z

        if 0 == handle:
            a_grab_pos = rotate(plate_corner,a_grab_pos,plate_degree)
            drop_x = a_drop_pos[0] + a_drop_pos_offset[0]
            drop_y = a_drop_pos[1] + a_drop_pos_offset[1]
            drop_z = a_drop_pos[2] + part_size[2]
            
            if self.truss.reset_x[1] - a_grab_pos[0] < 1900 or self.truss.reset_x[1] - drop_x < 1900:
                self.truss.b_join()
                _,y,z,r = self.truss.b_pos()
                self.truss.b_move([self.truss.area_x[1],round(y),z,r])

            self.truss.a_grab(
                a_grab_pos,a_grab_degree,
                (drop_x,drop_y,drop_z),a_drop_degree,
                a_magnetic_dots)
        elif 1 == handle:
            b_grab_pos = rotate(plate_corner,b_grab_pos,plate_degree)
            drop_x = b_drop_pos[0] + b_drop_pos_offset[0]
            drop_y = b_drop_pos[1] + b_drop_pos_offset[1]
            drop_z = b_drop_pos[2] + part_size[2]

            if b_grab_pos[0] - self.truss.reset_x[0] < 1900 or drop_x - self.truss.reset_x[0] < 1900:
                self.truss.a_join()
                _,y,z,r = self.truss.a_pos()
                self.truss.a_move([self.truss.area_x[0],round(y),z,r])

            self.truss.b_grab(
                b_grab_pos,b_grab_degree,
                (drop_x,drop_y,drop_z),b_drop_degree,
                b_magnetic_dots)
        else:
            a_grab_pos = rotate(plate_corner,a_grab_pos,plate_degree)
            a_drop_x = a_drop_pos[0] + a_drop_pos_offset[0]
            a_drop_y = a_drop_pos[1] + a_drop_pos_offset[1]
            a_drop_z = a_drop_pos[2] + part_size[2]
            b_grab_pos = rotate(plate_corner,b_grab_pos,plate_degree)
            b_drop_x = b_drop_pos[0] + b_drop_pos_offset[0]
            b_drop_y = b_drop_pos[1] + b_drop_pos_offset[1]
            b_drop_z = b_drop_pos[2] + part_size[2]

            self.truss.ab_grab(
                a_grab_pos,a_grab_degree,
                (a_drop_x,a_drop_y,a_drop_z),
                a_magnetic_dots,
                b_grab_pos,b_grab_degree,
                (b_drop_x,b_drop_y,b_drop_z),
                b_magnetic_dots)
        return handle

    def another_one(self, parts, part,grab_pos_offset, pallet, handle_width):
        part_name = part['id']
        part_handle = part['handle']
        if part_handle > 1: return None

        part_drop_pos,_,pallet_pos,_ = pallet[part_name]
        part_drop_pos = pallet_pos[0] + part_drop_pos[0], \
                        pallet_pos[1] + part_drop_pos[1], \
                        pallet_pos[2] + part_drop_pos[2]
        
        part_center = part['center']
        part_w, _, _ = part['size']
        part_w = part_w if part_w > handle_width else handle_width
        
        part_x = grab_pos_offset + part_center[0]
        part_grab_x = part_x
        part_drop_x = part_drop_pos[0]

        right = max(part_grab_x,part_drop_x) + part_w / 2
        left = min(part_grab_x,part_drop_x) - part_w / 2
        
        line1 = (left,right)

        for part in sorted(parts,key=lambda x:x['center'][0],reverse=True):
            part_name = part['id']
            if part['handle'] > 1: continue
            if part['handle'] == part_handle: continue
            if part_name not in pallet: continue
            if part['picked']: continue

            part_drop_pos,_,pallet_pos,_ = pallet[part_name]
            part_drop_pos = pallet_pos[0] + part_drop_pos[0], \
                            pallet_pos[1] + part_drop_pos[1], \
                            pallet_pos[2] + part_drop_pos[2]

            part_center = part['center']
            part_w, _, _ = part['size']
            part_w = part_w if part_w > handle_width else handle_width

            part_x = grab_pos_offset + part_center[0]
            part_grab_x = part_x
            part_drop_x = part_drop_pos[0]

            right = max(part_grab_x,part_drop_x) + part_w / 2
            left = min(part_grab_x,part_drop_x) - part_w / 2
            
            line2 = (left,right)
            if line2[0] < line1[0] and line1[0] < line2[1]: continue
            if line2[0] < line1[1] and line1[1] < line2[1]: continue
            if line1[0] < line2[0] and line2[0] < line1[1]: continue
            if line1[0] < line2[1] and line2[1] < line1[1]: continue
            return part
        return None

    def tile(self,host,port,pos,size,parts,pallet_name=''):
        '''
        放置点计算
        '''

        source = ''
        for part in sorted(parts,key=lambda x:x['center'][0],reverse=True):
        #for part in parts:
            id = part['id']
            (w,h,d) = part['size']
            handle = part['handle']
            source += f'{id} {handle+1} {int(w/10)+10} {int(h/10)+10}\n' #收集放置点计算数据
        
        if not parts: return [[]]

        try:
            sock = socket(AF_INET,SOCK_STREAM)
            sock.settimeout(60)
            sock.connect((host,port))
            sock.sendall(f'ResizePallet {int(size[0]/10)} {int(size[1]/10)}\n'.encode())
            buffer = sock.recv(1024)
            print(buffer)
            sock.sendall(source.encode())
            io = sock.makefile()
            
            vals = []
            val = {}
            count = len(parts)
            while count:
                row = io.readline()
                columns = row.split(' ')
                if len(columns) < 4:
                    continue

                if row == '0 0.000000 0.000000 0.000000 0 0 0\n': 
                    vals.append(val)
                    val = {}
                    continue

                n = columns[0]
                #将放置点偏移到xyz
                x = float(columns[1])*10
                y = float(columns[2])*10
                z = float(columns[3])*10

                val[n] = [x,y,z],[x,y,z],pos,pallet_name
                count -= 1
        except:
            print('漏掉了一些零件。')
            traceback.print_exc()
            pass
        finally:
            vals.append(val)
            sock.close()
        pprint(vals)
        return vals

    def stack(self,parts):
        val = {}

        parts = sorted(parts,key=lambda x:x['size'][0] * x['size'][1],reverse=True)
       
        left_pos = self.params['placing.pallets.left.pos']
        left_size = self.params['placing.pallets.left.size']
        l = picker.pallet.Pallet(left_size,self.stacks['left'])

        middle_pos = self.params['placing.pallets.middle.pos']
        middle_size = self.params['placing.pallets.middle.size']
        middle_left_section = self.params['placing.pallets.middle.left_section']
        middle_right_section = self.params['placing.pallets.middle.right_section']
        m = picker.pallet.Pallet(middle_size,self.stacks['middle'])

        right_pos = self.params['placing.pallets.right.pos']
        right_size = self.params['placing.pallets.right.size']
        r = picker.pallet.Pallet(right_size,self.stacks['right'])

        handle_size = [1200,700,0]
        
        if not val:
            for part in [part for part in parts if part['handle'] == 1]:
                part_size = deepcopy(part['maximum_size'])
                part_kind = part['kind']
                if part_size[0] < handle_size[0]: part_size[0] = handle_size[0]
                if part_size[1] < handle_size[1]: part_size[1] = handle_size[1]
                offset = r.put(part['id'],part_size,part_kind,part['maximum_size'])
                pos,pallet_name = right_pos,'right'
                
                if not offset: 
                    offset = m.put(part['id'],part_size,part_kind,part['maximum_size'],middle_right_section)
                    pos,pallet_name = middle_pos,'middle'
                if not offset: continue

                x,y,z = offset
                drop_pos_offset = part['b_drop_pos_offset']
                val[part['id']] = [x - drop_pos_offset[0] ,y - drop_pos_offset[1],z], \
                        [x - drop_pos_offset[0] ,y - drop_pos_offset[1],z], \
                        pos, pallet_name
                break

        if not val:
            for part in [part for part in parts if part['handle'] == 0]:
                part_size = deepcopy(part['maximum_size'])
                part_kind = part['kind']

                if part_size[0] < handle_size[0]: part_size[0] = handle_size[0]
                if part_size[1] < handle_size[1]: part_size[1] = handle_size[1]

                offset = l.put(part['id'],part_size,part_kind,part['maximum_size'])
                pos,pallet_name = left_pos,'left'
                if not offset: 
                    offset = m.put(part['id'],part_size,part_kind,part['maximum_size'],middle_left_section)
                    pos,pallet_name = middle_pos,'middle'
                if not offset: continue
                
                x,y,z = offset
                drop_pos_offset = part['a_drop_pos_offset']
                val[part['id']] = [x - drop_pos_offset[0] ,y - drop_pos_offset[1],z], \
                        [x - drop_pos_offset[0] ,y - drop_pos_offset[1],z], \
                        pos,pallet_name
                break

        for part in [part for part in parts if part['handle'] == 2]:
            part_size = deepcopy(part['maximum_size'])
            part_kind = part['kind']
            if part_size[0] < handle_size[0]: part_size[0] = handle_size[0]
            if part_size[1] < handle_size[1]: part_size[1] = handle_size[1]
            offset = m.put(part['id'],part_size,part_kind,part['maximum_size'])
            pos,pallet_name = middle_pos,'middle'
            if not offset: continue

            x,y,z = offset
            a_drop_pos_offset = part['a_drop_pos_offset']
            b_drop_pos_offset = part['b_drop_pos_offset']
            val[part['id']] = [x - a_drop_pos_offset[0] ,y - a_drop_pos_offset[1],z], \
                    [x - b_drop_pos_offset[0] ,y - b_drop_pos_offset[1],z], \
                    pos,pallet_name
            break

        self.stacks['left'] = l.stacks
        self.stacks['middle'] = m.stacks
        self.stacks['right'] = r.stacks

        return val