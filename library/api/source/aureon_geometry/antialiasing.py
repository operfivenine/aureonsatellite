"""Optional scene-only FXAA on the already rendered Qt/depth framebuffer.

Qt still owns the scene's depth/MSAA target. Resolve its color into one scratch
texture, then filter back before painting UI. No history or playback coupling.
The same operation can filter an ordinary reflection framebuffer.
"""
import os
from idle.gl.antialiasing import SceneAntialiasing


class GeometryAntialiasing(SceneAntialiasing):
    def initialize(self):
        if os.environ.get('AUREON_GEOMETRY_AA_FORCE_FAIL')=='1':
            self.disable('Requested geometry FXAA failure test')
            return False
        return super().initialize()

    def apply(self,destination,width,height):
        if not self.enabled or os.environ.get('AUREON_GEOMETRY_AA_OFF')=='1':return False
        funcs=self.context.functions()
        try:
            if not self.begin(width,height):return False
            extra=self.context.extraFunctions()
            extra.glBindFramebuffer(0x8CA8,destination)  # READ_FRAMEBUFFER
            extra.glBindFramebuffer(0x8CA9,self.framebuffer.handle())
            # NEAREST is required when resolving a multisample color buffer.
            extra.glBlitFramebuffer(0,0,width,height,0,0,width,height,0x4000,0x2600)
            funcs.glDisable(0x0B71);funcs.glDepthMask(False);funcs.glDisable(0x0BE2)
            funcs.glDisable(0x809D);funcs.glDisable(0x0C11)
            self.present(destination,width,height)
            return True
        except Exception as exc:
            self.disable(str(exc))
            return False
        finally:
            # A failed optional filter leaves the scene that was already drawn
            # in Qt's target intact; never leave a scratch framebuffer bound.
            funcs.glBindFramebuffer(0x8D40,destination);funcs.glViewport(0,0,width,height)

    def snapshot(self):
        fbo=self.framebuffer
        return dict(enabled=self.enabled and os.environ.get('AUREON_GEOMETRY_AA_OFF')!='1',reason=self.reason,
                    size=[fbo.width(),fbo.height()] if fbo else None,
                    scratch_bytes=fbo.width()*fbo.height()*4 if fbo else 0)
