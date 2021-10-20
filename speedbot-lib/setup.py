from setuptools import setup, find_packages

setup(
    name="speedbotlib", version="0.0.11", description="", 
    author="sl.truman", author_email='sl.truman@live.com',
    url='https://git.speedbot.net/speedbot-lib/speedbot-lib', # 项目地址,一般是代码托管的网站
    license='MIT',
    py_modules=[
        'speedbotlib.test',
        'speedbotlib.common.cache',
        'speedbotlib.simulation.plc',
        'speedbotlib.simulation.truss'
    ]   #  需要打包的模块
)