import json
import os
import traceback
import sys
from dict_recursive_update import recursive_update
import threading
import shutil

m = threading.Lock()

class dson:
    """
    缓存模块
    """
    def __init__(self, file_path, **kwargs):
        self.file_path = file_path
        self.base_name = os.path.basename(self.file_path)
        
        self.base_path = os.path.abspath(os.path.dirname(file_path) + "/.")
        self.swp_path = self.base_path + "/." + self.base_name + ".swp"
        
        try:
            m.acquire()
            
            try:
                with open(f'{self.swp_path}', 'r') as f:
                    self._value = json.load(f)
                with open(self.file_path, "w") as f:
                    json.dump(self._value, f, ensure_ascii=False, indent=4)
            except:pass

            try:
                with open(f'{self.file_path}', 'r') as f:
                    self._value = json.load(f)
            except:
                self._value = {}
            
            if kwargs:
                self._value = kwargs

                if self._value:
                    with open(self.swp_path, "w") as f:
                        json.dump(self._value, f, ensure_ascii=False, indent=4)
                    os.system(f'chmod o+rw {self.swp_path}')
                    shutil.move(self.swp_path,self.file_path)
        except:pass
        finally:
            m.release()
        
    def __delitem__(self, k):
        try:
            m.acquire()
            if k not in self._value: return
            del self._value[k]

            with open(self.swp_path, "w") as f:
                json.dump(self._value, f, ensure_ascii=False, indent=4)
            
            os.system(f'chmod o+rw {self.swp_path}')
            shutil.move(self.swp_path,self.file_path)
        except: pass
        finally:
            m.release()

    def __getitem__(self, k):
        return self._value[k]

    def __contains__(self, k):
        return k in self._value

    def __setitem__(self, k, v):
        try:
            m.acquire()

            # try:
            #     with open(f'{self.swp_path}', 'r') as f:
            #         self._value = json.load(f)
            # except:pass

            # if not self._value:
            #     try:
            #         with open(f'{self.file_path}', 'r') as f:
            #             self._value = json.load(f)
            #     except:
            #         self._value = {}

            self._value[k] = v
            
            with open(self.swp_path, "w") as f:
                json.dump(self._value, f, ensure_ascii=False, indent=4)
            os.system(f'chmod o+rw {self.swp_path}')
            shutil.move(self.swp_path,self.file_path)
        except:pass
        finally:
            m.release()
    
    @property
    def value(self):
        from copy import deepcopy
        return deepcopy(self._value)

    def update_l(self,**kwargs):
        '''合并数据'''
        try:
            m.acquire()
        
            self._value = recursive_update(self._value,kwargs)
            with open(self.swp_path, "w") as f:
                json.dump(self._value, f, ensure_ascii=False, indent=4)
            os.system(f'chmod o+rw {self.swp_path}')
            shutil.move(self.swp_path,self.file_path)
            return self._value
        finally:
            m.release()     

    def update_r(self,**kwargs):
        '''合并数据'''
        try:
            m.acquire()
            self._value = recursive_update(kwargs,self._value)
            with open(self.swp_path, "w") as f:
                json.dump(self._value, f, ensure_ascii=False, indent=4)
            os.system(f'chmod o+rw {self.swp_path}')
            shutil.move(self.swp_path,self.file_path)
            return self._value
        finally:
            m.release()  