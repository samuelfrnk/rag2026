import tomllib
from arxiv import Result
import datetime

data = {}

def load_config():

    global data

    with open("config.toml", "rb") as f:
        data = tomllib.load(f)

def check_config():
    if data == {}:
        load_config()


def get_arxiv_columns(res: Result):
    check_config()

    column_data = data["db_columns"]

    out_data = {}

    for key, val in column_data.items():

        dat = res.__getattribute__(val)

        if type(dat) == list:
            if type(dat[0]) == Result.Author:
                dat = [x.name for x in dat]

        if type(dat) == datetime.datetime:
            dat = dat.strftime("%d/%m/%Y-%H:%M:%S")
        
        out_data[key] = dat

    #for key,val in out_data.items():
    #    print(key, "\t", val)


    return out_data


if __name__ == "__main__":

    load_config()
