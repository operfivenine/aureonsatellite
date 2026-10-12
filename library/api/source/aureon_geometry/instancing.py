"""Context-local GL 3.3 entry points. No PyOpenGL or global renderer state."""
import ctypes

class Instancing:
    def __init__(self,context):
        abi=getattr(ctypes,'WINFUNCTYPE',ctypes.CFUNCTYPE)
        def proc(name,result,*args):
            address=int(context.getProcAddress(name.encode('ascii')) or 0)
            if address in (0,1,2,3,-1,ctypes.c_void_p(-1).value):raise RuntimeError('GPU lacks '+name)
            return abi(result,*args)(address)
        self.divisor=proc('glVertexAttribDivisor',None,ctypes.c_uint,ctypes.c_uint)
        self.draw=proc('glDrawArraysInstanced',None,ctypes.c_uint,ctypes.c_int,ctypes.c_int,ctypes.c_int)
