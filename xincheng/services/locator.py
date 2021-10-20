import os
import json
import config
from flask import Blueprint, jsonify, request as req
from speedbotlib.common.cache import dson
import traceback
import requests as http
from PIL import Image

blueprint = Blueprint('locator', __name__)


@blueprint.route('/large_sort_area/algo/status', methods=['POST'])
def vision_status():
    """
    视觉状态查询
    """
    try:
        args = req.get_json()
        try:
            args['sort_line']
            args['area_code']
        except KeyError:
            return dict(code=400, msg='参数错误！', data=args)
        params = config.agents
        list = []
        for i in range(len(params)):
            algo_code = params[i]['robot_name']
            host = params[i]['locating'][0]
            res = os.system('ping %s -c 1 -w 1 ' % host)
            if res == 0:
                algo_status = '1'
            else:
                algo_status = '0'
            js = dict(algo_code=algo_code, algo_status=algo_status)
            list.append(js)
        return jsonify(code=200, msg='success', data=list)
    except Exception as e:
        traceback.print_exc()
        return jsonify(code=400, msg=u'未知错误')


@blueprint.route('/large_sort_area/plc/status', methods=['POST'])
def plc_status():
    try:
        args = req.get_json()
        try:
            args['sort_line']
            args['area_code']
        except KeyError:
            return dict(code=400, msg='参数错误！', data=args)
        params = config.agents
        list = []
        for i in range(len(params)):
            plc_code = params[i]['robot_name']
            host = params[i]['plc'][0]
            res = os.system('ping %s -c 1 -w 1 ' % host)
            if res == 0:
                plc_status = '1'
            else:
                plc_status = '0'
            js = dict(plc_code=plc_code, plc_status=plc_status)
            list.append(js)
        return jsonify(code=200, msg='success', data=list)
    except Exception as e:
        traceback.print_exc()
        return jsonify(code=400, msg=u'未知错误')


@blueprint.route('/large_sort_area/system/queryPointEdge', methods=['POST'])
def QueryPointEdge():
    args = req.get_json()

    try:
        args['sort_line']
        args['area_code']
        station_name = args['location']
        params = config.stations(station_name)
        name = params['robot_name']
        cache_dir = f'static/vision/{name}'
    except KeyError:
        return dict(code=400, msg='参数错误！', data=args)

    if params['locating.version'] == 8:
        img_size = params['locating.photo_size']
        return dict(code=200, msg='success',data=dict(
            width=img_size[0],height=img_size[1],
            corner_img_url=f'{cache_dir}/current/originCorner.png', 
            edge_img_url=f'{cache_dir}/current/originEdge.png',
            corner_model_img_url=f'{cache_dir}/current/cornerResult.png',
            edge_model_img_url=f'{cache_dir}/current/edgeResult.png'))

    return dict(code=400,msg='错误得寻边版本',data='')

@blueprint.route('/large_sort_area/system/takePhoto', methods=['POST'])
def TakePhot():
    args = req.get_json()

    try:
        args['sort_line']
        args['area_code']
        args['location']

        params = config.stations(args['location'])
        host, port = params['agent']
        robot_name = params['robot_name']
        url = f'http://{host}:{port}/locating_photos/{robot_name}'
        res = http.get(url)
        val = res.json()['val']
        err = res.json()['err']
    except KeyError:
        return dict(code=400, msg='参数错误！', data=args)
    except:
        return dict(code=400, msg='连接错误!', data=None)
    return dict(code=200 if val else 400, msg='success' if val else err, data=None)


@blueprint.route('/large_sort_area/system/uptPointEdge', methods=['POST'])
def UpdatePointEdge():
    args = req.get_json()

    try:
        args['sort_line']
        args['area_code']
        args['location']
        x0 = args['corner_point_x']
        y0 = args['corner_point_y']
        x1 = args['edge_point_x']
        y1 = args['edge_point_y']

        params = config.stations(args['location'])
        host, port = params['agent']
        robot_name = params['robot_name']
        url = f'http://{host}:{port}/locating_calculation/{robot_name}'
        res = http.put(url, json=dict(x0=x0,y0=y0,x1=x1,y1=y1))
        val = res.json()['val']
        err = res.json()['err']

        # if val:
        #     res = http.put(f'http://{host}:{port}/recover/{robot_name}')
        #     val = res.json()['val']
        #     err = res.json()['err']
    except KeyError:
        return dict(code=400, msg='参数错误！', data=args)
    except:
        return dict(code=400, msg='连接错误!', data=None)

    return dict(code=200 if val else 400, msg='success' if val else err, data=None)
