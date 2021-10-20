import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import snap7
import speedbotlib.simulation.truss
import speedbotlib.robot.truss
import asyncio

graph = plt.figure(0)
view1 = graph.add_subplot(projection='3d')
view2 = None#graph.add_subplot(122,projection='3d')
plt.show(block=False)
plt.ion()


truss1 = speedbotlib.simulation.truss.Truss(view1,'7','../xincheng/db',[13,14],10200,[-3499,4299],[20,12000],[-510,500],[2300,4300],[-3400,2200])
truss1.power_on()
truss2 = speedbotlib.simulation.truss.Truss(view2,'8','../xincheng/db',[27,28],10300,[-4299,3499],[20,8000],[-510,500],[-4300,-2300],[-2200,3400])
truss2.power_on()

truss2.db2,truss1.db2 = truss1.db0,truss2.db0
truss2.db3,truss1.db3 = truss1.db1,truss2.db1

while plt.fignum_exists(0):
    asyncio.get_event_loop().run_until_complete(asyncio.wait([truss1.update()]))

    graph.canvas.draw()
    graph.canvas.flush_events()