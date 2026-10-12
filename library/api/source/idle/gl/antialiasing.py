"""One reusable, context-owned scene framebuffer and FXAA presentation pass."""
from pathlib import Path
import logging

from PySide6.QtCore import QSize
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram, QOpenGLVertexArrayObject, QOpenGLFramebufferObject


class SceneAntialiasing:
    def __init__(self):
        self.context = None
        self.program = None
        self.vao = None
        self.framebuffer = None
        self.enabled = False
        self.reason = 'not initialized'
        self.locations = {}

    def initialize(self):
        self.destroy()
        self.context = QOpenGLContext.currentContext()
        try:
            if self.context is None:
                raise RuntimeError('No current GL context')
            self.program = QOpenGLShaderProgram()
            root = Path(__file__).with_name('shaders')
            for kind, name in ((QOpenGLShader.Vertex, 'fullscreen.vert'),
                               (QOpenGLShader.Fragment, 'antialias.frag')):
                if not self.program.addShaderFromSourceCode(kind, (root/name).read_text(encoding='utf-8')):
                    raise RuntimeError(self.program.log())
            if not self.program.link():
                raise RuntimeError(self.program.log())
            self.locations = {name: self.program.uniformLocation(name)
                              for name in ('u_scene', 'u_source_texel', 'u_output_resolution')}
            if any(loc < 0 for loc in self.locations.values()):
                raise RuntimeError('Missing anti-aliasing uniforms')
            self.vao = QOpenGLVertexArrayObject()
            if not self.vao.create():
                raise RuntimeError('Could not create anti-aliasing VAO')
            self.enabled = True
            self.reason = ''
        except Exception as exc:
            self.disable(str(exc))
        return self.enabled

    def disable(self, reason):
        self.enabled = False
        self.reason = str(reason)
        self.framebuffer = None
        logging.getLogger('aureon').warning('Scene FXAA unavailable: %s', self.reason)

    def begin(self, width, height):
        if not self.enabled:
            return False
        if QOpenGLContext.currentContext() != self.context:
            self.disable('Context changed before reinitialization')
            return False
        try:
            size = QSize(width, height)
            if self.framebuffer is None or self.framebuffer.size() != size:
                # Release the old size first; never retain a resize history.
                self.framebuffer = None
                self.framebuffer = QOpenGLFramebufferObject(size)
                if not self.framebuffer.isValid():
                    raise RuntimeError('Scene anti-aliasing framebuffer allocation failed')
                funcs = self.context.functions()
                funcs.glActiveTexture(0x84C0)
                funcs.glBindTexture(0x0DE1, self.framebuffer.texture())
                for parameter, value in ((0x2801, 0x2601), (0x2800, 0x2601),
                                         (0x2802, 0x812F), (0x2803, 0x812F)):
                    funcs.glTexParameteri(0x0DE1, parameter, value)
                funcs.glBindTexture(0x0DE1, 0)
            if not self.framebuffer.bind():
                raise RuntimeError('Could not bind scene anti-aliasing framebuffer')
            return True
        except Exception as exc:
            self.disable(str(exc))
            return False

    def present(self, destination, width, height):
        if not self.enabled or self.framebuffer is None:
            raise RuntimeError('Anti-aliasing presentation without a scene frame')
        funcs = self.context.functions()
        funcs.glBindFramebuffer(0x8D40, destination)
        funcs.glViewport(0, 0, width, height)
        funcs.glActiveTexture(0x84C0)
        funcs.glBindTexture(0x0DE1, self.framebuffer.texture())
        try:
            if not self.program.bind():
                raise RuntimeError('Anti-aliasing shader bind failed')
            self.vao.bind()
            funcs.glUniform1i(self.locations['u_scene'], 0)
            size = self.framebuffer.size()
            funcs.glUniform2f(self.locations['u_source_texel'], 1.0/size.width(), 1.0/size.height())
            funcs.glUniform2f(self.locations['u_output_resolution'], float(width), float(height))
            funcs.glDrawArrays(0x0004, 0, 3)
        finally:
            self.vao.release()
            self.program.release()
            funcs.glBindTexture(0x0DE1, 0)

    def destroy(self):
        current = QOpenGLContext.currentContext()
        if current is not None and current == self.context:
            if self.vao is not None:
                self.vao.destroy()
            if self.program is not None:
                self.program.removeAllShaders()
        # Qt's resource guards also handle objects whose context was lost.
        self.framebuffer = None
        self.vao = None
        self.program = None
        self.locations.clear()
        self.context = None
        self.enabled = False
