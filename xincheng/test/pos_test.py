import math 

def rotate(angle,value_x,value_y):
    radius = angle * math.pi / 180
    real_x = math.cos(radius) * value_x - math.sin(radius) * value_y
    real_y = math.cos(radius) * value_y + math.sin(radius) * value_x
    return real_x,real_y


x,y = (-83.5, -59.0) #零件偏移
x,y = rotate(90,x,y) #零件旋转90度

print(x,y)
print(x+2586.5,y+616)  #零件中心
