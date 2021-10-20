from copy import deepcopy

class Pallet:
    def __init__(self,size,stacks):
        self.stacks = stacks
        self.size = size
        pass
    def __def__(self):
        pass
    def put(self,part_name,part_size,part_kind,part_real_size=[0,0,0],section_x=None):
        from copy import deepcopy
        part_size[0] = part_size[0] + 100
        part_size[1] = part_size[1] + 100

        if not self.size: return None
        if not section_x: section_x = [0,self.size[0]]

        stack = []

        stacks_placeable = [stack for stack in self.stacks if stack[-1][3] == part_kind]

        for stack in stacks_placeable:
            height = 0
            for _,_,stack_part_size,_,_ in stack: height += stack_part_size[2]
            
            if height > self.size[2]: 
                stack = []
                continue

        if stack:
            _,p0,_,_,_ = deepcopy(stack[-1])
            p0[2] = p0[2] + part_size[2]
            stack.append((part_name,p0,part_size,part_kind,part_real_size))
            return p0[0] + part_size[0] / 2,p0[1] + part_size[1] / 2,p0[2] # 放置点
        
        #没找到可放置的堆
        for x in range(section_x[0],section_x[1],10):
            for y in range(0,self.size[1],10):
                p0 = [x,y,0]              #左下
                p1 = x + part_size[0],y,0      #右下
                p2 = x + part_size[0],y + part_size[1],0  #右上
                p3 = x,y + part_size[1],0   #左上
                center = p0[0] + part_size[0] / 2,p0[1] + part_size[1] / 2,p0[2] # 放置点
                if center[0] > section_x[1] or p2[1] >= self.size[1]: # 超出边框
                    continue

                if self.detect_in_stacks(p0,part_size): # 检测到碰撞
                    continue
                
                layer = part_name,p0,part_size,part_kind,part_real_size
                stack.append(layer)
                self.stacks.append(stack)
                return center

        # stacks_mixed_placeable = sorted(self.stacks,key=lambda stack:stack[-1][4][0] * stack[-1][4][1]) #按大小排序
        # for stack in [s for s in stacks_mixed_placeable if s[-1][4][0] * s[-1][4][1] >= part_real_size[0] * part_real_size[1]]: #混码
        #     height = 0
        #     for _,_,stack_part_size,_,_ in stack: height += stack_part_size[2]
        #     if height > self.size[2]:
        #         stack = []
        #         continue
        
        # if stack:
        #     _,p0,stack_0_part_size,_,_ = deepcopy(stack[0])
        #     p0[2] = p0[2] + part_size[2]
        #     center = [p0[0] + stack_0_part_size[0] / 2, p0[1] + stack_0_part_size[1] / 2,p0[2]]
        #     center[0] = center[0] - part_size[0] / 2
        #     center[1] = center[1] - part_size[1] / 2
        #     stack.append((part_name,p0,part_size,part_kind,part_real_size))
        #     return center # 放置点
        
        print('put ',self.size,part_name,part_size,part_kind,section_x)
        return None

    def detect_in_stacks(self,offset,size):
        x_line1 = offset[0],offset[0] + size[0]
        y_line1 = offset[1],offset[1] + size[1]

        for stack in self.stacks:
            _,layer_offset,layer_size,_,_ = stack[0]

            x_line2 = (layer_offset[0],layer_offset[0] + layer_size[0])
            y_line2 = (layer_offset[1],layer_offset[1] + layer_size[1])

            if x_line1[1] < x_line2[0] or x_line1[0] > x_line2[1] or \
               y_line1[1] < y_line2[0] or y_line1[0] > y_line2[1]: continue
            
            return True
            
        return False