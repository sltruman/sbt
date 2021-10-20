#!/usr/bin/env python
import os
from flask import Flask,jsonify,request as req
from flask_cors import CORS
import config
import sys
import requests as http
import services.report
import services.station
import services.robot
import services.pallet
import services.locator

app = Flask(__name__)
CORS(app,send_wildcard=True)

if __name__ == '__main__':
    os.makedirs('db/plates',exist_ok=True)
    os.system('chmod ugo+rw db/plates')

    app.register_blueprint(services.report.blueprint)
    app.register_blueprint(services.station.blueprint)
    app.register_blueprint(services.robot.blueprint)
    app.register_blueprint(services.pallet.blueprint)
    app.register_blueprint(services.locator.blueprint)

    try:
        for params in config.agents:
            host,port = params['agent']
            name = params['robot_name']
            url = f'http://{host}:{port}/params/set/{name}'
            res = http.put(url,json=dict(params=params))
    except:
        print(f'无法连接到工作站{name}！')
    else:
        if 2 != len(sys.argv):
            print('usage: python scheduler.py <port>')
        else:
            #对外开放接口
            app.run('0.0.0.0',port=sys.argv[1],debug=False)