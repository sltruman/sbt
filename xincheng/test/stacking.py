import sys
sys.path.append('..')

from common.stacking import Pallet

parts = {
    'a':{
        'size':[3,3,1],
        'handle':0
    },
    'b':{
        'size':[2,3,1],
        'handle':0
    },
    'c':{
        'size':[3,3,1],
        'handle':0
    },
    'd':{
        'size':[2,3,1],
        'handle':1
    },
    'e':{
        'size':[2,3,1],
        'handle':1
    }
}

stacks = [
    [
        [
            ['a', [0, 0, 0], [3, 3, 1], [1.5, 1.5, 0]], # 零件名，# 偏移，# 零件大小 #中心点
            ['c', [0, 0, 1], [3, 3, 1], [1.5, 1.5, 1]]
        ], 
        [
            ['b', [0, 4, 0], [2, 3, 1], [1.0, 5.5, 0]], 
            ['d', [0, 4, 1], [2, 3, 1], [1.0, 5.5, 1]], 
            ['e', [0, 4, 2], [2, 3, 1], [1.0, 5.5, 2]]
        ]
    ]
]

p = Pallet('A',[0,0,0],[10,10,10],stacks)

for k,v in parts.items():
    print(p.put(k,v['size']))

p.draw()
print(stacks)
