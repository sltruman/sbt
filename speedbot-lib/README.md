最近有朋友问我如何把自己写的模块封装好，让别人来pip安装。

是啊，以往都是自己用pip安装别人封装好的模块，直接拿来用，如果自己写的模块封装好，以后自己用起来也方便，也可以给别人用，还可以拿来装X，一举两三得。

其实，过程非常简单，下面，就跟着笔者一步一步的试试吧！

## 第一步：自己写一个模块

比如叫mySeflSum.py

里面写上:

![img](https://pic1.zhimg.com/80/v2-0167c35ecdaf3f4f285573a45deba7d8_720w.jpg)

## 第二步:在顶层目录下建立setup.py

Setup.py中写入

```python
from setuptools import setup

setup(
    name='mySelfSum',# 需要打包的名字,即本模块要发布的名字
    version='v1.0',#版本
    description='A  module for test', # 简要描述
    py_modules=['mySelfSum'],   #  需要打包的模块
    author='Squidward', # 作者名
    author_email='vzhyu@foxmail.com',   # 作者邮件
    url='https://github.com/vfrtgb158/email', # 项目地址,一般是代码托管的网站
    # requires=['requests','urllib3'], # 依赖包,如果没有,可以不要
    license='MIT'
)
```

**pypi会根据包名建立索引,因此包名name必须是唯一的,否则会上传失败**

此时,顶层目录中是这样的

![img](https://pic3.zhimg.com/80/v2-d5a63266218e3e809c7c0050d083d00e_720w.jpg)

## 第三步:打包

请确保python控制台目录在myModel下

安装wheel

```text
pip install setuptools wheel
```

打包

```text
python setup.py sdist bdist_wheel
```



![img](https://pic3.zhimg.com/80/v2-cbc6bfb0e420aa3992fe3ae6da390aae_720w.jpg)



此时myModel目录下自动生成两个文件:

- mySelfSum-1.0.tar.gz
- mySelfSum-1.0-py3-none-any.whl

tar.gz文件是压缩的源文件，而whl文件是 内置发行版。新的pip版本优先安装内置发行版，速度比较快，尽量在发布时连同tar.gz一起上传

## 第四步：发布到pypi

首先需要在pypi上注册并绑定邮箱才有权限上传，上传时需要输入账号密码

注册地址：[https://pypi.org/account/register/](https://link.zhihu.com/?target=https%3A//pypi.org/account/register/)

上传前必须安装上传工具twine:

```text
pip install twine
```

然后上传dist下的两个文件:

```text
twine upload dist/*
```

此时会提示输入pypi账号密码,如果你的包名在pypi上没有重复的,就会上传成

功

![img](https://pic3.zhimg.com/80/v2-803240703e102d03f1a3d93ade73b4ea_720w.jpg)

如果上传失败,提示没有权限更改,则说明有包已经有了这个名字,在setup.py中更改一个NB的包名,删掉dist目录,并重新打包上传

![img](https://pic1.zhimg.com/80/v2-eeb4007e76d666735c5afb81073d6730_720w.jpg)



## 最后,来试试自己发布的模块是否能成功pip

![img](https://pic1.zhimg.com/80/v2-7c50829144192409544151bd4dfd1a08_720w.jpg)

![img](https://pic1.zhimg.com/80/v2-ac64d6f1dbb7a371d1d1bff504b71128_720w.jpg)

## 后续更新Python包

只需要在setup.py中把版本号变更,重新打包上传即可