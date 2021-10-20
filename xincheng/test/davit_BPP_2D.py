import sys
import numpy as np
import time




global tray_x, tray_y
tray_x, tray_y = 6000, 3000 

global left_limit_rate, right_limit_rate
left_limit_rate, right_limit_rate = 0.33, 0.33

global left_limit, right_limit
left_limit = tray_x * left_limit_rate
right_limit = tray_x * (1 - right_limit_rate)

class New_part:
    def __init__(self,num_p,id,l,w,state):
        self.type = "Part"
        self.num = num_p
        self.id = id
        self.len = l
        self.wid = w
        self.state = state

        self.posx = -1
        self.posy = -1
        self.posz = 0
        self.rotx = 0
        self.roty = 0
        self.rotz = 0

        if self.len < self.wid:
            self.wid = l
            self.len = w
            self.rotz = 90



class New_Box:
    def __init__(self,num_b,part):

        assert part.type == "Part"

        self.num = num_b
        self.type = "Box"
        self.id = part.id
        self.len = part.len
        self.wid = part.wid
        self.state = part.state

        self.pos_x = -1
        self.pos_y = 0
        
        self.max_count = tray_y//self.wid
        self.full = False
        self.count = 0

        self.parts = []
        self.add_part(part)

        

    def add_part(self,part):
        assert part.type == "Part"
        assert not self.full
        
        self.count += 1
        self.parts.append(part)

        part.posy = self.pos_y + self.wid/2
        self.pos_y += self.wid
        
        if self.count == self.max_count:
            self.full = True
    
    def place(self,x):
        assert self.pos_x < 0
        self.pos_x = x 

        for part in self.parts:
            part.posx = self.pos_x + part.len/2
        


class New_Tray:
    def __init__(self,num_t):
        
        self.num = num_t
        self.type = "Tray"
        self.x = tray_x
        self.y = tray_y
        
        self.reset()
    
    def reset(self):
        self.placed_boxes = []
        self.empty_space = [0,tray_x]
        self.empty_len = self.empty_space[1] - self.empty_space[0]

    def place_and_update(self,box):
        assert box.type == "Box"

        if box.state in [0,2]:
            box.place(self.empty_space[0])
            self.empty_space[0] += box.len
        else:
            self.empty_space[1] -= box.len
            box.place(self.empty_space[1])
        
        self.placed_boxes.append(box)
        self.empty_len = self.empty_space[1] - self.empty_space[0]





def msg2part(msgs):
    
    parts = []

    for i,msg in enumerate(msgs):
        num_p = i+1
        id_p = msg[0]
        l = msg[1]
        w = msg[2]
        state = msg[3]
        
        part = New_part(num_p,id_p,l,w,state)
        
        if part.len > tray_x or part.wid > tray_y:
            continue

        parts.append(part)
    

    print("msg2part complete")
    print("check part:")
    for p in parts:
        print(p.num," ",p.id," ",p.len," ",p.wid," ",p.state," \trotz:",p.rotz," ")
    print("")    

    return parts



def part2box(parts):

    boxes = []

    for part in parts:
        accessable_box_exist = False
        for box in boxes:
            if (part.id == box.id and part.state == box.state and box.full == 0):
                box.add_part(part)
                accessable_box_exist = True
                break
        if not accessable_box_exist:
            num_b = len(boxes) + 1
            tmp_box = New_Box(num_b,part)
            boxes.append(tmp_box)
    
    print("part2box complete")
    print("check box:")
    for b in boxes:
        print(b.num," ",b.id," ",b.len," ",b.wid," ",b.state," \tcount:",b.count," ")
    print("") 
    return boxes

def sort_boxes(boxes):
    boxes_left = []
    boxes_right = []
    boxes_both = []

    for box in boxes:
        if box.state == 0:
            boxes_left.append(box)
        elif box.state == 1:
            boxes_right.append(box)
        elif box.state == 2:
            boxes_both.append(box)
    
    sorted_boxes = sorted(boxes_left,key = lambda x:x.len, reverse = True) + \
        sorted(boxes_both,key = lambda x:x.len, reverse = True) + sorted(boxes_right,key = lambda x:x.len, reverse = True)
    
    print("boxsort complete")
    print("check sorted box:")
    for b in boxes:
        print(b.num," ",b.id," ",b.len," ",b.wid," ",b.state," \tcount:",b.count," ")
    print("") 
    
    return sorted_boxes[::-1]

