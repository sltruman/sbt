大件一次分拣

## 运行

````
scheduler.py
    运行启动大件一次分拣调度
agent.py
    运行启动大件一次分拣工作站实例
config.py
	配置分拣参数
data/
	测试数据
http.rest
    服务接口测试
测试说明：
    0.编译并启动2d_bin_packing/bin/server服务，用于放置点计算
    1.启动服务`python scheduler.py 60000`
    2.启动工作站`python agent.py 60001`
    3.调用`/large_sort_area/system/inPlace`接口
````

## Docker镜像

```bash
#创建镜像
docker build -t large_sorting_first:latest .

#标签
docker tag large_sorting_first:latest mirrors.speedbot.net/showroom/large_sorting_first:latest

#推送到服务器
docker login mirrors.speedbot.net
docker push mirrors.speedbot.net/showroom/large_sorting_first:latest

#创建内部网络
docker network create large_sorting_first --subnet 172.16.0.0/24 --gateway 172.16.0.1

#创建容器并启动
docker-compose up
```

# 资源
## 套料图
```yaml
- command='mount -t cifs -o username=speedbot,password=Speedbot12#$ //192.168.10.10/file_share `pwd`/data'
```

## 服务器
```yaml
ssh speedbot@192.168.10.15 -p 34
```

## PLC服务器

```yaml
- agents.0.plc=['192.168.1.105',102,0,1]      			#桁架PLC地址,端口,rack,slot
- agents.0.plc.areas=[-3400,3200],[20,8000],[0,700]   	 #桁架PLC坐标范围x,y,z
```

# 大件分拣服务-长沙新城

## 分拣启动

```sequence
title:总控:?.?.?.?:?\n调度:192.168.0.1:8008\n工作站1:192.168.0.2:6000\n工作站2:192.168.0.3:6000

participant 总控
participant 激光切割分拣.调度 as 调度
participant 缓存
participant 工作站1
participant 工作站2

note right of 总控:钢板到位
总控->调度:POST /large_sort_area/system/inPlace 钢板编号,尺寸,钢板信息
调度->缓存:写(钢板编号,钢板信息) if 钢板编号不在缓存
调度->缓存:钢板信息=读(钢板编号) else 钢板编号在缓存
note right of 工作站1:分拣开始
调度->工作站1:PUT /start/1 钢板编号,钢板信息
工作站1->缓存:写(钢板编号,钢板信息)
note right of 总控:分拣状态：分拣中
调度->总控:POST /control/system/recStatusData
note right of 工作站1:分拣中...
工作站1->工作站1:分拣一个
工作站1->缓存:写(钢板编号,钢板信息)
工作站1->调度:PUT /large_sorting/part
note right of 总控:零件报告
调度->总控:POST /speedbot/recPartSortData
工作站1->调度:PUT /large_sorting/pallet if 托盘已满
note right of 总控:零件分拣报告
调度->总控:POST /large_sort_area/system/recSortData
note right of 总控:流料
调度->总控:POST /large_sort_area/system/movePlate
note right of 总控:分拣状态：分拣结束
调度->总控:POST /control/system/recStatusData if 已分拣完钢板上所有零件
note right of 工作站1:分拣结束
```

## 分拣状态/暂停/恢复/停止

```sequence
title:总控:?.?.?.?:?\n调度:192.168.0.1:8008\n工作站1:192.168.0.2:6000\n工作站2:192.168.0.3:6000

participant 总控
participant 激光切割分拣.调度 as 调度
participant 缓存
participant 工作站1
participant 工作站2
note right of 工作站1:分拣开始
note right of 总控:工作站状态：分拣中...
总控->调度:POST /large_sort_area/system/status
调度->工作站1:GET /large_sorting/status/1
调度-->总控:ret 0
note right of 工作站1:分拣中...
工作站1->工作站1:分拣一个
note right of 总控:分拣暂停
总控->调度:POST /large_sort_area/system/stop
调度->工作站1:PUT /large_sorting/pause/1
note right of 工作站1:分拣结束
note right of 总控:工作站状态：分拣中...
总控->调度:POST /large_sort_area/system/status
调度->工作站1:GET /large_sorting/status/1
调度-->总控:ret 0
note right of 总控:分拣恢复
总控->调度:POST /large_sort_area/system/recover
调度->工作站1:PUT /large_sorting/recover/1
note right of 工作站1:分拣开始
note right of 工作站1:分拣中...
工作站1->工作站1:分拣一个
note right of 总控:分拣终止
总控->调度:POST /large_sort_area/system/end
调度->工作站1:PUT /large_sorting/stop/1
工作站1->调度:PUT /large_sorting/parts
note right of 总控:零件分拣报告
调度->总控:POST /large_sort_area/system/recSortData
note right of 工作站1:分拣结束
note right of 总控:工作站状态：分拣结束
总控->调度:POST /large_sort_area/system/status
调度->工作站1:GET /large_sorting/status/1
调度-->总控:ret 1
```

