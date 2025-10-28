#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 08:14:10 2024

@author: mague
"""

import logging
import sys
from mrlabContext import mrlabContext

from PyQt5 import QtWidgets, QtGui
 
from PyQt5.QtCore import QObject,\
                         pyqtSignal

from PyQt5.QtWidgets import QDialog, \
                        QVBoxLayout, \
                        QPushButton, \
                        QTextBrowser,\
                        QApplication

logger = logging.getLogger(__name__)

class XStream(QObject):
    _stdout = None
    _stderr = None

    messageWritten = pyqtSignal(str)

    def flush( self ):
        pass

    def fileno( self ):
        return -1

    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(str(msg))

    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class OutputLogger(QDialog):
    def __init__( self, parent = None ):
        super(OutputLogger, self).__init__(parent)

        # setup the ui
        
        self.mrCtx = mrlabContext()
        self._console = QTextBrowser(self)
        self._button  = QPushButton(self)
        self._button.setText('Clear list')

        # create the layout
        layout = QVBoxLayout()
        layout.addWidget(self._button)
        layout.addWidget(self._console)
        self.setLayout(layout)

        # create connections
        XStream.stdout().messageWritten.connect( self.insertTextFromStdout)
        XStream.stderr().messageWritten.connect( self.insertTextFromStdErr)

        self._button.clicked.connect(self._clearHistory)


    def insertTextFromStdout(self,t):
        self.insertNewText(t,QtGui.QColor(0,200,0))
        
    def insertTextFromStdErr(self,t):
        self.insertNewText(t,QtGui.QColor(255,0,0))
        
    def insertNewText(self,t,c=QtGui.QColor(0,0,0)):
        self._console.setTextColor(c)
        self._console.insertPlainText(t)
        # if t.startswith('Calc'):
        #     self.mrCtx.setStatus(t)
        self._console.moveCursor(QtGui.QTextCursor.End)
        
    def _clearHistory( self ):
        self._console.clear()
        

if ( __name__ == '__main__' ):
    logging.basicConfig()

    app = None
    if ( not QApplication.instance() ):
        app = QApplication([])

    dlg = OutputLogger()
    dlg.show()

    if ( app ):
        app.exec_()

class OutLog:
    def __init__(self, edit, out=None, color=None):
        """(edit, out=None, color=None) -> can write stdout, stderr to a
        QTextEdit.
        edit = QTextEdit
        out = alternate stream ( can be the original sys.stdout )
        color = alternate color (i.e. color stderr a different color)
        """
        self.edit = edit
        self.out = None
        self.color = color

    def write(self, m):
        if self.color:
            tc = self.edit.textColor()
            self.edit.setTextColor(self.color)

        self.edit.moveCursor(QtWidgets.QTextCursor.End)
        self.edit.insertPlainText( m )

        if self.color:
            self.edit.setTextColor(tc)

        if self.out:
            self.out.write(m)
