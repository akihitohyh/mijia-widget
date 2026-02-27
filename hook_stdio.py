"""运行时钩子：确保 sys.stdout/stderr 不为 None"""
import sys

class DummyStream:
    """虚拟流对象"""
    def isatty(self):
        return False
    def write(self, s):
        pass
    def flush(self):
        pass

# 打包后的 exe 没有控制台，stdout/stderr 为 None
if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()
