import os
import glob
import json
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QComboBox, QVBoxLayout, QPushButton, 
    QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

from mrlabContext import mrlabContext

class LectureLoader(QWidget):
    def __init__(self, *args,**kwargs):
        super().__init__(kwargs.get('parent'))
        self.setWindowTitle("Lecture → Building Blocks")
        self.lectures_dir = kwargs.get('lectures_dir',"lectures")
        self.lecture_files = []
        self.current_bbBlocks = {}

        self.mrCtx = mrlabContext()
        self.mrCtx.getSequence(seqname=kwargs.get('seqname'))

        # Combo for selecting lecture JSON
        self.combo = QComboBox()
        self.combo.addItem("Select a lecture…")
        self.combo.currentIndexChanged.connect(self.onLectureSelected)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Lecture:"))
        layout.addWidget(self.combo)

        self.loadLectureList()

        initial_lecture = kwargs.get('initial_lecture', "available")
        if initial_lecture:
            # assume LectureLoader contains a QComboBox for lecture selection
            combo = self.findChild(QComboBox)
            if combo:
                idx = combo.findText(initial_lecture)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

        
    def loadLectureList(self):
        """Scan for .json files and populate the combo box."""
        pattern = os.path.join(self.lectures_dir, "*.json")
        self.lecture_files = sorted(glob.glob(pattern))
        for path in self.lecture_files:
            name = os.path.splitext(os.path.basename(path))[0]
            self.combo.addItem(name)

    def onLectureSelected(self, index,reset=True):
        if index <= 0 or index > len(self.lecture_files):
            return
        if reset:
            self.mrCtx.reset()
        path = self.lecture_files[index - 1]
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        blocks_info  = data.get("blocks", [])
        general_tags = data.get('general_tags',[])
        storePermanently = data.get('storePermanently',False)

        self._refreshBuildingBlocks(blocks_info,general_tags,storePermanently)
        self._configureUI(data)
        self.mrCtx.lectureChange(data)

    def _refreshBuildingBlocks(self, blocks_info, general_tags=[],storePermanently=False):
        for old_block in self.current_bbBlocks:
            # print('removing bp',old_block["name"])
            self.mrCtx.removeBuildingBlock(old_block["name"])
        
        self.mrCtx.bblib.setFilterTags()
        """Create new ones from JSON."""
        # create
        for info in blocks_info:
            bpId  = info["id"]
            bp = self.mrCtx.lib.getBlueprintByName(bpId)
            if bp:
                prop = info['properties']
                elem = self.mrCtx.getElementForBpName(bp['name'],param_values=prop.get("parameters",{}),param_units=prop.get("parameter_units","pulseq"),checkCompleteLib=True)
                elem['name'] = info.get("name", "")
                elem['type'] = prop.get("type", "")
                tags = prop.get("tags", [])
                tags.extend(general_tags)
                elem['tags'] = tags
                self.mrCtx.addBuildingBlockFromSeqElement(elem,storePermanently=storePermanently)
            else:
                print('cannot find blueprint for',bpId,'- skipping')
        self.current_bbBlocks = blocks_info

    def _configureUI(self,data):       
        print('_configureUI',data.get('toolVisibility'))
        for tool,vis in data.get('toolVisibility',{}).items():
            self.mrCtx.setToolVisibility(tool, vis)

        for tool,presetname in data.get('toolPreset',{}).items():
            self.mrCtx.setToolPreset(tool, presetname)

            
# --- 4) Run the example ---
if __name__ == "__main__":
    from Selector import Selector

    app = QApplication(sys.argv)
    selector = Selector()
    selector.resize(500,800)
    selector.show()
    sys.exit(app.exec_())
