import os
import threading
from flask import Blueprint,jsonify,request as req
import traceback
from common import data_process as dp
from speedbotlib.common.cache import dson
import config
import requests as http
import datetime
from PIL import Image

blueprint = Blueprint('station',__name__)

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

@blueprint.route('/large_sort_area/system/inPlace',methods=['POST'])
def plate():
    def staring2(station_name,line_name,area_name,plate_name,plate_thickness,file_path,plate_offset):
        params = config.stations(station_name)
        robot_name = params['robot_name']
        
        plate_png_file = os.path.join(file_path,'plate.png')
        robot_plc_csv = os.path.join(file_path,'robot_plc_r.csv')
        
        if not os.path.exists('data' + robot_plc_csv) or not os.path.exists('data' + plate_png_file):
            print(f'没有找到套料图文件:{robot_plc_csv}或{plate_png_file}')
            return dict(val=False,err=f'没有找到套料图文件:{robot_plc_csv}或{plate_png_file}')

        if os.path.exists(f'db/plates/{plate_name}.json'):
            plate = dson(f'db/plates/{plate_name}.json')
            if plate['finished']:
                print(f'钢板{plate_name}早已分拣！')
                return dict(val=False,err=f'钢板{plate_name}早已分拣！')
            else:
                print(f'钢板{plate_name}继续分拣.')
        else:
            print(f'钢板{plate_name}开始分拣.')
            img_size = Image.open('data' + plate_png_file).size
            plate_size = [img_size[0],img_size[1],plate_thickness]
            plate_parts = dp.csv3_to_json(plate_size,'data' + robot_plc_csv)
            plate = dson(f'db/plates/{plate_name}.json',name=plate_name,size=plate_size,parts=plate_parts,plate_png_path=plate_png_file,finished=False,offset=plate_offset)
        
        try:
            host,port = params['agent']
            url = f'http://{host}:{port}/start/{robot_name}'
            res = http.put(url,json=dict(params=params,plate=plate.value))
        except:
            traceback.print_exc()
            print('启动分拣失败！')
            res = dict(err='无法连接桁架代理！',val=False)
        else:
            try:
                host,port = config.scheduler['general_control']
                url = f'http://{host}:{port}/speedbot/system/recStatusData'
                json=dict(plate_id=plate_name,time=str(datetime.datetime.now())[0:19],sort_line=line_name,area_code=area_name,location=station_name,area_status='0')
                http.post(url,json=json,timeout=10)
            except:
                print('上报钢板分拣状态：失败')
                traceback.print_exc()
            else: 
                print('上报钢板分拣状态：成功')

        return res.json()

    args = req.get_json()
    print('钢板到位:',args)
    
    try:
        line_name = args['sort_line']
        station_name = args['location']
        area_name = args['area_code'] 
        plate_name = args['plate_id']
        plate_size = float(args['length']),float(args['width']),float(args['thickness'])
        file_path = args['file_path'] + '/large_first_result'
        import re
        m = re.match(r'(-?\d+);(-?\d+);-?\d+;-?\d+;(-?[0-9]+\.[0-9]+)',args['plate_location'])
        if m: plate_offset = int(m.group(2)),int(m.group(1)),float(m.group(3))
        else: plate_offset = 0,0,0.0
    except:
        return jsonify(code=400,msg='参数错误!',data=args)
    
    try:
        params = config.stations(station_name)
    except:
        return jsonify(code=400,msg=f'找不到分拣区{station_name}!',data=args)
    
    for params in config.agents:
        status_sync(params)
    
    #os.system('mount -t cifs -o username=speedbot,password=Speedbot12#$ //192.168.10.10/file_share `pwd`/data')
    res = staring2(station_name,line_name,area_name,plate_name,plate_size[2],file_path,plate_offset)
    #os.system('umount `pwd`/data')
    return jsonify(code=200 if res['val'] else 400,msg='成功！' if res['val'] else res['err'],data=None)


@blueprint.route('/large_sort_area/system/end',methods=['POST'])
def stop():
    try:
        args = req.get_json()
        line_name = args['sort_line']
        station_name = args['location']
    except:
        traceback.print_exc()
        return jsonify(code=400,msg='参数错误！',data=None)

    try:
        params = config.stations(station_name)
        host,port = params['agent']
        robot_name = params['robot_name']
        url = f'http://{host}:{port}/stop/{robot_name}'
        res = http.put(url)
        err = res.json()['err']
        val = res.json()['val']
    except:
        traceback.print_exc()
        return jsonify(code=400,msg=f'无法与工作站{station_name}通信！',data=None)
    
    status_sync(params) #更新工作站状态

    if err: return jsonify(code=400,msg=err,data=None)
    return jsonify(code=200,msg='成功！',data=None)

@blueprint.route('/large_sort_area/system/status',methods=['POST'])
def station_status():
    args = req.get_json()
    line_name = args['sort_line']
    station_name = args['location']

    params = config.stations(station_name)
    host,port = params['agent']
    robot_name = params['robot_name']
    
    try:
        url = f'http://{host}:{port}/status/{robot_name}'
        res = http.get(url,timeout=2)
        status = res.json()['val']
    except:
        print(f'无法获得工作区{station_name}的状态！')
        traceback.print_exc()
        step_code = '2'
    else:
        if status['disabled']:
            step_code = '2'
        elif status['step'] == 'waiting':
            step_code = '3'
        else:
            step_code = '1' if status['step'] != 'initial' else '0'
    return jsonify(code=200,msg='成功！',data=step_code)

