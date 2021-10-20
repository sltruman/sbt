import sys

sys.path.append("../")
import picker.camera
import config

plate_png_file = '/2021-07-02/M210626610L8A52/M210626610L8A52/large_first_result/plate.png'
name = '7'
size=[6100, 1600]

if name == '7':
    params = {"plc":['192.168.1.105',102,0,1],"plc.areas":([-3400,3200],[20,8000],[-500,500]),"plc.dbs":[13,14],
              "locating.points.A":[-143.68, 6532.74, 500, -90],"locating.points.B":[3200, 6452.64, 500, 90],
              "locating":['192.168.10.15',30002]}
else:
    params = {"plc":['192.168.1.105',102,0,1],"plc.areas":([-3400,3200],[20,8000],[-500,500]),"plc.dbs":[27,28],
              "locating.points.A":[453.68, 6532.16, 500, -90],"locating.points.B":[3333, 6452.64, 500, 90],
              "locating":['192.168.10.15',30002]}
plate = {"size": size, "plate_png_path": plate_png_file}
print(picker.camera.take_photos(name=name, params=params, plate=plate))

