import os
import sys   
import traceback
import json

from snap7 import exceptions
from speedbotlib.common.cache import dson
from flask import Flask,jsonify,request as req
from flask_cors import CORS
import requests as http
import picker.truss

workers = dict()

app = Flask(__name__,'')
CORS(app,send_wildcard=True)

@app.route('/params/set/<name>',methods=['PUT'])
def params_set(name):
    args = req.get_json()
    params = dson(f'db/params/{name}.json',**args['params'])
    if name not in workers:
        print(f'初始化机器人{name}配置！')
        workers[name] = picker.truss.Truss(params)
    else: 
        print(f'更新机器人{name}配置！')
        workers[name].params = params
    return jsonify(err='',val=True)

@app.route('/status/<name>',methods=['GET'])
def status(name):
    try:
        worker = workers[name]
        status = worker.status.value
        status['step'] = worker.state
        status['plate'] = dson(f'db/plates_sorting/{status["plate_name"]}.json').value
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}异常！',val=None)

    return jsonify(err=None,val=status)

@app.route('/status/placeable/<name>',methods=['PUT'])
def status_placeable(name):
    args = req.get_json()

    try:
        worker = workers[name]
        worker.status['placeable'] = args['placeable']
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}异常！',val=False)

    return jsonify(err=None,val=True)

@app.route('/start/<name>',methods=['PUT'])
def start(name):
    args = req.get_json()
    plate = args['plate']
    plate_name = plate['name']

    worker = workers[name]
    plate = dson(f'db/plates_sorting/{plate_name}.json',**plate)
        
    if worker.state == 'initial' or worker.state == 'waiting':
        workers[name].start(plate)
        return jsonify(err=None,val=True)

    return jsonify(err=f'机器人{name}处于工作状态，无法再次启动！',val=False)

@app.route('/pause/<name>',methods=['PUT'])
def pause(name):
    try:
        workers[name].pause()
    except:
        return jsonify(err=f'机器人{name}处于待机状态，无法暂停！',val=False)

    return jsonify(err=None,val=True)

@app.route('/recover/<name>',methods=['PUT'])
def recover(name):
    try:
        worker = workers[name]
        status = worker.status
        plate_name = status["plate_name"]
        plate = dson(f'db/plates_sorting/{plate_name}.json')
        worker.start(plate)
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}处于工作状态，无法恢复！',val=False)
    return jsonify(err=None,val=True)

@app.route('/stop/<name>',methods=['PUT'])
def stop(name):
    try:
        worker = workers[name]
        if worker.state != 'initial': worker.stop()
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}处于待机状态，无法停止！',val=False)
    return jsonify(err=None,val=True)
    
@app.route('/plate/<name>',methods=['PUT'])
def plate(name):
    args = req.get_json()
    params = args['params']
    plc = params['plc']
    line_name = params['line_name']
    area_name = params['area_name']

    host,port,rack,slot = params['plc']
    area_x,area_y,area_z = params['plc.areas.x'],params['plc.areas.y'],params['plc.areas.z']
    truss = truss.Truss(name,host,port,rack,slot,area_x,area_y,area_z)
    rfid = truss.plate_rfid()
    del plc

    return jsonify(err=None,val=rfid)

@app.route('/<name>/status/pallets/<pallet_name>/in',methods=['PUT'])
def pallet_in(name,pallet_name):
    try:
        worker = workers[name]
        if worker.state != 'initial' and worker.state != 'waiting' and worker.state != 'placing':
            return jsonify(err=f'机器人{name}处于工作状态，无法清框！',val=False)

        stacks = workers[name].stacks
        stacks[pallet_name] = []
    except:
        return jsonify(err=f'清框失败！',val=False)
    return jsonify(err=None,val=True)

