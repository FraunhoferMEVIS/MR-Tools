import os
import json
import numpy as np
import time
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QCheckBox,
    QLineEdit, QFileDialog, QMessageBox, QComboBox, QInputDialog, QDoubleSpinBox, QStackedWidget,
    QSizePolicy, QDialog, QLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QObject, pyqtSignal

from mrlabContext import mrlabContext, Status
import mrlab_utils as utils

# ----------- SettingsDialog class: holds sliders and save preset button -------------

class SettingsDialog(QDialog):
    def __init__(self, initial_grid_params, presets, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.grid_params = initial_grid_params.copy()
        self.presets = presets

        self.sliders = {}

        main_layout = QVBoxLayout()
        self.phantom_checkbox = QCheckBox("Use current phantom")
        self.phantom_checkbox.toggled.connect(self._usePhantom)
        main_layout.addWidget(self.phantom_checkbox)
        
        # T1/T2 & Relaxation toggle
        relax_layout = QHBoxLayout()
        self.t1_spin = QDoubleSpinBox()
        self.t1_spin.setRange(0.0, 10.0)
        self.t1_spin.setSingleStep(0.1)
        self.t1_spin.setValue(self.grid_params.get('T1', 1.5))
        self.t2_spin = QDoubleSpinBox()
        self.t2_spin.setRange(0.0, 10.0)
        self.t2_spin.setSingleStep(0.1)
        self.t2_spin.setValue(self.grid_params.get('T2', 0.4))
        self.relax_checkbox = QCheckBox("Disable Relaxation")
        self.relax_checkbox.setChecked(False)

        relax_layout.addWidget(QLabel("T1 [s]:"))
        relax_layout.addWidget(self.t1_spin)
        relax_layout.addWidget(QLabel("T2 [s]:"))
        relax_layout.addWidget(self.t2_spin)
        relax_layout.addWidget(self.relax_checkbox)
        main_layout.addLayout(relax_layout)

        self.phantom_checkbox.setChecked(False)

        # Helper to create slider rows
        def create_slider_row(labels, params, is_float=False, scale=1.0):
            layout = QHBoxLayout()
            for label, param in zip(labels, params):
                vbox = QVBoxLayout()
                val = self.grid_params.get(param, 0)
                lbl = QLabel(f"{label}: {val:.2f}" if is_float else f"{label}: {int(val)}")
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(int(-10*scale) if 'Center' in label else 1)
                slider.setMaximum(int(10 * scale) if is_float else 300)
                slider.setSingleStep(max(1,int(scale/100)))
                slider.setPageStep(max(1,int(scale/100)))
                slider.setValue(int(val * scale) if is_float else int(val))
                def on_val_change(val, l=lbl, p=param, s=scale, lab=label, is_f=is_float):
                    l.setText(f"{lab}: {val / s:.2f}" if is_f else f"{lab}: {val}")
                slider.valueChanged.connect(on_val_change)
                self.sliders[param] = (slider, scale)
                vbox.addWidget(lbl)
                vbox.addWidget(slider)
                layout.addLayout(vbox)
            return layout

        main_layout.addLayout(create_slider_row(["X Count", "Y Count", "Z Count"], ['nx', 'ny', 'nz'], scale=1.0))
        main_layout.addLayout(create_slider_row(["Size X", "Size Y", "Size Z"], ['sx', 'sy', 'sz'], scale=1.0))
        main_layout.addLayout(create_slider_row(["Center X", "Center Y", "Center Z"], ['cx', 'cy', 'cz'], is_float=True, scale=10.0))

        # Background Gradient selection
        bg_layout = QVBoxLayout()
        bg_label = QLabel("Background Field Type:")
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["None", "Gradient", "Random"])
        self.bg_combo.setCurrentIndex(0)
        self.bg_combo.currentIndexChanged.connect(self.update_background_ui)
        bg_layout.addWidget(bg_label)
        bg_layout.addWidget(self.bg_combo)

        self.gradient_stack = QStackedWidget()
        self.gradient_stack.setFixedHeight(70)

        self.none_widget = QWidget()

        # Gradient sliders
        self.gradient_widget = QWidget()
        g_layout = QHBoxLayout()
        self.grad_sliders = {}
        for label in ['X', 'Y', 'Z']:
            vbox = QVBoxLayout()
            lbl = QLabel(f"G{label}: 0.00")
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setSingleStep(1)
            slider.setPageStep(1)
            slider.setValue(0)
            slider.valueChanged.connect(lambda val, l=lbl, lab=label: l.setText(f"G{lab}: {val / 100:.2f}"))
            self.grad_sliders[label] = slider
            vbox.addWidget(lbl)
            vbox.addWidget(slider)
            g_layout.addLayout(vbox)
        self.gradient_widget.setLayout(g_layout)

        # Random noise slider
        self.random_widget = QWidget()
        r_layout = QVBoxLayout()
        self.random_slider = QSlider(Qt.Horizontal)
        self.random_slider.setMinimum(0)
        self.random_slider.setMaximum(100)
        self.random_slider.setValue(0)
        self.random_label = QLabel("Random field: 0.00")
        self.random_slider.valueChanged.connect(lambda val: self.random_label.setText(f"Random field: {val / 100:.2f}"))
        self.grad_sliders['bgRandom'] = self.random_slider
        r_layout.addWidget(self.random_label)
        r_layout.addWidget(self.random_slider)
        self.random_widget.setLayout(r_layout)

        self.gradient_stack.addWidget(self.none_widget)
        self.gradient_stack.addWidget(self.gradient_widget)
        self.gradient_stack.addWidget(self.random_widget)

        bg_layout.addWidget(self.gradient_stack)
        main_layout.addLayout(bg_layout)

        # Save preset button
        self.save_preset_btn = QPushButton("Save Preset")
        self.save_preset_btn.clicked.connect(self.save_current_preset)
        main_layout.addWidget(self.save_preset_btn)

        # OK and Cancel buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        self.update_background_ui(0)

    def update_background_ui(self, index):
        self.gradient_stack.setCurrentIndex(index)
        # for k,s in self.grad_sliders.items():
        #     s.setValue(0)
        # self.random_slider.setValue(0)

    def _usePhantom(self,_use):
        self.grid_params['usePhantom'] = _use
        self.t1_spin.setEnabled(not _use)
        self.t2_spin.setEnabled(not _use)
        # self.relax_checkbox.setEnabled(not _use)
        if _use:
            slider,scale = self.sliders['sx']
            slider.setValue(200)            
            slider,scale = self.sliders['sy']
            slider.setValue(200)            
            slider,scale = self.sliders['sz']
            slider.setValue(10)
        
    def save_current_preset(self):
        # Ask for a name
        name, ok = QInputDialog.getText(
            self,
            "Save Preset",
            "Enter name for new preset:"
        )
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

        # Refresh self.grid_params from the current UI
        self.grid_params.update(self.get_grid_params())

        # Store a copy of the full params dict
        self.presets[name] = self.grid_params.copy()

        try:
            self.presets[name].pop('positions')
        except:
            pass
        
        # Save presets file
        os.makedirs("presets", exist_ok=True)
        with open("presets/blochsim.json", "w") as f:
            json.dump(self.presets, f, indent=2)

        QMessageBox.information(
            self,
            "Preset Saved",
            f"Preset '{name}' has been saved."
        )

    def get_grid_params(self):
        # Collect all parameters from sliders and widgets into dict
        params = {}
        
        params['usePhantom'] = self.phantom_checkbox.isChecked()
        params['disableRelaxation'] = self.relax_checkbox.isChecked()
        
        # the grid sliders
        for key, (slider, scale) in self.sliders.items():
            params[key] = slider.value() / scale

        # T1/T2 (and disable‐relaxation hack)
        if self.relax_checkbox.isChecked():
            params['T1'] = 1e24
            params['T2'] = 1e23
        else:
            params['T1'] = self.t1_spin.value()
            params['T2'] = self.t2_spin.value()

        # Background type
        bg_idx = self.bg_combo.currentIndex()
        params['bgType'] = self.bg_combo.currentText()
        params['gbIdx'] = int(bg_idx)

        # Gradient vs random
        if bg_idx == 1:  # Gradient
            params['bgGradX'] = self.grad_sliders['X'].value() / 100.0
            params['bgGradY'] = self.grad_sliders['Y'].value() / 100.0
            params['bgGradZ'] = self.grad_sliders['Z'].value() / 100.0
            params['bgRandom'] = 0.0
        elif bg_idx == 2:  # Random
            params['bgGradX'] = 0.0
            params['bgGradY'] = 0.0
            params['bgGradZ'] = 0.0
            params['bgRandom'] = self.random_slider.value() / 100.0
        else:  # None
            params['bgGradX'] = params['bgGradY'] = params['bgGradZ'] = 0.0
            params['bgRandom'] = 0.0

        return params

    def set_grid_params(self, params):
        # Set sliders and widgets from params dict
        self.phantom_checkbox.setChecked(params.get('usePhantom',False))
        for key, val in params.items():
            if key in self.sliders:
                slider, scale = self.sliders[key]
                slider.setValue(int(val * scale))
        self.t1_spin.setValue(params.get('T1', 1.5))
        self.t2_spin.setValue(params.get('T2', 0.4))
        self.relax_checkbox.setChecked(params.get('usePhantom',False))
        # Update bg combo and sliders accordingly
        self.grad_sliders['X'].setValue(int(params.get('bgGradX', 0)*100))
        self.grad_sliders['Y'].setValue(int(params.get('bgGradY', 0)*100))
        self.grad_sliders['Z'].setValue(int(params.get('bgGradZ', 0)*100))
        self.random_slider.setValue(int(params.get('bgRandom', 0)*100))
        self.bg_combo.setCurrentIndex(params.get('gbIdx',0)) 

