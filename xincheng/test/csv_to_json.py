import sys
sys.path.append('..')
import pandas as pd
from pprint import pprint as print

def csv3_to_json(plate_name,plate_size,csv_file_path):
    import math

    def rotate(angle,value_x,value_y):
        radius = angle * math.pi / 180
        real_x = math.cos(radius) * value_x - math.sin(radius) * value_y
        real_y = math.cos(radius) * value_y + math.sin(radius) * value_x
        return [real_x,real_y]

    plate = dict(name=plate_name,size=plate_size,parts={})

    pd.read_csv(csv_file_path)
    middle_line = plate_size[0]/2

    for i,row in pd.read_csv(csv_file_path,keep_default_na=True).iterrows():
        level = row['size']
        if level < 2: continue
        if level == 3: handle = 2
        else: handle = 0 if row["bdcenter_x"] < middle_line and level == 2 else 1

        id = row['color_id']
        center = [row['center_x'],row["center_y"],plate_size[2]]
        a_offset = row["left_offset"].replace('(','').replace(')','').replace(' ','').split(',')
        b_offset = row['right_offset'].replace('(','').replace(')','').replace(' ','').split(',')
        a_offset = [float(a_offset[0]),float(a_offset[1])]
        b_offset = [float(b_offset[0]),float(b_offset[1])]
        if handle == 1: a_offset,b_offset = b_offset,a_offset

        a_magnetic = row["left_one"],row["left_two"],row["left_three"],row["left_four"],row["left_five"],row["left_six"]
        b_magnetic = row["right_one"],row["right_two"],row["right_three"],row["right_four"],row["right_five"],row["right_six"]
        if handle == 1: a_magnetic,b_magnetic = b_magnetic,a_magnetic

        a_grab_degree_offset = row["left_angleoffset"]
        b_grab_degree_offset =  row["right_angleoffset"]
        if handle == 1: a_grab_degree_offset,b_grab_degree_offset = b_grab_degree_offset,a_grab_degree_offset

        part_degree = row['angle']
        a_pos_offset = rotate(part_degree,a_offset[0],a_offset[1])
        b_pos_offset = rotate(part_degree,b_offset[0],b_offset[1])

        a_grab_pos = [center[0] + a_pos_offset[0],center[1] + a_pos_offset[1],0]
        b_grab_pos = [center[0] + b_pos_offset[0],center[1] + b_pos_offset[1],0]

        rotatable_180 = row['part_rotation']
        a_drop_degree = (180 - part_degree if rotatable_180 else 0) + a_grab_degree_offset
        b_drop_degree = (180 - part_degree if rotatable_180 else 0) + b_grab_degree_offset

        a_grab_degree = part_degree + a_grab_degree_offset
        b_grab_degree = part_degree + b_grab_degree_offset
        
        a_drop_pos_offset = [-a_offset[0],-a_offset[1]] if rotatable_180 else a_offset
        b_drop_pos_offset = [-b_offset[0],-b_offset[1]] if rotatable_180 else b_offset

        center[1] = plate_size[1] - center[1]
        a_drop_pos_offset[1] = -a_drop_pos_offset[1]
        b_drop_pos_offset[1] = -b_drop_pos_offset[1]
        a_grab_pos[1] = plate_size[1] - a_grab_pos[1]
        b_grab_pos[1] = plate_size[1] - b_grab_pos[1]

        if handle == 0:
            b_grab_pos = []
            b_grab_degree = 0
            b_drop_pos_offset= []
            b_drop_degree = 0
            b_magnetic = []
        elif handle == 1:
            a_grab_pos = []
            a_grab_degree = 0
            a_drop_pos_offset= []
            a_drop_degree = 0
            a_magnetic = []

        part = dict(id=id,handle=handle,center=center,
                    a_grab_pos=a_grab_pos,b_grab_pos=b_grab_pos,
                    a_grab_degree=a_grab_degree,b_grab_degree=b_grab_degree,
                    a_drop_pos_offset=a_drop_pos_offset,b_drop_pos_offset=b_drop_pos_offset,
                    a_drop_degree=a_drop_degree,b_drop_degree=b_drop_degree,
                    a_magnetic_dots=a_magnetic,b_magnetic_dots=b_magnetic,
                    kind=row['part_class']
                    )

        plate['parts'][id] = part
        print(part)

    
    return plate['parts']

csv3_to_json('a',[8100.0,1450.0,4.0],r'../data/2021-07-02/M210626610L8A52/M210626610L8A52/large_first_result/robot_plc_r.csv')
# csv3_to_json('a',[8100.0,1450.0,4.0],r'../data/2021-07-02/M210630610L8A15/M210630610L8A17/large_first_result/robot_plc_r.csv')
