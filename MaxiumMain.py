# Temp
from bs4 import BeautifulSoup
import json

# Mostly Quality of Life Wrapper
class mcontrol:
    print_off = False

class _mBunch(object):
  def __init__(self, adict):
    self.__dict__.update(adict)


def mexec(filepath):
    exec(open(filepath, encoding='utf-8').read())
    return _mBunch(locals())


def mdoc(obj):
    print(obj.__doc__)


def mprint(*txts):
    if mcontrol.print_off:
        return None
    print("#########################################################################")
    for txt in txts:
        print(txt, end='')
    print("\n#########################################################################")
    return None

# concat(filePath, data) -> json serializable data
def msaveJson(filePath, data, concat):
    try:
        open(filePath, 'x').write()
    except:
        print("saveIndex: file already exists")

    with open(filePath, '+') as fh:
        data_written = fh.read()
        if data_written == '':
            data_written = '{}'

        data_written = concat(data_written, data)
    
        fh.write(json.dumps(data_written))
