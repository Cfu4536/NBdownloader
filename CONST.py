import json
import sys
import os

try:
    with open("./config.json", mode="r", encoding="utf-8") as f:
        config = json.load(f)

        TEMP_DIR = config["TEMP_DIR"]
        OUTPUTS_DIR = config["OUTPUTS_DIR"]

        COOKIE_BILIBILI = config["COOKIES"]['BILIBILI']
        MAX_THREADS = config["max_threads"]
except:
    sys.exit("config error")

