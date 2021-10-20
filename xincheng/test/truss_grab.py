import sys
sys.path.append('..')
import robot.truss


truss = robot.truss.Truss('7','127.0.0.1',102,0,0,dbs=[0,1],area_x=(-3300,3400),area_y=(20,8000),area_z=(-500,500))
# truss.a_grab(
#     [0,5000,-130],90,
#     [0,1000,-500],0,
#     [0b11111111,0b11111111,
#     0b11111111,0b11111111,
#     0b11111111,0b00001111])

# truss.a_join()
# truss.a_reset()
# truss.a_join()

# truss.b_grab(
#     [0,5000,500],90,
#     [0,1000,100],0,
#     [0b11111111,0b11111111,
#     0b11111111,0b11111111,
#     0b11111111,0b00001111])
# truss.b_join()
# truss.b_reset()
# truss.b_join()

truss.ab_grab(
    [-1000,5000,0],90,
    [-1000,1000,100],
    [0b11111111,0b11111111,
    0b11111111,0b11111111,
    0b11111111,0b00001111],
    [1000,5000,100],90,
    [1000,1000,100],
    [0b11111111,0b11111111,
    0b11111111,0b11111111,
    0b11111111,0b00001111])
# truss.a_join()
# truss.b_join()
# truss.a_reset()
# truss.b_reset()
# truss.a_join()
# truss.b_join()
