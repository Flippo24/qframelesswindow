# coding:utf-8
from PySide6.QtCore import QCoreApplication, QEvent, Qt, QSize, QRect, QPoint, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QMainWindow, QDialog

from ..titlebar import TitleBar
from ..utils.linux_utils import LinuxMoveResize
from .window_effect import LinuxWindowEffect


class LinuxFramelessWindowBase:
    """ Frameless window base class for Linux system """

    BORDER_WIDTH = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._isSystemButtonVisible = False

    def _initFrameless(self):
        self.windowEffect = LinuxWindowEffect(self)
        self.titleBar = TitleBar(self)
        self._isResizeEnabled = True

        self.updateFrameless()
        QCoreApplication.instance().installEventFilter(self)

        self.titleBar.raise_()
        self.resize(500, 500)

    def _windowRect(self) -> QRect:
        """Return the window rect in global coordinates."""
        return QRect(self.mapToGlobal(QPoint(0, 0)), self.size())

    def _edgesAt(self, globalPos) -> Qt.Edges:
        """Return resize edges for a global cursor position."""
        if (
            not self._isResizeEnabled
            or not self.isVisible()
            or self.windowState() != Qt.WindowNoState
        ):
            return Qt.Edge(0)

        rect = self._windowRect()
        if not rect.contains(globalPos):
            return Qt.Edge(0)

        x = globalPos.x() - rect.x()
        y = globalPos.y() - rect.y()
        edges = Qt.Edge(0)

        if x < self.BORDER_WIDTH:
            edges |= Qt.LeftEdge
        elif x >= rect.width() - self.BORDER_WIDTH:
            edges |= Qt.RightEdge

        if y < self.BORDER_WIDTH:
            edges |= Qt.TopEdge
        elif y >= rect.height() - self.BORDER_WIDTH:
            edges |= Qt.BottomEdge

        return edges

    def _cursorShapeForEdges(self, edges):
        """Map resize edges to the matching cursor shape."""
        if edges in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge):
            return Qt.SizeFDiagCursor
        if edges in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge):
            return Qt.SizeBDiagCursor
        if edges in (Qt.TopEdge, Qt.BottomEdge):
            return Qt.SizeVerCursor
        if edges in (Qt.LeftEdge, Qt.RightEdge):
            return Qt.SizeHorCursor
        return Qt.ArrowCursor

    def _syncResizeCursor(self):
        """Keep the top-level cursor aligned with the current pointer position."""
        self.setCursor(self._cursorShapeForEdges(self._edgesAt(QCursor.pos())))

    def _scheduleCursorSync(self):
        """Refresh again after native move/resize handling settles."""
        for delay in (0, 50, 150):
            QTimer.singleShot(delay, self._syncResizeCursor)

    def updateFrameless(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

    def resizeEvent(self, e):
        self.titleBar.resize(self.width(), self.titleBar.height())

    def setTitleBar(self, titleBar):
        """ set custom title bar

        Parameters
        ----------
        titleBar: TitleBar
            title bar
        """
        self.titleBar.deleteLater()
        self.titleBar.hide()
        self.titleBar = titleBar
        self.titleBar.setParent(self)
        self.titleBar.raise_()

    def setResizeEnabled(self, isEnabled: bool):
        """ set whether resizing is enabled """
        self._isResizeEnabled = isEnabled
        if not isEnabled:
            self.setCursor(Qt.ArrowCursor)

    def isSystemButtonVisible(self):
        """ Returns whether the system title bar button is visible """
        return self._isSystemButtonVisible

    def setSystemTitleBarButtonVisible(self, isVisible):
        """ set the visibility of system title bar button, only works for macOS """
        pass

    def systemTitleBarRect(self, size: QSize) -> QRect:
        """ Returns the system title bar rect, only works for macOS

        Parameters
        ----------
        size: QSize
            original system title bar rect
        """
        return QRect(0, 0, size.width(), size.height())

    def eventFilter(self, obj, event):
        et = event.type()

        if obj is self and et in (QEvent.Move, QEvent.Resize, QEvent.WindowStateChange, QEvent.Show, QEvent.Hide):
            self._syncResizeCursor()
            return False

        if et not in (
            QEvent.Enter,
            QEvent.Leave,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseMove,
        ):
            return False

        self._syncResizeCursor()

        if obj in (self, self.titleBar) and et == QEvent.MouseButtonPress:
            edges = self._edgesAt(event.globalPos())
            if edges:
                LinuxMoveResize.starSystemResize(self, event.globalPos(), edges)
                self._scheduleCursorSync()
        elif et == QEvent.MouseButtonRelease:
            self._scheduleCursorSync()

        return False


class LinuxFramelessWindow(LinuxFramelessWindowBase, QWidget):
    """ Frameless window for Linux system """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._initFrameless()


class LinuxFramelessMainWindow(LinuxFramelessWindowBase, QMainWindow):
    """ Frameless main window for Linux system """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._initFrameless()


class LinuxFramelessDialog(LinuxFramelessWindowBase, QDialog):
    """ Frameless dialog for Windows system """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._initFrameless()
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