@app.route('/<name>/pallets/<pallet_name>/stacks/offset',methods=['PUT'])
def pallet_stack_offset(name,pallet_name):
    try:
        args = req.get_json()
        stack_name,stack_offset = args['stack_name'],args['stack_offset']

        def find_stack(stack_name,stacks):
            for stack in stacks:
                _,_,_,kind,_ = stack[0]
                if stack_name == kind: return stack
            return []

        def clear_empty_stack(stacks):
            try:
                while True:
                    stacks.remove([])
            except ValueError:
                pass

        def stack_increment(stack):
            layer = stack[0]
            name,offset,size,kind,_ = layer
            offset = offset[0],offset[1],offset[2] + size[2]
            stack.append([name,offset,size,kind])
            
        def stack_decrement(stack):
            stack.pop()

        pallets = workers[name].stacks
        pallet = pallets[pallet_name]

        stack = find_stack(stack_name,pallet)

        if not stack: return jsonify(err='没有找到码垛！',val=False)
        for i in range(0,stack_offset,1 if 0 < stack_offset else -1):
            stack_increment(stack) if 0 < stack_offset else stack_decrement(stack)
            
        clear_empty_stack(pallet)
        pallets[pallet_name] = pallet
    except KeyError:
        return jsonify(err=f'没有找到码垛！',val=False)
    except:
        traceback.print_exc()
        return jsonify(err=f'无法修改码垛！',val=False)
    return jsonify(err=None,val=True)

@app.route('/<name>/status/pallets/<pallet_name>',methods=['GET'])
def pallets(name,pallet_name):
    try:
        all_stacks = workers[name].stacks
        stacks = all_stacks[pallet_name]
    except:
        stacks = []
    return jsonify(err=None,val=stacks)

@app.route('/locating_photos/<name>',methods=['GET'])
def locating_photos(name):
    try:
        worker = workers[name]
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}不存在！',val=False)

    step = worker.status['step']
    print('请求拍照：',name,step)

    if step != 'initial' and step != 'waiting':
        e = f'机器人{name}正在分拣中，无法进行拍照！'
        print(e)
        return jsonify(err=e,val=False)

    del worker.status['corner']

    try:
        import picker.camera
        picker.camera.take_photos(name,worker.params)
    except Exception as e: 
        return jsonify(err=str(e),val=False)

    return jsonify(err=None,val=True)

@app.route('/locating_calculation/<name>',methods=['PUT'])
def locating_calculation(name):
    args = req.get_json()
    x0 = args['x0']
    y0 = args['y0']
    x1 = args['x1']
    y1 = args['y1']

    try:
        worker = workers[name]
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}不存在！',val=False)

    step = worker.status['step']
    print('角点计算：',name,step)
    if step != 'initial' and step != 'waiting':
        return jsonify(err=f'机器人{name}正在分拣中，无法进行手动定位寻边！',val=False)

    try:
        import picker.camera
        worker.status['corner'] = picker.camera.calculating_offset(name,worker.params,x0,y0,x1,y1)
    except Exception as e:
        return jsonify(err=str(e),val=False)

    return jsonify(err=None,val=True)


@app.route('/losted_parts/<name>',methods=['PUT'])
def losted_parts(name):
    try:
        worker = workers[name]
    except:
        traceback.print_exc()
        return jsonify(err=f'机器人{name}不存在！',val=False)

    args = req.get_json()
    plate_name = args['plate_name']
    part_names = args['part_names']

    print(f'补抓钢板{plate_name}零件：{part_names}')

    step = worker.state
    # if step != 'initial' and step != 'waiting' and step != 'placing':
    #     e = f'机器人{name}正在分拣中，无法进行补抓！'
    #     print(e)
    #     return jsonify(err=e,val=False)

    plate_path = f'db/plates_sorting/{plate_name}.json'
    if not os.path.exists(plate_path):
        e = f'钢板不存在！'
        print(e)
        return jsonify(err=e,val=False)

    if worker.plate: plate = worker.plate
    else: plate = dson(plate_path)

    if plate['finished']:
        e = f'钢板已分拣完！'
        print(e)
        return jsonify(err=e,val=False)

    parts = plate['parts']
    for part in parts:
        if part['id'] in [name for name in part_names]:
            part['picked'] = False
            print(part)

    plate['parts'] = parts
    return jsonify(err=None,val=True)


if __name__ == '__main__':
    os.makedirs('db/plates_sorting',exist_ok=True)
    os.system('chmod ugo+rw db/plates_sorting')
    
    if 3 != len(sys.argv):
        print('usage: python agent.py <port> <name>')
    else:
        name = sys.argv[2]
        params = dson(f'db/params/{name}.json')
        print(f'初始化机器人{name}配置！')

        try:
            workers[name] = picker.truss.Truss(params)
        except:
            pass

        #对外开放接口
        app.run('0.0.0.0',port=sys.argv[1],debug=False)