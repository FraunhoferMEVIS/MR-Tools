
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QEvent, Qt, QSize
from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QWidget, QMenu, QAction,QHBoxLayout,
                             QListWidgetItem, QDialog, QDialogButtonBox, QPushButton,QSizePolicy,
                             QHeaderView, QListWidget, QTabWidget, QLineEdit, QMessageBox)
from PyQt5.QtGui import QPixmap, QDrag, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QMimeData, QByteArray, QDataStream, QIODevice, QSize, QPoint

from mrlabContext import mrlabContext
import numpy as np

from ParameterEditor import ParameterEditor
from ParameterSetWidget import ParameterSetWidget
from SequenceDropdown import SequenceDropdown
      
class myQListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        super(myQListWidget, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.mrCtx = mrlabContext()

    def dragMoveEvent(self,e):
        pass
            
    def dropEvent(self, e):
        print('dropEvent in myQListWidget')
        seq = self.mrCtx.getSequence()
        elems = seq.getSortedElements()
        time2insertAt = seq.getDuration()
        add2Children = False
        fromIndex = self.currentRow()
        toIndex = self.count()
        ix = self.indexAt(e.pos())
        if ix.isValid():
            toIndex = ix.row()
            rect = self.visualRect(ix)
            if e.pos().x()<rect.center().x():
                time2insertAt = elems[toIndex].getTstart() - 1e-4
            else:
                time2insertAt = elems[toIndex].getTstart() + elems[toIndex].getDuration() + 1e-4
            if e.pos().y()> rect.top() + 30 and elems[toIndex].isNested():
                add2Children = True
            
        if fromIndex>-1:
            if add2Children and not elems[fromIndex].isNested():
                seq.remove(elems[fromIndex]['name'])
                elems[toIndex].appendElement(elems[fromIndex])
            else:
                seq.shiftElement(elems[fromIndex]['name'],time2insertAt)
            e.accept()
        else:
            elem = self.parseEvent(e).get('seqElement')
            if '.' in elem.get('name'):
                seq.remove(elem.get('name'))
            if elem:                      
                elem['name']=elem['name'].split('.')[-1]
                if add2Children:
                    elems[toIndex].appendElement(elem)
                else:
                    seq.insert(elem,time2insertAt)
                e.accept()
            else:
                e.ignore()
        self.mrCtx.getSequence().repairTiming()
        self.mrCtx.seqModified()

    def parseEvent(self,e):
        mime = e.mimeData()
        data = dict()

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

class SeqDisplay(QtWidgets.QWidget):
    """
    Custom Qt Widget to select a sequence and an sequence element in gammaSTAR.
    """
    def __init__(self, *args, **kwargs):
        super(SeqDisplay, self).__init__()

        self.selectedElement = None
        # self.setAcceptDrops(True)
        self.icon_size = 150
        self.setMinimumWidth(800)
        self.setMinimumHeight(self.icon_size+30)
        self.resize(1000,280)
        
        self.mrCtx = mrlabContext()
        self.mrCtx.getSequence(seqname=kwargs.get('seqname'))

        layout = QtWidgets.QVBoxLayout(self)

        
        layoutH2 = QtWidgets.QHBoxLayout()
        bt_seqSelect = SequenceDropdown()

        bt_removeCurrent = QtWidgets.QPushButton("remove selected")
        bt_removeCurrent.clicked.connect(self.removeCurrentElement)

        bt_removeAll = QtWidgets.QPushButton("remove all")
        bt_removeAll.clicked.connect(self.removeAll)

        bt_squeeze = QtWidgets.QPushButton("squeeze timing")
        bt_squeeze.clicked.connect(self.squeeze)

        self.bt_addSpinEcho = QtWidgets.QPushButton("add spin-echo constraint")
        self.bt_addSpinEcho.clicked.connect(self.addSpinEcho)
        self.bt_addSpinEcho.setHidden(True)

        # now, for each button, lock in its sizeHint() as its minimum width:
        for btn in (bt_seqSelect, bt_removeCurrent, bt_removeAll, bt_squeeze, self.bt_addSpinEcho):
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            btn.setMinimumWidth(btn.sizeHint().width())
            layoutH2.addWidget(btn)        # no stretch, no extra alignment
        
        # 2) set up the label so it EXPANDS to fill whatever space is left
        self.sequenceTextDisplay = QLabel()
        self.sequenceTextDisplay.setSizePolicy(
            QSizePolicy.Expanding,      # can grow horizontally
            QSizePolicy.Fixed          # keep its normal height
        )
        self.sequenceTextDisplay.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layoutH2.addWidget(self.sequenceTextDisplay, 1, alignment=Qt.AlignLeft)  # stretch=1

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layoutH2.addStretch(1)
        layout.addLayout(layoutH2)

        self.sequenceDisplay =  myQListWidget()
        self.sequenceDisplay.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.sequenceDisplay.setUniformItemSizes(False)
        self.sequenceDisplay.installEventFilter(self)

        layout.addWidget(self.sequenceDisplay,stretch=1)

        self.sequenceDisplay.setIconSize(QtCore.QSize(self.icon_size, self.icon_size))
        self.sequenceDisplay.setMovement(QtWidgets.QListView.Static)
        self.sequenceDisplay.setViewMode(QtWidgets.QListView.IconMode)
        # self.sequenceDisplay.setLayoutMode(QtWidgets.QListView.Batched)
        # self.sequenceDisplay.setBatchSize(100)
        self.sequenceDisplay.setFlow(QtWidgets.QListView.LeftToRight)
        self.sequenceDisplay.setWrapping(False)
        self.sequenceDisplay.setResizeMode(QtWidgets.QListView.Adjust)
        self.sequenceDisplay.setDragEnabled(True)
        self.sequenceDisplay.setAcceptDrops(True)
        self.sequenceDisplay.currentItemChanged.connect(self.seqElement_selected)
        self.sequenceDisplay.itemDoubleClicked.connect(self._on_edit)
        self.mrCtx.sequenceChanged.connect(self._refresh)
        self._refresh()
        
    def seqElement_selected(self,e):
        if e:
            self.selectedElement = [t.text() for t in self.sequenceDisplay.selectedItems()]
            print('selected element:',self.selectedElement)
            self.selectedElement.append(e.text())
        else:
            self.selectedElement = None
        if self.selectedElement and len(self.selectedElement)==3:
            self.bt_addSpinEcho.setHidden(False)
        else:
            self.bt_addSpinEcho.setHidden(True)

    def _on_edit(self, item: QListWidgetItem):
        w = self.sequenceDisplay.itemWidget(item)
        if w is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit “{w.name}”")
        v = QVBoxLayout(dlg)
        print('on_edit',w.name,w.parameters)
        editor = ParameterEditor(w.parameter_dict, w.parameters, elem=w.elem, mrCtx=self.mrCtx, parent=dlg)
        v.addWidget(editor)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|
                                   QDialogButtonBox.Cancel)
        v.addWidget(buttons)
        buttons.accepted.connect(lambda: (editor.apply(), dlg.accept()))
        buttons.rejected.connect(lambda: (editor.reset(), dlg.reject()))

        if dlg.exec_():
            w._refresh(editor.value_dict)
            if self.mrCtx:
                self.mrCtx.updateSeqElement(w.elem)
        else:
            w._refresh(editor.value_dict)

    def eventFilter(self, obj, event):
        # Catch Ctrl+wheel on our list
        if obj is self.sequenceDisplay and event.type() == QEvent.KeyPress:
            if event.modifiers() & Qt.ControlModifier:
                text = event.text()
                step  = 10
                if len(text) and (text == '+' or ord(text) == 29):
                    self.icon_size += step
                elif text == '-':
                    self.icon_size = max(50, self.icon_size - step)
                    
                self._refresh()
                return True    # eat the event
        return super().eventFilter(obj, event)

    def removeCurrentElement(self):
        if self.selectedElement:
            [self.mrCtx.getSequence().remove(e) for e in self.selectedElement]
            self.mrCtx.seqModified()
            self.selectedElement = None
    
    def removeAll(self):
        self.mrCtx.getSequence().removeAll()
        self.mrCtx.seqModified()
        
    def squeeze(self):
        self.mrCtx.getSequence().squeezeTiming()
        self.mrCtx.seqModified()
    
    def addSpinEcho(self):
        if self.selectedElement and len(self.selectedElement)==3:
            self.mrCtx.getSequence().addSpinEchoConstraint(self.selectedElement)
            self.mrCtx.seqModified()

    def _refresh(self,e=None):
        # import time
        # stime = time.time()

        self.sequenceDisplay.clear()
        seq = self.mrCtx.getSequence()
        if seq:
            self.sequenceTextDisplay.setText(str(seq))
            elems = seq.getSortedElements()
            bps = [self.mrCtx.getBuildingBlock(e['template_name']) for e in elems]
            for i,bp in enumerate(bps):
                pixmap = QPixmap()
                pixmap.load(elems[i]['fname'])
                icon = QtGui.QIcon(pixmap)
                widget = ParameterSetWidget(icon=icon,name=elems[i]['name'],param_desc=elems[i].get('param_desc',{}), elem=elems[i], icon_size=self.icon_size)
                item = QListWidgetItem(elems[i]['name'], self.sequenceDisplay)
                item.setData(Qt.UserRole,elems[i])
                item.setSizeHint(widget.sizeHint())
                self.sequenceDisplay.addItem(item)
                self.sequenceDisplay.setItemWidget(item, widget)   
            
                
        # print(time.time()-stime)
    
    def dropEvent(self, event):
         print('dropEvent at SeqDisplay')
         fromIndex = self.currentRow()
         toIndex = self.count()
         ix = self.indexAt(event.pos())
         if ix.isValid():
             toIndex = ix.row()
         print("from {} to {}".format(fromIndex, toIndex))
         self.sequenceDisplay.dropEvent(self, event)

