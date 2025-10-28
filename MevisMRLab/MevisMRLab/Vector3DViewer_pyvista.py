import sys
import os
import json
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QSlider, QLabel, QComboBox, QCheckBox,
    QDialog, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import numba
import matplotlib.cm as cm
import time
from mrlabContext import mrlabContext
import mrlab_utils as utils

# ---- Preset Dialog ----
class Vector3DPresetDialog(QDialog):
    def __init__(self, parent, presets, current_settings):
        super().__init__(parent)
        self.setWindowTitle("Viewer Parameters")
        self.presets = presets
        self.current_settings = current_settings.copy()

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Show vectors
        row = QHBoxLayout()
        row.addWidget(QLabel("Show Vectors:"))
        self.show_vectors = QComboBox()
        self.show_vectors.addItems(['Show all','Show XY only','Show Z only','Show none'])
        self.show_vectors.setCurrentIndex(current_settings.get('show_vectors', 0))
        row.addWidget(self.show_vectors)
        layout.addLayout(row)

        # Show shadows
        self.show_shadows = QCheckBox("Show Shadows")
        self.show_shadows.setChecked(current_settings.get('show_shadows', True))
        layout.addWidget(self.show_shadows)

        # Show locations
        self.show_locations = QCheckBox("Show Locations")
        self.show_locations.setChecked(current_settings.get('show_locations', False))
        layout.addWidget(self.show_locations)

        # Color mode and colormap
        row = QHBoxLayout()
        row.addWidget(QLabel("Color Mode:"))
        self.color_mode = QComboBox()
        self.cmap_map = {'magZ':['bwr','seismic','RdBu'],'magXY':['gray','viridis','inferno'],
                         'phaseXY':['hsv','jet','twilight'],'combXY':['hsv','jet','twilight']}
        self.color_mode.addItems(list(self.cmap_map.keys()))
        self.color_mode.setCurrentIndex(current_settings.get('color_mode', 0))
        self.color_mode.currentIndexChanged.connect(self._update_cmap_choices)
        row.addWidget(self.color_mode)

        row.addWidget(QLabel("Colormap:"))
        self.cmap = QComboBox()
        self._update_cmap_choices(self.color_mode.currentIndex())
        self.cmap.setCurrentIndex(current_settings.get('cmap', 0))
        row.addWidget(self.cmap)
        layout.addLayout(row)

        # Arrow size slider
        row = QHBoxLayout()
        row.addWidget(QLabel("Arrow Size:"))
        self.arrow_size_slider = QSlider(Qt.Horizontal)
        self.arrow_size_slider.setMinimum(1)
        self.arrow_size_slider.setMaximum(2000)
        self.arrow_size_slider.setValue(current_settings.get('arrow_size', 100))
        self.arrow_size_label = QLabel(f"{current_settings.get('arrow_size', 100)/100.0:.2f}")
        self.arrow_size_slider.valueChanged.connect(
            lambda val: self.arrow_size_label.setText(f"{val/100.0:.2f}")
        )
        row.addWidget(self.arrow_size_slider)
        row.addWidget(self.arrow_size_label)
        layout.addLayout(row)

        # # Display current camera (not editable)
        # cam = current_settings
        # layout.addWidget(QLabel(f"Camera Focal Point: {np.round(cam.get('focal_point', [0,0,0]),2)}"))
        # layout.addWidget(QLabel(f"Camera Position:    {np.round(cam.get('position', [0,0,10]),2)}"))
        # layout.addWidget(QLabel(f"Camera Up:         {np.round(cam.get('up', [0,0,1]),2)}"))

        # Save preset button
        save_btn = QPushButton("Save Preset")
        save_btn.clicked.connect(self.save_preset)
        layout.addWidget(save_btn)

        # OK/cancel
        ok_cancel = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_cancel.addWidget(ok_btn)
        ok_cancel.addWidget(cancel_btn)
        layout.addLayout(ok_cancel)

    def _update_cmap_choices(self, idx):
        mode = self.color_mode.itemText(idx)
        self.cmap.clear()
        self.cmap.addItems(self.cmap_map.get(mode, []))

    def get_settings(self):
        return {
            'show_vectors': self.show_vectors.currentIndex(),
            'show_shadows': self.show_shadows.isChecked(),
            'show_locations': self.show_locations.isChecked(),
            'color_mode': self.color_mode.currentIndex(),
            'cmap': self.cmap.currentIndex(),
            'arrow_size': self.arrow_size_slider.value(),
            'focal_point': self.current_settings.get('focal_point', [0,0,0]),
            'position': self.current_settings.get('position', [0,0,10]),
            'up': self.current_settings.get('up', [0,0,1]),
        }

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter name for new preset:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self.presets:
            reply = QMessageBox.question(
                self,
                "Overwrite Preset?",
                f"A preset named '{name}' already exists.\nOverwrite it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.presets[name] = self.get_settings()
        os.makedirs("presets", exist_ok=True)
        with open("presets/vector3dviewer.json", "w") as f:
            json.dump(self.presets, f, indent=2)
        QMessageBox.information(self, "Preset Saved", f"Preset '{name}' has been saved.")
        if hasattr(self.parent(), "update_preset_dropdown"):
            self.parent().presets = self.presets
            self.parent().update_preset_dropdown()

@numba.njit(parallel=True)
def _interp_vectors_numba(vectors_old, idx_lo, idx_hi, w_lo, w_hi, out):
    new_T, N, dim = out.shape
    for i in numba.prange(new_T):
        ilo = idx_lo[i]; ihi = idx_hi[i]
        wli = w_lo[i]; whi = w_hi[i]
        for j in range(N):
            out[i, j, 0] = wli*vectors_old[ilo,j,0] + whi*vectors_old[ihi,j,0]
            out[i, j, 1] = wli*vectors_old[ilo,j,1] + whi*vectors_old[ihi,j,1]
            out[i, j, 2] = wli*vectors_old[ilo,j,2] + whi*vectors_old[ihi,j,2]
    return out

class FixedQtInteractor(QtInteractor):
    def resizeEvent(self, ev):
        w, h = self.width(), self.height()
        self._Iren.SetSize(w, h)
        self._Iren.ConfigureEvent()

class Vector3DViewer_pyvista(QWidget):
    settingsChanged = pyqtSignal()
    markerChanged   = pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(kwargs.get('parent','don\'t forget to set parent!'))
        self.setWindowTitle("3D Vector Visualization with Presets")
        self.mrCtx = mrlabContext()
        
        # --- Presets ---
        self.presets_file = "presets/vector3dviewer.json"
        self.presets = self.load_presets()
        self.current_preset_name = None
        self.params = self.presets[list(self.presets.keys())[0]].copy() if self.presets else self.default_params()

        self.num_timepoints = 500
        self.current_index  = 0
        self.current_time   = 0
        self.times          = (-1, -1)

        self._camera_locked = False

        self.positions    = None
        self.positions_all= None

        self.num_vectors  = 0
        self.vectors_all  = None
        self.vectors      = None
        self.vector_times = None
        self.arrow_size   = self.params['arrow_size']/100.0

        self.arrow_actor    = None
        self.cube_actor     = None
        self.shadow_actor   = None
        self.location_actor = None
        self.plane_actor    = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.increment_time)

        self.blochsim = kwargs.get('blochSim')
        if self.blochsim:
            self.blochsim.blochSim_finished.connect(self.set_vector_data)  
        self.mrCtx.toolPresetChanged.connect(self.update_preset)

        self.init_ui()
        self.update_grid_params() 
        self.reset_view()
        self.update_plot()

    def default_params(self):
        return {
            'show_vectors': 0,  # "Show all"
            'show_shadows': True,
            'show_locations': False,
            'color_mode': 0,
            'cmap': 0,
            'arrow_size': 100,
            'focal_point': [0,0,0],
            'position': [0,0,10],
            'up': [0,0,1],
        }

    def init_ui(self):
        layout = QVBoxLayout(self)
        # -- Preset row --
        preset_row = QHBoxLayout()
        self.preset_dropdown = QComboBox()
        self.preset_dropdown.addItems(list(self.presets.keys()))
        self.preset_dropdown.currentIndexChanged.connect(self.apply_preset)
        self.settings_btn = QPushButton("Settings...")
        self.settings_btn.clicked.connect(self.open_preset_dialog)
        self.save_preset_btn = QPushButton("Save Preset")
        self.save_preset_btn.clicked.connect(self.save_current_preset)
        preset_row.addWidget(QLabel("Presets:"))
        preset_row.addWidget(self.preset_dropdown)
        preset_row.addWidget(self.settings_btn)
        preset_row.addWidget(self.save_preset_btn)
        layout.addLayout(preset_row)

        # Canvas
        self.plotter = FixedQtInteractor(self)
        layout.addWidget(self.plotter.interactor, stretch=1)
        self.plotter.camera.AddObserver("ModifiedEvent", self._on_camera_modified)

        # Playback controls
        ctrl = QHBoxLayout()
        self.play_btn = QPushButton("Play"); self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self.toggle_play)
        ctrl.addWidget(self.play_btn)
        ctrl.addWidget(QLabel("Time:"))
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0); self.time_slider.setMaximum(self.num_timepoints-1)
        self.time_slider.valueChanged.connect(self.update_time_from_slider) 
        ctrl.addWidget(self.time_slider)
        self.time_label = QLabel("0"); ctrl.addWidget(self.time_label)
        layout.addLayout(ctrl)

        # View buttons in 2x3 grid (RESTORED)
        grid = QGridLayout()
        btns = [
            ("View1", lambda: self.set_predefined_view("view1")),
            ("View2", lambda: self.set_predefined_view("view2")),
            ("Top X", lambda: self.set_predefined_view("topX")),
            ("Side X",lambda: self.set_predefined_view("sideX")),
            ("Top Y", lambda: self.set_predefined_view("topY")),
            ("Side Y",lambda: self.set_predefined_view("sideY")),
        ]
        for i, (lbl, fn) in enumerate(btns):
            b = QPushButton(lbl)
            b.clicked.connect(fn)
            grid.addWidget(b, 0, i)
        layout.addLayout(grid)
        self.setLayout(layout)
        self.set_predefined_view('view1')

    def update_preset(self,preset="",name="3DViewer"):
        print('update_preset:',name,preset)
        if name == "3DViewer":
            params = self.presets.get(preset)
            if params:
                idx = self.preset_dropdown.findText(preset)
                if idx >= 0:
                    self.preset_dropdown.setCurrentIndex(idx)
            else:
                print(preset,'is not a known preset for blochsim')
                print('available presets:', self.presets.keys())
               
    def set_predefined_view(self, view):
        if self.positions is None or self.positions.shape[0] == 0:
            return
        center = np.mean(self.positions, axis=0)
        xspan = np.ptp(self.positions[:,0])
        yspan = np.ptp(self.positions[:,1])
        zspan = np.ptp(self.positions[:,2])
        maxspan = max(xspan, yspan, zspan, 1)
        dist = maxspan

        viewdefs = {
            "view1":  dict(pos=center + np.array([+2*dist, +2*dist, +2*dist]), up=(0,0,1)),
            "view2":  dict(pos=center + np.array([  0,   -2*dist, +2*dist]), up=(0,0,1)),
            "topX":   dict(pos=center + np.array([0, 0, +3 * dist]),        up=(1,0,0)),
            "sideX":  dict(pos=center + np.array([+3 * dist,0,0]),          up=(0,0,1)),
            "topY":   dict(pos=center + np.array([0, 0, +3 * dist]),        up=(0,1,0)),
            "sideY":  dict(pos=center + np.array([0,+3 * dist,0]),          up=(0,0,1)),
        }
        v = viewdefs[view]
        self.params['focal_point'] = list(center)
        self.params['position'] = list(v['pos'])
        self.params['up'] = list(v['up'])
        self._camera_locked = False
        self.update_plot()

    def set_viewer_settings(self, params):
        self.params = params.copy()
        self.arrow_size = self.params['arrow_size']/100.0
        self._camera_locked = False
        self.update_plot()

    def open_preset_dialog(self):
        self.params['focal_point'] = list(self.plotter.camera.focal_point)
        self.params['position'] = list(self.plotter.camera.position)
        self.params['up'] = list(self.plotter.camera.up)
        dlg = Vector3DPresetDialog(self, self.presets, self.params)
        if dlg.exec_() == QDialog.Accepted:
            self.set_viewer_settings(dlg.get_settings())

    def save_current_preset(self):
        self.params['focal_point'] = list(self.plotter.camera.focal_point)
        self.params['position'] = list(self.plotter.camera.position)
        self.params['up'] = list(self.plotter.camera.up)
        dlg = Vector3DPresetDialog(self, self.presets, self.params)
        dlg.save_preset()
        self.presets = self.load_presets()
        self.update_preset_dropdown()

    def update_preset_dropdown(self):
        self.preset_dropdown.blockSignals(True)
        self.preset_dropdown.clear()
        self.preset_dropdown.addItems(list(self.presets.keys()))
        self.preset_dropdown.blockSignals(False)

    def apply_preset(self, index):
        if index < 0: return
        name = self.preset_dropdown.itemText(index)
        if name in self.presets:
            self.current_preset_name = name
            self.set_viewer_settings(self.presets[name])
            try:
                self.plotter.camera.focal_point = self.params['focal_point']
                self.plotter.camera.position = self.params['position']
                self.plotter.camera.up = self.params['up']
            except Exception as e:
                print("Failed to apply camera from preset:", e)
            self.plotter.render()

    def load_presets(self):
        if os.path.exists(self.presets_file):
            with open(self.presets_file, "r") as f:
                return json.load(f)
        return {}

    def closeEvent(self, event):
        try:
            self.plotter.close()
        except:
            pass
        super().closeEvent(event)

    def _on_camera_modified(self, caller, event):
        # self.params['focal_point'] = list(self.plotter.camera.focal_point)
        # self.params['position'] = list(self.plotter.camera.position)
        # self.params['up'] = list(self.plotter.camera.up)
        self._camera_locked = True

    def toggle_play(self, checked):
        if checked:
            self.play_btn.setText("Pause")
            self.timerStart = time.time() - (self.current_index / self.num_timepoints * 10)
            self.timer.start(50)
        else:
            self.play_btn.setText("Play")
            self.timer.stop()

    def increment_time(self):
        if self.num_timepoints == 0: return
        dt = time.time() - self.timerStart
        idx = int((dt/10*self.num_timepoints) % self.num_timepoints)
        self.time_slider.setValue(idx)

    def update_time_from_slider(self, val):
        self.current_index = val
        if self.vector_times is not None:
            self.current_time = float(self.vector_times[val])
            self.time_label.setText(f"{self.current_time:.2e}s")
            self.markerChanged.emit(self.current_time)
        self.update_plot()

    def get_current_time(self):
        return self.current_time

    def set_current_time(self, time):
        self.current_time = time
        time = max(time,self.vector_times[0])
        time = min(time,self.vector_times[-1])
        idx = np.abs(self.vector_times - time).argmin()
        self.time_slider.setValue(int(idx))

    def update_grid_params(self, grid_params=None):
        if grid_params:
            pos3d = grid_params.get('positions')
            if pos3d.ndim == 3:                                    # already (Nt,N,3)
                self.positions_all= pos3d
                self.positions = self.positions_all[self.current_index]
            else:
                self.positions = pos3d
            self.num_vectors  = int(self.positions.shape[0])
            self.vectors      = np.zeros((self.num_timepoints, self.num_vectors, 3))
            sx = grid_params.get('sx',10)/grid_params.get('nx',1) if grid_params.get('nx',1)>1 else 0.01
            sy = grid_params.get('sy',10)/grid_params.get('ny',1) if grid_params.get('ny',1)>1 else 0.01
            sz = grid_params.get('sz',10)/grid_params.get('nz',1) if grid_params.get('nz',1)>1 else 0.01
            _arrowSize = int(100*max(sx,sy,sz,0.01))
            if _arrowSize>self.params['arrow_size']:
                self.params['arrow_size'] =  int(100*max(sx,sy,sz,0.01))
        else:
            self.positions   = None
            self.num_vectors = 0
        self.arrow_actor    = None
        self.cube_actor     = None
        self.shadow_actor   = None
        self.location_actor = None
        self.plane_actor    = None
        self.update_plot()

    def set_vector_data(self, data, grid_params):
        if "signal_amp" in data.keys() and len(data["signal_amp"]["v"])==0:
            return

        tstart, tend = data.get('t',[0])[0],data.get('t',[0])[-1]
        self.data = data

        if "mx" in data.keys():
            n, nt = data["mx"].shape
            stacked = np.stack([data["mx"], data["my"], data["mz"]], axis=-1)
            reshaped = stacked.reshape(-1, nt, 3)
            vectors = reshaped.transpose(1, 0, 2)
            self.positions_all = data["positions"]
            self.times = data.get("t", np.cumsum(data.get("times", np.zeros(nt))))
            self.positions = self.positions_all[self.current_index,:,:]
        else:
            self.positions_all = None
            self.positions = None
            self.times = None

        
        if not isinstance(vectors, np.ndarray) or vectors.ndim != 3 or vectors.shape[2] != 3:
            raise ValueError("Expected a NumPy array of shape (T, N, 3)")
        if self.positions is None or vectors.shape[1] != self.positions.shape[0]:
            raise ValueError("Mismatch: vector count does not match number of grid positions")

        self.update_grid_params(grid_params)
        self.vectors = vectors
        self.set_time_range(tstart, tend)

        self.update_plot()

    def set_time_range(self, tstart, tend):
        self.vector_times = self.times
        self.num_timepoints = len(self.vector_times)
        self.time_slider.setMaximum(self.num_timepoints - 1)
        self.set_current_time(self.current_time)

    def reset_view(self):
        try:
            self.plotter.camera.focal_point = self.params['focal_point']
            self.plotter.camera.position = self.params['position']
            self.plotter.camera.up = self.params['up']
        except Exception as e:
            print("Failed to reset view to preset camera:", e)
        self._camera_locked = True
        self.update_plot()

    def update_plot(self):
        cmap_map = {'magZ':['bwr','seismic','RdBu'],'magXY':['gray','viridis','inferno'],
                    'phaseXY':['hsv','jet','twilight'],'combXY':['hsv','jet','twilight']}
        mode_keys = list(cmap_map.keys())
        mode = mode_keys[self.params['color_mode']]
        cmap_name = cmap_map[mode][self.params['cmap']]
        show_vectors = ['Show all','Show XY only','Show Z only','Show none'][self.params['show_vectors']]
        show_shadows = self.params['show_shadows']
        show_locations = self.params['show_locations']
        arrow_size = self.params['arrow_size']/100.0

        if self.positions is None or self.num_vectors == 0 or self.vectors is None:
            return
        if self.positions_all is not None:
            self.positions = self.positions_all[self.current_index,:,:]
        raw_vectors = self.vectors[self.current_index]
        # 1) Compute unit + scaled vectors (prevent division by zero)
        norms = np.linalg.norm(raw_vectors, axis=1, keepdims=True)
        norms[norms == 0] = arrow_size
        unit_vectors = raw_vectors / norms
        scaled_vectors = unit_vectors * norms
        shadow_dirs = scaled_vectors.copy()

        main_pd = pv.PolyData(self.positions)
        main_pd["magXY"]   = np.linalg.norm(unit_vectors[:, :2], axis=1)
        phase = np.mod(np.arctan2(unit_vectors[:,1], unit_vectors[:,0]) + 3*np.pi, 2*np.pi)
        main_pd["phaseXY"]   = phase/np.pi - 1.0
        main_pd["magZ"]   = unit_vectors[:, 2] 
        if show_vectors=='Show all':
            main_pd["vectors"] = scaled_vectors
        elif show_vectors=='Show XY only':
            scaled_vectors[:,2] = 0
            main_pd["vectors"] = scaled_vectors
        elif show_vectors=='Show Z only':
            scaled_vectors[:,:2] = 0
            main_pd["vectors"] = scaled_vectors

        if mode == 'combXY':
            cmap = cm.get_cmap("bwr")
            rgb = (cmap(main_pd["phaseXY"])[:, :3]*255).astype(np.uint8)
            rgba = np.empty((self.positions.shape[0], 4), dtype=np.uint8)
            rgba[:, :3] = rgb
            rgba[:, 3]  = (main_pd["magXY"] * 255).astype(np.uint8)
            main_pd["combXY"]    = rgba
            _rgb = True
        else:
            _rgb = False
            
        main_pd.set_active_scalars(mode)
        
        # 2) MAIN ARROWS
        if not show_vectors=='Show none':        
            main_glyphs = main_pd.glyph(
                orient="vectors",
                scale="vectors",
                factor=arrow_size
            )
            
            main_glyphs.set_active_scalars(mode)
            
            if self.arrow_actor is None:
                self.arrow_actor = self.plotter.add_mesh(
                    main_glyphs,
                    scalars=mode,
                    clim=[-1, 1],
                    rgb=_rgb,
                    name="arrow_actor",
                    pickable=False,
                    show_scalar_bar=False
                )
            else:
                self.arrow_actor.mapper.dataset.deep_copy(main_glyphs)
 
            lut = pv.LookupTable(cmap_name)
            mapper = self.arrow_actor.mapper
            mapper.SetLookupTable(lut)
            sc_min, sc_max = mapper.GetScalarRange()
            mapper.SetScalarRange(sc_min, sc_max)
            self.arrow_actor.SetVisibility(True)
        else:
            if self.arrow_actor:
                self.arrow_actor.SetVisibility(False)

        plane_z = np.min(self.positions[:,2])-1
        plane_size = 5 * np.ptp(self.positions[:,0])        
        if show_shadows:
            shadow_positions = self.positions.copy()
            shadow_positions[:, 2] = plane_z
            shadow_dirs[:, 2] = 0.0
            shadow_pd = pv.PolyData(shadow_positions)
            shadow_pd["vectors"] = shadow_dirs
            shadow_glyphs = shadow_pd.glyph(orient="vectors",
                                            scale="vectors",
                                            factor=arrow_size)
            if self.shadow_actor is None:
                self.shadow_actor = self.plotter.add_mesh(
                    shadow_glyphs,
                    color="gray",
                    name="shadow_actor",
                    pickable=False,
                    show_scalar_bar=False
                )
            else:
                self.shadow_actor.mapper.dataset.deep_copy(shadow_glyphs)
            self.shadow_actor.SetVisibility(True)
        else:
            if self.shadow_actor is not None:
                self.shadow_actor.SetVisibility(False)

        if show_locations:
            if self.location_actor is None:
                self.location_actor = self.plotter.add_points(
                    self.positions,
                    color="red",
                    point_size=3,
                    render_points_as_spheres=False,
                    name="location_actor"
                )
            self.location_actor.SetVisibility(True)
        else:
            if self.location_actor is not None:
                self.location_actor.SetVisibility(False)

        plane_center = (np.mean(self.positions[:,0]), np.mean(self.positions[:,1]), plane_z)
        plane = pv.Plane(center=plane_center,
                         direction=(0, 0, 1),
                         i_size=plane_size,
                         j_size=plane_size)
        if show_locations:
            if self.plane_actor is None:
                self.plane_actor = self.plotter.add_mesh(
                    plane,
                    color="#F5DEB3",
                    opacity=0.5,
                    name="plane_actor",
                    pickable=False,
                    show_scalar_bar=False
                )
            else:
                self.plane_actor.mapper.dataset.deep_copy(plane)
            self.plane_actor.SetVisibility(True)
        else:
            if self.plane_actor is not None:
                self.plane_actor.SetVisibility(False)

        if not self._camera_locked:
            try:
                self.plotter.camera.focal_point = self.params['focal_point']
                self.plotter.camera.position = self.params['position']
                self.plotter.camera.up = self.params['up']
            except Exception as e:
                print("Failed to set camera state:", e)

        self.plotter.render()

# Minimal test harness
if __name__ == '__main__':
    class SeqTest:
        def __init__(self, T=50, N=100):
            self.time=np.arange(T)
            th=np.linspace(0,2*np.pi,N)
            self.positions=np.column_stack((np.cos(th),np.sin(th),np.zeros(N)))
            self.vectors=np.stack([np.column_stack((np.cos(th+t/10),np.sin(th+t/10),np.sin(2*np.pi*t/T))) for t in range(T)])
    app=QApplication(sys.argv)
    vw=Vector3DViewer_pyvista(blochSim=SeqTest())
    vw.set_vector_data({'mx':vw.blochsim.vectors[:,:,0].T,'my':vw.blochsim.vectors[:,:,1].T,'mz':vw.blochsim.vectors[:,:,2].T, 
                        'positions':vw.blochsim.positions, 'abs_times': np.linspace(0,1,50)}, 
                       {'positions':vw.blochsim.positions,'tstart':0,'tend':1}, convert=True)
    vw.show(); sys.exit(app.exec_())