## 滚筒线状态查询小托盘/到位/状态/高度

```sequence
title:总控:?.?.?.?:?\n调度:192.168.0.1:8008\n工作站1:192.168.0.2:6000\n工作站2:192.168.0.3:6000

participant 总控
participant 激光切割分拣.调度 as 调度
participant 缓存
participant 工作站1
note right of 总控:托盘到位
总控->调度:POST /speedbot/system/emptyFrameInPlace
总控->调度:POST /speedbot/system/uptFrameHeight
总控->调度:POST /speedbot/system/frameProcess
note right of 总控:钢板到位
调度->总控:POST /large_sort_area/system/queryLineEmpty
note right of 工作站1:分拣开始
note right of 工作站1:分拣中...
工作站1->工作站1:分拣一个
调度->总控:POST /speedbot/system/
```

## 放置到滚筒线

```sequence
participant 天桥
participant 总控
participant 工作站1
participant 工作站2
note left of 总控:等待天桥信号
天桥->总控:钢板到位
天桥->总控:滚筒线到位
note left of 工作站1:通知工作站1开始分拣-第一次
总控->工作站1:钢板到位(10个零件，2次分拣，1次5个零件)
工作站1->总控:查询放置到滚筒线还是料框
工作站1->工作站1:分拣完（5个零件，滚筒线满了）
工作站1->总控:上报分拣状态（未分拣完）
工作站1->总控:流料
总控->天桥:流料
天桥->总控:滚筒线到位
note left of 工作站1:通知工作站1开始分拣-第二次
总控->工作站1:钢板到位(10个零件，2次分拣，1次5个零件)
工作站1->总控:查询放置到滚筒线还是料框
工作站1->工作站1:分拣完（5个零件，滚筒线满了）
工作站1->总控:上报分拣状态（分拣完）
工作站1->总控:流料
总控->天桥:流料
note left of 总控:等待天桥信号
天桥->总控:钢板到位
天桥->总控:滚筒线到位
note left of 工作站2:通知工作站2开始分拣
总控->工作站2:钢板到位

```


## 最新套料图放置位置

1.每块钢板到位后将最新套料图更新到指定路径

/templImgData/templ.png

## 拍照识别匹配，大件一次发送视觉服务指令
1. pick;x;y;     x，y->表示拍照点桁架坐标x，y;

## 视觉服务返回匹配结果

### success

pick;x;y;angle;    
1. x，y->表示桁架坐标系的套料图角点坐标; 
2. angle->表示桁架坐标系的套料图角点坐标


### error

failed;error_code;error_msg;
1. error_code -> 表示错误编码
2. error_msg -> 表示错误具体信息
   | 错误编码 | 错误内容 | 错误信息|
   | :-----| ----: | :----: | 
   | 2 | 相机拍照错误 | ... |
   | 3 | 深度学习错误 | ... |
   | 4 | 深度学习检测为空 | ... |
   | 5 | 识别范围超出 | ... |
   | 6 | 匹配失败 | ... |   


# 测试用例

## 钢板定位寻边

**场景描述**
	桁架PLCx1，桁架机械臂x2，Linux服务器x1，寻边相机x2，4000x2000毫米托盘x1，3900x1400毫米钢板x1，光照充足的环境
