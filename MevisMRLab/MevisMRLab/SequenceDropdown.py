# -*- coding: utf-8 -*-
"""
Created on Tue Jun 24 10:51:06 2025

@author: mguenther
"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QComboBox, QVBoxLayout
from mrlabContext import mrlabContext

class SequenceDropdown(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(SequenceDropdown, self).__init__(*args, **kwargs)
        self.mrCtx = mrlabContext()

        # layout
        layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.combo.setMinimumWidth(100)
        layout.addWidget(self.combo,stretch=1)

        # fill it
        self._refresh_items()

        # when user picks something, tell the context
        self.combo.currentTextChanged.connect(self._on_user_select)

        # whenever mrCtx.currentSequenceName changes, update the dropdown
        # (so external loads/new deletes get reflected in this widget)
        self.mrCtx.sequenceChanged.connect(self._refresh_items)

    def _refresh_items(self):
        """Re-populate the menu with all available sequences."""
        # e.g. if you want “loaded” sequences:
        names = list(self.mrCtx._seq_cache.keys())
        # or if you want library-saved ones:
        # names = [n for n in self.mrCtx.lib.getAvailableSequences()
        #          if n != self.mrCtx.default_sequenceTemplate]

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        self.combo.blockSignals(False)

        # after repopulating, make sure the current mrCtx name is selected
        self._refresh_selection()

    def _refresh_selection(self):
        """Highlight whatever sequence is currently active in mrCtx."""
        current = self.mrCtx.currentSequenceName
        idx = self.combo.findText(current)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

    def _on_user_select(self, name):
        """When the user picks from the combo, switch the context to that seq."""
        if name:
            self.mrCtx.currentSequenceName = name
