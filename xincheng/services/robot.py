import threading
from flask import Blueprint,jsonify,request as req
import traceback
from speedbotlib.common.cache import dson
import config
import requests as http
import os
import json

blueprint = Blueprint('robot',__name__)

def status_sync(params):
    host,port = params['agent']
    name = params['robot_name']

    try:
        url = f'http://{host}:{port}/status/{name}'
        res = http.get(url)
    except:
        traceback.print_exc()
        return

    status = res.json()['val']
    plate_later = status['plate']

    if plate_later:
        dson(f'db/plates/{plate_later["name"]}.json',**plate_later)
    pass

@blueprint.route('/large_sort_area/robot/status',methods=['POST'])
def robot_status():
    args = req.get_json()      
    try:
        line_name = args['sort_line']
        area_name = args['area_code']
    except:
        traceback.print_exc()
        return jsonify(code=400,msg=f'参数错误！',data=args)

    vals = []

    for params in config.agents:
        host,port = params['agent']
        name = params['robot_name']
        try:
            url = f'http://{host}:{port}/status/{name}'
            res = http.get(url)
            status = res.json()['val']
        except:
            print(f'无法获得机器人{name}的状态！')
            traceback.print_exc()
            robot_state = '2' #报错
        else:
            if status['disabled']:
                robot_state = '2'
            elif status['step'] == 'waiting':
                robot_state = '3'
            else:
                robot_state = '1' if status['step'] != 'initial' else '0'
        vals.append(dict(robot_code=name,robot_status=robot_state))
    return jsonify(code=200,msg='成功！',data=vals)

@blueprint.route('/large_sort_area/robot/pause',methods=['POST'])
def robot_pause():
    data = []
    try:
        args = req.get_json()
        line_name = args['sort_line']

        for robot_name in args['robot_code']:
            try:
                station = config.robots(robot_name)
                host,port = station['agent']
                url = f'http://{host}:{port}/pause/{robot_name}'
                res = http.put(url)
                if res.json()['err']: raise Exception
            except:
                data.append(f'pausing robot {robot_name} failed!')
    except KeyError:
        return jsonify(code=400,msg=f'params error!',data=args)

    return jsonify(code=200,msg='success',data=data)

@blueprint.route('/large_sort_area/robot/recover',methods=['POST'])
def robot_recover():
    try:
        args = req.get_json()
        line_name = args['sort_line']
        data = []
        for robot_name in args['robot_code']:
            try:
                params = config.robots(robot_name)
                host,port = params['agent']

                url = f'http://{host}:{port}/recover/{robot_name}'
                res = http.put(url)
                if res.json()['err']: raise Exception
            except:
                pass
    except KeyError:
        return jsonify(code=400,msg='params error!',data='')

    return jsonify(code=200,msg='success',data=data)