**测试内容**
	测试`钢板`位于`托盘`之上时，通过`寻边定位服务`得到的`钢板`相对于`托盘`的偏移数据是否准确？
**测试方法**
	部署`定位寻边服务`到Linux服务器；
	部署`大件分拣服务-寻边测试`到Linux服务器；
	确保`Linux服务器`与`桁架PLC`能够连通；
	将`钢板`放置于`托盘`之上；
	运行`大件分拣服务-寻边测试`触发定位寻边；
	`寻边相机x2`打开灯光并伸出；
	得到`定位寻边服务`返回的结果并验证。

## 零件分拣

**场景描述**
	桁架PLCx1；桁架机械臂x2；Linux服务器x1；寻边相机x2；4000x2000毫米托盘x1；3900x1400毫米钢板xN；光照充足的环境。
**测试内容**
	`桁架机械臂x2`能否正确的将零件从`钢板`上抓取到？
**测试方法**
	部署`定位寻边服务`到Linux服务器；
	部署`大件分拣服务`到Linux服务器；
	确保`Linux服务器`与`桁架PLC`能够连通；
	将`钢板`放置于`托盘`之上；
	通过Post Man调用`大件分拣服务`的钢板到位接口；
	`寻边相机x2`打开灯光并伸出；
	`桁架机械臂x2`开始对`钢板`上的零件进行抓取；
	从抓取点判断抓取是否准确；
	多用几块钢板进行测试。

## 双臂抓取同一个零件

**场景描述**
	桁架PLCx1；桁架机械臂x2；Linux服务器x1；寻边相机x2；4000x2000毫米托盘x1；3900x1400毫米钢板xN；光照充足的环境。
**测试内容**
	`桁架机械臂x2`在抓取期间，能否将需要双臂同时抓取的大零件从`钢板`上抓取并放置？
**测试方法**
	部署`定位寻边服务`到Linux服务器；
	部署`大件分拣服务`到Linux服务器；
	确保`Linux服务器`与`桁架PLC`能够连通；
	将`钢板`放置于`托盘`之上；
	通过Post Man调用`大件分拣服务`的钢板到位接口；
	`寻边相机x2`打开灯光并伸出；
	`桁架机械臂x2`开始对`钢板`上的大零件进行抓取；
	从抓取点判断抓取是否准确；
	多用几块钢板进行测试。

## 断电后恢复工作

**场景描述**
	桁架PLCx1；桁架机械臂x2；Linux服务器x1；寻边相机x2；4000x2000毫米托盘x1；3900x1400毫米钢板x1；光照充足的环境。
**测试内容**
	`桁架机械臂x2`在抓取期间，突然断电重启后是否会恢复工作？
**测试方法**
	部署`定位寻边服务`到Linux服务器；
	部署`大件分拣服务`到Linux服务器；
	确保`Linux服务器`与`桁架PLC`能够连通；
	将`钢板`放置于`托盘`之上；
	通过Post Man调用`大件分拣服务`的钢板到位接口；
	`寻边相机x2`打开灯光并伸出；
	`桁架机械臂x2`开始对`钢板`上的零件进行抓取；
	抓取过程中，对`Linux服务器`进行断电；
	`Linux服务器`重启后，`大件分拣服务`启动后抓取工作将继续；
	（另一种）如果桁架机械臂x2断电，可能出现正在抓取的零件因无法吸附而落在无法确定的地方而影响恢复后的抓取工作。	

## 暂停/恢复工作

**场景描述**
	桁架PLCx1；桁架机械臂x2；Linux服务器x1；寻边相机x2；4000x2000毫米托盘x1；3900x1400毫米钢板x1；光照充足的环境。
**测试内容**
	`桁架机械臂x2`在抓取期间，总控请求暂停后再恢复是否正常工作？
**测试方法**
	部署`定位寻边服务`到Linux服务器；
	部署`大件分拣服务`到Linux服务器；
	确保`Linux服务器`与`桁架PLC`能够连通；
	将`钢板`放置于`托盘`之上；
	通过Post Man调用`大件分拣服务`的钢板到位接口；
	`寻边相机x2`打开灯光并伸出；
	`桁架机械臂x2`开始对`钢板`上的零件进行抓取；
	在抓取时，通过Post Man调用`大件分拣服务`的暂停接口；
	判断`桁架机械臂x2`是否会返回安全点；
	通过Post Man调用`大件分拣服务`的恢复接口；
	判断`桁架机械臂x2`是否会继续未完成的分拣工作；

