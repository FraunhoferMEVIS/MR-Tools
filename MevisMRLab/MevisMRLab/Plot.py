#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 21:52:10 2024

@author: mague
"""
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import numpy as np

import mrlab_utils as utils

from mrlabContext import mrlabContext, Status


class SeqElement(patches.Rectangle):
    def __init__(self, *args, **kwargs):
        self.elem = kwargs.pop('elem')
        super(SeqElement, self).__init__(*args, **kwargs)
        
class Draggable(object):
    """
    https://stackoverflow.com/questions/21654008/matplotlib-drag-overlapping-points-interactively
    """
    def __init__(self, artists, axes, draggable=True, tolerance=5, plot_widget=None):
        for artist in artists:
            artist.set_picker(tolerance)
        self.mrCtx = mrlabContext()
        self.artists = artists
        self.plot_widget = plot_widget
        self.currently_dragging = False
        self.current_artist = None
        self.artistClicked = None
        self.axes = axes
        self.xoffset = 0
        self.xClick = 0
        self.seq = None
        self.canvasSet = set(artist.figure.canvas for artist in self.artists)
        
        for canvas in self.canvasSet:
            canvas.mpl_connect('button_press_event', self.on_press)
            canvas.mpl_connect('button_release_event', self.on_release)
            if draggable: canvas.mpl_connect('pick_event', self.on_pick)
            canvas.mpl_connect('motion_notify_event', self.on_motion)
       
    def on_press(self, event):
        if event.button == 3:  # Right mouse button 
            if self.plot_widget:
                self.plot_widget.set_marker(event.xdata, signal=True)
            return
        self.currently_dragging = True
        self.xClick = event.xdata
        self.seq = self.mrCtx.getSequence()        

    def on_release(self, event):
        if event.button == 3:  # Right mouse button 
            if self.plot_widget:
                self.plot_widget.set_marker(event.xdata, signal=True)
            return
        if self.seq and self.current_artist:
            self.mrCtx.seqModified(self.seq)
        if event.button == 1 and not self.artistClicked:
            if self.plot_widget:
                self.plot_widget.set_times_for_viewer3d(signal=True)
        if self.artistClicked:
            self.artistClicked.set(ec='r',lw=2)
            self.artistClicked.figure.canvas.draw()

        self.currently_dragging = False
        self.current_artist = None


    def on_pick(self, event):
        self.seq = self.mrCtx.getSequence()        
        if self.current_artist is None:
            self.current_artist = event.artist
            x0 = event.artist._x0
            x1 = event.mouseevent.xdata
            self.offset = (x0 - x1)

    def on_motion(self, event):
        if not event or not self.currently_dragging:
            return
        if self.current_artist is None:
            xoffset = self.xClick-event.xdata
            curLim = self.axes[0].get_xlim()
            if curLim[0]>curLim[1]:
                curLim = curLim[::-1]
            for ax in self.axes:
                if curLim[0]+xoffset<0:
                    ax.set_xlim(0, curLim[1]+xoffset)
                else:
                    ax.set_xlim(curLim[0]+xoffset, curLim[1]+xoffset)
            for canvas in self.canvasSet:
                canvas.draw()
        else:
            dx = self.xoffset
            if event.xdata:
                self.current_artist._x0 = event.xdata + dx
            if self.current_artist._x0<0:
                self.current_artist._x0 = 0
            self.current_artist.figure.canvas.draw()
            self.seq.shiftElement(self.current_artist.elem['name'],self.current_artist._x0)
            
class Plot(QtWidgets.QWidget):
    """
    Custom Qt Widget to plot a sequence in gammaSTAR.
    """
    markerChanged = pyqtSignal(float)
    timesChanged = pyqtSignal(float,float)
    def __init__(self,*args, **kwargs):
        super(Plot, self).__init__()

        # supported keywords include:
        #  seqname
        #  path
        #  showGUI
        self.noContext = kwargs.get('noContext',False)
        if not self.noContext:
            self.mrCtx = mrlabContext()      
            self.seqname = kwargs.get('seqname',None)
            self.curSeq = self.mrCtx.getSequence(seqname=self.seqname)
            self.tempDir = self.mrCtx.tempDir
        else:
            self.tempDir = 'temp/'
            
        self.colors = dict(readout='g',rfpulse='r',preparation='b',fullsequence='orange',template='purple')
        
        self.availVisModes = {'full':    [(0,'adc','orange','x',''),(0,'rf_am','black','',''),(0,'rf',('red','green'),'',''),
                                          (1,'grx','r','',''), (2,'gry','g','',''), (3,'grz','b','','')],
                          'condensed':   [(0,'adc','orange','x',''),(0,'rf_am','black','',''),(0,'rf',('red','green'),'',''),
                                          (1,'grx','r','',''), (1,'gry','g','',''), (1,'grz','b','','')],
                          'condensed_ext':   [(0,'adc','orange','x',''),(0,'rf_am','black','',''),(0,'rf',('red','green'),'',''),
                                              (1,'grx','r','',''), (1,'gry','g','',''), (1,'grz','b','',''),
                                              (2,'srx','r','',''), (2,'sry','g','',''), (2,'srz','b','','')],
                          'fully_cond.': [(0,'adc','orange','x',''),(0,'rf_am','black','',''),(0,'rf',('red','green'),'',''),
                                          (0,'grx','r','',''), (0,'gry','g','',''), (0,'grz','b','','')],
                          'sim_cond.': [(0,'adc','orange','x',''),(0,'rf_am','black','',''),(0,'rf',('red','green'),'',''),
                                        (0,'grx','r','',''), (0,'gry','g','',''), (0,'grz','b','',''), 
                                        (1,'signal_amp','purple','',''), (2,'magZ','black','',(-1,1))],
                          'sim_ext.': [(0,'adc','orange','x',''),(0,'rf_am','black','',''),(0,'rf',('red','green'),'',''),
                                        (0,'grx','r','',''), (0,'gry','g','',''), (0,'grz','b','',''), 
                                        (1,'signal_amp','black','',''), (2,'magZ','black','',(-1,1)),
                                        (1,'mxy','','',(0,1)), (2,'fz','bwr','',(-1,1)),
                                        ],
                          'icon_mode': [(0,'adc','orange','x',''),(0,'rf',('red','green'),'',''),
                                          (0,'grx','r','',''), (0,'gry','g','',''), (0,'grz','b','','')],
                           }
        self.visMode = kwargs.get('visMode','sim_ext.')
        self._showModules = kwargs.get('showModules',True)
        self._dynamic_ax = None
        self._text_ax = None
        self._zoom_timer = None
        self.areModulesDraggable = kwargs.get('areModulesDraggable',True)
        self.setAcceptDrops(True)
        self.relBorderWidth = kwargs.get('relBorderWidth',0.05)
        self.noLegend = kwargs.get('noLegend',False)
        self.noAxis = kwargs.get('noAxis',False)
        self.scaling_factors = dict(rf=0.1, rf_am=0.1,adc=10)
        self.hideUnusedPlots = kwargs.get('hideUnusedPlots',False)
        self.current_time = 0
        self.blochsim = kwargs.get('blochSim')
        self.viewer3d = None
        if self.blochsim:
            self.blochsim.blochSim_finished.connect(self._update_some_plots)

        self.store = [None] * 10
        if kwargs.get('noExtraScaling'):
            self.scaling_factors = {}
        layout = QtWidgets.QVBoxLayout(self)
        self.preset_dropdown = QtWidgets.QComboBox()
        self.preset_dropdown.addItems(self.getAvailableVisModes())
        self.preset_dropdown.setCurrentText(self.visMode)
        self.preset_dropdown.currentTextChanged.connect(self.setVisMode)
        if not self.noContext:
            self.mrCtx.toolPresetChanged.connect(self.update_preset)

        ui_showModules = QtWidgets.QCheckBox('Show modules')
        ui_showModules.setChecked(self._showModules)
        ui_showModules.toggled.connect(self.showModules)
        ui_draggableModules = QtWidgets.QCheckBox('Draggable modules')
        ui_draggableModules.setChecked(self.areModulesDraggable)
        ui_draggableModules.toggled.connect(self.draggableModules)
        update_btn = QtWidgets.QPushButton("Reset view")
        update_btn.setStyleSheet("font-size: 10pt;") 
        update_btn.clicked.connect(self._refresh)
        hBoxLayout = QtWidgets.QHBoxLayout()
        hBoxLayout.addWidget(QtWidgets.QLabel('visMode:'))
        hBoxLayout.addWidget(self.preset_dropdown)
        hBoxLayout.addWidget(ui_showModules)
        hBoxLayout.addWidget(ui_draggableModules)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(update_btn)
        
        if kwargs.get('showGUI',True):
            layout.addLayout(hBoxLayout)
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(kwargs.get('width',15), kwargs.get('height',10))))
        layout.addWidget(self.dynamic_canvas)
        # layout.addWidget(NavigationToolbar(self.dynamic_canvas, self))

        self.dynamic_canvas.figure.subplots_adjust(  left=self.relBorderWidth,right=1-self.relBorderWidth,
                                                bottom=self.relBorderWidth+0.05,top=1-self.relBorderWidth,
                                                wspace=0,hspace=0)
        self.dynamic_canvas.mpl_connect('scroll_event', self.on_scroll)

        # self.dynamic_canvas.mpl_connect('button_press_event', self.on_click)
        if not self.noContext:
            if kwargs.get('autoUpdate',True):
                self.mrCtx.sequenceUpdated.connect(self._refresh)
            self.mrCtx.currentSequenceName = self.seqname

    def update_preset(self,preset="",name="Plot"):
        print('update_preset:',name,preset)
        if name == "Plot":
            idx = self.preset_dropdown.findText(preset)
            if idx >= 0:
                self.preset_dropdown.setCurrentIndex(idx)

            else:
                print(preset,'is not a known preset for',name)
                print('available presets:', self.getAvailableVisModes())
               

    def set_times_for_viewer3d(self,signal=True):
        curLim = self._dynamic_ax[0].get_xlim()
        # print('set_times_for_viewer3d: signal',signal,curLim)
        if (curLim[0]==0 and curLim[1]==1) or \
           (curLim[0]==-0.05 and curLim[1]==1.05):
            return
        if signal:
            self.timesChanged.emit(float(curLim[0]),float(curLim[1]))
            
    def set_viewer(self,viewer3d):
        self.viewer3d = viewer3d
        viewer3d.markerChanged.connect(self.set_marker)
        # self.timesChanged.connect(viewer3d.set_time_range)
        self.markerChanged.connect(viewer3d.set_current_time)
        
    def setBackgroundColor(self,_type):
        self.dynamic_canvas.figure.patch.set_facecolor(self.colors.get(_type,'white'))
        
    def set_marker(self,time=None, signal=False):
        if time:
            self.current_time = time
        else:
            time = self.current_time
        if self._dynamic_ax is not None:
            for i,ax in enumerate(self._dynamic_ax):
                if self.store[i]:
                    try:
                        self.store[i].remove()
                    except:
                        pass
                self.store[i] = ax.axvline(x=time, color='red', linestyle='--', linewidth=1.0)
            self.dynamic_canvas.draw()
            if signal:
                self.markerChanged.emit(time)           
        
    def on_click(self, event):
        print('on_click event')
        
    def showEvent(self,event):
        self._refresh()
        
    def showModules(self,item):
        self._showModules = item
        self._refresh()
        
    def draggableModules(self,item):
        self.areModulesDraggable = item
        self._refresh()
        
    def setVisMode(self,_mode):
        if _mode not in self.getAvailableVisModes():
            print('visMode:',_mode,'not supported')
            return
        self.visMode = _mode
        self._refresh()
        
    def getAvailableVisModes(self):
        return list(self.availVisModes.keys())
        
    def on_scroll(self, event):
        if not self._zoom_timer:
            self._zoom_timer = QTimer(self)
            self._zoom_timer.setSingleShot(True)
            self._zoom_timer.timeout.connect(self._apply_zoom)

        # print('scrolling!')
        curPos = event.xdata or 0
        curLim = self._dynamic_ax[0].get_xlim()
        span = (curLim[1]-curLim[0])
        ratio = (curPos-curLim[0])/span
        span = span*(1-event.step/4)
        newLim=curPos-span*ratio
        if newLim<0: newLim=0

        for ax in self._dynamic_ax:
            ax.set_xlim(newLim,newLim+span)
        self._zoom_timer.start(200)
        self.dynamic_canvas.draw()

    def _apply_zoom(self):
        self._zoom_timer = None
        self.set_times_for_viewer3d()

    def on_xlim_change(self, event):
        # print('on_xlim_change!')
        self.set_times_for_viewer3d(signal=False)
       
    def saveFigure(self,fname,format='svg'):
        self.dynamic_canvas.figure.savefig(fname+"."+format)

    def _refresh(self,_seq=None):
        print('plot: refresh')
        if self.noContext:
            return
        
        if not _seq or isinstance(_seq,dict):
            _seq = self.mrCtx.getSequence()
            
        if _seq:
            self.curSeq = _seq
            self._update_canvas(self.curSeq)
        
        self.set_times_for_viewer3d(signal=True)

    def _update_some_plots(self,data,grid_params_not_used=None):
        self._update_canvas(data=data,no_clearance=True)
    
    def _update_canvas(self,_seq=None,**kwargs):
        
        if self._showModules:
            _addPlot = 1
        else:
            _addPlot = 0
        if not kwargs.get('no_clearance', False):    
            self.dynamic_canvas.figure.clear()
                
            num_ax = max([i for i, d, c, m, b in self.availVisModes.get(self.visMode)])+1+_addPlot
            if self.visMode == 'icon_mode':
                if kwargs.get('infoBlock',True):
                    _axes = self.dynamic_canvas.figure.subplots(num_ax,2,
                           gridspec_kw={'width_ratios': [4, 5]},sharex=True)
                else:
                    if num_ax==1:
                        _axes = [self.dynamic_canvas.figure.subplots(num_ax,1,sharex=True)]
                    else:
                        _axes = self.dynamic_canvas.figure.subplots(num_ax,1,sharex=True)
                self._dynamic_ax = _axes[-1]
                self._text_ax = _axes[0]
                if not isinstance(self._text_ax,np.ndarray):
                    self._text_ax = [self._text_ax]
            else:
                if self._showModules:
                    self._dynamic_ax = self.dynamic_canvas.figure.subplots(num_ax,1,\
                       gridspec_kw={'height_ratios': np.append([1], [2]*(num_ax-1))},sharex=True)
                else:
                    self._dynamic_ax = self.dynamic_canvas.figure.subplots(num_ax,1,sharex=True)
                self._text_ax = None

            if not isinstance(self._dynamic_ax,np.ndarray):
                self._dynamic_ax = [self._dynamic_ax]
            self._dynamic_ax[-1].callbacks.connect('xlim_changed', self.on_xlim_change)
                            
        self._dynamic_ax[-1].set_xlabel("Time [s]")

        if _seq and len(_seq.getSortedElements()) and not self.noContext:
            elements = []
            full_data = {}
            for e,elem in _seq['elements'].items():
                data,_f = elem.create_plots_and_pulseq(_seq.getGlobals())
                for d in data.keys():
                    t = full_data.get(d,dict(t=[],v=[]))['t']
                    t.extend([_t+elem.getTstart() for _t in data[d]['t']])
                    v = full_data.get(d,dict(t=[],v=[]))['v']
                    v.extend(data[d]['v'])
                    full_data[d] = dict(t=t,v=v)
                if self._showModules:        
                    t = elem.getTstart()
                    d = elem.getDuration()
                    elements.append(SeqElement((t,0), d, 1.0,ec='black',
                                               fc=self.colors.get(elem['type'],'r'), 
                                               alpha=0.4, elem=elem))
            data = full_data
                
            # data = full_data
            self.data = data
            for i, d, c, m, b in self.availVisModes.get(self.visMode):
                if d in data.keys():
                    t = data[d]['t']
                    v = data[d]['v']
                    if len(t):
                        v = np.array(v)*self.scaling_factors.get(d,1.0)
                    if m:
                        if self.noLegend:
                            self._dynamic_ax[i+_addPlot].plot(t,v,c,marker=m,label='_nolegend_')
                        else:
                            self._dynamic_ax[i+_addPlot].plot(t,v,c,marker=m,label=d)
                    else:
                        if np.iscomplexobj(v):
                            if self.noLegend:
                                self._dynamic_ax[i+_addPlot].plot(t,np.real(v),c[0],linestyle='-',label='_nolegend_')
                                self._dynamic_ax[i+_addPlot].plot(t,np.imag(v),c[1],linestyle='-.',label='_nolegend_')
                            else:
                                self._dynamic_ax[i+_addPlot].plot(t,np.real(v),c[0],linestyle='-',label=d)                            
                                self._dynamic_ax[i+_addPlot].plot(t,np.imag(v),c[1],linestyle='-.',label='_nolegend_')                            
                        else:
                            if self.noLegend:
                                self._dynamic_ax[i+_addPlot].plot(t,v,c,label='_nolegend_')
                            else:
                                self._dynamic_ax[i+_addPlot].plot(t,v,c,label=d)

                    self._dynamic_ax[i+_addPlot].axhline(y=0,color='black',linewidth=.2)
                    self._dynamic_ax[i+_addPlot].legend(fontsize=8)

            if self._showModules:
                for seqElem in elements:
                    self._dynamic_ax[0].add_artist(seqElem)
                self._dynamic_ax[0].set_ylim(-0.1,1.1)
                self._dynamic_ax[0].get_yaxis().set_visible(False)
                self.draggables = Draggable(elements, self._dynamic_ax, self.areModulesDraggable, plot_widget=self)
                
            self.dynamic_canvas.draw()

            # if any(item in [item[1] for item in self.availVisModes.get(self.visMode)] for item in ['signal_amp','signal_phs','magZ','b1']): 
            #     if self.blochsim:
            #         print('simulation requested')
            #         self.blochsim.check4update()
                    
        elif kwargs.get('data'):
            data = kwargs.get('data')
            cleared = []
            _min = data.get('t',[-1])[0] 
            _max = data.get('t',[-1])[-1] 
            if self.visMode == 'icon_mode':
                self.fillCurves = True
            else:
                self.fillCurves = False
            if self.noAxis and self.noLegend:
                lw=3
            else:
                lw=1
            _ax_grad = None
            _ax_rf = None
            for i, d, c, m, b in self.availVisModes.get(self.visMode):
                if i not in cleared:
                    self._dynamic_ax[i+_addPlot].clear()
                    cleared.append(i)
                _cur_ax = self._dynamic_ax[i+_addPlot]
                if d in data.keys():
                    t = data[d]['t']
                    v = data[d]['v']
                    if not np.all(np.array(t).shape)==0:
                        if len(t):
                            _min=min(_min,min(t))
                            _max=max(_max,max(t))
                            v = np.array(v)*self.scaling_factors.get(d,1.0)
                        if self.visMode == 'icon_mode' and kwargs.get('fixRfScaling') and kwargs.get('fixGradientScaling'):
                            if 'gr' in d:
                                if not _ax_grad:
                                    _ax_grad = self._dynamic_ax[i+_addPlot].twinx()
                                _cur_ax = _ax_grad
                            if 'rf' in d:
                                if not _ax_rf:
                                    _ax_rf = self._dynamic_ax[i+_addPlot].twinx()
                                _cur_ax = _ax_rf
                        if m:
                            if self.noLegend:
                                _cur_ax.plot(t,v,c,marker=m,label='_nolegend_',lw=lw)
                            else:
                                _cur_ax.plot(t,v,c,marker=m,label=d,lw=lw)
                        else:
                            if np.iscomplexobj(v):
                                if self.noLegend:
                                    _cur_ax.plot(t,np.real(v),c[0],linestyle='-',label='_nolegend_',lw=lw)
                                    _cur_ax.plot(t,np.imag(v),c[1],linestyle='-.',label='_nolegend_',lw=lw)
                                else:
                                    _cur_ax.plot(t,np.real(v),c[0],linestyle='-',label=d,lw=lw)                            
                                    _cur_ax.plot(t,np.imag(v),c[1],linestyle='-.',label='_nolegend_',lw=lw)                            
                                if self.fillCurves:
                                    _cur_ax.fill_between(t,np.real(v),color=c[0],alpha=0.3)  
                                    _cur_ax.fill_between(t,np.imag(v),color=c[1],alpha=0.3)  
                            elif len(np.array(v).shape)==1:
                                if self.noLegend:
                                    _cur_ax.plot(t,v,c,label='_nolegend_',lw=lw)
                                else:
                                    _cur_ax.plot(t,v,c,label=d,lw=lw)
                                if self.fillCurves:
                                    _cur_ax.fill_between(t,v,color=c,alpha=0.3)  
                            elif len(np.array(v).shape)==2:
                                _cur_ax.imshow(v, aspect='auto', 
                                    extent=[t[0], t[-1], b[0],b[1]], vmin=b[0],vmax=b[1], origin='lower', cmap=c, alpha=0.5)
                            elif len(np.array(v).shape)==3:
                                _cur_ax.imshow(v, aspect='auto', 
                                    extent=[t[0], t[-1], b[0],b[1]], origin='lower', alpha=0.5)
                        _cur_ax.axhline(y=0,color='black',linewidth=.2,lw=lw/2)
                        if not self.noLegend:
                            _cur_ax.legend(fontsize=8)
                        if self.noAxis:
                            self._dynamic_ax[i+_addPlot].set_xticklabels([])
                            self._dynamic_ax[i+_addPlot].set_yticklabels([])
                        
            if kwargs.get('fixRfScaling') and _ax_rf:
                _ax_rf.set_ylim(-kwargs.get('fixRfScaling'),kwargs.get('fixRfScaling'))
            maxGrad = kwargs.get('fixGradientScaling')
            if maxGrad and _ax_grad:
                _ax_grad.set_ylim(-maxGrad,maxGrad)

            if self.noContext:
                print('plot: setting xLim!',_min,_max)
                for ax in self._dynamic_ax:
                    ax.set_xlim(_min,_max)

            self._dynamic_ax[-1].set_xlabel("Time [s]")
            self.dynamic_canvas.draw()

        elif True:
            self.dynamic_canvas.figure.clear()
            self.dynamic_canvas.draw()

        if self.viewer3d:
            self.set_marker(self.viewer3d.get_current_time())


    def annotate_gradients(self, gradients=None, fontsize=24,
                           x=0.02, y_top=0.4, y_bottom=0.03,
                           fmt="{val:+05.1f}", **text_kwargs):
        """
        Draw each value from `gradients` evenly spaced along the left of your dynamic axis.
        """
        if self._text_ax:
            ax = self._text_ax[0]
            ax.axis('off')
        else:
            ax = self._dynamic_ax[0]
        rect = patches.Rectangle(
                    (0, 0),             # lower left corner in axis coordinates
                    1, 0.5,               # width and height (full axis)
                    transform=ax.transAxes,
                    color='white',      # or 'black' or any other background
                    alpha=0.5,          # 0 = fully transparent, 1 = fully opaque
                    zorder=0            # draw behind everything else
                )
        ax.add_patch(rect)
        if gradients is None:
            return
        ys = np.linspace(y_top, y_bottom, len(gradients))
        for y, val in zip(ys, gradients):
            if isinstance(val,str):
                s = "VAR"
            else:
                s = fmt.format(val=val)
            ax.text(
                x, y, s,
                transform=ax.transAxes,
                ha="left", va="center",
                fontsize=fontsize, fontweight='normal',
                **text_kwargs
            )
    
    def annotate_flip_phase(self, flip_angle=None, phase_deg=None,
                    fontsizes=(30,24),
                    x=0.98,  y_top=0.98, line_gap=0.26,     # vertical step between lines
                    **text_kwargs):
        """
        Draw flip-angle on top-right, then a phase-label, then the phase in degrees.
        flip_angle: in degrees (will be rounded to an int)
        phase_deg:   in degrees (0–360)
        fontsizes:   tuple (flipfont, phasefont)
        """
        if self._text_ax:
            ax = self._text_ax[0]
            ax.axis('off')
        else:
            ax = self._dynamic_ax[0]
        rect = patches.Rectangle(
                    (0, 0.5),             # lower left corner in axis coordinates
                    1, 1,               # width and height (full axis)
                    transform=ax.transAxes,
                    color='white',      # or 'black' or any other background
                    alpha=0.5,          # 0 = fully transparent, 1 = fully opaque
                    zorder=0            # draw behind everything else
                )
        ax.add_patch(rect)

        if flip_angle is None:
            return
        fa_fs, ph_fs = fontsizes
        y = y_top
    
        # 1) Flip‐angle as 3-digit int (005, 090, 180)
        if isinstance(flip_angle,str):
            fa_label = "VAR°"
        else:
            fa_label = f"{int(round(flip_angle)):3d}°"
        ax.text(x, y, fa_label,
                transform=ax.transAxes,
                ha='right', va='top',
                fontsize=fa_fs, fontweight='bold', 
                **text_kwargs)
    
        # 2) Middle label: map multiples of 45° or default “Phase”
        phase_map = {
            0:   'X',
            45:  'XY',
            90:  'Y',
            135: '-XY',
            180: '-X',
            225: '-X-Y',
            270: '-Y',
            315: 'X-Y'
        }
        y -= line_gap
        if isinstance(phase_deg,str):
            label = "VAR°"
        else:
            ph_mod = phase_deg % 360
            if ph_mod in phase_map:
                label = phase_map[ph_mod]
            else:
                label = f"{int(round(ph_mod)):d}°"
        ax.text(x, y, label,
                transform=ax.transAxes,
                ha='right', va='top',
                fontsize=ph_fs, fontweight='bold',
                **text_kwargs)
        ax.text(-0.02, y, 'P',
                transform=ax.transAxes,
                ha='left', va='top',
                fontsize=ph_fs, fontweight='normal',
                **text_kwargs)

    def parseEvent(self,e):
        mime = e.mimeData()
        x, y = self._dynamic_ax[0].transData.inverted().transform([e.pos().x(),e.pos().y()])

        data = dict(x=x,y=y)
        if mime.hasFormat('application/x-qabstractitemmodeldatalist'):
           stream = QtCore.QDataStream(mime.data('application/x-qabstractitemmodeldatalist'))
           while not stream.atEnd():
                # we're not using row and columns, but we *must* read them
                data['row'] = stream.readInt()
                data['col'] = stream.readInt()
                for dataSize in range(stream.readInt()):
                    role, value = stream.readInt(), stream.readQVariant()
                    if role == Qt.UserRole:
                        data['seqElement'] = value
        return data

    def reactOnData(self,data,permanentChange=True):
        seq = self.mrCtx.getSequence()
        if permanentChange:
            elem = data['seqElement']
            elem['name'] = self._curDraggingName
            seq.insert(elem,data['x'])
            self.mrCtx.seqModified(seq)   
        else:
            elem = self.mrCtx.getElementForBpName(data['name'])
            elem['name'] = self._curDraggingName
            seq.insert(elem,data['x'],uniqueKey=False)
            self._refresh(seq)
        
    def dragEnterEvent(self, e):
        elem = self.parseEvent(e).get('seqElement')
        seq = self.mrCtx.getSequence()
        self._curDraggingName = elem['name']
        e.accept()

    # def dragLeaveEvent(self, e):
    #     self._refresh()        

    # def dragMoveEvent(self,e):
    #     elem = self.parseEvent(e).get('seqElement')
    #     if elem:
    #         e.accept()
    #     else:
    #         e.ignore()
            
    def dropEvent(self,e):
        if self.mrCtx.getSubtaskStatus('blochSim') == Status.RUNNING:
            e.ignore()
            return
        print('dropEvent:',e.pos())
        data = self.parseEvent(e)
        elem = data.get('seqElement')
        if elem:           
            self.reactOnData(data,permanentChange=True)
            e.accept()
        else:
            e.ignore()
           
if __name__ == '__main__':
    qapp = QtWidgets.QApplication.instance()

    mr=mrlabContext()
    seq=mr.getSequence()
    seq.insert(mr.getElementForBpName('epi2D_RO'),0)
    plot = Plot()
    plot.show()
    plot.activateWindow()
    plot.raise_()
    plot._refresh()
    qapp.exec()
    

