#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 21:52:10 2024

@author: mague
"""
import os
from pathlib import Path as FilePath

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer

from mrlabContext import mrlabContext, Status

# from MrSequence_constrained import MrSequence
from MrSequence import MrSequence

import MRzeroCore as mr0
import pypulseq as pp
import torch
import torchkbnufft as tkbn

import mrlab_utils as utils     

def round_nearest(x, a=1e-5,limit=False):
    if limit:
        return max(round(x / a) * a,0)
    else:
        return round(x / a) * a
 
class Simulation(QtWidgets.QWidget):
    """
    Custom Qt Widget to plot a sequence in gammaSTAR.
    """
    sequenceUpdateOccured = QtCore.pyqtSignal()

    def __init__(self,*args, **kwargs):
        super(Simulation, self).__init__()

        self.mrCtx = mrlabContext()      
        self.curSeq = self.mrCtx.getSequence(seqname=kwargs.get('seqname'))

        try:
            self.seqDirectory = kwargs.get('seqDir',FilePath(__file__).parent/'export')
            self.phantomDirectory = kwargs.get('seqDir',FilePath(__file__).parent/'phantoms')
        except:
            self.seqDirectory = FilePath(kwargs.get('seqDir',os.getcwd()+'/export'))
            self.phantomDirectory = FilePath(kwargs.get('seqDir',os.getcwd()+'/phantoms'))
        
        # self.phantomName = kwargs.get('phantomName',"subject05_small.npz")
        self.phantomName = kwargs.get('phantomName',self.mrCtx.getAvailablePhantoms()[0])
        self.phantom = None
        self.size = kwargs.get('size',(64,64,32))  
        self.setPhantom(self.phantomName, self.size)
# this is hardcoded, change as soon as possible to get info from acquired data!
        self.Nphase = kwargs.get('Nphase',64)
        self.Nread  = kwargs.get('Nread',64)
        self.mrzeroseq = None
        self.graph = None
        self.signal = None
        self.space = None
        self.kspace = None
        self.curSlice = 0
        self.numSlices= 1
        self._showTrajectory = False
        self._showMoments = False
        self._showKSpace = True
        self._showImage = True
        self._autoUpdate = False
        
        layout = QtWidgets.QVBoxLayout(self)
        hBoxLayout = QtWidgets.QHBoxLayout()
        hBoxLayout.addWidget(QtWidgets.QLabel('Phantom:'), stretch=0, alignment=Qt.AlignLeft);
        ui_phantoms = QtWidgets.QComboBox()
        ui_phantoms.addItems(self.mrCtx.getAvailablePhantoms())
        ui_phantoms.setCurrentText(self.phantomName)
        ui_phantoms.currentTextChanged.connect(self.setPhantom)
        hBoxLayout.addWidget(ui_phantoms, stretch=0, alignment=Qt.AlignLeft);
        bt_showPhantom = QtWidgets.QPushButton('show Phantom')
        bt_showPhantom.clicked.connect(self.phantom.plot)
        hBoxLayout.addWidget(bt_showPhantom, stretch=0, alignment=Qt.AlignLeft);

        self.autoUpdate = QtWidgets.QCheckBox('autoUpdate')
        self.autoUpdate.setChecked(self._autoUpdate)
        hBoxLayout.addWidget(self.autoUpdate, stretch=0, alignment=Qt.AlignLeft);
        self.bt_simulate = QtWidgets.QPushButton()
        self.bt_simulate.setIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_MediaPlay))
        self.bt_simulate.setIconSize(QtCore.QSize(30,30))
        self.bt_simulate.setAutoFillBackground(True)
        self.bt_simulate.setStyleSheet('background-color: lightgrey')
        self.bt_simulate.clicked.connect(self.startSimulation)
        hBoxLayout.addWidget(self.bt_simulate, stretch=10, alignment=Qt.AlignLeft);

        hBoxLayout2 = QtWidgets.QHBoxLayout()
        dummy = QtWidgets.QCheckBox('Show trajectory')
        dummy.setChecked(self._showTrajectory)
        dummy.toggled.connect(self.showTrajectory)
        hBoxLayout2.addWidget(dummy, stretch=0, alignment=Qt.AlignLeft);
        dummy = QtWidgets.QCheckBox('Show moments')
        dummy.setChecked(self._showMoments)
        dummy.toggled.connect(self.showMoments)
        hBoxLayout2.addWidget(dummy, stretch=0, alignment=Qt.AlignLeft);
        dummy = QtWidgets.QCheckBox('Show kspace')
        dummy.setChecked(self._showKSpace)
        dummy.toggled.connect(self.showKSpace)
        hBoxLayout2.addWidget(dummy, stretch=0, alignment=Qt.AlignLeft);
        dummy = QtWidgets.QCheckBox('Show image')
        dummy.setChecked(self._showImage)
        dummy.toggled.connect(self.showImage)
        hBoxLayout2.addWidget(dummy, stretch=1, alignment=Qt.AlignLeft);        
        if kwargs.get('showGUI',True):
            layout.addLayout(hBoxLayout)
            layout.addLayout(hBoxLayout2)

        self.canvas_trajectory = FigureCanvas(Figure(figsize=(kwargs.get('width',5), kwargs.get('height',3))))
        layout.addWidget(self.canvas_trajectory)

        self.canvas_trajectory.figure.subplots_adjust(  left=0.05,right=0.98,
                                                bottom=0.1,top=0.94,
                                                wspace=0.2,hspace=0)
        self.canvas_data = FigureCanvas(Figure(figsize=(kwargs.get('width',5), kwargs.get('height',3))))
        self.canvas_data.mpl_connect('button_press_event', self.on_click)

        layout.addWidget(self.canvas_data)

        self.canvas_data.figure.subplots_adjust(  left=0.03,right=0.98,
                                                bottom=0.07,top=0.98,
                                                wspace=0,hspace=0)

        self.mrCtx.sequenceUpdated.connect(self.check4Update)

        self.sequenceUpdateOccured.connect(self.refreshTrajectory)
        
    def setStatus(self,status,_timer_in_s=-1):
        color = status.get('color','lightgrey')
        self.bt_simulate.setStyleSheet(f"background-color: {color}")
        self.bt_simulate.repaint()
        self.setEnabled(not status.get('blockUI',False))
        # if _timer_in_s>0:
        #     try:
        #         self.timer.stop()
        #     except:
        #         pass
            # self.timer = QTimer(self)
            # self.timer.timeout.connect(lambda: self.setStatus(Status.IDLE))  
            # self.timer.start(_timer_in_s*1000)                  
        
    def startSimulation(self,e=None):
        import time
        self.mrCtx.setStatus('starting simulation')
        self.canvas_data.figure.clear()
        self.canvas_data.draw()
        self.kspace = None 
        self.space = None
        self.setStatus(Status.RUNNING)
        self.updateSequence(True)
        try:
            if self.mrCtx.getSequence().getDuration()!=0:
                s=time.time()
                self.graph = mr0.compute_graph(self.mrzeroseq, self.builtPhantom, 1000, 1e-7)
                print(time.time()-s)
                self.signal = mr0.execute_graph(self.graph, self.mrzeroseq, self.builtPhantom, print_progress=True)
                print(time.time()-s)
                self.setStatus(Status.FINISHED_OK)
                self.kspace, self.space, self.reco = self.getImageData()
                self.curSlice = 0
                self.mrCtx.setStatus('simulation finished')
        except Exception as e:
            print(e)
            self.setStatus(Status.STOPPED_ERROR,5)
            self.mrCtx.setStatus('simulation stopped with error\n'+str(e))

        self.refreshImages()
                
    def showEvent(self,event):
        pass
        
    def check4Update(self,e=None):
        print('checking for update')
        if self.autoUpdate.isChecked():
            self.startSimulation()
        else:
            self.setStatus(Status.UPDATE_REQUIRED)
            self.clearDisplay()
            
    def showTrajectory(self,item):
        self._showTrajectory = item
        self.refreshTrajectory()

    def showMoments(self,item):
        self._showMoments = item
        self.refreshTrajectory()

    def showKSpace(self,item):
        self._showKSpace = item
        self.refreshImages()

    def showImage(self,item):
        self._showImage = item
        self.refreshImages()

    def setPhantomSize(self,size):
        self.setPhantom(self.phantomName,size)
        
    def setPhantom(self, phantomName=None,size=(64, 64, 32)):
        if not phantomName:
            phantomName = self.phantomName
        self.phantom = mr0.VoxelGridPhantom.load(self.phantomDirectory/phantomName)
        self.phantom = self.phantom.interpolate(*size).slices([int(size[-1]/2)])
        # self.phantom = self.phantom.interpolate(*size).slices(list(range(size[-1])))
        self.builtPhantom = self.phantom.build()
        self.phantomName = phantomName
        self.size = size
        self.mrCtx.setPhantom(phantomName)
        
    def on_scroll(self, event):
        curPos = event.xdata
        curLim = self._ax[-1].get_xlim()
        span = (curLim[1]-curLim[0])
        ratio = (curPos-curLim[0])/span
        span = span*(1-event.step/4)
        newLim=curPos-span*ratio
        if newLim<0: newLim=0

        for ax in self._ax:
            ax.set_xlim(newLim,newLim+span)
        self.canvas.draw()

    def on_click(self,event):
        if event.button is MouseButton.RIGHT:
            self.curSlice = np.mod(self.curSlice+1,self.numSlices)
            self.refreshImages()

            
    def on_press(self,event):
        print('key:',event.key)
        if event.key == 'right':
            self.curSlice = np.mod(self.curSlice+1,self.numSlices)
        if event.key == 'left':
            self.curSlice = np.mod(self.curSlice-1,self.numSlices)
                
    def updateSequence(self,state=None):
        # updates sequence
        if self.mrCtx.getSequence():
            if state is None:
                _, self.pulseq = self.mrCtx.getSequence().getPlotsAndPulseq()
                self.pulseq.write(self.mrCtx.tempPulseqFile,create_signature=False)
            self.mrzeroseq = mr0.Sequence.import_file(self.mrCtx.tempPulseqFile)
            self.sequenceUpdateOccured.emit()
        
    def refreshTrajectory(self):
        if not self._showTrajectory and not self._showMoments:
            self.canvas_trajectory.setHidden(True)
        else:
            self.canvas_trajectory.setHidden(False)
            
        if self.mrzeroseq and (self._showTrajectory or self._showMoments):
            self.canvas_trajectory.figure.clear()
            self.trajectory_subplots = utils.plot_kspace_trajectory(self.mrzeroseq,self.canvas_trajectory,
                                                                    plot_timeline   = self._showMoments, 
                                                                    plot_trajectory = self._showTrajectory)
            self.canvas_trajectory.draw()
        
    def _refresh(self):
        self.refreshTrajectory()
        self.refreshImages()
        
    def getImageData(self):    
        kspace = []
        space = []
        reco = []
        if self.signal is not None:
            kspaceInfo = self.mrzeroseq.get_kspace()
            _numSlices = (kspaceInfo.shape[0] / self.Nread / self.Nphase)
            print(_numSlices)
            self.numSlices = int(_numSlices+0.99)
            for c in range(int(_numSlices+0.99)):
               _signal    = self.signal[c*self.Nread*self.Nphase:int((c+min(_numSlices-c,1))*self.Nread*self.Nphase),:]
               _kspaceInfo=  kspaceInfo[c*self.Nread*self.Nphase:int((c+min(_numSlices-c,1))*self.Nread*self.Nphase),:]

               _reco = mr0.reco_adjoint(_signal, _kspaceInfo,resolution=(127,64,1),FOV=(0.4,0.2,1))
               shape = _reco.shape
               reco.append(_reco[int(shape[0]/2-self.Nread/2):int(shape[0]/2+self.Nread/2),
                                 int(shape[1]/2-self.Nphase/2):int(shape[1]/2+self.Nphase/2),:])
               _kspace = self.scatter_regrid(np.array(_kspaceInfo[:, :3]), np.array(_signal))[:,:,31]
               kspace.append(_kspace)
               spectrum = np.fft.fftshift(_kspace)
               _space = np.fft.fft2(spectrum)
               _space = np.fft.ifftshift(_space)
               space.append(_space)
               print(_kspace.shape)
        return kspace,space,reco
    
    def scatter_regrid(self, k, adc,
                       grid_size=64, k_min=-160, k_max=160):
        """
        Scatter (tri-linear) interpolation of complex k-space samples
        onto a regular 3D grid.
    
        Parameters
        ----------
        k : ndarray, shape (N, 3), float
            Sample coordinates in k-space, each in [k_min, k_max].
        adc : ndarray, shape (N,), complex
            Complex sample values.
        grid_size : int
        k_min, k_max : float
    
        Returns
        -------
        grid_adc : ndarray, shape (grid_size,grid_size,grid_size), complex
            The gridded k-space array.
        """
        # ensure proper dtypes
        k   = np.asarray(k,    dtype=float)
        adc = np.asarray(adc,  dtype=np.complex128).ravel()
    
        # normalize coords→[0, grid_size-1]
        coords = (k - k_min) / (k_max - k_min) * (grid_size - 1)
        i0 = np.floor(coords).astype(int)    # base indices
        d  = coords - i0                     # fractional offsets
    
        # allocate output: complex grid + real weights
        grid_adc = np.zeros((grid_size,)*3, dtype=np.complex128)
        weight   = np.zeros_like(grid_adc,   dtype=float)
    
        # scatter each sample onto its 8 neighboring voxels
        for dx in (0, 1):
            wx = (1 - d[:,0]) if dx == 0 else d[:,0]
            ix = i0[:,0] + dx
            valid_x = (0 <= ix) & (ix < grid_size)
    
            for dy in (0, 1):
                wy = (1 - d[:,1]) if dy == 0 else d[:,1]
                iy = i0[:,1] + dy
                valid_y = (0 <= iy) & (iy < grid_size)
    
                for dz in (0, 1):
                    wz = (1 - d[:,2]) if dz == 0 else d[:,2]
                    iz = i0[:,2] + dz
                    valid_z = (0 <= iz) & (iz < grid_size)
    
                    mask = valid_x & valid_y & valid_z
                    if not np.any(mask):
                        continue
    
                    w = wx[mask] * wy[mask] * wz[mask]
                    v = adc[mask]              # complex samples
    
                    # accumulate weighted complex values and weights
                    grid_adc[ix[mask], iy[mask], iz[mask]] += v * w
                    weight  [ix[mask], iy[mask], iz[mask]] += w
    
        # normalize: avoid division by zero
        nonzero = weight > 0
        grid_adc[nonzero] /= weight[nonzero]
    
        return grid_adc

    def regridding(self, k, adc, grid_size=64, k_min=-0.5*400, k_max=0.5*400, nneighbors=4):
        from scipy.spatial import cKDTree
        import numpy as np
    
        # make sure adc is 1D
        adc = np.asarray(adc).ravel()
    
        # 1. build 3D grid …
        kx = np.linspace(k_min, k_max, grid_size)
        ky = np.linspace(k_min, k_max, grid_size)
        kz = np.linspace(k_min, k_max, grid_size)
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        grid_points = np.stack([KX.ravel(), KY.ravel(), KZ.ravel()], axis=1)
    
        # 2. neighbor search
        tree = cKDTree(k)
        dists, idxs = tree.query(grid_points, k=nneighbors)
    
        # grab & squeeze: now adc_neighbors is (M, nneighbors)
        adc_neighbors = np.squeeze(adc[idxs], axis=-1) if adc.ndim > 1 else adc[idxs]
    
        # weights (M, nneighbors)
        weights = 1.0 / (dists + 1e-8)
        weights /= weights.sum(axis=1, keepdims=True)
    
        # 3. interpolation
        grid_adc = np.sum(adc_neighbors * weights, axis=1)
        grid_adc = grid_adc.reshape((grid_size, grid_size, grid_size))
    
        return grid_adc, kx, ky, kz

    def clearDisplay(self):
        self.canvas_data.figure.clear()
        self.canvas_data.draw()
        self.canvas_trajectory.figure.clear()
        self.canvas_trajectory.draw()
       
    def refreshImages(self):        
        self.canvas_data.figure.clear()
        if not self._showTrajectory and not self._showMoments:
            self.canvas_trajectory.setHidden(True)
        else:
            self.canvas_trajectory.setHidden(False)
        try:
            if self.kspace is not None and self.space is not None:
                self.numSlices = len(self.reco)
                num_kspace_data = 1
                if num_kspace_data*self._showKSpace+self._showImage:
                    _ax = self.canvas_data.figure.subplots(1,num_kspace_data*self._showKSpace+self._showImage)
                    # if (not self._showKSpace and self._showImage):
                    if (num_kspace_data*self._showKSpace+self._showImage)==1:
                        _ax = [_ax]
                    if self._showKSpace:
                        _ax[0].imshow(np.flipud(np.abs(self.kspace[self.curSlice].T)))
                        _ax[0].set_title('kspace: slice '+str(self.curSlice)+'/'+str(self.numSlices-1))
                        if num_kspace_data>1:
                            _ax[1].imshow(np.flipud(np.abs(self.space[self.curSlice].T)))
                            _ax[1].set_title('space: slice '+str(self.curSlice)+'/'+str(self.numSlices-1))
                    if self._showImage:
                        _max = 0
                        try:
                            for e in self.reco:
                                _max = max(_max, torch.max(e.abs().cpu().flatten()))
                            curData = self.reco[self.curSlice].abs().cpu()
                            _ax[int(num_kspace_data*self._showKSpace)].imshow(curData[:, :, 0].T, 
                                                              origin='lower', vmin=0, vmax=_max)
                            _ax[int(num_kspace_data*self._showKSpace)].set_title('space: int:'+str(int(torch.max(curData)))+\
                                               '  slice '+str(self.curSlice)+'/'+str(self.numSlices-1))
                        except:
                            curData = self.reco[self.curSlice].abs().cpu()
                            _ax[int(num_kspace_data*self._showKSpace)].imshow(curData[:, :, 0].T, origin='lower')
                            _ax[int(num_kspace_data*self._showKSpace)].set_title('space: int:'+str(int(torch.max(curData)))+\
                                               '  slice '+str(self.curSlice)+'/'+str(self.numSlices-1))
            self.canvas_data.draw()
        except Exception as e:
            print(e)
                       
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mr=mrlabContext()
    seq=mr.getSequence(autoCreate=True)
    # seq.insert(mr.getElementForBpName('bSSFP_2D'),0)
    seq.insert(mr.getElementForBpName('epi2D_RO'),0)
    sim = Simulation(seqname='seq')
    sim.updateSequence()
    sim.show()
    sim.activateWindow()
    sim.raise_()
    sim._refresh()
    app.exec_()
    