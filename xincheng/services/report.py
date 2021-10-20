import threading
from flask import Blueprint,jsonify,request as req
import traceback
from speedbotlib.common.cache import dson
import config
import requests as http
import datetime
import services.pallet

blueprint = Blueprint('report',__name__)


# @blueprint.route('/report/begin',methods=['PUT'])
# def begin():
#     args = req.get_json()
#     robot_name = args['name']
#     plate_name = args['plate_name']
#     params = config.robots(robot_name)
#     host,port = config.scheduler['general_control']

#     try:
#         host,port = config.scheduler['general_control']
#         url = f'http://{host}:{port}/speedbot/system/recStatusData'
#         json=dict(
#             plate_id=plate_name,
#             time=str(datetime.datetime.now())[0:19],
#             sort_line=params['line_name'],
#             area_code=params['area_name'],
#             location=params['station_name'],
#             area_status='0'
#         )
#         http.post(url,json=json,timeout=10)
#     except:
#         print('上报钢板分拣状态：失败')
#         traceback.print_exc()
#     else: 
#         print('上报钢板分拣状态：成功')

@blueprint.route('/report/error',methods=['PUT'])
def error():
    args = req.get_json()
    robot_name = args['name']
    msg = args['message']
    module = args['module']
    solve = args['solve']
    plate_name = args['plate_name']

    params = config.robots(robot_name)
    host,port = config.scheduler['general_control']

    try:
        url = f'http://{host}:{port}/speedbot/system/recStatusData'
        json=dict(
            plate_id=plate_name,
            time=str(datetime.datetime.now())[0:19],
            sort_line=params['line_name'],
            area_code=params['area_name'],
            location=params['station_name'],
            area_status='2'
        )
        res = http.post(url,json=json,timeout=4)
        print(res.json())
    except:
        print('上报状态：失败！')
        traceback.print_exc()
    else: 
        print('上报状态：成功！')

    try:
        url = f'http://{host}:{port}/control/system/errMsgReport'
        json = dict(
            sort_line=params['line_name'],
            area_code=params['area_name'],
            location=params['station_name'],
            err_model=module,
            device_index=robot_name,
            err_msg=msg,
            err_time=str(datetime.datetime.now())[0:19],
            solve_method=solve
        )
        res = http.post(url,json=json,timeout=4)
    except:
        print('上报错误失败！')
    
    return jsonify(val=True,err=None)


@blueprint.route('/report/full_mini_pallet',methods=['PUT'])
def full_mini_pallet():
    args = req.get_json()
    pallet_name = args['pallet_name']
    rfid = args['rfid']
    robot_name = args['name']
    params = config.robots(robot_name)
    progress = args['progress']

    host,port = config.scheduler['general_control']
    try:
        url = f'http://{host}:{port}/speedbot/system/frameFull'
        res = http.post(url,json=dict(
            sort_line=params['line_name'],
            area_code=params['area_name'],
            location=params['station_name'],
            robot_id=robot_name,
            place_id=pallet_name,
            epc_id=rfid,
            frame_status= '0' if 90 < progress and progress < 100 else '1'
        ),timeout=4)
    except:pass
    
    return jsonify(val=True,err=None)

@blueprint.route('/report/finished',methods=['PUT'])
def finished():
    args = req.get_json()
    robot_name = args['name']
    plate = args['plate']
    plate_name = plate['name']
    parts = plate['parts']
    finished = plate['finished']
    params = config.robots(robot_name)
    thickness = plate['size'][2]
    host,port = config.scheduler['general_control']

    try: #回报钢板分拣状态
        url = f'http://{host}:{port}/speedbot/system/recStatusData'
        json=dict(
            plate_id=plate_name,
            time=str(datetime.datetime.now())[0:19],
            sort_line=params['line_name'],
            area_code=params['area_name'],
            location=params['station_name'],
            area_status='1' if finished else '4')
        res = http.post(url,json=json,timeout=4)
        print(res.json())
    except:
        print('钢板分拣状态上报：失败')
    else:
        print('钢板分拣状态上报：成功')

    return jsonify(err=None,val=True)

@blueprint.route('/report/part',methods=['PUT'])
def part():
    args = req.get_json()
    robot_name = args['name']
    plate_name = args['plate_name']
    part = args['part']
    pallet_name = args['pallet_name']
    params = config.robots(robot_name)
    station_name = params['station_name']
    host,port = config.scheduler['general_control']
    
    try:#回报零件状态-新城
        url = f'http://{host}:{port}/speedbot/system/recPartSortData'
        http.post(url,json=dict(
            sort_line=params['line_name'],
            area_code=params['area_name'],
            plate_id=plate_name,
            color_code=part['id'],
            part_code=part['kind'],
            robot_id=robot_name,
            location=station_name,
            part_type= '3' if int(part['handle']) < 2 else '4',
            place_id=pallet_name,
            epc_id=pallet_name,
            fj_start_time=str(datetime.datetime.now())[0:19],
            fj_end_time=str(datetime.datetime.now())[0:19],
        ),timeout=4)
    except:
        traceback.print_exc()
        print('上报零件：失败')
    else:
        print('上报零件：失败')
    
    return jsonify(err=None,val=True)