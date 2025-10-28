#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 21:52:10 2024

@author: mague
"""
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QTreeWidget, QTreeWidgetItem, 
                             QTableWidget, QTableWidgetItem, 
                             QHeaderView, QListWidget, QTabWidget, QLineEdit)

from mrlabContext import mrlabContext

class SequenceSelector(QtWidgets.QWidget):
    """
    Custom Qt Widget to select a sequence
    """
    def __init__(self, *args, **kwargs):
        super(SequenceSelector, self).__init__(*args, **kwargs)

        self.setMinimumWidth(250)
        
        self.mrCtx = mrlabContext()

        layout = QtWidgets.QVBoxLayout(self)
        layoutH = QtWidgets.QHBoxLayout(self)
        self.newSeqName = QtWidgets.QLineEdit()
        layoutH.addWidget(self.newSeqName) 
        bt_new = QtWidgets.QPushButton("new")
        bt_new.clicked.connect(self.newSeq)
        layoutH.addWidget(bt_new)

        layout.addLayout(layoutH)

        layoutH2 = QtWidgets.QHBoxLayout(self)
        bt_save = QtWidgets.QPushButton("save")
        bt_save.clicked.connect(self.saveSeq)
        layoutH2.addWidget(bt_save)        
        bt_export = QtWidgets.QPushButton("export")
        bt_export.clicked.connect(self.exportSeq)
        layoutH2.addWidget(bt_export)
        layout.addLayout(layoutH2)
        
        self.curSeqName = QtWidgets.QLabel()
        layout.addWidget(self.curSeqName)
        layout.addWidget(QtWidgets.QLabel('loaded sequences:'))

        self.loaded_selector =  QListWidget()
        layout.addWidget(self.loaded_selector)

        layout.addWidget(QtWidgets.QLabel(''))
        bt_load = QtWidgets.QPushButton("load existing sequence")
        bt_load.clicked.connect(self.loadSeq)
        layout.addWidget(bt_load)        
        bt_remove = QtWidgets.QPushButton("remove existing sequence")
        bt_remove.clicked.connect(self.removeSeq)
        layout.addWidget(bt_remove)        
        bt_refreshLList = QtWidgets.QPushButton("refresh list")
        bt_refreshLList.clicked.connect(self.refreshList)
        layout.addWidget(bt_refreshLList) 
        self.existing_selector =  QListWidget()
        layout.addWidget(self.existing_selector)

        self.loaded_selector.currentItemChanged.connect(self.seqname_selected)
        
        self.mrCtx.sequenceChanged.connect(self._refresh)
        
        self._refresh()

    def seqname_selected(self,e=None):
        if e:
            seqname = e.text()
        else:
            seqname = self.mrCtx.currentSequenceName        
        self.curSeqName.setText(seqname)
        self.newSeqName.setText(seqname)
        self.mrCtx.currentSequenceName = seqname

    def newSeq(self,e):
        if len(self.newSeqName.text()):
            newSeqName = self.newSeqName.text()
        else:
            newSeqName = 'seq'  
        newSeqName = self.mrCtx.getUniqueName(newSeqName,self.mrCtx.lib.getAvailableBlueprints())
        print('new sequence:',newSeqName)
        seq = self.mrCtx.getSequence(seqname = newSeqName,autoCreate=True)
        self.mrCtx.currentSequenceName = seq['name']
            
    def loadSeq(self,e):
        # load existing sequence and change Id, so that existing sequences are not overwritten
        seqname = self.existing_selector.currentItem().text()
        self.mrCtx.currentSequenceName = seqname
        self.mrCtx.createNewBpIdForSeq()
        
    def saveSeq(self,e=None):
        newSeqName = self.newSeqName.text()
        self.mrCtx.saveSequenceToBlueprint(self.mrCtx.getSequence(), seqname = newSeqName)
        self._refresh()
        
    def removeSeq(self,e):
        seqname = self.existing_selector.currentItem().text()
        self.mrCtx.lib.removeBlueprint(seqname)
        self._refresh()
       
    def exportSeq(self,e):
        newSeqName = self.newSeqName.text()
        bp = self.mrCtx.saveSequenceToBlueprint(self.mrCtx.getSequence(), seqname = newSeqName)
        _dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory for exporting sequence"))
        self.mrCtx.lib.exportBlueprint(bp['name'], seqname = bp['name'],dirName=_dir, exportAll=True)
        self.mrCtx.lib.removeBlueprint(bp['name'])

    def refreshList(self,e=None):
        self.mrCtx.reset
        
    def _refresh(self,e=None):
        print('refreshing sequenceSelector',self.mrCtx.currentSequenceName)
        self.curSeqName.setText(self.mrCtx.currentSequenceName)
        self.newSeqName.setText(self.mrCtx.currentSequenceName)

        seqnames=self.mrCtx._seq_cache.keys()
        self.loaded_selector.clear()
        self.loaded_selector.addItems(seqnames)
        self.curSeqName.setText(self.mrCtx.currentSequenceName)

        self.existing_selector.clear()
        seqnames = [e for e in self.mrCtx.lib.getAvailableSequences() 
                    if e != self.mrCtx.default_sequenceTemplate]
        self.existing_selector.addItems(seqnames)

if __name__ == '__main__':

    win = SequenceSelector()
    win.show()
    win.activateWindow()
    win.raise_()
#    qapp.exec()
