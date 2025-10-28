import sys
import json
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, 
    QLineEdit, QFileDialog, QMessageBox, QComboBox, QCheckBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QObject, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from scipy.interpolate import interp1d

class Vector3DViewer(QWidget):
    settingsChanged = pyqtSignal()
    markerChanged = pyqtSignal(float)
    def __init__(self,*args, **kwargs):
        super().__init__()
        self.setWindowTitle("3D Vector Visualization with Presets")
        self.setMinimumWidth(400)
        # Default parameters
        self.num_timepoints = 500
        self.current_index = 0
        self.current_time = 0
        self.ax = None

        self.blochsim = kwargs.get('blochSim')
        if self.blochsim:
            self.blochsim.blochSim_finished.connect(self.set_vector_data)
            self.blochsim.settingsChanged.connect(self.update_grid_params)

        self.update_grid_params()
        self.reset_view()

        self.init_ui()
      
        self.update_plot()

    def init_ui(self):
        layout = QVBoxLayout()

        # Matplotlib canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas,stretch=1)

        # Playback controls
        playback_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self.toggle_play)
        playback_layout.addWidget(self.play_btn)

        playback_layout.addWidget(QLabel("Time:"))
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(self.num_timepoints - 1)
        self.time_slider.valueChanged.connect(self.update_time_from_slider)
        playback_layout.addWidget(self.time_slider)

        self.time_label = QLabel("0")
        playback_layout.addWidget(self.time_label)

        layout.addLayout(playback_layout,stretch=0)
        
        preset_layout = QHBoxLayout()

        # Reset view button
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.clicked.connect(lambda x: self.reset_view(elev=30,azim=-60,dist=15))
        preset_layout.addWidget(reset_view_btn)
        top_view1_btn = QPushButton("Top View X")
        top_view1_btn.clicked.connect(lambda x: self.reset_view(elev=90,azim=90))
        preset_layout.addWidget(top_view1_btn)
        top_view2_btn = QPushButton("Top View Y")
        top_view2_btn.clicked.connect(lambda x: self.reset_view(elev=90,azim=0))
        preset_layout.addWidget(top_view2_btn)
        side_view1_btn = QPushButton("Side View X")
        side_view1_btn.clicked.connect(lambda x: self.reset_view(elev=0,azim=90))
        preset_layout.addWidget(side_view1_btn)
        side_view2_btn = QPushButton("Side View Y")
        side_view2_btn.clicked.connect(lambda x: self.reset_view(elev=0,azim=0))
        preset_layout.addWidget(side_view2_btn)
        self.show_vectors_checkbox = QCheckBox("Show vectors")
        self.show_vectors_checkbox.setChecked(True)
        self.show_vectors_checkbox.toggled.connect(self.update_plot)
        preset_layout.addWidget(self.show_vectors_checkbox)
        self.show_shadows_checkbox = QCheckBox("Show shadows")
        self.show_shadows_checkbox.setChecked(True)
        self.show_shadows_checkbox.toggled.connect(self.update_plot)
        preset_layout.addWidget(self.show_shadows_checkbox)
        self.show_locations_checkbox = QCheckBox("Show locations")
        self.show_locations_checkbox.setChecked(True)
        self.show_locations_checkbox.toggled.connect(self.update_plot)
        preset_layout.addWidget(self.show_locations_checkbox)

        layout.addLayout(preset_layout)

        # Timer for playback
        self.timer = QTimer()
        self.timer.timeout.connect(self.increment_time)

        self.setLayout(layout)

    def update_plot(self):
        # Preserve orientation and zoom
        if self.ax:
            try:
                self.elev = self.ax.elev
                self.azim = self.ax.azim
                self.dist = self.ax.dist
                xlim = self.ax.get_xlim()
                ylim = self.ax.get_ylim()
                zlim = self.ax.get_zlim()
            except AttributeError:
                xlim = ylim = zlim = None
        else:
            xlim = ylim = zlim = None
    
        if self.num_vectors:
            # Clear and recreate self.axes
            self.figure.clear()
            self.ax = self.figure.add_subplot(111, projection='3d')
            self.ax.view_init(elev=self.elev, azim=self.azim)
            self.ax.dist = self.dist
            positions = self.positions
            vectors = self.vectors[self.current_index]

            # Avoid division by zero for zero-length vectors
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0  # prevent divide-by-zero
            unit_vectors = vectors / norms
            scaled_vectors = unit_vectors * norms  # you can apply length scaling here if needed
        
            # Main arrows (batched)
            if self.show_vectors_checkbox.isChecked():
                self.ax.quiver(
                    positions[:, 0], positions[:, 1], positions[:, 2],
                    scaled_vectors[:, 0], scaled_vectors[:, 1], scaled_vectors[:, 2],
                    normalize=False, color='blue', linewidth=1.5
                )
    
            if self.show_locations_checkbox.isChecked():        
                self.ax.scatter3D(positions[:, 0], positions[:, 1], positions[:, 2],color='red',s=3,depthshade=False)
     
            # Shadow projections
            if self.show_shadows_checkbox.isChecked():
                self.ax.quiver(
                    positions[:, 0], positions[:, 1], 0,
                    scaled_vectors[:, 0], scaled_vectors[:, 1], np.zeros_like(scaled_vectors[:, 2]),
                    normalize=False, color='gray', linewidth=1.0
                )
           
           # Infinite XY plane at Z = -15
            plane_size = 50
            xx, yy = np.meshgrid(np.linspace(-plane_size, plane_size, 2), np.linspace(-plane_size, plane_size, 2))
            zz = np.full_like(xx, -5)
            self.ax.plot_surface(xx, yy, zz, color='#F5DEB3', alpha=0.5)
        
            # Hide axis, ticks, grid, and labels
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_zticks([])
            self.ax.set_axis_off()
    
            # Restore previous zoom (if available), else default
            if xlim and ylim and zlim:
                self.ax.set_xlim(xlim)
                self.ax.set_ylim(ylim)
                self.ax.set_zlim(zlim)
            else:
                 # Set equal aspect and limits so all points are visible
                self.ax.set_xlim(self.x_mid - self.max_range, self.x_mid + self.max_range)
                self.ax.set_ylim(self.y_mid - self.max_range, self.y_mid + self.max_range)
                self.ax.set_zlim(self.z_mid - self.max_range, self.z_mid + self.max_range)
                self.ax.view_init(elev=self.elev, azim=self.azim)  # elevation and azimuth
          
            self.figure.tight_layout()
            self.ax.set_position([-0.5, -0.5, 2.0, 2.0])  # fill full canvas: [left, bottom, width, height]
            self.canvas.draw_idle()

    def toggle_play(self, playing):
        self.play_btn.setText("Pause" if playing else "Play")
        self.timer.start(50) if playing else self.timer.stop()

    def increment_time(self):
        self.current_index = (self.current_index + 1) % self.num_timepoints
        self.time_slider.setValue(self.current_index)

    def get_current_time(self):
        return self.current_time
    
    def set_current_time(self,time):
        self.current_time = time 
        idx = np.abs(self.vector_times - time).argmin() 
        self.time_slider.setValue(idx)

    def update_time_from_slider(self, val):
        self.current_index = val
        self.current_time = self.vector_times[val]
        self.time_label.setText(str(f"{self.current_time:.2e}"))
        self.update_plot()
        self.markerChanged.emit(self.current_time)

    def update_grid_params(self,grid_params=None):
        if grid_params:
            self.positions = grid_params.get('positions')
            self.num_vectors = self.positions.shape[0]
            self.vectors = np.zeros( (self.num_timepoints, self.num_vectors, 3))
        else:
            self.positions = None
            self.num_vectors = 0
        self.update_plot()

    def set_vector_data(self, data, grid_params, convert=True):
        if 'signal_amp' in data.keys() and data['signal_amp']['v'] is []:
            return
        self.data = data
        self.update_grid_params(grid_params)
        """Externally set vector data. Must be shape (T, N, 3). If this is not the case, data can be converted by setting convert to True"""
        if convert and 'mx' in data.keys():
                nx, ny, nz, nt = data['mx'].shape
                stacked = np.stack([data['mx'], data['my'], data['mz']], axis=-1)
                reshaped = stacked.reshape(-1, nt, 3)
                vectors = reshaped.transpose(1, 0, 2)
                self.positions = data['positions']
                self.times = data['abs_times']

        else:
            vectors = data
            
        if not isinstance(vectors, np.ndarray) or vectors.ndim != 3 or vectors.shape[2] != 3:
            raise ValueError("Expected a NumPy array of shape (T, N, 3)")
        if vectors.shape[1] != self.positions.shape[0]:
            raise ValueError("Mismatch: vector count does not match number of grid positions")
        self.vectors_all = vectors
        self.set_time_range(grid_params['tstart'],grid_params['tend'])
        self.update_plot()

    def set_time_range(self, tstart,tend):
        """
        Resample vector data to new time points using linear interpolation.
        :param new_times: 1D array of new time points (e.g., np.linspace(0, T-1, N))
        :return: resampled vector array of shape (len(new_times), num_vectors, 3)
        """
        if not hasattr(self, 'vectors_all'):
            return
            raise AttributeError("No vector data available to resample.")
        
        # print('viewer3d time range changed:',tstart,tend)  

        tstart = max(0,tstart)
        tend = max(tend,tstart+1e-6)
        new_times = np.linspace(tstart,tend,self.num_timepoints)
        
        t_old = self.times
        self.vector_times = new_times
        nt, nv, dim = self.vectors_all.shape
        # Interpolate each component separately
        resampled = np.empty((len(new_times), nv, dim))
        for i in range(dim):
            # shape (nt, nv) → transpose to (nv, nt) for vectorized interpolation
            component = self.vectors_all[:, :, i].T
            interpolator = interp1d(t_old, component, kind='linear', axis=1, bounds_error=False, fill_value="extrapolate")
            resampled[:, :, i] = interpolator(new_times).T

        self.num_timepoints = len(new_times)
        self.time_slider.setMaximum(self.num_timepoints - 1)
        self.time_slider.setValue(0)
    
        self.vectors = resampled
    
    def reset_view(self,elev=30,azim=-60,dist=None):
        if not dist and self.positions is not None:
            # Extract x, y, z
            x, y, z = self.positions[:,0], self.positions[:,1], self.positions[:,2]
            
            # Compute bounding box
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            z_min, z_max = z.min(), z.max()
            
            # Compute center and mself.ax range
            self.x_mid = (x_min + x_max) / 2
            self.y_mid = (y_min + y_max) / 2
            self.z_mid = (z_min + z_max) / 2
            
            self.max_range = max(x_max - x_min, y_max - y_min, z_max - z_min) / 2
            dist = self.max_range
        else:
            dist = 10
            self.x_mid = 0
            self.y_mid = 0
            self.z_mid = 0
            self.max_range = 10
        self.elev, self.azim, self.dist = elev,azim,dist
        if self.ax:
            self.ax.elev, self.ax.azim, self.ax.dist = self.elev, self.azim, self.dist
            self.update_plot()

from Plot import Plot
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Combined Plot + Vector3D Viewer")
        self.resize(1800, 800)

        layout = QHBoxLayout()

        self.plot_widget = Plot()  # imported widget
        self.viewer3d = Vector3DViewer()  # your 3D vector viewer

        self.plot_widget.set_viewer(self.viewer3d)
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.viewer3d)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
