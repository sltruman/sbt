from os import environ 

def env(k,default):
    if k in environ:
        return eval(environ[k])
    return default


scheduler = {
    'general_control': env('general_control',['192.168.60.52',7852]),      #总控
    'station_2_critical_x': env('station_2_critical_x',4400)                    #2区托盘右侧x范围
}

agents = [{
        'line_name': env('agents.0.line_name','1'),            # 1：等离子切割；2：激光切割
        'area_name': env('agents.0.area_name','2'),            # 2：大件一次分拣区
        'station_name': env('agents.0.station_name','1'),         # 工作站编号
        'robot_name': env('agents.0.robot_name','7'),          # 机器人编号
        'scheduler':env('agents.0.scheduler',['192.168.20.141',60000]),
        'agent':    env('agents.0.agent',['192.168.20.141',60001]),# 分拣实例地址
        'plc':      env('agents.0.plc',['192.168.1.12',102,0,1]), #地址,端口,rack,slot
        'plc2.port':env('agents.0.plc2.port',103), #地址,端口,rack,slot
        'plc.dbs': env('agents.0.plc.dbs',[0,0,0]),
        'plc.areas': env('agents.0.plc.areas',([-2000,2000],[0,2800],[-200,2000],[9999,9999])),
        'locating': env('agents.0.locating',["192.168.10.212",30002]), #定位服务地址,端口
        'locating.version': env('agents.0.locating.version',1), #定位版本
        'locating.value': env('agents.0.locating.value',([3014.11, 6420.70],1.37)),
        'locating.points.A': env('agents.0.locating.points.A',[54.3, 491.0, 287.5]),
        'locating.points.B': env('agents.0.locating.points.B',[1906.84, 491.0, 287.57]),
        'locating.photo_size': env('agents.0.locating.photo_size',[100,100]),
        'placing': env('agents.0.placing',['127.0.0.1',9898]), #放置点计算服务地址,端口j
        'placing.no_wait': env('agents.0.placing.no_wait',False),
        'placing.pallet_pos': env('agents.0.placing.pallet_pos',[0,2200,-25]), #放置点
        'placing.pallet_size': env('agents.0.placing.pallet_size',[3000,1000,100]), #长宽高
        'placing.pallets.left.pos':env('agents.0.placing.pallets.left.pos', None), #放置点
        'placing.pallets.left.size': env('agents.0.placing.pallets.left.size', None), #长宽高
        'placing.pallets.middle.pos':env('agents.0.placing.pallets.middle.pos',[-4500,7500,-400]),  #放置点
        'placing.pallets.middle.size': env('agents.0.placing.pallets.middle.size',[6000,1500,500]), #长宽高
        'placing.pallets.middle.left_section': env('agents.0.placing.pallets.middle.left_section',[900,5000]), #填充抓手中心放置偏移，左，右，下，上
        'placing.pallets.middle.right_section': env('agents.0.placing.pallets.middle.right_section',[4000,6000]), #填充抓手中心放置偏移，左，右，下，上
        'placing.pallets.right.pos':env('agents.0.placing.pallets.right.pos',[1800,7500,-400]),  #放置点
        'placing.pallets.right.size': env('agents.0.placing.pallets.right.size',[2000,1500,500]), #长宽高
        'sorting.handle_width':env('agents.0.sorting.handle_width',2000),    #桁架宽度，决定最小避障宽度
        'sorting.grab_z': env('agents.0.sorting.grab_z',0),   #抓取高度
    },{
        'line_name': env('agents.1.line_name','1'),            # 1：等离子切割；2：激光切割
        'area_name': env('agents.1.area_name','2'),            # 2：大件一次分拣区
        'station_name': env('agents.1.station_name','2'),         # 工作站编号
        'robot_name': env('agents.1.robot_name','8'),          # 机器人编号
        'scheduler':env('agents.1.scheduler',['192.168.20.141',60000]),
        'agent':    env('agents.1.agent',['192.168.20.141',60001]),# 分拣实例地址
        'plc':      env('agents.1.plc',['192.168.1.12',102,0,1]), #地址,端口,rack,slot
        'plc2.port':      env('agents.1.plc2.port',103), #地址,端口,rack,slot
        'plc.dbs': env('agents.1.plc.dbs',[0,0,0]),
        'plc.areas': env('agents.1.plc.areas',([-2000,2000],[0,2800],[-200,2000],[9999,9999])),
        'locating': env('agents.1.locating',["192.168.10.212",30002]), #定位服务地址,端口
        'locating.version': env('agents.1.locating.version',0), #定位版本
        'locating.value': env('agents.1.locating.value',([3500, 6000],0)),
        'locating.points.A': env('agents.1.locating.points.A',[54.3, 491.0, 287.5]), 
        'locating.points.B': env('agents.1.locating.points.B',[1906.84, 491.0, 287.57]), 
        'locating.photo_size': env('agents.1.locating.photo_size',[100,100]),
        'placing.no_wait': env('agents.1.placing.no_wait',False),
        'placing':   env('agents.1.placing',['192.168.20.141',9898]), #放置点计算服务地址,端口
        'placing.pallet_pos': env('agents.1.placing.pallet_pos',[0,2200,-25]), #放置点
        'placing.pallet_size': env('agents.1.placing.pallet_size',[3000,1000,100]),     #长宽高
        'placing.pallets.left.pos':env('agents.1.placing.pallets.left.pos',[-4400,7500,-400]), #放置点
        'placing.pallets.left.size': env('agents.1.placing.pallets.left.size',[2000,1500,100]), #长宽高
        'placing.pallets.middle.pos':env('agents.1.placing.pallets.middle.pos',[-1800,7500,-400]),  #放置点
        'placing.pallets.middle.size': env('agents.1.placing.pallets.middle.size',[4000,1500,100]), #长宽高
        'placing.pallets.middle.left_section': env('agents.1.placing.pallets.middle.left_section',[0,2000]), #填充抓手中心放置偏移，左，右，下，上
        'placing.pallets.middle.right_section': env('agents.1.placing.pallets.middle.right_section',[2000,4000]), #填充抓手中心放置偏移，左，右，下，上
        'placing.pallets.right.pos':env('agents.1.placing.pallets.right.pos',[1600,7500,-400]),  #放置点
        'placing.pallets.right.size': env('agents.1.placing.pallets.right.size',[2000,1500,100]), #长宽高
        'sorting.handle_width':env('agents.1.sorting.handle_width',2000),    #桁架宽度，决定最小避障宽度
        'sorting.grab_z': env('agents.1.sorting.grab_z',0),   #抓取高度
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
