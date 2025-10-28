#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 21:52:10 2024

@autor: mague
Enhanced: full positive/negative tag list via lecture config and lecture-specific subsets
"""
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QEvent, Qt, QSize
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QListView
from PyQt5.QtGui import QPixmap, QIcon, QColor
from pathlib import Path as FilePath
import json

from LectureLoader import LectureLoader
from mrlabContext import mrlabContext

class Selector(QtWidgets.QWidget):
    """
    Custom Qt Widget to select a sequence element with tag-based filtering
    and lecture-defined blueprint subsets.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs.get('parent'))
        self.mrCtx = mrlabContext()
        self.mrCtx.getSequence(seqname=kwargs.get('seqname'))
        self.currentSubset = ['basic']

        self.icon_width = 100
        self.icon_height = 60
        layout = QtWidgets.QVBoxLayout(self)

        # load subsets definitions
        self.bluePrintSubsets = {}
        filepath = FilePath.cwd() / 'setup'
        for file in filepath.glob("*.json"):
            with open(file, "r", encoding="utf-8") as _f:
                self.bluePrintSubsets.update(json.load(_f))

        # lecture selector
        self.lectureLoader = LectureLoader()
        layout.addWidget(self.lectureLoader)
        self.mrCtx.lectureChanged.connect(lambda config: self.update(config,reset=True))

        # tag selector
        self.tagSelector = QListWidget()
        self.tagSelector.setSelectionMode(QListWidget.NoSelection)
        self.tagSelector.setMaximumHeight(80)
        self.tagSelector.setToolTip("Filter building blocks by tags")
        self.tagSelector.itemChanged.connect(self._on_tags_changed)
        self.tagSelector.itemDoubleClicked.connect(self._on_tag_double_clicked)
        self.tagSelector.setWrapping(True)                            # allow items to wrap at the boundary :contentReference[oaicite:0]{index=0}
        self.tagSelector.setMovement(QtWidgets.QListView.Static)
        self.tagSelector.setViewMode(QtWidgets.QListView.IconMode)

        self.tagSelector.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # disable horizontal scroll :contentReference[oaicite:3]{index=3}
        self.tagSelector.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)      # vertical scroll as needed :contentReference[oaicite:4]{index=4}
 
        layout.addWidget(self.tagSelector)

        # blueprint icons
        self.blueprintSelector = QListWidget()
        layout.addWidget(self.blueprintSelector)
        self.blueprintSelector.setIconSize(QtCore.QSize(self.icon_width, self.icon_height))
        self.blueprintSelector.setMovement(QtWidgets.QListView.Static)
        self.blueprintSelector.setViewMode(QtWidgets.QListView.IconMode)
        self.blueprintSelector.setLayoutMode(QtWidgets.QListView.Batched)
        self.blueprintSelector.setBatchSize(3)
        self.blueprintSelector.setFlow(QtWidgets.QListView.LeftToRight)
        self.blueprintSelector.setWrapping(True)
        self.blueprintSelector.setResizeMode(QtWidgets.QListView.Adjust)
        self.blueprintSelector.setDragEnabled(True)        
        self.blueprintSelector.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.blueprintSelector.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # install event filter to catch key events
        self.blueprintSelector.installEventFilter(self)

        # initial fill
        self.mrCtx.bbLibChanged.connect(self._refresh)
        self.update({})

    def update(self, config={}, reset=False):
        """
        Refresh tags and subsets based on lecture config.
        config keys:
          - 'filter': list of positive tags
          - 'neg_filter': list of negative tags
          - 'subset': name of blueprint subset to display
        """

        pos = config.get('filter', [])
        neg = config.get('neg_filter', [])
        self.currentSubset = config.get('subset', None)

        # rebuild tag list
        self.tagSelector.blockSignals(True)
        self.tagSelector.clear()
        for tag in sorted(self.mrCtx.bblib.getAvailableBlueprintTags()):
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if tag in pos:
                item.setCheckState(Qt.Checked)
                item.setBackground(QColor('white'))
            elif tag in neg:
                item.setCheckState(Qt.PartiallyChecked)
                item.setBackground(QColor('red'))
            else:
                item.setCheckState(Qt.Unchecked)
                item.setBackground(QColor('white'))
            self.tagSelector.addItem(item)
        self.tagSelector.blockSignals(False)

        # initial refresh
        self._refresh(_filter=pos, _exclude=neg)
        
        self.mrCtx.removeAllSequenceFromCache()
        self.mrCtx.getSequence()

    def _on_tags_changed(self, item):
        """Gather include/exclude tags and refresh view."""
        include, exclude = [], []
        for i in range(self.tagSelector.count()):
            it = self.tagSelector.item(i)
            if it.checkState() == Qt.Checked:
                include.append(it.text())
                it.setBackground(QColor('white'))
            elif it.checkState() == Qt.PartiallyChecked:
                exclude.append(it.text())
            else:
                it.setBackground(QColor('white'))
        self._refresh(_filter=include, _exclude=exclude)

    def _on_tag_double_clicked(self, item):
        """
        Cycle through states on double‑click:
          ○ Unchecked → Checked   (include)
          ○ Checked   → PartiallyChecked (exclude)
          ○ PartiallyChecked → Unchecked
        """
        state = item.checkState()
        if state == Qt.Unchecked:
            item.setCheckState(Qt.Checked)
            item.setBackground(QColor("white"))
        elif state == Qt.Checked:
            item.setCheckState(Qt.PartiallyChecked)
            item.setBackground(QColor("red"))
        else:
            item.setCheckState(Qt.Unchecked)
            item.setBackground(QColor("white"))
        # trigger a refresh now that the tag state changed
        self._on_tags_changed(item)

    def _refresh(self, e=None, _filter=[], _exclude=[]):
        """Populate blueprint icons, applying positive tags, negative tags, and subset."""
        self.blueprintSelector.clear()

        # apply positive tag filter
        self.mrCtx.bblib.setFilterTags(_filter)

        # determine allowed blueprint names via subset
        allowed = None
        if self.currentSubset in self.bluePrintSubsets:
            allowed = set(self.bluePrintSubsets[self.currentSubset])

        types = self.mrCtx.bblib.getAvailableBlueprintTypes()
        types.sort(reverse=True)
        
        seen = set()

        for _type in types:
            bps_all = self.mrCtx.bblib.getBlueprintsByTypes(_type)
            # apply subset filter
            if allowed is not None:
                bps = {n: bps_all[n] for n in allowed if n in bps_all}
            else:
                bps = bps_all
            if not bps:
                continue

            # separator
            sep = QtWidgets.QListWidgetItem('--'+_type+'-'*(150-len(_type)))
            sep.setFlags(QtCore.Qt.NoItemFlags)
            sep.setFont(QtGui.QFont('Helvetica', 12, QtGui.QFont.Bold))
            sep.setForeground(QtGui.QColor('black'))
            self.blueprintSelector.addItem(sep)

            for name, bp in sorted(bps.items()):
                try:
                    if name in seen:
                        continue
                    seen.add(name)
                    tags = bp['properties'].get('tags', [])
                    if any(t in _exclude for t in tags):
                        continue
                    pix = QPixmap(bp['properties']['fname'])
                    icon = QIcon(pix)
                    item = QListWidgetItem(icon, name)
                    item.setData(Qt.UserRole, dict(self.mrCtx.getElementForBpName(bp['name'])))
                    size = QSize(self.icon_width+10, self.icon_height+20)
                    item.setSizeHint(size)
                    self.blueprintSelector.addItem(item)
                except Exception as e:
                    print('Error:',e,'\n',bp['name'],bp['id'],bp['properties']['fname'])
    
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

    def eventFilter(self, obj, event):
        # Handle Ctrl+Plus and Ctrl+Minus to resize icons
        if obj is self.blueprintSelector and event.type() == QEvent.KeyPress and event.modifiers() & Qt.ControlModifier:
            step = 10
            text = event.text()
            if len(text) and (text == '+' or ord(text) == 29):
                self.icon_width += step
                self.icon_height += step
                self._updateIconSizes()
                return True
            elif text == '-':
                self.icon_width = max(20, self.icon_width - step)
                self.icon_height = max(20, self.icon_height - step)
                self._updateIconSizes()
                return True
        return super().eventFilter(obj, event)

    def _updateIconSizes(self):
        size = QSize(self.icon_width, self.icon_height)
        self.blueprintSelector.setIconSize(size)
        for i in range(self.blueprintSelector.count()):
            item = self.blueprintSelector.item(i)
            if item.flags() == QtCore.Qt.NoItemFlags: continue
            item.setSizeHint(QSize(self.icon_width+10, self.icon_height+20))

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = Selector()
    win.resize(300,800)
    win.show()
    app.exec()
