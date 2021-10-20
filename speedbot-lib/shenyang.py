import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import snap7
import speedbotlib.simulation.truss2
import asyncio

graph = plt.figure(0)
view1 = graph.add_subplot(121,projection='3d')
view2 = graph.add_subplot(122,projection='3d')
plt.show(block=False)
plt.ion()

truss1 = speedbotlib.simulation.truss.Truss(view1,'7','../bigonesort/db',[59],10200,[-3900,8200],[-1800,3700],[-340,203],[-3900,8200])
truss1.power_on()

while plt.fignum_exists(0):
    asyncio.get_event_loop().run_until_complete(
        asyncio.wait(
            [
                truss1.update()
            ]
        )
    )

    graph.canvas.draw()
    graph.canvas.flush_events()