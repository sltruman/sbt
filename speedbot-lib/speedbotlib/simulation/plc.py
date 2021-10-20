import re
import struct
import time
import ctypes
from typing import Tuple, Optional, Callable, Any

import logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

import snap7
import snap7.types
from snap7.common import check_error, load_library, ipv4

server = snap7.server.Server()
size = 100

db8 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * size)()
server.register_area(snap7.types.srvAreaDB, 8, db8)
db9 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * size)()
server.register_area(snap7.types.srvAreaDB, 9, db9)
db13 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * size)()
server.register_area(snap7.types.srvAreaDB, 13, db13)
db14 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * size)()
server.register_area(snap7.types.srvAreaDB, 14, db14)
db27 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * size)()
server.register_area(snap7.types.srvAreaDB, 27, db27)
db28 = (snap7.types.wordlen_to_ctypes[snap7.types.S7WLByte] * size)()
server.register_area(snap7.types.srvAreaDB, 28, db28)

server.start(tcpport=102)

while True:
    while True:
        event = server.pick_event()
        if event:
            logger.info(server.event_text(event))
        else:
            break
    time.sleep(1)
