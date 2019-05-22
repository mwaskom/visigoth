"""Psychopy ElementArrayStim with flexible pedestal luminance.

Psychopy authors have said on record that this functionality should exist in
Psychopy itself. Future users of this code should double check as to whether
that has been implemented and if this code can be excised.

Note however that we have also added some functinoality to set the contrast in
a way that depends on the pedestal, which may not get added.

This module is adapted from a similar extension to GratingStim
Original credit to https://github.com/nwilming/PedestalGrating/

Covered under the PsychoPy license, as it is a simple extension of prior code:

Copyright (C) 2015 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).

"""
from __future__ import division
import pyglet
pyglet.options['debug_gl'] = False
import ctypes  # noqa: 402
GL = pyglet.gl

from psychopy.visual.elementarray import ElementArrayStim  # noqa: 402
from psychopy.visual.basevisual import MinimalStim, TextureMixin  # noqa: 402
try:
    from psychopy.visual import shaders
except ImportError:
    from psychopy import _shadersPyglet as shaders

# Framgent shader for the gabor stimulus. This is needed to add the pedestal to
# the color values for each location. I'm keeping it in this file to make the
# stimulus fairly self contained and to avoid messing with anything else.
# Almost a one to one copy of the original psychopy shader.
fragSignedColorTexMask = '''
    uniform sampler2D texture, mask;
    uniform float pedestal;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[1].st);
        gl_FragColor.a = gl_Color.a*maskFrag.a*textureFrag.a;
        gl_FragColor.rgb =  ((pedestal+1.0)/2.0)
                            + ((textureFrag.rgb
                            * (gl_Color.rgb*2.0-1.0)+1.0)/2.0) -0.5;
    }
    '''


class ElementArray(ElementArrayStim, MinimalStim, TextureMixin):
    """Field of elements that are independently controlled and rapidly drawn.

    This stimulus class defines a field of elements whose behaviour can be
    independently controlled. Suitable for creating 'global form' stimuli or
    more detailed random dot stimuli.

    This stimulus can draw thousands of elements without dropping a frame, but
    in order to achieve this performance, uses several OpenGL extensions only
    available on modern graphics cards (supporting OpenGL2.0). See the
    ElementArray demo.

    """
    def __init__(self,
                 win,
                 units=None,
                 fieldPos=(0.0, 0.0),
                 fieldSize=(1.0, 1.0),
                 fieldShape='circle',
                 nElements=100,
                 sizes=2.0,
                 xys=None,
                 rgbs=None,
                 colors=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacities=1.0,
                 depths=0,
                 fieldDepth=0,
                 oris=0,
                 sfs=1.0,
                 contrs=1,
                 phases=0,
                 elementTex='sin',
                 elementMask='gauss',
                 texRes=48,
                 interpolate=True,
                 name=None,
                 autoLog=False,
                 maskParams=None,
                 pedestal=None):

        super(ElementArray, self).__init__(
            win, units=units, fieldPos=fieldPos, fieldSize=fieldSize,
            fieldShape=fieldShape, nElements=nElements, sizes=sizes, xys=xys,
            rgbs=rgbs, colors=colors, colorSpace=colorSpace,
            opacities=opacities, depths=depths, fieldDepth=fieldDepth,
            oris=oris, sfs=sfs, contrs=contrs, phases=phases,
            elementTex=elementTex, elementMask=elementMask, texRes=texRes,
            interpolate=interpolate, name=name, autoLog=autoLog,
            maskParams=maskParams)

        # Set the default pedestal assuming a gray window color
        pedestal = win.background_color if pedestal is None else pedestal
        self.pedestal = pedestal

        self._progSignedTexMask = shaders.compileProgram(
            shaders.vertSimple, fragSignedColorTexMask)

    @property
    def pedestal_contrs(self):
        """Stimulsu contrast, accounting for pedestal"""
        return self.contrs / (self.pedestal + 1)

    @pedestal_contrs.setter
    def pedestal_contrs(self, values):
        """Stimulus contrast, accounting for pedestal."""
        adjusted_values = values * (self.pedestal + 1)
        self.contrs = adjusted_values

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.update() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win is None:
            win = self.win
        self._selectWindow(win)

        if self._needVertexUpdate:
            self._updateVertices()
        if self._needColorUpdate:
            self.updateElementColors()
        if self._needTexCoordUpdate:
            self.updateTextureCoords()

        # scale the drawing frame and get to centre of field
        GL.glPushMatrix()
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)

        # GL.glLoadIdentity()
        self.win.setScale('pix')

        GL.glColorPointer(
            4, GL.GL_DOUBLE, 0,
            self._RGBAs.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        GL.glVertexPointer(
            3, GL.GL_DOUBLE, 0,
            self.verticesPix.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))

        # setup the shaderprogram
        ped = self.pedestal
        GL.glUseProgram(self._progSignedTexMask)
        GL.glUniform1i(
            GL.glGetUniformLocation(self._progSignedTexMask, "texture"), 0)
        GL.glUniform1i(
            GL.glGetUniformLocation(self._progSignedTexMask, "mask"), 1)
        GL.glUniform1f(
            GL.glGetUniformLocation(self._progSignedTexMask, "pedestal"), ped)

        # bind textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        # setup client texture coordinates first
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._texCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._maskCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, self.verticesPix.shape[0]*4)

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # disable states
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glUseProgram(0)
        GL.glPopClientAttrib()
        GL.glPopMatrix()
