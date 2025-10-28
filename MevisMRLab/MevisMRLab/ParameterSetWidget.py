import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QListView,QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QLabel, QDialog, QDialogButtonBox,QMenu,QAction,
    QFormLayout, QDoubleSpinBox, QSpinBox, QPushButton, QSlider,QTabWidget,
    QMessageBox, QStyle, QGroupBox, QFormLayout, QLineEdit, QSplitter,QFrame,
)
from PyQt5.QtGui import QPixmap, QDrag, QPainter, QPen, QColor, QBrush, QPalette
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, QDataStream
from PyQt5.QtSvg import QSvgGenerator
import sys
import mrlab_utils as utils     

from Plot import Plot
from mrlabContext import mrlabContext
from ParameterEditor import ParameterEditor

def save_item_as_svg(w, filename):
    # # 1) Get the widget that’s actually displayed for this item
    # w = list_widget.itemWidget(item)
    # if w is None:
    #     raise RuntimeError("This list item has no associated widget!")

    # 2) Set up the SVG generator
    svg = QSvgGenerator()
    svg.setFileName(filename)
    svg.setSize(w.size())               # size in pixels
    svg.setViewBox(w.rect())            # match widget coords
    svg.setTitle("ListWidgetItem Export")
    svg.setDescription(f"Export of item '{w.elem['name']}'")

    # 3) Paint the widget into the SVG
    painter = QPainter(svg)
    w.render(painter)
    painter.end()

