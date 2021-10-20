import sys
sys.path.append('..')
import requests as http
import time
import uuid
i = 0
url2 = "http://localhost:60000/large_sort_area/system/status"
def query_station(location):
    res = http.post(url2, json={
        "sort_line": "1",
        "area_code": "2",
        "location": location
    })
    flag=res.json()["data"]
    
    return flag

def cycle(station):
    url = "http://localhost:60000/large_sort_area/system/inPlace"
    if station=="1":
        http.post(url, json={"sort_line": "1",
                             "location": "1",
                             "in_place_time": "2021-02-05 12:23:23",
                             "area_code": "2",
                             "plate_id": str(uuid.uuid1()),
                             "length": 8000,
                             "width": 1450,
                             "thickness": 8,
                             "file_path": "/2021-06-30/M210626610L8A52/M210626610L8A52"
                             })
        time.sleep(10)
    elif station=="2":
        http.post(url, json={"sort_line": "1",
                             "location": "1",
                             "in_place_time": "2021-02-05 12:23:23",
                             "area_code": "2",
                             "plate_id": str(uuid.uuid1()),
                             "length": 8000,
                             "width": 1450,
                             "thickness": 8,
                             "file_path": "/2021-06-30/M210626610L8A52/M210626610L8A52"
                             })
        time.sleep(10)
    pass

def test():
    while True:
        flag1 = query_station("1")
        flag2 = query_station("2")
        if flag1 == "1" or flag2=="1":
            if flag1=="1":
                cycle("1")
            if flag2=="1":
                cycle("2")
            time.sleep(10)
            continue
        else:
            time.sleep(10)
            continue


test()









