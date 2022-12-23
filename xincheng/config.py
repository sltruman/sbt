from os import environ 

def env(k,default):
    if k in environ:
        return eval(environ[k])
    return default


scheduler = {
    'general_control': env('general_control',['127.0.0.1',7852]),      #总控
    'station_2_critical_x': env('station_2_critical_x',4400)                    #2区托盘右侧x范围
}

agents = [{
        'line_name': env('agents.0.line_name','1'),            # 1：等离子切割；2：激光切割
        'area_name': env('agents.0.area_name','2'),            # 2：大件一次分拣区
        'station_name': env('agents.0.station_name','1'),         # 工作站编号
        'robot_name': env('agents.0.robot_name','7'),          # 机器人编号
        'scheduler':env('agents.0.scheduler',['127.0.0.1',60000]),
        'agent':    env('agents.0.agent',['127.0.0.1',60001]),# 分拣实例地址
        'plc':      env('agents.0.plc',['127.0.0.1',10200,0,0]), #地址,端口,rack,slot
        'plc.dbs': env('agents.0.plc.dbs',[13,14,28]),
        'plc.areas': env('agents.0.plc.areas',([-4299,3499],[20,8800],[-530,500],[-4300,-2300],[-2200,3400])),
        'plc2.port': env('agents.0.plc2.port',10300),
        'locating': env('agents.0.locating',["127.0.0.1",30002]), #定位服务地址,端口
        'locating.version': env('agents.0.locating.version',4), #定位版本
        'locating.value': env('agents.0.locating.value',([3014.11, 6420.70],1.37)),
        'locating.points.A': env('agents.0.locating.points.A',[54.3, 491.0, 287.5]),
        'locating.points.B': env('agents.0.locating.points.B',[1906.84, 491.0, 287.57]),
        'locating.photo_size': env('agents.0.locating.photo_size',[100,100]),
        'placing': env('agents.0.placing',['127.0.0.1',9898]), #放置点计算服务地址,端口j
        'placing.no_wait': env('agents.0.placing.no_wait',True),
        'placing.pallet_pos': env('agents.0.placing.pallet_pos',[-4299,20,-520]), #放置点
        'placing.pallet_size': env('agents.0.placing.pallet_size',[7800,2100,100]), #长宽高
        'placing.pallets.left.pos':env('agents.0.placing.pallets.left.pos', [-4400,7500,-400]), #放置点
        'placing.pallets.left.size': env('agents.0.placing.pallets.left.size', [2000,1500,100]), #长宽高
        'placing.pallets.middle.pos':env('agents.0.placing.pallets.middle.pos',[-1800,7600,-400]),  #放置点
        'placing.pallets.middle.size': env('agents.0.placing.pallets.middle.size',[3000,1500,100]), #长宽高
        'placing.pallets.middle.left_section': env('agents.0.placing.pallets.middle.left_section',[0,2000]), #填充抓手中心放置偏移，左，右，下，上
        'placing.pallets.middle.right_section': env('agents.0.placing.pallets.middle.right_section',[2000,4000]), #填充抓手中心放置偏移，左，右，下，上
        'placing.pallets.right.pos':env('agents.0.placing.pallets.right.pos',[1600,7500,-400]),  #放置点
        'placing.pallets.right.size': env('agents.0.placing.pallets.right.size',[2000,1500,100]), #长宽高
        'sorting.handle_width':env('agents.0.sorting.handle_width',2100),  #放置点
        'sorting.grab_z': env('agents.0.sorting.grab_z',-135) #长宽高
    }
]

import os

def stations(name):
    for params in agents:
        if params['station_name'] == name: 
            name = params['robot_name']
            return params
    return {}

def robots(name):
    for params in agents:
        if params['robot_name'] == name: 
            return params
    return {}