# ----------- Modified BlochSimulation widget -------------

class BlochSimulation(QWidget):
    blochSim_finished = pyqtSignal(dict,dict)
    settingsChanged = pyqtSignal(dict)

    def __init__(self,*args, **kwargs):
        super(BlochSimulation, self).__init__()
        self.mrCtx = mrlabContext()      
        self.mrCtx.getSequence(seqname=kwargs.get('seqname'))
        if kwargs.get('autoUpdate',True):
            self.mrCtx.sequenceUpdated.connect(self.simulate)
        self.thread = None
        self.threadingOn = False
        self.time_simFinished = time.time()

        self.width = kwargs.get('width',(11,11,1))
        self.size  = kwargs.get('size',(1.5,1.5,.1))
        self.T1 = kwargs.get('T1',1.500)
        self.T2 = kwargs.get('T2',1.000)
        self.bgField = kwargs.get('bgField',None)
        self.use_gpu = kwargs.get('use_gpu',False)
        self.tstart = -1
        self.tend = -1
        self.full_data = {}

        # Initial grid parameters
        self.grid_params = {
            'nx': 11, 'ny': 11, 'nz': 1,
            'sx': 10, 'sy': 10, 'sz': 10,
            'cx': 0.0, 'cy': 0.0, 'cz': 0.0,
            'T1': self.T1,
            'T2': self.T2,
            'bgGradX': 0.0, 'bgGradY': 0.0, 'bgGradZ': 0.0,
            'bgRandom': 0, 'bgField':None,
            'usePhantom':False,
        }
        self.settingsChanged.connect(self.check4Update)
        self.mrCtx.phantomChanged.connect(self.update_grid_from_phantom)
        self.mrCtx.toolPresetChanged.connect(self.update_preset)

        self.presets_file = "presets/blochsim.json"
        self.presets = self.load_presets()

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Controls layout with only preset dropdown, update button, autoupdate, settings button
        control_layout = QHBoxLayout()

        self.preset_dropdown = QComboBox()
        self.preset_dropdown.addItems(list(self.presets.keys()))
        self.preset_dropdown.currentIndexChanged.connect(self.select_preset)

        self.update_btn = QPushButton("Update")
        self.update_btn.clicked.connect(lambda: self.simulate())

        self.autoUpdate = QCheckBox("AutoUpdate")
        self.autoUpdate.setChecked(True)
        self.autoUpdate.toggled.connect(self.set_autoUpdate)

        self.settings_btn = QPushButton("Settings...")
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        control_layout.addWidget(QLabel("Presets:"))
        control_layout.addWidget(self.preset_dropdown)
        control_layout.addWidget(self.settings_btn)
        control_layout.addStretch(3)
        control_layout.addWidget(self.update_btn)
        control_layout.addWidget(self.autoUpdate)

        main_layout.addLayout(control_layout)
        main_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.setMaximumHeight(50)

        self.setLayout(main_layout)
        self.setStatus(Status.IDLE)

    def open_settings_dialog(self):
        dlg = SettingsDialog(initial_grid_params=self.grid_params, presets=self.presets, parent=self)
        dlg.set_grid_params(self.grid_params)
        if dlg.exec_() == QDialog.Accepted:
            new_params = dlg.get_grid_params()
            self.grid_params.update(new_params)
            # Optionally update preset dropdown if presets changed
            self.presets = dlg.presets
            self.update_preset_dropdown()
            self.update_grid_params(signal=True)
        else:
            # Cancel pressed, do nothing
            pass

    def update_preset_dropdown(self):
        self.preset_dropdown.blockSignals(True)
        self.preset_dropdown.clear()
        self.preset_dropdown.addItems(list(self.presets.keys()))
        self.preset_dropdown.blockSignals(False)

    def setStatus(self,status,_timer_in_s=-1):
        self.mrCtx.setSubtaskStatus('blochSim',status)
        self.status = status
        color = status.get('color','lightgrey')
        self.update_btn.setStyleSheet(f"background-color: {color}")
        self.update_btn.repaint()
        self.setEnabled(not status.get('blockUI',False))

    def set_autoUpdate(self,check):
        if check:
            self.mrCtx.sequenceUpdated.connect(self.simulate)
        else:
            self.mrCtx.sequenceUpdated.disconnect(self.simulate)

    def update_preset(self,preset="",name="BlochSim"):
        print('update_preset:',name,preset)
        if name == "BlochSim":
            params = self.presets.get(preset)
            if params:
                idx = self.preset_dropdown.findText(preset)
                if idx >= 0:
                    self.preset_dropdown.setCurrentIndex(idx)
                # Update grid params and emit
                self.grid_params.update(params)
                self.update_grid_params(signal=True) 
            else:
                print(preset,'is not a known preset for blochsim')
                print('available presets:', self.presets.keys())
               
    def load_presets(self):
        if os.path.exists(self.presets_file):
            with open(self.presets_file, "r") as f:
                return json.load(f)
        return {}

    def save_presets(self):
        with open(self.presets_file, "w") as f:
            json.dump(self.presets, f, indent=2)

    def select_preset(self, index):
        if index < 0:
            return
        preset = self.preset_dropdown.itemText(index)
        params = self.presets.get(preset)
        if params:
            idx = self.preset_dropdown.findText(preset)
            if idx >= 0:
                self.preset_dropdown.setCurrentIndex(idx)
            # Update grid params and emit
            self.grid_params.update(params)
            self.update_grid_params(signal=True) 
        else:
            print(preset,'is not a known preset for blochsim')
            print('available presets:', self.presets.keys())

    def update_grid_from_phantom(self,phantomName=None):
        print('updating grid from current phantom',phantomName)
        phantom = self.mrCtx.getBuiltPhantom((self.grid_params.get('nx',10),self.grid_params.get('ny',10),self.grid_params.get('nz',1)),
                                              slices = list(range(self.grid_params.get('nz',1))))
        self.pos3d = np.array(phantom.voxel_pos).T

        if hasattr(phantom, 'voxel_flow'):
            # expect phantom.voxel_flow shape (3, N_voxels)
            self.flow3d = np.array(phantom.voxel_flow)
            # store in params for simulateBloch
            self.grid_params['flow'] = self.flow3d
        else:
            self.flow3d = None
            
            
    def update_grid_params(self,_dummy=None, signal=True, check4autoupdate=False):
        # This function can update the internal grid_params from sliders/settings

        # If sliders were removed from main widget, just use grid_params dict
        # Validate counts are int:
        for k in ['nx','ny','nz']:
            if k in self.grid_params:
                self.grid_params[k] = int(round(self.grid_params[k]))

        nx, ny, nz = self.grid_params.get('nx', 11), self.grid_params.get('ny', 11), self.grid_params.get('nz', 1)
        sx, sy, sz = self.grid_params.get('sx', 10), self.grid_params.get('sy', 10), self.grid_params.get('sz', 10)
        cx, cy, cz = self.grid_params.get('cx', 0.0), self.grid_params.get('cy', 0.0), self.grid_params.get('cz', 0.0)

        x = np.linspace(cx-sx/2.0, cx+sx/2.0, nx) if nx > 1 else [0]
        y = np.linspace(cy-sy/2.0, cy+sy/2.0, ny) if ny > 1 else [0]
        z = np.linspace(cz-sz/2.0, cz+sz/2.0, nz) if nz > 1 else [0]

        p = np.array(np.meshgrid(x, y, z, indexing='ij'))
        print('use phantom',self.grid_params.get('usePhantom'))
        if not self.grid_params.get('usePhantom',False):
            self.flow3d = np.zeros_like(p)
            # self.flow3d[2,0,0,:]=0.1 # m/s
            self.flow3d = self.flow3d.reshape(3,-1).T
            self.pos3d = p.reshape(3, -1)
            if self.grid_params.get('disableRelaxation', False):
                self.T1 = 1e24
                self.T2 = 1e23
            else:
                self.T1 = self.grid_params.get('T1', 1.5)
                self.T2 = self.grid_params.get('T2', 0.4)
                self.bgField = None

        else:
            phantom = self.mrCtx.getBuiltPhantom((self.grid_params.get('nx',10),self.grid_params.get('ny',10),self.grid_params.get('nz',1)))
            self.pos3d = np.array(phantom.voxel_pos*1000).T
            if hasattr(phantom, 'voxel_flow'):
                # expect phantom.voxel_flow shape (3, N_voxels)
                self.flow3d = np.array(phantom.voxel_flow)
            else:
                self.flow3d = None
                
            # store in params for simulateBloch
            if self.grid_params.get('disableRelaxation', False):
                print('relaxation switched off')
                self.grid_params['T1map'] = 1e24
                self.grid_params['T2map'] = 1e23
            else:
                self.grid_params['T1map'] = np.array(phantom.T1).T
                self.grid_params['T2map'] = np.array(phantom.T2).T
            self.bgField = np.array(phantom.B0).T
        self.posShape = list(self.pos3d.shape)
        if nx*ny*nz>1.5e5:
            QMessageBox.warning(self, "Warning", "Overall number of vectors is too high!\n Reduce to not more than 100,000 spins.")
            self.grid_params['nz']=1
            
        if check4autoupdate:
            if nx*ny*nz>2000:
                self.autoUpdate.setCheckState(False)
            else:
                self.autoUpdate.setCheckState(True)

        self.grid_params.update({
            'T1': self.T1,
            'T2': self.T2,
            'positions': self.pos3d.T,
            'bgField': self.bgField,
            'flow': self.flow3d
            
        })

        if signal:
            self.settingsChanged.emit(self.grid_params)

    def set_time_range(self,tstart,tend):
        tstart = max(0,tstart)
        tend = max(tend,tstart+1e-6)
        self.tstart,self.tend = tstart,tend
        if self.status!=Status.RUNNING and self.autoUpdate.isChecked():
            self.simulate()
        else:
            self.setStatus(Status.UPDATE_REQUIRED)
    
    def check4Update(self,e=None):
        if self.autoUpdate.isChecked():
            self.simulate()
        else:
            self.setStatus(Status.UPDATE_REQUIRED)
            
    
    def simulate(self,_seq_state=None):
        if not self.thread and self.status!=Status.RUNNING:
            if self.mrCtx.getSequence().getDuration():
                self.update_grid_params(signal=False)
                full_data = self.mrCtx.getPlotData()
                self.start = time.time()
                if self.threadingOn:
                    self.thread = threading.Thread(target=self._simulateBloch, args=(full_data, self.grid_params, self.use_gpu))
                    self.thread.start()
                else:
                    self._simulateBloch(full_data, self.grid_params, self.use_gpu)

    def _simulateBloch(self,full_data, params, use_gpu = False, abort_flag=None):
        self.setStatus(Status.RUNNING)
        if self.tstart==-1 or self.tend==-1:
            self.tstart = 0
            self.tend = self.mrCtx.getSequence().getDuration()
            
        start = time.time()
        bgGrads = (self.grid_params.get('bgGradX',0),self.grid_params.get('bgGradY',0),self.grid_params.get('bgGradZ',0))
        print('time since last bloch simulation', time.time() - self.time_simFinished,'s')
        if not (time.time() - self.time_simFinished)<1:
            try:
                if params.get('usePhantom',False):
                    _T1 = params.get('T1map',1.5)
                    _T2 = params.get('T2map',0.4)
                else:
                    _T1 = params.get('T1',1.5)
                    _T2 = params.get('T2',0.4)
                full_data_out = simulateBloch(full_data,self.pos3d,self.posShape, _T1, _T2,
                              bgGrads=bgGrads, times4display=(self.tstart,self.tend),use_gpu=use_gpu,regularSampling=True,
                              bgRandom=params.get('bgRandom',0)*100,bgField=params.get('bgField',None),
                              flow=params.get('flow'),samples=3000)
                self.full_data = full_data_out
                self.setStatus(Status.FINISHED_OK)
            except Exception as e:
                print('error occured in _simulateBloch')
                print(e)
                self.setStatus(Status.STOPPED_ERROR)
        else:
            self.setStatus(Status.FINISHED_OK)

        self.thread = None
        self.tstart = full_data.get('t',[self.tstart])[0] 
        self.tend = full_data.get('t',[self.tend])[-1] 
        self.grid_params.update(dict(tstart=self.tstart,tend=self.tend))
        self.time_simFinished = time.time()
        end = time.time()
        print(f"total simulation time: {end - start:.6f} seconds")
        self.blochSim_finished.emit(self.full_data,self.grid_params)

     
