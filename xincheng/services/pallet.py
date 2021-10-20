import os
import json
import config
from flask import Blueprint,jsonify,request as req
from speedbotlib.common.cache import dson
import requests as http
import traceback

blueprint = Blueprint('pallet',__name__)

@blueprint.route('/pallet/primary/next',methods=['GET'])
def primary_pallet_next():
    args = req.get_json()
    robot_name = args['name']
    plate = args['plate']
    plate_name = plate['name']
    parts = plate['parts']
    
    finished = plate['finished']
    params = config.robots(robot_name)
    host,port = config.scheduler['general_control']

    part_kinds = [part['kind'] for part in parts if part['picked'] and part['id'] in plate['tiling']]
    if not part_kinds:
        print('没零件上报！')
        return jsonify(val=True,err=None)

    try:
        #回报零件状态
        url = f'http://{host}:{port}/large_sort_area/system/recSortData'
        json=dict(
            sort_line=params['line_name'],
            area_code=params['area_name'],
            robot_id=robot_name,
            plate_id=plate_name,
            part_num=len(part_kinds),
            part_code=part_kinds,
            move_status='0' if finished else '1') #0：正常结束 1：强制结束
        print(json)
        res = http.post(url,json=json,timeout=4)
        print(res.json())
    except:
        print('零件分拣状态上报：失败')
        return jsonify(val=False,err=None)
    print('零件分拣状态上报：成功')
    return jsonify(val=True,err=None)

@blueprint.route('/pallet/primary/ready',methods=['GET'])
def primary_pallet_ready():
    args = req.get_json()
    robot_name = args['name']
    params = config.robots(robot_name)
    host,port = config.scheduler['general_control']

    try:
        url = f'http://{host}:{port}/large_sort_area/system/queryLineEmpty'
        res = http.post(url,json=dict(sort_line=params['line_name'],area_code=params['area_name'],location=params['station_name']))
        ready = res.json()['data'] == 'ok'
    except:
        ready = False

    return jsonify(val=ready,err=None)


@blueprint.route('/large_sort_area/system/emptyFrameInPlace',methods=['POST'])
def pallet_in_place():
    args = req.get_json()

    try:
        line_name = args['sort_line']
        area_name = args['area_code']
        station_name = args['location']
        robot_name = args['robot_id']
        pallet_name = args['place_id']
        time = args['in_place_time']
    except KeyError:
        return jsonify(code=400,msg='参数错误!',data=args)

    params = config.robots(robot_name)
    if not params:
        return jsonify(code=400,msg=f'机器代理{robot_name}不存在!',data='')

    host,port = params['agent']
    res = http.put(f'http://{host}:{port}/{robot_name}/status/pallets/{pallet_name}/in')
    val = res.json()['val']
    err = res.json()['err']
    return jsonify(code=200 if val else 400,msg='success' if val else err,data='')

@blueprint.route('/large_sort_area/system/uptFrameStackHeight',methods=['POST'])
def pallet_stack_offset():
    args = req.get_json()
    try:
        line_name = args['sort_line']
        area_name = args['area_code']
        args['location']
        robot_name = args['robot_id']
        pallet_name = args['place_id']
        stack_offset = int(args['part_num'])
        stack_name = args['stack_id']
    except:
        return jsonify(code=400,msg='参数错误!',data=args)

    params = config.robots(robot_name)
    if not params:
        return jsonify(code=400,msg=f'机器代理{robot_name}不存在!',data='')

    host,port = params['agent']
    url = f'http://{host}:{port}/{robot_name}/pallets/{pallet_name}/stacks/offset'
    res = http.put(url,json=dict(
        stack_name=stack_name,
        stack_offset=stack_offset
    ))

    val = res.json()['val']
    err = res.json()['err']
    return jsonify(code=200 if val else 400,msg='success' if val else err,data='')

@blueprint.route('/pallet/progress',methods=['PUT'])
@blueprint.route('/large_sort_area/system/frameProcess',methods=['POST'])
def pallet_progress():
    args = req.get_json()
       
    try:
        args['sort_line']
        args['area_code']
        args['robot_id']
        args['location']
    except KeyError as e:
        return jsonify(code=400,msg='参数错误！',data=args)
    
    def stack_bulk(stack):
        if not stack: return 0
        _,_,size,_,_ = stack[0]
        return size[0] * size[1] * size[2] * len(stack)

    def pallet_process(size,stacks):
        pallet_bulk = size[0] * size[1] * size[2]
        bulk = 0
        for stack in stacks:
            bulk += stack_bulk(stack)

        if bulk: bulk = bulk / pallet_bulk * 100
        return int(bulk)

    data = []
    for params in config.agents:
        if args['robot_id'] and args['robot_id'] != params['robot_name']: continue
        # if args['sort_line'] and args['sort_line'] != params['line_name']: continue
        # if args['area_code'] and args['area_code'] != params['area_name']: continue
        
        robot_name = params['robot_name']
        host,port = params['agent']
        frame_process = []
        for pallet_name,pallet_size in [('left',params['placing.pallets.left.size']),
                        ('middle',params['placing.pallets.middle.size']),
                        ('right',params['placing.pallets.right.size'])]:
            if not pallet_size: continue
            
            res = http.get(f'http://{host}:{port}/{robot_name}/status/pallets/{pallet_name}')
            stacks = res.json()['val']
        
            progress = pallet_process(pallet_size,stacks)
            frame_process.append(dict(place_id=pallet_name,process=str(progress)))
        data.append(dict(robot_id=robot_name,frame_process=frame_process))

    return jsonify(code=200,msg='success',data=data)

@blueprint.route('/large_sort_area/system/queryFrameStack',methods=['POST'])
def stacking():
    args = req.get_json()

    try:
        line_name = args['sort_line']
        area_name = args['area_code']
        robot_name = args['robot_id']
        pallet_name = args['place_id']
        args['location']
    except KeyError as e:
        return jsonify(code=400,msg='参数错误！',data=args)
    
    params = config.robots(robot_name)
    if not params:
        return jsonify(code=400,msg=f'机器代理{robot_name}不存在!',data='')
    
    host,port = params['agent']
    res = http.get(f'http://{host}:{port}/{robot_name}/status/pallets/{pallet_name}')

    stack_info = []
    thickness = '?'
    
    try:
        pallet_size = params[f'placing.pallets.{pallet_name}.size']
        for stack in res.json()['val']:
            if not stack: continue
            part_id,_,size,stack_id,_ = stack[-1]
            thickness = str(size[2])
            stack_info.append(dict(part_code=part_id,stack_height=str(int(size[2] * len(stack) / pallet_size[2]  * 100)),stack_id=stack_id))
        data = dict(
            next_process='未知',
            thickness=thickness,
            stack_info=stack_info
        )
    
    except KeyError:
        traceback.print_exc()
        return jsonify(code=400,msg=f'料框{pallet_name}不存在!',data='')
    return jsonify(code=200,msg='success',data=data)