## 停止分拣并再次启动

**场景描述**
	桁架PLCx1；桁架机械臂x2；Linux服务器x1；寻边相机x2；4000x2000毫米托盘x1；3900x1400毫米钢板x1；光照充足的环境。
**测试内容**
	`桁架机械臂x2`在抓取期间，总控请求暂停后并转移到另一个工作站是否正常工作？
**测试方法**
	部署`定位寻边服务`到Linux服务器；
	部署`大件分拣服务`到Linux服务器；
	确保`Linux服务器`与`桁架PLC`能够连通；
	将`钢板`放置于`托盘`之上；
	通过Post Man调用`大件分拣服务`的钢板到位接口；
	`寻边相机x2`打开灯光并伸出；
	`桁架机械臂x2`开始对`钢板`上的零件进行抓取；
	在抓取时，通过Post Man调用`大件分拣服务`的停止接口；
	判断`桁架机械臂x2`是否会返回安全点；
	通过Post Man调用`大件分拣服务`的钢板到位接口；
	`寻边相机x2`打开灯光并伸出；
	`桁架机械臂x2`是否会继续未完成的分拣工作；

## 异常恢复案例

**可恢复**
	服务器断电；异常关机；服务崩溃；非硬盘的硬件损坏；网络中断。
**不可恢复**
	硬盘损坏；桁架机械臂断电；人为使坏。

## 开机自启动

**安装**
	运行`install.sh`即可安装大件分拣服务。
**设置自启动**
	运行`systemctl enable large-sorting-first`即可设置自启动。

## 代理与其他模块接口（总控，桁架，视觉，PLC）

**连通测试**
	运行`大件分拣-PLC测试`程序；
	运行`大件分拣-视觉测试`程序；
	运行`大件分拣-桁架测试`程序。

# 操作手册

## 两个桁架PLC电源

<img src="/home/sl.truman/Downloads/500302554.jpg" alt="img" style="zoom:25%;" /><img src="/home/sl.truman/Downloads/561361373.jpg" alt="561361373" style="zoom:25%;" />

## 桁架控制台

<img src="/home/sl.truman/Downloads/1870370931.jpg" alt="img" style="zoom:25%;" /><img src="/home/sl.truman/Downloads/1172321937.jpg" alt="img" style="zoom:25%;" />

## 自动模式

1. 打开两个桁架PLC的电源。
2. 在控制台解除急停，并按下启动按钮，回原位钮，来使桁架进行初始状态。
3. 将模式切换为自动。
4. 等待钢板到位，即可自动分拣。

## 手动模式

1. 打开两个桁架PLC的电源。
2. 在控制台解除急停，并按下启动按钮，回原位钮，来使桁架进行初始状态。
3. 将模式切换为手动。
4. 等待钢板到位。
5. 在WEB控制台按下相应工作区的“恢复”按钮，即可开始分拣。

## 钢板挂板被带起后继续

1. 在控制台迅速按下暂停按钮后，拍下急停，切换模式为手动。
2. 解除急停，并按下启动按钮，通过手动操作解除卡板情况。
3. 确保钢板能够继续分拣后在WEB控制台按下相应工作区的“恢复”按钮。

## 钢板挂板被带起后停止

1. 在控制台迅速按下暂停按钮后，拍下急停，切换模式为手动。
2. 解除急停，并按下启动按钮，通过手动操作解除卡板情况。
3. 确定钢板无法继续分拣后在WEB控制台-状态监控按下“强制移动”按钮。

## 零件补抓

1. 在桁架控制台按下暂停按钮后，拍下急停，切换模式为手动。
2. 解除急停，并按下启动按钮，桁架回原位，切换模式为自动。
3. 在WEB控制台-大件分拣区-？区补抓，勾选相应的零件后按下发送零件数据按钮。
4. WEB控制台-状态监控按下“恢复”按钮。

