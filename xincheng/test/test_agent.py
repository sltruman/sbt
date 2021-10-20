import sys

sys.path.append('..')
from flask import Flask, jsonify, request as req
import robot.plc

app = Flask(__name__, '')


@app.route("/test/move", methods=['POST'])
def test_val():
    try:
        args = req.get_json()
        try:
            station_name = args['station_name']
            truss_name = args['truss_name']
            move_point = args['move_point']
        except:
            return dict(code=400, msg='参数错误！', data=args)
        if station_name == '7':
            dbs = [13, 14]
        else:
            dbs = [27, 28]

        print(f"***************写入点位{move_point}******************")
        truss = robot.plc.Truss('192.168.1.105', dbs=dbs, name=station_name,
                                area_x=(-3400, 3200), area_y=(20, 8000), area_z=(0, 1000.99))
        if truss_name == 'a':
            truss.a_move(move_point)
        else:
            truss.b_move(move_point)
    except:
        return jsonify(code=400, msg='fail', data='')
    return jsonify(code=200, msg='success', data='')


if __name__ == '__main__':
    app.run('0.0.0.0', port=9527, debug=False)
