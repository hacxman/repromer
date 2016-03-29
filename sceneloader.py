import objloader
from viewerwidget import *

def loadScene(filename):
  with open(filename) as fin:
    objects = []
    for line in fin.readlines():
      line = line.strip()
      if line.startswith('#'):
        continue
      items = line.split()
      o = objloader.OBJ(items[0])
      items[1:] = map(float, items[1:])
      objects.append(Obj3d(o.gl_list, o.gl_list_noncolor, position = items[1:4],
        rotation=items[4:7], scale=items[7:10]))
    return objects


