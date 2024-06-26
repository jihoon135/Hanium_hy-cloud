from fastapi import FastAPI
from collections import OrderedDict

import uvicorn
import os
import sys
import datetime
import pandas as pd
from pydantic import BaseModel
from common import ConfigManager, MySQLWrapper

config_manager = None
interface_process = None
logger = None

class MonitorInfo(BaseModel):
    vendor: str
    instance_id: str
    instance_name: str
    metric: str
    value: float
    time: str
    time_key: str

app = FastAPI()

@app.post("/monitor_info")
def post_monitor_info(monitorInfo: MonitorInfo):
    try:
        myfunc = sys._getframe().f_code.co_name
        global logger
        logger.info(f"[{myfunc}] called api. item:{monitorInfo}")

        _dict = {}
        _dict['vendor'] = str(monitorInfo.vendor)
        _dict['instance_id'] = str(monitorInfo.instance_id)
        _dict['instance_name'] = str(monitorInfo.instance_name)
        _dict['metric'] = str(monitorInfo.metric)
        _dict['value'] = str(monitorInfo.value)
        _dict['time'] = str(monitorInfo.time)
        _dict['time_key'] = str(monitorInfo.time_key)
        logger.info(f"[{myfunc}] item:{_dict}")

        mysql_wrapper = MySQLWrapper.MySQLWrapper()
        mysql_wrapper.set_logger(config_manager.get_logger())
        mysql_wrapper.db_connect(config_manager.get_db_connection_info())

        df = pd.json_normalize(_dict)
        mysql_wrapper.db_insert(df, 'monitor', "insertonly")
        mysql_wrapper.db_commit()
        mysql_wrapper.db_close()

        json_data = make_json_result(True, "0", "", "")
        return json_data

    except Exception as err:
        json_data = make_json_result(False, "99", f"{str(err)}", None)
        logger.error(f"[{myfunc}] Exception err:{str(err)}, data:{_dict}")
        mysql_wrapper.db_close()
        return json_data


@app.on_event("startup")
def startup():

    global config_manager
    global interface_process
    global logger
    config_manager = ConfigManager.ConfigManager()
    config_file = os.getenv('SERVER_CONFIG', './config/config.xml')
    config_manager.load_config(config_file)
    logger = config_manager.get_logger()

@app.on_event("shutdown")
def shutdown():
    pass

def make_json_result(is_success, result_code, result_message, data):
    json_data = OrderedDict()
    json_data['success'] = is_success
    json_data['resultCode'] = result_code
    json_data['resultMessage'] = result_message
    json_data['data'] = data
    return json_data


if __name__ == '__main__':

    os.environ.setdefault('SERVER_HOME', 'C:\\Users\\jino\\PycharmProjects\\gc_monitoring_server')

    try:
        server_home = os.getenv('SERVER_HOME')
        now = datetime.datetime.now()
        if server_home == None:
            print(f"{now} ENV SERVER_HOME not found")
            raise Exception

        config_file = os.getenv('SERVER_CONFIG', './config/config.xml')
        config_manager = ConfigManager.ConfigManager()
        config_manager.load_config(config_file)
        config_server = config_manager.get_server_info()
        uvicorn.run("main:app", host=config_server.ip, port=config_server.port, reload=True)

        sys.exit(0)
    except Exception as err:
        print(f"{now} process terminated with exception")
        raise SystemExit(-1)



