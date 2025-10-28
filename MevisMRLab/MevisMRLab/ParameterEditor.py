# -*- coding: utf-8 -*-
"""
Created on Mon Jun  9 09:09:33 2025

author: mguenther
"""

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QPushButton, QSlider, QTabWidget, QGroupBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QSplitter
)
from PyQt5.QtCore import Qt
import sys
import mrlab_utils as utils

from Plot import Plot
from mrlabContext import mrlabContext

class ParameterEditor(QWidget):
    """
    Edit parameters in metric units; conversions to/from pulseq units
    are handled by mrCtx.convertUnitsToMetric/Pulseq on full dicts.

    Adds an expression field for each parameter: a formula string that
    will be multiplied by the numeric value (shown in spinbox/slider).
    """
    def __init__(self, parameter_dict, value_dict=None, mrCtx=None, elem=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parameter Editor")
        self.mrCtx = mrCtx or mrlabContext()
        self.parameter_dict = parameter_dict or {}
        self.elem = elem or {}

        # initialize pulseq values
        if value_dict is None:
            self.value_dict = {k: self.parameter_dict[k].get('pulseq_value', 0.0)
                               for k in self.parameter_dict}
        else:
            self.value_dict = value_dict.copy()
        self.original_values = self.value_dict.copy()

        self.original_name = self.elem.get('name', '')
        self.widgets = {}
        self.sliders = {}
        self.expr_fields = {}
        self.modified = False

        # Layout setup
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Tabs
        tabs = QTabWidget()
        splitter.addWidget(tabs)

        # Parameters tab
        param_tab = QWidget()
        param_layout = QVBoxLayout(param_tab)
        param_box = QGroupBox("Parameters")
        param_form = QFormLayout(param_box)

        # Buttons
        btn_apply = QPushButton("Apply")
        btn_reset = QPushButton("Reset")
        btn_defaults = QPushButton("Defaults")
        btn_apply.clicked.connect(self.apply)
        btn_reset.clicked.connect(self.reset)
        btn_defaults.clicked.connect(self.set_defaults)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_defaults)

        # Compute metric values dict
        metric_values = self.mrCtx.convertUnitsToMetric(self.value_dict)

        # Build parameter rows
        for key, meta in self.parameter_dict.items():
            desc    = meta.get('description', '')
            ui_unit = meta.get('unit', '')
            ui_min  = meta.get('min', 0.0)
            ui_max  = meta.get('max', 1e9)
            step    = meta.get('step', 1.0)

            # metric numeric value
            ui_val = metric_values.get(key, 0.0)

            # expression field
            expr_edit = QLineEdit()
            expr_edit.setPlaceholderText("expr")
            expr_edit.setToolTip(f"Formula for {key}: will be multiplied by numeric value")
            expr_edit.textChanged.connect(self._mark_modified)
            self.expr_fields[key] = expr_edit

            # numeric widget
            if meta.get('type') == 'int':
                widget = QSpinBox()
                widget.setRange(int(ui_min), int(ui_max))
                widget.setSingleStep(int(step))
            else:
                widget = QDoubleSpinBox()
                widget.setRange(ui_min, ui_max)
                widget.setSingleStep(step)
                widget.setDecimals(4)
            widget.setToolTip(f"{desc} [{ui_unit}]")
            if isinstance(ui_val,str):
                widget.setValue(eval(ui_val.split('*')[-1]))
            else:
                widget.setValue(ui_val)

            widget.valueChanged.connect(self._mark_modified)

            # slider setup
            slider = QSlider(Qt.Horizontal)
            if ui_unit == 'deg':
                slider.setRange(0, 360)
                slider.setSingleStep(45)
                slider.setPageStep(45)
                slider.setTickInterval(45)
                slider.setTickPosition(QSlider.TicksBelow)
                def make_deg_sync(slider_ref, widget_ref):
                    def on_slide(raw_v):
                        quant = round(raw_v / 45) * 45
                        slider_ref.blockSignals(True)
                        slider_ref.setValue(quant)
                        slider_ref.blockSignals(False)
                        widget_ref.blockSignals(True)
                        widget_ref.setValue(quant)
                        widget_ref.blockSignals(False)
                    return on_slide
                slider.valueChanged.connect(make_deg_sync(slider, widget))
            else:
                slider.setRange(int(ui_min), int(ui_max))
                _step = int(min(int(int((ui_max-ui_min)/100)*10)/10,step))
                slider.setSingleStep(_step)
                slider.setPageStep(_step)
                slider.setTickInterval(_step)
                slider.valueChanged.connect(
                    lambda v, w=widget: w.blockSignals(True) or w.setValue(int(v/10)*10) or w.blockSignals(False)
                )
            widget.valueChanged.connect(
                lambda v, s=slider: s.blockSignals(True) or s.setValue(int(v/10)*10) or s.blockSignals(False)
            )

            self.widgets[key] = widget
            self.sliders[key] = slider

            # layout row: expr * widget + slider
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0,0,0,0)
            h.addWidget(expr_edit)
            h.addWidget(QLabel("*"))
            h.addWidget(widget)
            h.addWidget(slider)
            param_form.addRow(f"{key} [{ui_unit}]:", row)

        param_layout.addWidget(param_box)
        param_layout.addLayout(btn_layout)
        tabs.addTab(param_tab, "Parameters")

        # Info tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_box = QGroupBox("Info")
        info_form = QFormLayout(info_box)
        self.name_edit = QLineEdit(self.original_name)
        self.name_edit.textChanged.connect(self._mark_modified)
        info_form.addRow("Name:", self.name_edit)
        for label, val in (self.elem or {}).items():
            if not isinstance(val, dict):
                info_form.addRow(f"{label}:", QLabel(str(val)))
        info_layout.addWidget(info_box)
        tabs.addTab(info_tab, "Info")

        # Plot area
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0,0,0,0)
        self.plot = Plot(visMode='condensed', showModules=False,
                         showGUI=False, width=5, height=4,
                         autoUpdate=False, noContext=True)
        plot_layout.addWidget(self.plot)
        splitter.addWidget(plot_container)
        splitter.setSizes([300,400])

        # initial reset
        self.reset()

    def _mark_modified(self):
        self.modified = True

    def apply(self):
        # store name
        self.original_name = self.name_edit.text()
        # numeric metrics
        metric_dict = {k: w.value() for k,w in self.widgets.items()}
        # convert metrics back to pulseq
        self.value_dict.update(self.mrCtx.convertUnitsToPulseq(metric_dict))
        # attach formulas (strip braces if present)
        for k, expr in self.expr_fields.items():
            raw = expr.text().strip()
            if raw:
                s = raw.lstrip('{').rstrip('}')
                self.value_dict[k] = f"{s} * {self.value_dict[k]}"
        self.original_values = self.value_dict.copy()

        # update element, merging parameters into globals
        if self.elem is not None:
            self.elem['parameters'] = self.value_dict
            if 'loopLength' in self.value_dict.keys():
                self.elem.setLoopLength(self.value_dict.get('loopLength'))
            seq_globals = self.mrCtx.getCounters().copy()
            seq_globals.update(self.value_dict)
            data,_ = self.elem.create_plots_and_pulseq(_globals=seq_globals)
            self.elem['fname'] = self.mrCtx.createIcon(self.elem, data=data)
            self.elem.setDuration(utils.get_time_bounds(data)[-1])
            self.plot._update_canvas(data=data, fixRfScaling=50.0, fixGradientScaling=40.0)
        self.modified = False

    def reset(self):
        # revert name
        self.name_edit.blockSignals(True)
        self.name_edit.setText(self.original_name)
        self.name_edit.blockSignals(False)
        # revert values and formulas
        metric_values = self.mrCtx.convertUnitsToMetric(self.original_values)
        for k in self.parameter_dict:
            # reset numeric
            widget = self.widgets[k]
            v = metric_values.get(k, 0.0)
            widget.blockSignals(True)
            if isinstance(v,str):
                v = eval(v.split('*')[-1])
                widget.setValue(v)
            else:
                widget.setValue(v)
            widget.blockSignals(False)
            self.sliders[k].blockSignals(True)
            self.sliders[k].setValue(int(v))
            self.sliders[k].blockSignals(False)
            # reset formula field
            expr = self.expr_fields[k]
            orig = self.original_values.get(k)
            formula = ''
            if isinstance(orig, str) and '*' in orig:
                formula = orig.split('*',1)[0].strip()
            expr.blockSignals(True)
            expr.setText(formula)
            expr.blockSignals(False)
        # refresh display
        self.apply()

    def set_defaults(self):
        # reset all to default values (no formulas)
        for k, meta in self.parameter_dict.items():
            default = meta.get('default', 0.0)
            widget = self.widgets[k]
            widget.blockSignals(True)
            widget.setValue(default)
            widget.blockSignals(False)
            self.sliders[k].blockSignals(True)
            self.sliders[k].setValue(int(default))
            self.sliders[k].blockSignals(False)
            expr = self.expr_fields[k]
            expr.blockSignals(True)
            expr.clear()
            expr.blockSignals(False)
        self.apply()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mr = mrlabContext()
    seq = mr.getSequence()
    seq.append(mr.getElementForBpName('gradient'))
    seq.append(mr.getElementForBpName('rf_ns'))
    seq.append(mr.getElementForBpName('rf_ns'))
    seq.append(mr.getElementForBpName('loop'))
    seq.append(mr.getElementForBpName('FA090_ns'))
    w = seq.getSortedElements()[-1]
    editor = ParameterEditor(w.get('param_desc'), w.get('parameters'), mrCtx=mr, elem=w)
    editor.show()
    sys.exit(app.exec_())