class ParameterSetWidget(QWidget):
    """
    A little card: icon on top, name underneath;
    if elem.getType()=='loop' then a horizontal sub-list below.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs.get('parent'))
        self._parent = kwargs.get('parent')
        self.elem=kwargs.get('elem')
        name=kwargs.get('name')
        icon=kwargs.get('icon')
        self.mrCtx=kwargs.get('mrCtx',mrlabContext())
        if not name:
            name = self.elem.get('name','unknown')
        self.name = name
        self.parameter_dict = kwargs.get('param_desc',{})
        self.parameters = self.elem.get('parameters', {}) if self.elem else {}
        self.icon_size = kwargs.get('icon_size',150)
        self.width = self.icon_size
        self.bg_color = QColor(180, 200, 255)
        self._width = self.icon_size
        self._height = self.icon_size+10

        # ─── Main layout ─────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        layout.setSpacing(5)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # 2) Name underneath
        name = self.elem.get('name', '') if self.elem else ''
        if self.elem.isNested():
            name_label = QLabel(f"<b>{name}: {self.elem.getLoopLength()}x</b>")
        else:
            name_label = QLabel(f"<b>{name}</b>")
        layout.addWidget(name_label, alignment=Qt.AlignHCenter,stretch=0)

        # ─── Optional loop-sublist ───────────────────────────
        if self.elem.isNested():
            self._width = self.icon_size + 60 
            layout.setContentsMargins(24,0,24,0)
            self.sequenceDisplay = loopQListWidget(seq=self.elem.getInternalSequence(),icon_size=self.icon_size-10)
            self.sequenceDisplay.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.sequenceDisplay.setUniformItemSizes(False)
            self.sequenceDisplay.setFlow(QListWidget.LeftToRight)
            self.sequenceDisplay.setWrapping(False)
            self.sequenceDisplay.setResizeMode(QListView.Adjust)
            self.sequenceDisplay.setDragEnabled(True)
            self.sequenceDisplay.setAcceptDrops(True)
            self.sequenceDisplay.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.sequenceDisplay.setMinimumWidth(self.icon_size*self.elem.getNumberOfElements())
            self.sequenceDisplay.setMaximumHeight(self._height-10)
            self.sequenceDisplay.setFrameShape(QFrame.NoFrame)
            self.sequenceDisplay.setFrameShadow(QFrame.Plain)
            self.sequenceDisplay.setAutoFillBackground(False)
            self.sequenceDisplay.viewport().setAutoFillBackground(False)
            # layout.addWidget(self.sequenceDisplay, alignment=Qt.AlignHCenter, stretch=1)

            # you can re-use your adjust_size logic here
            self.sequenceDisplay.currentItemChanged.connect(self.seqElement_selected)
            self.sequenceDisplay.itemDoubleClicked.connect(self._on_edit)
            # 1) Icon on top (if provided)
            data, _ = self.elem.getInternalSequence().getPlotsAndPulseq()
            pixmap = QPixmap()
            pixmap.load(self.mrCtx.createIcon(self.elem,data=data,showInfoBlock=False,width=4))
            icon = QIcon(pixmap)
            if icon is not None:
                icon_label = QLabel()
                # pick whatever size you like:
                pix = icon.pixmap(self.icon_size-10, self.icon_size-4)
                icon_label.setPixmap(pix)
                layout.addWidget(icon_label, alignment=Qt.AlignHCenter,stretch=1)
        else:
            # 1) Icon on top (if provided)
            if icon is not None:
                icon_label = QLabel()
                # pick whatever size you like:
                pix = icon.pixmap(self.icon_size-10, self.icon_size-4)
                icon_label.setPixmap(pix)
                layout.addWidget(icon_label, alignment=Qt.AlignHCenter,stretch=1)
        layout.addStretch(1)

        # ─── Final touches ───────────────────────────────────
        self.setLayout(layout)
        self.update_tooltip()

        self.refresh_display()

    def paintEvent(self, event):
        if self.elem.isNested():
            if self.elem.getLoopLength()==1:
                x1,y1,x2,y2 = self.rect().getCoords()
                y1 += 5
                y2 -= 8
                qp = QPainter(self)
                qp.setBrush(Qt.black)
                qp.setPen(QPen(Qt.black, 8, Qt.SolidLine))
                qp.drawLine(6,y1,6,y2)
                qp.drawLine(x2-6,y1,x2-6,y2)
                # qp.setPen(QPen(Qt.black, 4, Qt.SolidLine))
                # qp.drawLine(14,y1,14,y2)
                # qp.drawLine(x2-18,y1,x2-18,y2)
                qp.drawLine(6,y1,25,y1)
                qp.drawLine(6,y2,25,y2)
                qp.drawLine(x2-6,y1,x2-25,y1)
                qp.drawLine(x2-6,y2,x2-25,y2)
            else:
                x1,y1,x2,y2 = self.rect().getCoords()
                y1 += 5
                y2 -= 8
                qp = QPainter(self)
                qp.setBrush(Qt.black)
                qp.setPen(QPen(Qt.black, 8, Qt.SolidLine))
                qp.drawLine(6,y1,6,y2)
                qp.drawLine(x2-10,y1,x2-10,y2)
                qp.setPen(QPen(Qt.black, 4, Qt.SolidLine))
                qp.drawLine(14,y1,14,y2)
                qp.drawLine(x2-18,y1,x2-18,y2)
                qp.setPen(QPen(Qt.black, 1, Qt.SolidLine))
                qp.drawEllipse(18,int(y1+0.3*(y2-y1)),5,5)
                qp.drawEllipse(18,int(y1+0.7*(y2-y1)),5,5)
                qp.drawEllipse(x2-28,int(y1+0.3*(y2-y1)),5,5)
                qp.drawEllipse(x2-28,int(y1+0.7*(y2-y1)),5,5)
        super().paintEvent(event)
        
    def sizeHint(self) -> QSize:
        # return whatever default size you'd like
        return QSize(self._width, self._height)

    def minimumSizeHint(self) -> QSize:
        # if you want to enforce a minimum
        return QSize(self._width, self._height)
 
    def update_tooltip(self):
        lines = []
        for n, desc in self.parameter_dict.items():
            val  = self.parameters.get(n, "<n/a>")
            unit = desc.get("pulseq_unit", "")
            lines.append(f"{n}: {val}{unit}")
        self.setToolTip("\n".join(lines))

    def show_context_menu(self, position):
        # item = self.itemAt(position)
        # if not item:
        #     return
    
        menu = QMenu(self)
        save_action = QAction("Save permanently as building block", self)
        add_action = QAction("Add as building block to this session", self)
        menu.addAction(save_action)
        menu.addAction(add_action)
    
        # assume you have a list self.existing_bb_names
        save_action.triggered.connect(lambda: self._ask_and_save_bb(position=position))
        add_action.triggered.connect(lambda: self._ask_and_save_bb(storePermanently=False,position=position))
    
        menu.exec_(self.mapToGlobal(position))

    def _ask_and_save_bb(self,storePermanently=True,position=None):
        dlg = SaveAsBBDialog( existing_names=self.mrCtx.bblib.getAvailableBlueprints(),
                             initial_name=self.elem['name'], parent=self)
        if not dlg.exec_():
            return
        new_name = dlg.chosen_name
        # now actually save it
        icon = f"temp/{new_name}.svg"
        save_item_as_svg(self,icon)

        self.mrCtx.addBuildingBlockFromSeqElement(
            self.elem, new_name=new_name, icon=icon, storePermanently=storePermanently)
        
    def refresh_display(self,e=None):
        if self.elem.isNested():
            seq = self.elem.getInternalSequence()
            if seq:
                self.sequenceDisplay.clear()
                elems = seq.getSortedElements()
                bps = [self.mrCtx.getBuildingBlock(e['template_name']) for e in elems]
                for i,bp in enumerate(bps):
                    pixmap = QPixmap()
                    pixmap.load(elems[i]['fname'])
                    icon = QIcon(pixmap)
                    widget = ParameterSetWidget(icon=icon,name=elems[i]['name'],
                                               # param_desc=bp['properties']['param_desc'],
                                                param_desc=elems[i].get('param_desc',{}),
                                                elem=elems[i],icon_size=self.icon_size-10)
                    item = QListWidgetItem(elems[i]['name'], self.sequenceDisplay)
                    item.setData(Qt.UserRole,elems[i])
                    item.setSizeHint(widget.sizeHint())
                    self.sequenceDisplay.addItem(item)
                    self.sequenceDisplay.setItemWidget(item, widget)                


    def seqElement_selected(self,e):
        if e:
            self.selectedElement = [t for t in self.sequenceDisplay.selectedItems()]
            self.selectedElement = self.sequenceDisplay.selectedItems()
            print('selected element:',self.selectedElement)
            self.selectedElement.append(e.text())
        else:
            self.selectedElement = None

    def _on_edit(self, item: QListWidgetItem):
        w = self.sequenceDisplay.itemWidget(item)
        if w is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit “{w.name}”")
        v = QVBoxLayout(dlg)
        editor = ParameterEditor(w.parameter_dict, w.parameters, elem=w.elem, mrCtx=self.mrCtx, parent=dlg)
        v.addWidget(editor)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|
                                   QDialogButtonBox.Cancel)
        v.addWidget(buttons)
        buttons.accepted.connect(lambda: (editor.apply(), dlg.accept()))
        buttons.rejected.connect(lambda: (editor.reset(), dlg.reject()))

        if dlg.exec_():
            w._refresh(editor.value_dict)
            w.elem['parameters']=editor.value_dict
            print('on_edit',w.name,w.elem['parameters'])
            self.mrCtx.updateSeqElement(w.elem)
        else:
            w._refresh(editor.value_dict)

    def _on_edit2(self, event):
        # event.pos() is in viewport‐coordinates
        rect = self.rect
        relative_y = event.pos().y() - rect.top()
        if relative_y < rect.height() / 2:
            print(f"double-clicked UPPER half of: {rect}")
        else:
            print(f"double-clicked LOWER half of: {rect}")
        # don’t forget to call the base implementation so selection, signals, etc. still happen
        super().mouseDoubleClickEvent(event)
 
    def _refresh(self,parameters):
        if self.elem:
            self.elem['parameters']=parameters

class loopQListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        super(loopQListWidget, self).__init__()
        self.setAutoFillBackground(False)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.mrCtx = mrlabContext()
        self.seq = kwargs.get('seq')
        self.icon_size=kwargs.get('icon_size',150)
        self.setMinimumSize(120,self.icon_size)
    def dragMoveEvent(self,e):
        pass
 
    def dragEnterEvent(self, event):
        event.ignore()   # never accept the drag

    def dragMoveEvent(self, event):
        event.ignore()   # never accept movement

    def dropEvent(self, event):
        event.ignore()   # never accept a drop


class SaveAsBBDialog(QDialog):
    def __init__(self, existing_names, initial_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save as Building Block")
        self.existing = set(existing_names)
        self.chosen_name = None

        # Widgets
        self.label = QLabel("Enter new building-block name:")
        self.edit  = QLineEdit()
        self.edit.setText(initial_name)
        self.save_btn   = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")

        # Layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.edit)
        layout.addLayout(btn_layout)

        # Signals
        self.edit.textChanged.connect(self._on_text_changed)
        self.edit.returnPressed.connect(self._on_save)
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

        # Initial state
        self._on_text_changed(self.edit.text())

    def _on_text_changed(self, text):
        """Color background red if name exists, green otherwise."""
        text = text.strip()
        if not text:
            color = "white"
        elif text in self.existing:
            color = "#f88"  # light red
        else:
            color = "#8f8"  # light green
        self.edit.setStyleSheet(f"background:{color}")

    def _on_save(self):
        name = self.edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Name cannot be empty.")
            return
        if name in self.existing:
            # confirm overwrite
            reply = QMessageBox.question(
                self,
                "Overwrite?",
                f"'{name}' already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        # accept
        self.chosen_name = name
        self.accept()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mr=mrlabContext()
    seq=mr.getSequence()
    seq.insert(mr.getElementForBpName('gradient'),0)
    seq.insert(mr.getElementForBpName('rf_ns'),0)
    w=seq.getSortedElements()[-1]
    standard_pixmap = QStyle.SP_FileDialogNewFolder
    icon = app.style().standardIcon(standard_pixmap)    
    p = ParameterSetWidget(icon,w['name'],param_desc=w['param_desc'], elem=w)
    p.show()
    sys.exit(app.exec_())#