@blueprint.route('/large_sort_area/system/catchPointPartInfos',methods=['POST'])
def losted_parts():
    try:
        args = req.get_json()
        station_name = args['location']
        plate_name = args['plate_id']
        part_names = [info['color_code'] for info in args['part_infos']]

        params = config.stations(station_name)
        host,port = params['agent']
        robot_name = params['robot_name']
    except:
        print(args)
        traceback.print_exc()
        return jsonify(code=400,msg='参数错误!',data=args)
    
    try:
        url = f'http://{host}:{port}/losted_parts/{robot_name}'
        res = http.put(url,json=dict(plate_name=plate_name,part_names=part_names))
        val = res.json()['val']
        err = res.json()['err']
    except:
        traceback.print_exc()
        return jsonify(code=400,msg='无法连接到代理！',data=None)    
    if err: return jsonify(code=400,msg=err,data=None)
    return jsonify(code=200,msg='成功！',data=None)

@blueprint.route('/large_sort_area/system/uptLargeModelState',methods=['POST'])
@blueprint.route('/large_sort_area/system/queryLargeModelState',methods=['POST'])
def mode():
    args = req.get_json()
    station_name = args['location']
    # area_name = args['area_code']
    
    params = config.stations(station_name)
    host,port = params['agent']
    robot_name = params['robot_name']
    
    try:
        placeable = True if args['status_val'] == '0' else False

        try:
            url = f'http://{host}:{port}/status/placeable/{robot_name}'
            res = http.put(url,json=dict(placeable=placeable))
            val = res.json()['val']
            err = res.json()['err']
        except:
            traceback.print_exc()
            return jsonify(code=400,msg='无法连接到代理！',data=None)    
    except:
        try:
            res = http.get(f'http://{host}:{port}/status/{robot_name}')
            val = res.json()['val']
            err = res.json()['err']
        except:
            traceback.print_exc()
            return jsonify(code=400,msg='无法连接到代理！',data=None)    
        if err: return jsonify(code=400,msg=err,data=None)
        return jsonify(code=200,msg='成功！',data='0' if val['placeable'] else '1')
    else:
        if err: return jsonify(code=400,msg=err,data=None)
        return jsonify(code=200,msg='成功！',data=None)

@blueprint.route('/large_sort_area/system/judgePlateBelongLocation',methods=['POST'])
def judge_plate():
    try:
        args = req.get_json()
        plate_name = args['plate_id']
        plate_size = float(args['length']),float(args['width']),float(args['thickness'])
        file_path = args['file_path'] + '/large_first_result'
        import re
        m = re.match(r'(-?\d+);(-?\d+);-?\d+;-?\d+;(-?[0-9]+\.[0-9]+)',args['plate_location'])
        if m: plate_offset = int(m.group(2)),int(m.group(1)),float(m.group(3))
        else: plate_offset = 0,0,0.0
    except:
        return jsonify(code=400,msg='参数错误!',data=args)
    
    try:
        plate_png_file = os.path.join(file_path,'plate.png')
        robot_plc_csv = os.path.join(file_path,'robot_plc_r.csv')
        
        if not os.path.exists('data' + robot_plc_csv) or not os.path.exists('data' + plate_png_file):
            print(f'没有找到套料图文件:{robot_plc_csv}或{plate_png_file}')
            return jsonify(code=400,msg='没有找到套料图文件:{robot_plc_csv}或{plate_png_file}',data='')

        img_size = Image.open('data' + plate_png_file).size
        plate_size = [img_size[0],img_size[1],plate_size[2]]
        plate_parts = dp.csv3_to_json(plate_size,'data' + robot_plc_csv)
        
        station_2_critical_x = config.scheduler['station_2_critical_x']
        plate_left = station_2_critical_x - plate_offset[0] - plate_size[0]
    except:
        traceback.print_exc()
        return jsonify(code=400,msg='未知错误！',data='')
    
    return jsonify(code=200,msg='成功！',data='data')

@blueprint.route('/large_sort_area/system/sortFinishStatus',methods=['POST'])
def focused_parts():
    try:
        args = req.get_json()
        station_name = args['location']
    except:
        return jsonify(code=400,msg='参数错误!',data=args)

    try:
        try:
            params = config.stations('1')
            host,port = params['agent']
            name = params['robot_name']
            url = f'http://{host}:{port}/status/{name}'
            res = http.get(url)
        except:
            traceback.print_exc()
            return jsonify(code=400,msg='无法连接代理！',data='')

        status = res.json()['val']
        plate_later = status['plate']

        if status['step'] == 'initial':
            return jsonify(code=200,msg='成功！',data='0')

        plate_size = plate_later['size']
        plate_parts = plate_later['parts']
        plate_offset = plate_later['offset']
        
        station_2_critical_x = config.scheduler['station_2_critical_x']
        plate_left = station_2_critical_x - plate_offset[0] - plate_size[0]
        params = config.stations('2')
        area_x = params['plc.areas'][0]

        for part in plate_parts:
            if part['handle'] == 0: continue
            grab_pos_x = plate_left + part['b_grab_pos'][0]
            if grab_pos_x > area_x[1] and not part['picked']: 
                return jsonify(code=200,msg='成功！',data='2')
    except:
        traceback.print_exc()
        return jsonify(code=400,msg='无法获取任务信息！',data='')
    
    return jsonify(code=200,msg='成功！',data='1')
