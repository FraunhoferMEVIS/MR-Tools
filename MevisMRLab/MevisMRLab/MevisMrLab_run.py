import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from mrlabContext import mrlabContext

from Plot import Plot
from Selector import Selector
from SeqDisplay import SeqDisplay
from SequenceSelector import SequenceSelector
from Simulation import Simulation
from simulateBloch import BlochSimulation
try:
    from Vector3DViewer_pyvista import Vector3DViewer_pyvista as Vector3DViewer
except Exception:
    from Vector3DViewer import Vector3DViewer

from OutputLogger import OutputLogger

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Feature flags
        self.ADVANCEDMODE = False
        self.LOGGER = False

        # Allow nested docks for splitter handles
        self.setDockOptions(
            self.dockOptions() |
            QtWidgets.QMainWindow.AllowNestedDocks |
            QtWidgets.QMainWindow.AnimatedDocks
        )

        # Initialize context
        self.mrCtx = mrlabContext()
        self.setAcceptDrops(True)

        # Instantiate widgets
        self.seqDisplay     = SeqDisplay()
        self.seqSelector    = SequenceSelector()
        self.buildingBlocks = Selector()
        self.simulator      = Simulation()
        self.blochsim       = BlochSimulation()
        self.plot           = Plot(showGUI=True, blochSim=self.blochsim)
        self.viewer3D       = Vector3DViewer(blochSim=self.blochsim, parent=self)
        self.outputLogger   = OutputLogger() if self.LOGGER      else None

        # Auto-update mapping
        self._auto_update_tools = {
            'Simulation': self.simulator,
            'BlochSim':   self.blochsim,
            '3DViewer':   self.viewer3D,
        }

        # Connect signals
        self.plot.set_viewer(self.viewer3D)
        self.plot.timesChanged.connect(self.blochsim.set_time_range)

        # Define tools list
        tools = [
            ('seqDisplay',    self.seqDisplay,     True),
            ('seqSelector',   self.seqSelector,    True),
            ('buildingBlocks',self.buildingBlocks, True),
            ('Simulation',    self.simulator,      False),
            ('BlochSim',      self.blochsim,       True),
            ('3DViewer',      self.viewer3D,       True),
            ('Plot',          self.plot,           True),
        ]
        if self.LOGGER:
            tools.append(('OutputLogger', self.outputLogger, True))
        if self.ADVANCEDMODE:
            tools.append(('ConvertToScanner', self.converter, True))

        # Register tools
        for name, widget, visible in tools:
            self.mrCtx.registerTool(name, widget, visible=visible)

        # Create toolbar for toggling
        tb_layout = QtWidgets.QHBoxLayout()
        tb_layout.addWidget(QtWidgets.QLabel('Show Tools:'), 0, Qt.AlignLeft)
        self.tool_checkboxes = {}
        for name, _, _ in tools:
            if name == 'Plot':
                continue
            cb = QtWidgets.QCheckBox(name)
            cb.setChecked(self.mrCtx.isToolVisible(name))
            cb.toggled.connect(lambda checked, n=name: self.mrCtx.setToolVisibility(n, checked))
            tb_layout.addWidget(cb, 0, Qt.AlignLeft)
            self.tool_checkboxes[name] = cb
        tb_layout.addStretch(1)
        tb_container = QtWidgets.QWidget()
        tb_container.setLayout(tb_layout)
        tb_dock = QtWidgets.QDockWidget('', self)
        tb_dock.setWidget(tb_container)
        tb_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.TopDockWidgetArea, tb_dock)

        # Layout map for docks
        layout_map = {
            'seqSelector':    Qt.LeftDockWidgetArea,
            'buildingBlocks': Qt.LeftDockWidgetArea,
            'seqDisplay':     Qt.BottomDockWidgetArea,
            'BlochSim':       Qt.RightDockWidgetArea,
            'Simulation':     Qt.RightDockWidgetArea,
            '3DViewer':       Qt.RightDockWidgetArea,
            'OutputLogger':   Qt.BottomDockWidgetArea,
            'ConvertToScanner':Qt.RightDockWidgetArea,
        }

        # Create docks
        self.tool_docks = {}
        for name, widget, _ in tools:
            if name == 'Plot':
                continue
            dock = QtWidgets.QDockWidget(name, self)
            dock.setWidget(widget)
            dock.setFeatures(
                QtWidgets.QDockWidget.DockWidgetMovable |
                QtWidgets.QDockWidget.DockWidgetFloatable
            )
            area = layout_map.get(name, Qt.RightDockWidgetArea)
            self.addDockWidget(area, dock)
            self.tool_docks[name] = dock

        # Tabify sequence docks
        self.tabifyDockWidget(
            self.tool_docks['seqSelector'],
            self.tool_docks['buildingBlocks']
        )

        # Central widget
        self.setCentralWidget(self.plot)

        # Sync visibility and auto-update
        self.mrCtx.toolVisibilityChanged.connect(self.onToolVisibilityChanged)
        for name, dock in self.tool_docks.items():
            dock.setHidden(not self.mrCtx.isToolVisible(name))

        # Maximize
        self.showMaximized()

    def onToolVisibilityChanged(self, toolname, visible):
        dock = self.tool_docks.get(toolname)
        self.tool_checkboxes[toolname].setChecked(visible)
        if dock:
            dock.setHidden(not visible)
        if not visible and toolname in self._auto_update_tools:
            tool = self._auto_update_tools[toolname]
            if hasattr(tool, 'autoUpdate'):
                try:
                    tool.autoUpdate.setChecked(False)
                except Exception:
                    pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    app.exec_()
    window.close()
    window.deleteLater()
    sys.exit()
