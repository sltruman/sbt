FROM centos
WORKDIR /home
COPY prebuild/2d_bin_packing/build/tiling-service0 /home/tiling-service0
COPY prebuild/2d_bin_packing/build/tiling-service1 /home/tiling-service1
COPY prebuild/2d_bin_packing/build/server /home/tiling-service
COPY prebuild /home/prebuild
COPY common /home/common
COPY picker /home/picker
COPY robot /home/robot
COPY services /home/services
COPY agent.py /home/agent.py
COPY config.py /home/config.py
COPY scheduler.py /home/scheduler.py

RUN dnf install make gcc-c++ python38 -y && \
    make -C prebuild/snap7-full-1.4.2/build/unix/ -f x86_64_linux.mk && \
    make -C prebuild/snap7-full-1.4.2/build/unix/ -f x86_64_linux.mk install && \
    make -C prebuild/snap7-full-1.4.2/build/unix/ -f x86_64_linux.mk clean && \
    pip3 install prebuild/kiwisolver-1.3.1-cp38-cp38-manylinux1_x86_64.whl \
                 prebuild/Pillow-8.3.1-cp38-cp38-manylinux_2_5_x86_64.manylinux1_x86_64.whl \
                 prebuild/numpy-1.21.1-cp38-cp38-manylinux_2_12_x86_64.manylinux2010_x86_64.whl \
                 prebuild/matplotlib-3.4.3-cp38-cp38-manylinux1_x86_64.whl \
                 prebuild/pandas-1.3.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl \
                 transitions flask flask_cors requests speedbotlib python-snap7 dict_recursive_update --timeout 360 && \
    rm -rf prebuild && \
    ldconfig && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' > /etc/timezone