import sys
from PyQt5.QtWidgets import QApplication
if __name__ == '__main__':
    qapp = QApplication(sys.argv)
    mr=mrlabContext()
    seq=mr.getSequence()
    seq.append(mr.getElementForBpName('tableX'))
    seq.append(mr.getElementForBpName('gradient',param_values=dict(grad_flat=2000,gradX_amp=-200000.0,gradY_amp=0,gradZ_amp=600000)))
    seq.append(mr.getElementForBpName('rf_ns'))
    seq.append(mr.getElementForBpName('FA090_ns'))
    loop = mr.getElementForBpName('loop')
    loop.setLoopLength(2)
    loop.appendElement(mr.getElementForBpName('rf_ss_sym',param_values=dict(delay='loop_counter*2000+100')))
    loop.appendElement(mr.getElementForBpName('gradient',param_values=dict(grad_flat=2000,gradX_amp=-200000.0,gradY_amp=0,gradZ_amp=600000)))
    loop.appendElement(mr.getElementForBpName('gradient',param_values=dict(grad_flat=2000,gradX_amp=200000.0,gradY_amp=-400000,gradZ_amp=0)))
    seq.append(loop)
    seq.append(mr.getElementForBpName('gradient',param_values=dict(grad_flat=2000,gradX_amp=200000.0,gradY_amp=-400000,gradZ_amp=0)))
    win = SeqDisplay(seqname=seq['name'])
    win.show()
    qapp.exec()
    