def box_placable_into_tray(box,tray):

    if box.len > tray.empty_len:
        return False
    if box.state == 0 and tray.empty_space[0] + box.len/2 > left_limit:
        return False
    if box.state == 1 and tray.empty_space[1] - box.len/2 < right_limit:
        return False
    return True


def BPP(boxes):
    
    trays = []
    num_t = 1
    while len(boxes)>0:
        tray = New_Tray(num_t)
        for box in boxes[::-1]:
            if box_placable_into_tray(box,tray):
                tray.place_and_update(box)
                boxes.remove(box)
        
        if len(tray.placed_boxes) ==0:
            print("rest boxes unplacable,they are")
            for box in boxes[::-1]:
                print(box.num,"\tid:",box.id,"\tlen:",box.len,"\twid:",box.wid,"\tstate:",box.state,"\tcount:",box.count)
            break
        else:
            trays.append(tray)
            num_t += 1
    
    print("BPP complete")
    print("check tray:")
    for t in trays:
        print(t.num,"\tplaced boxes:",len(t.placed_boxes),"\tempty space:",t.empty_space,"\tempty len:",t.empty_len)
        for b in t.placed_boxes:
            print("\tbox:\t",b.num,"\t",b.id,"\tpos_x:",[b.pos_x,b.pos_x+b.len])
            for p in b.parts:
                print("\t\tpart:\t",p.num,"\t",p.id,"\tpos_y:",[p.posy-p.wid/2,p.posy+p.wid/2])

    print("") 

    return trays


def extract_placed_parts_info(trays):

    placed_parts_msg = []
    total_count = 0
    f = open('data.txt','a')
    f.write(time.asctime())
    f.write("\n")
    print("FINAL RESULT:")
    for tray in trays:
        placed_parts_in_a_tray =[]
        parts_count = 0
        print("parts in tray:",tray.num)
        f.write("parts in tray: " + str(tray.num) + "\n")
        for box in tray.placed_boxes:
            for part in box.parts:
                num_p = part.num
                id_p = part.id
                posx = part.posx
                posy = part.posy
                posz = part.posz
                rotx = part.rotx
                roty = part.roty
                rotz = part.rotz
                placed_parts_in_a_tray.append([num_p, id_p, posx, posy, posz, rotx, roty, rotz])
                print([num_p, id_p, posx, posy, posz, rotx, roty, rotz])
                f.write(str([num_p, id_p, posx, posy, posz, rotx, roty, rotz]) + "\n")
                parts_count += 1
        print("number of parts placed here is:",parts_count)
        f.write("number of parts placed here is: " + str(parts_count) + "\n")
        placed_parts_msg.append(placed_parts_in_a_tray)
        total_count += parts_count
    print("total placed parts count:",total_count)
    f.write("total placed parts count: " + str(total_count)+"\n\n\n\n")
    print("mission complete\n")
    f.close()
    return placed_parts_msg   



    return placed_parts_msg

def BPP_calculation(msgs):

    print("msg received, msg count:",len(msgs))
    parts = msg2part(msgs)
    boxes = part2box(parts)
    reversed_sorted_boxes = sort_boxes(boxes)
    trays = BPP(reversed_sorted_boxes)
    placed_parts_msg = extract_placed_parts_info(trays)

    return placed_parts_msg





#####demo#####

#input format:  input = [part,part,part],   part = [id,len,wid,state]
msg = [["a",1000,1000,1],["a",1000,1000,1],["a",1000,1000,0],["d",1000,1000,0],["b",1500,2500,0],["b",1500,2500,1],["c",3000,1000,2]]
msg = [["aaa",4000,3000,2]]
#call the function
response = BPP_calculation(msg)

#output format: output = [tray,tray,tary],  tray = [part,part,part], part = [input_number, id, posx, posy, posz, rotx, roty, rotz]
print("response:\n",response)