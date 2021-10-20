import json
import pandas as pd
import math

def csv3_to_json(plate_size,csv_file_path):
    import math

    def rotate(angle,value_x,value_y):
        radius = angle * math.pi / 180
        real_x = math.cos(radius) * value_x - math.sin(radius) * value_y
        real_y = math.cos(radius) * value_y + math.sin(radius) * value_x
        return [real_x,real_y]

    pd.read_csv(csv_file_path)
    middle_line = plate_size[0] / 2 if plate_size[0] > 5000 else 0
    parts = []

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

        a_grab_degree = part_degree - a_grab_degree_offset
        b_grab_degree = part_degree - b_grab_degree_offset

        if handle < 2:
            rotatable_180 = row['part_rotation']
            a_drop_degree = (180 if rotatable_180 else 0) - a_grab_degree_offset
            b_drop_degree = (180 if rotatable_180 else 0) - b_grab_degree_offset
            if a_drop_degree > 180: a_drop_degree = -(180 + a_grab_degree_offset)
            if b_drop_degree > 180: b_drop_degree = -(180 + b_grab_degree_offset)
        else:                
            a_drop_degree,b_drop_degree=a_grab_degree,b_grab_degree
        
        center[1] = plate_size[1] - center[1]
        a_grab_pos[1] = plate_size[1] - a_grab_pos[1]
        b_grab_pos[1] = plate_size[1] - b_grab_pos[1]
       
        a_pos_offset = rotate(part_degree,a_offset[0],a_offset[1]) if level==3 else a_offset
        b_pos_offset = rotate(part_degree,b_offset[0],b_offset[1]) if level==3 else b_offset
        a_drop_pos_offset = [-a_pos_offset[0],a_pos_offset[1]] if handle < 2 and rotatable_180 else [a_pos_offset[0],-a_pos_offset[1]]
        b_drop_pos_offset = [-b_pos_offset[0],b_pos_offset[1]] if handle < 2 and rotatable_180 else [b_pos_offset[0],-b_pos_offset[1]]
        
        def count_one(n):
            count = 0  # 用来计数
            while n > 0:
                if n!= 0:
                    n = n &(n - 1)
                count += 1
            return count

        weight = 0
        for v in a_magnetic + b_magnetic:
            weight += count_one(v)

        part = dict(id=id,handle=handle,center=center,
                    a_grab_pos=a_grab_pos,b_grab_pos=b_grab_pos,
                    a_grab_degree=a_grab_degree,b_grab_degree=b_grab_degree,
                    a_drop_pos_offset=a_drop_pos_offset,b_drop_pos_offset=b_drop_pos_offset,
                    a_drop_degree=a_drop_degree,b_drop_degree=b_drop_degree,
                    a_magnetic_dots=a_magnetic,b_magnetic_dots=b_magnetic,
                    size=[row["width"],row["height"],plate_size[2]],weight=weight,
                    maximum_size=[row["width"] + abs(a_offset[0]),row["height"] + abs(a_offset[1]),plate_size[2]],
                    degree=part_degree,kind=row['part_class'],level=level,
                    picked=False)

        if handle == 0:
            del part['b_grab_pos']
            del part['b_grab_degree']
            del part['b_drop_pos_offset']
            del part['b_drop_degree']
            del part['b_magnetic_dots']
        elif handle == 1:
            del part['a_grab_pos']
            del part['a_grab_degree']
            del part['a_drop_pos_offset']
            del part['a_drop_degree']
            del part['a_magnetic_dots']
        parts.append(part)
    return sorted(parts,key=lambda v:v['weight'])