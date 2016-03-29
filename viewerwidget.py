#!/usr/bin/python
#GPLv2
import sys
import os
from OpenGL.GL import *
from PyQt5 import QtGui, uic, QtCore, QtWidgets
from PyQt5.QtOpenGL import *
import numpy as np

#import util

from OpenGL.GL.ARB.shader_objects import *
from OpenGL.GL.ARB.fragment_shader import *
from OpenGL.GL.ARB.vertex_shader import *

class Obj3d(object):
  def __init__(self, display_list, ncdl, position=None, rotation=None):
    if position is None:
      position = [0,0,0]
    self.position = position

    if rotation is None:
      rotation = [0,0,0]
    self.rotation = rotation
    self.display_list = display_list
    self.nc_display_list = ncdl

  def paint(self, noncolored=False):
    glPushMatrix()
    glTranslate(self.position[0], self.position[1], self.position[2])
#    glScale(ViewerWidget.scale, ViewerWidget.scale, ViewerWidget.scale)
    glRotate(float(self.rotation[0]), 1.0, 0.0, 0.0)
    glRotate(float(self.rotation[1]), 0.0, 0.0, 1.0)
    glRotate(float(self.rotation[2]), 0.0, 1.0, 0.0)
    if noncolored:
      glCallList(self.nc_display_list)
    else:
      glCallList(self.display_list)
    glPopMatrix()
  def obj_hash(self):
      intcolor = id(self)
      rcolor = ((intcolor & 0xff0000) >> 16) / 255.0; 
      gcolor = ((intcolor & 0x00ff00) >>  8) / 255.0; 
      bcolor = ((intcolor & 0x0000ff) >>  0) / 255.0; 
      return id(self) & 0xffffff



class ViewerWidget(QGLWidget):
    rotx = 0
    roty = 0
    tranx = 0
    trany = 0
    tranz = 0
    scale = 1.0
    gcodelist = -1

    objects = []

    def __init__(self, parent = None):
#        print 'ogl version: ', glGetString(GL_VERSION)
        fmt = QGLFormat.defaultFormat()
        fmt.setSampleBuffers(True)
        fmt.setSamples(32)
#        if not glInitShaderObjectsARB():
#          raise RuntimeError( 
#            """ARB Shader Objects extension is required """
#            """but not supported on this machine!""" 
#          )

        super(ViewerWidget, self).__init__(fmt, parent)
        self.gcode_points = []
        self.oldpos = 0, 0
        self.filename = ''
        self.objsize = 0, 0, 0
        self.gcodesize = 0
        self._oc = (0, 0, 0)
        self._ogc = None
        self.selected_obj = [255,255,255,255]
        #self.setMouseTracking(True)

    def quad_to_hash(self, quad):
      return quad[0] << 16 | quad[1] << 8 | quad[2]
 
    def object_size(self, obj):
      try:
        x = map(lambda _x: float(_x['X']), obj)
        xmax = max(x)
        xmn = min(x)

        y = map(lambda _y: float(_y['Y']), obj)
        ymax =max(y)
        ymn = min(y)

        z = map(lambda _z: float(_z['Z']), obj)
        zmax =max(z)
        zmn = min(z)

        return (xmax-xmn), (ymax-ymn), (zmax-zmn)
      except ValueError:
        return 0,0,0

    def _recalc_object_center(self, obj):
        if len(obj) > 2:
          obj = obj[1:-1]
        x = sum(map(lambda _x: float(_x['X']), obj))
        y = sum(map(lambda _x: float(_x['Y']), obj))
        z = sum(map(lambda _x: float(_x['Z']), obj))
        l = len(obj)
        if l == 0:
          self._oc = 0, 0, 0
        self._oc = (x/l, y/l, z/l)

    def resetView(self):
      ViewerWidget.rotx = 0
      ViewerWidget.roty = 0
      self._recalc_object_center(self.gcode_points)
      ViewerWidget.tranx = 0
      ViewerWidget.trany = 0
      sz = self.object_size(self.gcode_points)
      ViewerWidget.tranz = (self._oc[1]+sz[1])#*2.2

      self.update()

    def paintGL(self):
        wtf = False

        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        L = 0
        glRotate(180, 0, 0, 1)
        glRotate(180, 0, 1, 0)
        glPushMatrix()
        glEnable(GL_MULTISAMPLE)

        for obj in self.objects:
          glPushMatrix()

          glTranslate(ViewerWidget.tranx, ViewerWidget.trany, ViewerWidget.tranz)
          glScale(ViewerWidget.scale, ViewerWidget.scale, ViewerWidget.scale)
          glRotate(float(ViewerWidget.roty), 1.0, 0.0, 0.0)
          glRotate(float(ViewerWidget.rotx), 0.0, 0.0, 1.0)
          glTranslate(-self._oc[0], -self._oc[1], -self._oc[2])

          if self.quad_to_hash(self.selected_obj) == obj.obj_hash():
            glColor3f(1,0.25,0.25)
            obj.paint(noncolored=True)
          else:
            obj.paint()
          glPopMatrix()


        glPopMatrix()
        glDisable(GL_DEPTH_TEST)
        glColor3f(0.8, 0.8, 0.8)
        self.renderText(20, 20, '{} | {} cmds'.format(
          self.filename, self.gcodesize))
        self.renderText(20, 40, '{:.4f} x {:.4f} x {:.4f} mm'.format(
          self.objsize[0], self.objsize[1], self.objsize[2]))
        self.renderText(20, 60, '{:.4f} , {:.4f} deg'.format(
          self.rotx, self.roty))
        self.renderText(20, 80, 'v: {:.4f} , {:.4f} , {:.4f}'.format(
          ViewerWidget.tranx, ViewerWidget.trany, ViewerWidget.tranz))
        self.renderText(20, 100, '{:.4f} x {:.4f} x {:.4f} mm'.format(
          self._oc[0], self._oc[1], self._oc[2]))
        glEnable(GL_DEPTH_TEST)


        self.swapBuffers()
        if wtf:
          self.update()

    def paint_with_idcolor_and_get_pixels(self, x, y):
    #def paintGL(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glClearColor(1, 1, 1, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotate(180, 0, 0, 1)
        glRotate(180, 0, 1, 0)
        glEnable(GL_DEPTH_TEST)

        glEnable(GL_MULTISAMPLE)

        for obj in self.objects:
          glPushMatrix()

          intcolor = id(obj) #.display_list
          rcolor = ((intcolor & 0xff0000) >> 16) / 255.0; 
          gcolor = ((intcolor & 0x00ff00) >>  8) / 255.0; 
          bcolor = ((intcolor & 0x0000ff) >>  0) / 255.0; 
          glColor3f(rcolor, gcolor, bcolor)
          print(rcolor, gcolor, bcolor)
          glMaterialfv(GL_FRONT,GL_DIFFUSE,[rcolor, gcolor, bcolor])
          glTranslate(ViewerWidget.tranx, ViewerWidget.trany, ViewerWidget.tranz)
          glScale(ViewerWidget.scale, ViewerWidget.scale, ViewerWidget.scale)
          glRotate(float(ViewerWidget.roty), 1.0, 0.0, 0.0)
          glRotate(float(ViewerWidget.rotx), 0.0, 0.0, 1.0)
          glTranslate(-self._oc[0], -self._oc[1], -self._oc[2])

          obj.paint(noncolored=True)
          glPopMatrix()

        glFlush()
        glFinish()
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        import struct
        print x,y

        data = glReadPixels(x, self.size().height()-y, 1,1, GL_RGBA, GL_UNSIGNED_BYTE)
        return struct.unpack('=BBBB', data)