from typing import Dict, Tuple, Any
from gpu_bloch import bloch_simulation

# -----------------------------------------------------------------------------
# Haupt‑API -------------------------------------------------------------------
# -----------------------------------------------------------------------------

def simulateBloch(full_data: Dict[str, Any],
                  pos3d: np.ndarray,          # shape (3, N)
                  pos_shape: Tuple[int, int, int] | None,
                  T1: float | np.ndarray = 1.500,
                  T2: float | np.ndarray = 0.100,
                  bgGrads: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                  times4display: Tuple[float, float] = (0, 0.01),
                  use_gpu: bool = False,
                  regularSampling: bool = True,
                  bgRandom: float = 0.0,
                  bgField: float | None = None,
                  flow: np.ndarray | None = None,
                  samples: int = 1000) -> Dict[str, Any]:
    """Wrapper um *bloch_simulation*.

    Parameters
    ----------
    full_data : Sequenz‑Dictionary, siehe Modul‑Docstring.
    pos3d     : (3,N) – Spin‑Positionen in **mm**.
    pos_shape : Voxel‑Form (nx,ny,nz) – für spätere Grid‑Interpolation.
    bgGrads   : konstante Hintergrund‑Gradienten in T/m.
    flow      : (3,N) – Flow‑Vektor pro Spin (m/s).  Wenn *None*, wird nach
                 `full_data['flow']` gesucht.
    """

    # 1) Build unique, sorted time axis
    t_list = []
    for key in ('rf','grx','gry','grz'):
        t_list.extend(full_data.get(key, {}).get('t', []))

    if len(t_list) <= 2:
        print("No time points defined in sequence data.")
        return 
    
    # 5) Build sampling indices
    if regularSampling and len(t_list)>2:
        samp_times = np.linspace(times4display[0], times4display[1], num=samples)
        t_list.extend(samp_times)
        ta = np.unique(np.array(t_list, dtype=float))
        ta.sort()
        # find nearest indices
        sampling_idx = np.searchsorted(ta, samp_times)
        sampling_idx = np.clip(sampling_idx, 0, len(ta)-1)
    else:
        ta = np.unique(np.array(t_list, dtype=float))
        ta.sort()
        sampling_idx = list(range(len(ta)))

    if ta.size == 0:
        print("No time points defined in sequence data.")
        return 
    # 2) Interpolate RF
    rf_t = full_data.get('rf', {})
    if rf_t.get('t') and rf_t.get('v'):
        b1 = np.interp(ta, rf_t['t'], rf_t['v'], left=0.0, right=0.0)
    else:
        b1 = np.zeros_like(ta)
    # scale to mT
    b1 = b1 * 1e-7 * 53/225

    # 3) Interpolate gradients or zero if missing
    def interp_or_zero(key):
        entry = full_data.get(key, {})
        if entry.get('t') and entry.get('v'):
            arr = np.interp(ta, entry['t'], entry['v'], left=0.0, right=0.0)
        else:
            arr = np.zeros_like(ta)
        return arr

    grx = interp_or_zero('grx')*1e-6 + bgGrads[0]*1e-5
    gry = interp_or_zero('gry')*1e-6 + bgGrads[1]*1e-5
    grz = interp_or_zero('grz')*1e-6 + bgGrads[2]*1e-5

    # 4) Off-resonance map
    N = pos3d.shape[1]
    if bgField is None:
        df = (2*np.random.rand(N)-1) * bgRandom
    else:
        df = bgField + (2*np.random.rand(N)-1) * bgRandom

    # ---------------------------------------------------------------------
    # Zeit‑Schritt‑Vektor dt & Sampling‑Indizes ----------------------------
    # ---------------------------------------------------------------------
    dt = np.diff(ta, prepend=ta[0])
    dt[0] = 1e-9  # winziger Dummy‑Schritt am Anfang, falls ta[0]==0


    # ---------------------------------------------------------------------
    # Initial‑Magnetisierung ----------------------------------------------
    # ---------------------------------------------------------------------
    Nspins = pos3d.shape[1]
    mx0 = np.zeros(Nspins, dtype=np.float32)
    my0 = np.zeros(Nspins, dtype=np.float32)
    mz0 = np.ones (Nspins, dtype=np.float32)

    # Flow in m/s?  Wir erwarten pos in **mm** → umgerechnet in m im Low‑Level.
    if flow is not None and flow.shape != pos3d.T.shape:
        raise ValueError("flow shape mismatch: expected (N,3)")
    if flow is not None:
        flow_mps = flow.astype(np.float32)
    else:
        flow_mps = None

    # ---------------------------------------------------------------------
    # Bloch‑Kern‑Aufruf ----------------------------------------------------
    # ---------------------------------------------------------------------
    start = time.perf_counter()
    mx, my, mz, pos = bloch_simulation(b1, np.vstack((grx,gry,grz)), dt,
                                  T1=T1, T2=T2, df=df,
                                  pos3d=pos3d,
                                  mode=2,
                                  mx0=mx0, my0=my0, mz0=mz0,
                                  sampling_idx=sampling_idx,
                                  flow=flow_mps, t_abs=None,
                                  use_gpu=use_gpu)
    dur = time.perf_counter() - start
    print(f"Bloch‑Simulation: {dur*1e3:.1f} ms  ({'GPU' if use_gpu else 'CPU'})")

    # ---------------------------------------------------------------------
    # Post‑Processing ------------------------------------------------------
    # ---------------------------------------------------------------------
    mxy = mx + 1j*my  # (N, Nt_samp)
    mean_mxy = mxy.mean(axis=0)
    full_data_out = dict(full_data)  # shallow copy OK
    full_data_out['positions'] = pos
    full_data_out['mx'] = mx
    full_data_out['my'] = my
    full_data_out['mz'] = mz
    full_data_out['t']  = ta[sampling_idx]
    full_data_out['signal_amp'] = {'t': ta[sampling_idx], 'v': np.abs(mean_mxy)}
    full_data_out['signal_phs'] = {'t': ta[sampling_idx], 'v': np.angle(mean_mxy)}

    mzm = mz[int(mz.shape[0]/2)]
    full_data_out['magZ'] = {'t':ta[sampling_idx],'v':np.transpose(mzm)}
        
    from scipy.interpolate import RegularGridInterpolator
    from matplotlib.colors import hsv_to_rgb

    # Reshape to 2D: (voxels, time)
    mxy_2d = mxy.reshape(-1, mxy.shape[-1]) 
    mz_2d = mz.reshape(-1, mz.shape[-1]) 
    
    # Voxel index (spatial dimension)
    y = np.arange(mxy_2d.shape[0])  # shape: (voxels,)
    t = ta[sampling_idx]  # sampling time axis

    if mxy_2d.shape[0] < 1025:
    
        t_interp = np.linspace(*times4display, samples)  # new time samples
        yy, tt = np.meshgrid(y, t_interp, indexing='ij')
        points = np.stack((yy.ravel(), tt.ravel()), axis=-1)  # shape: (voxels * time, 2)
    
        # Create interpolators
        fabs_interp = RegularGridInterpolator((y, t), np.abs(mxy_2d), bounds_error=False, fill_value=0)
        farg_interp = RegularGridInterpolator((y, t), np.angle(mxy_2d), bounds_error=False, fill_value=0)
        fz_interp   = RegularGridInterpolator((y, t), mz_2d,           bounds_error=False, fill_value=0)
    
        # Evaluate on interpolation grid
        fabs_img = fabs_interp(points).reshape(len(y), len(t_interp))
        farg_img = farg_interp(points).reshape(len(y), len(t_interp))
        fz_img   = fz_interp(points).reshape(len(y), len(t_interp))
    
        full_data_out['fabs'] = {'t': t_interp, 'v': fabs_img}
        full_data_out['farg'] = {'t': t_interp, 'v': farg_img}
        full_data_out['fz']   = {'t': t_interp, 'v': fz_img}    

        # Compute phase and magnitude
        phase = full_data_out['farg']['v']        # range [-π, π]
        magnitude = full_data_out['fabs']['v']
        
        hue = (phase + np.pi) / (2 * np.pi)
        if magnitude.max():
            norm_mag = (magnitude / magnitude.max())
        else:
            norm_mag = magnitude*0

        # norm_mag = np.log1p(magnitude)
        # norm_mag /= norm_mag.max()
        value = np.ones_like(norm_mag) 
        saturation = norm_mag
        hsv = np.stack((hue, saturation, value), axis=-1)
        full_data_out['mxy'] = {'t': t_interp, 'v': hsv_to_rgb(hsv)}
        
    return full_data_out

from Plot import Plot
try:
    from Vector3DViewer_pyvista import Vector3DViewer_pyvista as Vector3DViewer
except:
    from Vector3DViewer import Vector3DViewer
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Combined Plot + Blochsimulator")
        self.resize(1400, 800)
        seqname='SPAMM'
        self.blochsim = BlochSimulation()  # your 3D vector viewer
        self.plot = Plot(seqname=seqname,showGUI=True,blochSim=self.blochsim)  # imported widget
        self.viewer3D = Vector3DViewer(parent=self,blochSim=self.blochsim)  # imported widget
        self.plot.set_viewer(self.viewer3D)
        self.plot.timesChanged.connect(self.blochsim.set_time_range)
        
        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left column: plot fills all vertical space
        left_layout = QVBoxLayout()
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.plot)
        main_layout.addLayout(left_layout, 1)  # Optional stretch factor

        # Right column: view3d on top, blochsim on bottom (fixed height)
        right_layout = QVBoxLayout()
        self.viewer3D.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.blochsim.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        right_layout.addWidget(self.viewer3D)
        right_layout.addWidget(self.blochsim)

        main_layout.addLayout(right_layout, 1)  # Equal column widths (adjust as needed)

        self.setLayout(main_layout)
        
        
import sys
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
