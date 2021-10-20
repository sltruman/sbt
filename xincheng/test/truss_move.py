import sys
sys.path.append('..')
import robot.truss

truss = robot.truss.Truss('7','127.0.0.1',102,0,0,dbs=[0,1],area_x=(-3300,3400),area_y=(20,8000),area_z=(-500,500))
truss.a_move([0,6471.46,0,90])
truss.a_join()
truss.b_move([2000,1000,0,45])
truss.b_join()
truss.ab_move([-1000,1000,200,45],[1000,1000,100,0])
# truss.b_reset(
# )
# truss.b_join()

# truss.ab_move([-1000,1000,200],[1000,1000,100])
# truss.a_join()
# truss.b_join()
# truss.a_reset()
# truss.b_reset()
# truss.a_join()
# truss.b_join()