#        self.swapBuffers()


    def add_object(self, d):
      self.objects.append(d)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        x = float(w) / h
#        glOrtho(-100, 100, -100, 100, -15000.0, 15000.0)
        glFrustum(-x, x, -1, 1, 1, 15000.0)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, -1300, 0])
        glEnable(GL_COLOR_MATERIAL)




#    def loadGCode(self, filename):
#      if not ViewerWidget.gcodelist == -1:
#        glDeleteLists(ViewerWidget.gcodelist, 1)
#        ViewerWidget.gcodelist = -1
#      self.gcode_points = util.load_gcode_commands(filename)
#      s = self.object_size(self.gcode_points)
##      ViewerWidget.tranx = -s[0]/2
##      ViewerWidget.trany = -s[2]/2
#      ViewerWidget.tranz = -s[1]*3
#      #ViewerWidget.scale = -s[1]*3
#      self.filename = filename
#      self.gcodesize = len(self.gcode_points)
#      self.objsize = s
#      self._recalc_object_center(self.gcode_points)
#      self.updateGL()

    def mousePressEvent(self, m):
      self.oldpos = m.x(), m.y()
      clr = self.paint_with_idcolor_and_get_pixels(m.x(), m.y())
      self.selected_obj = clr
      self.update()

    def wheelEvent(self, m):
#      ViewerWidget.scale *= (120+m.angleDelta().y()/12)/120.0
      ViewerWidget.tranz -= m.angleDelta().y()/24.0
      self.update()

    def mouseMoveEvent(self, m):
      button = int(m.buttons())
      if button == 1:
        ViewerWidget.roty -= (self.oldpos[1]-m.y())/10.0
        if (int(ViewerWidget.roty) % 360) > 0 and (int(ViewerWidget.roty) % 360) < 180:
          ViewerWidget.rotx -= (self.oldpos[0]-m.x())/10.0
        else:
          ViewerWidget.rotx += (self.oldpos[0]-m.x())/10.0
      elif button == 2:
        c = 1
        if ViewerWidget.tranz < 0:
          c = -ViewerWidget.tranz/100.0
        ViewerWidget.tranx -= c*(self.oldpos[0]-m.x())/4.0
        ViewerWidget.trany -= c*(self.oldpos[1]-m.y())/4.0
      self.oldpos = m.x(), m.y()
      self.update()


