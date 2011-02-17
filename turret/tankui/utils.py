from PyQt4 import QtGui

# helper for changing the cursor
def pyqtOverrideCursor(cursor):
    def decorator(func):
        def _func(*args, **kwargs):
            QtGui.QApplication.setOverrideCursor(cursor)
            try:
                return func(*args, **kwargs)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
        return _func
    return decorator
