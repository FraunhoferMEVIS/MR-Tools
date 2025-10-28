from PyQt5 import QtCore, QtWidgets
from jsonLibrary import JSONLibrary

from pathlib import Path as FilePath
import sys
from uuid import uuid4
import json   
import os 
import numpy as np
# newer numpy versions don't contain this, but pypulseq still relies on it
np.int = int
np.float = float
np.complex = complex
import pypulseq as pp
import mrlab_utils as utils
import MRzeroCore as mr0

import copy

# from MrSequence_constrained import MrSequence
from MrSequence import seqElementFactory, MrSequence

try:
    import sequenceEditor.gsContext as gsContext
except:
    pass

def round_nearest(x, a=1e-5,limit=False):
    if limit:
        return max(round(x / a) * a,0)
    else:
        return round(x / a) * a
 
class Status():
    FINISHED_OK = dict(description="finished without error", color="green", blockUI=False)
    STOPPED_ERROR = dict(description="stopped with error", color="purple", blockUI=False)
    RUNNING = dict(description="running", color="darkred", blockUI=True)
    UPDATE_REQUIRED = dict(description="update required", color="orange", blockUI=False)
    IDLE = dict(description="idle", color="lightgrey", blockUI=False)
    UNKNOWN = dict(description="unknown", color="darkyellow", blockUI=False)
    
# Implementation of gsContext for access to gammaSTAR Functionality
# uses Singleton pattern to create unique instance
class Singleton(type(QtCore.QObject), type):
    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

import math
# γ/2π for 1H in Hz/T
_GAMMA_HZ_PER_T = 42.576e6

class mrlabContext(QtCore.QObject, metaclass=Singleton):
    sequenceChanged = QtCore.pyqtSignal(dict)
    sequenceUpdated = QtCore.pyqtSignal(dict)
    phantomChanged = QtCore.pyqtSignal(str)
    bbLibChanged = QtCore.pyqtSignal()
    lectureChanged = QtCore.pyqtSignal(dict)
    statusChanged = QtCore.pyqtSignal(str)
    globalsChanged = QtCore.pyqtSignal(dict)
    toolVisibilityChanged = QtCore.pyqtSignal(str, bool)  # toolname, visible
    toolPresetChanged = QtCore.pyqtSignal(str, str)  # presetName, toolname

    UNIT_CONVERSION = {
        # ── delays and ramps are in μs both for UI and pulseq ─────────────
        ("loopLength","metric"): lambda x: x,
        ("loopLength","pulseq"): lambda x: x,
    
        ("delay",     "metric"): lambda x: x,
        ("delay",     "pulseq"): lambda x: x,
    
        ("grad_ramp", "metric"): lambda x: x,
        ("grad_ramp", "pulseq"): lambda x: x,
    
        ("grad_flat", "metric"): lambda x: x,
        ("grad_flat", "pulseq"): lambda x: x,
    
        # ── gradient amplitudes: UI in mT/m, pulseq in Hz/m ──────────────
        ("gradX_amp", "pulseq"): lambda x: x / (1e-3 * _GAMMA_HZ_PER_T),
        ("gradX_amp", "metric"): lambda x: x * (1e-3 * _GAMMA_HZ_PER_T),
    
        ("gradY_amp", "pulseq"): lambda x: x / (1e-3 * _GAMMA_HZ_PER_T),
        ("gradY_amp", "metric"): lambda x: x * (1e-3 * _GAMMA_HZ_PER_T),
    
        ("gradZ_amp", "pulseq"): lambda x: x / (1e-3 * _GAMMA_HZ_PER_T),
        ("gradZ_amp", "metric"): lambda x: x * (1e-3 * _GAMMA_HZ_PER_T),
    
        # ── RF amplitude: UI in degrees, pulseq in Hz (197.491 Hz ↔ 90°) ─
        ("rf_amp",    "pulseq"): lambda x: x * (90.0 / 197.491),
        ("rf_amp",    "metric"): lambda x: x * (197.491 / 90.0),
    
        # ── RF frequency offset: UI and pulseq both in Hz ────────────────
        ("rf_freq",   "metric"): lambda x: x,
        ("rf_freq",   "pulseq"): lambda x: x,
    
        # ── RF phase: UI in deg, pulseq in rad ────────────────────────────
        ("rf_phase",  "pulseq"): lambda x: x * (180.0 / math.pi),
        ("rf_phase",  "metric"): lambda x: x * (math.pi / 180.0),

        # ── ADC phase: UI in deg, pulseq in rad ────────────────────────────
        ("adc_phase",  "pulseq"): lambda x: x * (180.0 / math.pi),
        ("adc_phase",  "metric"): lambda x: x * (math.pi / 180.0),
    }

    def __init__(self,*args, **kwargs):
        super(mrlabContext, self).__init__()
        # Load library
        try:
            self.dir = FilePath(__file__).parent 
        except:
            self.dir = FilePath.cwd() 

        self.availableScannerTypes = [f.name for f in (self.dir/'buildingBlock').glob('*/')]
        self.default_sequenceTemplate = 'Empty sequence'
        self.state = {'curSeqName': kwargs.get('seqname',None),
                      'curBlueprintId': None,
                      'curSequenceElement': kwargs.get('path','root')
                      }
        self.state_subtasks={}
         # choose the scanner limits
        self.systems = dict( VidaFit = dict( system=pp.Opts(
                                max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s',
                                rf_ringdown_time=20e-6, rf_dead_time=100e-6,
                                adc_dead_time=20e-6, grad_raster_time=10 * 10e-6
                            ), fov = 200e-3, slice_thickness = 2e-3),
                        # TableTop =dict( system= pp.Opts(
                        #             max_grad=150, grad_unit='mT/m', max_slew=1000, slew_unit='T/m/s',
                        #             rf_ringdown_time=20e-6, rf_dead_time=100e-6,
                        #             adc_dead_time=20e-6, grad_raster_time=10 * 10e-6
                        #         ), fov = 20e-3, slice_thickness = 2e-3),
                        )
        self.tempDir = 'temp/'
        self.tempPulseqFile = self.tempDir+'.mrlab_dummy.seq'
        for filename in os.listdir(self.tempDir):
            file_path = os.path.join(self.tempDir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                
        self.seqDirectory = kwargs.get('seqDir',self.dir/'export')
        self.phantomDirectory = kwargs.get('seqDir',self.dir/'phantoms')
        self.phantomName = kwargs.get('phantomName',self.getAvailablePhantoms()[0])
        self.phantom = None
        self.tools = {}
        self.tools_visible = {}
        self.size = kwargs.get('size',(64,64,32))  

        self.reset(**kwargs)
    
    def getCounters(self):
        return copy.deepcopy(self._counters)

    def updateCounters(self,_updateDict={},signal=True):
        self._counters.update(_updateDict)
        if signal:
            self.globalsChanged.emit(self._counters)
        
    def setStatus(self,text):
        self.statusChanged.emit('STATUS: '+ text)
        
    def setSubtaskStatus(self,key,status):
        self.state_subtasks.update({key:status})
    
    def getSubtaskStatus(self,key):
        return self.state_subtasks.get(key,Status.UNKNOWN)
        
    def reset(self,**kwargs):
        scannerType = kwargs.get('scannerType','VidaFit')
        if scannerType in self.availableScannerTypes:
            self.scannerType = scannerType
        self.seq_path = self.dir / 'blueprints' / self.scannerType
        self.pulseq_path = self.dir / 'buildingBlock' / self.scannerType         
        self.bblib = JSONLibrary(self.pulseq_path)
        self.lib = JSONLibrary(self.seq_path)
        self.bbLibChanged.emit()
        self._seq_cache={}
        self._counters = dict(seq_loop_counter=0,seq_loop_length=4,seq_loop_loop_counter=0,seq_loop_loop_length=1,seq_loop_loop_loop_counter=0,seq_loop_loop_loop_length=1,)
        self.currentSequenceName = kwargs.get('seqname','seq')

    def getSystemInfo(self,_scannerType=None):
        if not _scannerType:
            _scannerType = self.scannerType
        if _scannerType in self.systems.keys():
            return self.systems.get(_scannerType)
       
    def setPhantomSize(self,size):
        self.setPhantom(self.phantomName,size)
        
    def setPhantom(self, phantomName=None,size=(64, 64, 32)):
        print('setting phanton name',phantomName)
        if not phantomName:
            phantomName = self.phantomName
        self.phantom = mr0.VoxelGridPhantom.load(self.phantomDirectory/phantomName)
        # self.phantom = self.phantom.interpolate(*size).slices([int(size[-1]/2)])
        # self.phantom = self.phantom.interpolate(*size).slices(list(range(size[-1])))
        self.phantom_built = None
        self.phantomName = phantomName
        self.phantomSize = size
        self.phantomChanged.emit(phantomName)
                    
    def getAvailablePhantoms(self):
        l = list(self.phantomDirectory.glob('*.npz'))
        if not len(l):
            # '3T', '3T-highres-fat'
            mr0.generate_brainweb_phantoms(self.phantomDirectory, '3T-highres-fat')
            l = list(self.phantomDirectory.glob('*.npz'))
        return [_l.name for _l in l]
    
    def getCurrentPhantom(self):
        if not self.phantom:
            self.setPhantom()
        return self.phantom
    
    def getBuiltPhantom(self,size=(64,64,32),slices=[0]):
        if not self.phantom:
            self.setPhantom()
        interp_phantom = self.phantom.interpolate(*size)
        # interp_phantom = self.phantom.interpolate(*size).slices(slices)
        b = interp_phantom.build()
        return b


    def registerTool(self, name, tool, visible=True):
        if not hasattr(self, 'tools'):
            self.tools = {}
            self.tools_visible = {}
        if name in self.tools.keys():
            print('Warning: tool with name', name, 'already registered. Overwriting it!')
        self.tools[name] = tool
        self.tools_visible[name] = visible
        self.toolVisibilityChanged.emit(name, visible)
        print('Tool', name, 'registered')

    def setToolVisibility(self, name, visible):
        if not hasattr(self, 'tools_visible'):
            self.tools_visible = {}
        if name not in self.tools_visible:
            print('Warning: tool', name, 'not registered, cannot set visibility.')
            return
        if self.tools_visible[name] != visible:
            self.tools_visible[name] = visible
            self.toolVisibilityChanged.emit(name, visible)

    def setToolPreset(self, name, presetName):
        if not hasattr(self, 'tools_presets'):
            self.tools_presets = {}
        if name not in self.tools:
            print('Warning: tool', name, 'not registered, cannot set preset.')
            return
        self.tools_presets[name] = presetName
        self.toolPresetChanged.emit(presetName,name)
        
    def getToolVisibility(self):
        if not hasattr(self, 'tools_visible'):
            self.tools_visible = {}
        return self.tools_visible.copy()

    def isToolVisible(self, name):
        return self.getToolVisibility().get(name, False)

    def safePathHandling(f):
        def _func(self,*args, **kwargs):
            path = kwargs.get('path',None)
            seqname = kwargs.get('path',None)
            if not path:
                path = self.currentSequenceElement
            if path not in self.getSequence(seqname=seqname).sequenceElements.keys():
                print('Error: in current sequence no path exists with name ',path,file=sys.stderr)
                return None
            return f(self,path=path)
        return _func

    def updateSeqElement(self,elem, **kwargs):
        seq = kwargs.get('seq',self.getSequence(seqname=kwargs.get('seqname')))
        seq.updateSeqElement(elem)
        seq.repairTiming()
        if kwargs.get('signal',True):
            self.handleSequenceChanged()


    def createBlueprintsFromPulseqFile(self):
        _list = list(self.pulseq_path.glob("**/*.seq"))
        _list.extend(list(self.pulseq_path.glob("**/*.pulseq")))
        for fname in _list:
            with open(fname, "r") as file1:
                seq_dump = file1.read() 
                seq_dump.replace('\nName \n', '\nName dummy\n')
            self.createPulseqBlueprint(fname.stem,seq_dump,True)
                        
            
    def getAvailableBuildingBlocks(self,checkCompleteLib=True):
        if checkCompleteLib:
            self.bblib.setFilterTags(doNotStore=True)
        bb =  self.bblib.getAvailableBlueprints()
        if checkCompleteLib:
            self.bblib.applyFilterTags()        
        return bb
    
    def getBuildingBlock(self, bb_name,checkCompleteLib=True):
        if checkCompleteLib:
            self.bblib.setFilterTags(doNotStore=True)
        bb = self.bblib.getBlueprintByName(bb_name)
        if checkCompleteLib:
            self.bblib.applyFilterTags()        
        return bb
    
    def getAvailableBlueprints(self,checkCompleteLib=True):
        if checkCompleteLib:
            self.lib.setFilterTags(doNotStore=True)
        bp =  self.lib.getAvailableBlueprints()
        if checkCompleteLib:
            self.lib.applyFilterTags()        
        return bp
    
    def getBlueprint(self, bp_name,checkCompleteLib=True):
        if checkCompleteLib:
            self.lib.setFilterTags(doNotStore=True)
        bp = self.lib.getBlueprintByName(bp_name)
        if checkCompleteLib:
            self.lib.applyFilterTags()        
        return bp
    
    def createDefaultDescriptionForPulseqBlueprints(self,name,data):
        text = 'This is performed outside mrlabContext. See file createPulseqSamples.py'
        print(text)
        return text
    
    def writePulseqFilesFromBlueprints(self):
        l = self.getBlueprintIdsByTags('pulseq')
        for bpId in l:
            bp=self.getBlueprintById(bpId)
            with open(self.pulseq_path/bp.get('name')+'.seq', "w") as file1:
               file1.dump(bp['definitions']['pulseq_element.pulseq']['script']) 
                
    @property    
    def currentSequenceName(self):
        return self.state.get('curSeqName')
    
    @currentSequenceName.setter    
    def currentSequenceName(self,seqname,urgeUpdate=False):
        if seqname==self.currentSequenceName and not urgeUpdate:
            return
        self.state.update({'curSeqName':seqname})
        self.getSequence(seqname=seqname)
        self.currentSequenceElement = 'root'
        self.handleSequenceChanged()

    def removeSequence(self,seqname):
        if seqname in self._seq_cache.keys():
            _seq = self._seq_cache.pop(seqname)
            _seq.removeAll()

    def removeAllSequenceFromCache(self):
        self._seq_cache = {}
                    
    def getSequence(self,*args, **kwargs):
        seqname = kwargs.get('seqname',self.currentSequenceName)
        if not seqname:
            seqname = 'seq'
        newlyCreated=False
        if seqname in self._seq_cache.keys() and not kwargs.get('uniqueKey',False):
            return self._seq_cache[seqname]
        else:
            seqname = self.getUniqueName(seqname,existing=self._seq_cache.keys())
            if kwargs.get('autoCreate',True):
                if seqname in self.lib.getAvailableSequences():
                    print(seqname,': found it in lib!')
                    bp= self.lib.getBlueprintByName(seqname)
                else:              
                    print('creating it from scratch!')
                    bp = self.createNewSequenceBlueprint(seqname=seqname)
                    seqname = bp['name']
                newlyCreated=True
            else:
                return
            seq = self.parseSequenceBlueprint(bp)
            self._seq_cache[seqname] = seq
            if newlyCreated:
                print(seqname,'newly created')
                if kwargs.get('activate',True):
                    self.currentSequenceName = seqname
        return self._seq_cache[seqname]

    def convertUnits(self,params,current_units='pulseq'):
        conv_params=dict()
        for k,v in params.items():
            fn = self.UNIT_CONVERSION.get((k, current_units))
            if not fn:
                fn = lambda x: x
                print('warning: unknown parameter for conversion:',k)
            if isinstance(v,str):
                s = v.split('*')
                new_v = "*".join(s[:-1])+"*"+str(fn(eval(s[-1])))
                conv_params.update({k:new_v})
            else:
                conv_params.update({k:fn(v)})
        return conv_params

    def convertUnitsToMetric(self,params,current_units='pulseq'):
        if current_units == 'metric':
            return params
        if current_units == 'pulseq':
            return self.convertUnits(params,current_units)
        raise ValueError("Unsupported unit type",current_units)

    def convertUnitsToPulseq(self,params,current_units='metric'):
        if current_units == 'metric':
            return self.convertUnits(params,current_units)
        if current_units == 'pulseq':
            return params
        raise ValueError("Unsupported unit type",current_units)

    
    def createIcon(self,elem, data=None, showInfoBlock=True, width=3):
        if not data:
            data,_f = elem.create_plots_and_pulseq(_globals=self.getCounters())
        # convert values from pulseq to display values
        fname = utils.make_icon(None,elem['name'],data,self.convertUnits(elem['parameters']),
                                        _type=elem.get('type'),showInfoBlock=showInfoBlock,width=3)
        return fname

    def handleSequenceChanged(self):
        self.full_data = {}
        self.pulseq = None
        self.sequenceChanged.emit(self.state)
        self.full_data, self.pulseq = self.getSequence().getPlotsAndPulseq(_globals=self.getCounters())
        self.pulseq.write(self.tempPulseqFile,create_signature=False)
        print('sequence updated')
        self.sequenceUpdated.emit(self.state)

    def getPlotData(self,complete=False):
        if complete:
            accepted_keys = self.full_data.keys()
        else:
            accepted_keys = ['grx','gry','grz','rf','rf_am','adc',]
        new_dict = {}
        for k,v in self.full_data.items():
            if k in accepted_keys:
                new_dict.update({k:v})
        return copy.deepcopy(new_dict)
    
    def lectureChange(self,lectureConfig={}):
        self.getSequence().removeAll()
        self.seqModified()
        self.lectureChanged.emit(lectureConfig)

    def createNewBpIdForSeq(self,seqname=None):
        self.getSequence(seqname)['bpId'] = str(uuid4())
    
    def seqModified(self,modSeq=None):
        if modSeq:
            modSeq.repairTiming()
            self._seq_cache[modSeq['name']] = modSeq
        self.handleSequenceChanged()
        
    def getElementForBpId(self,bpId,name=None,param_values = {},param_units='pulseq',checkCompleteLib=False):
        bp = self.bblib.getBlueprintById(bpId)
        if not bp:
            return
        return self.getElementFromBpDescription(bp,name,param_values,param_units)
        # if not name:
        #     name = bp['name']
        # elem = dict(name = name,bpId=str(uuid4()),template_bpId = bpId, 
        #             template_name = bp['name'],sequence = bp.get('sequence',[]),tstart=0)
        # elem.update(bp.get('properties'))
        # elem['parameters'].update(self.convertUnitsToPulseq(param_values,param_units))
        # return seqElementFactory.create(copy.deepcopy(elem))

    def getElementForBpName(self,bpName,name=None,param_values = {},param_units='pulseq',checkCompleteLib=False):
        bp = self.bblib.getBlueprintByName(bpName)
        if not bp:
            return
        return self.getElementFromBpDescription(bp,name,param_values,param_units)
        # if not name:
        #     name = bp['name']
        # elem = dict(name = name,bpId=str(uuid4()), template_name = bpName, 
        #             template_bpId = bp['id'],sequence = bp.get('sequence',[]),tstart=0)
        # elem.update(bp.get('properties'))
        # elem['parameters'].update(self.convertUnitsToPulseq(param_values,param_units))
        # return seqElementFactory.create(copy.deepcopy(elem))

    def getElementFromBpDescription(self,bp,name=None,param_values = {},param_units='pulseq',checkCompleteLib=False):
        if not name:
            name = bp['name']
        name = self.getUniqueName(name,existing=[e['name'] for e in self.getSequence().getSortedElements()])
        elem = dict(name = name,id=str(uuid4()), template_name = bp.get('template_name',bp['name']), 
                    template_bpId = bp.get('template_bpId',bp['id']),sequence = bp.get('sequence',[]),tstart=0)
        elem.update(bp.get('properties'))
        elem['parameters'].update(self.convertUnitsToPulseq(param_values,param_units))
        elem = seqElementFactory.create(copy.deepcopy(elem))
        if not elem['fname'] or not os.path.isfile(elem['fname']) or len(param_values)>0:
            elem['fname'] = self.createIcon(elem)
        return elem
        
    def insertElement(self,bpId,time,name=None,seqname=None):
        if not seqname:
            seqname = self.currentSequenceName
        elem = self.getElementForBpId(bpId,name)
        if seqname in self._seq_cache.keys() and elem:
            newName = self._seq_cache[seqname].insert(elem,time,uniqueKey=True)
            self.handleSequenceChanged()

            return newName
        
    def parseSequenceBlueprint(self,bp):
        defs = bp['definitions']
        seDefs = [i for i,se in defs.items() if se.get('type','undefined')=='sequence_element_definition']
        seq = MrSequence(name=bp['name'], elements={}, bpId=bp['id'])
        for se in seDefs:
            par_tstart = defs.get(se+'.tstart')
            par_duration = defs.get(se+'.duration')
            par_parameters = {k.split('.')[-1]:eval(v.get('script','0').replace('return','')) for k,v in defs.items() if k.startswith(se+'.parameters.')}
            if par_tstart and par_duration:
                elem = self.getElementForBpId(defs[se].get('blueprint_id'))
                elem.update(dict(name=se, parameters=par_parameters,
                                 duration= float(par_duration.get('script','0').replace('return',''))))   
                seq.insert(seqElementFactory(elem),float(par_tstart.get('script','0').replace('return','')))
        return seq

    def saveSequenceToBlueprint(self,seq,*args, **kwargs):
        seq.remove('bpId')
        bp = self.createNewSequenceBlueprint(seqname=kwargs.get('seqname',seq['name']),addToLib=False)
        for name,elem in seq['elements'].items():
            bp['definitions'].update({**self.getDefinitions(elem)})
        tags=set(bp['properties'].get('tags',[]))
        tags.add('sequence')
        bp['properties']['tags'] = list(tags)
        self.lib.addBlueprint(bp,copyToDir=kwargs.get('dirName'),type='../sequence')
        
        self.handleSequenceChanged()

        return bp

    def getDefinitions(self,elem):
        se_d = dict(blueprint_id=elem['template_bpId'],name = elem['name'],type = "sequence_element_definition")
        p_t = dict(name = elem['name']+'.tstart',script='return '+str(elem.getTstart()),
                  sources={}, type = "parameter_definition")
        p_d = dict(name = elem['name']+'.duration',script='return '+str(elem.getDuration()),
                  sources={}, type = "parameter_definition")
        defs = {elem['name']:se_d,elem['name']+'.tstart':p_t, elem['name']+'.duration':p_d}
        params = elem.get('parameters')
        for p in params:
            p_p = dict(name = elem['name']+'.parameters.'+p,script='return '+str(params[p]),
                      sources={}, type = "parameter_definition")
            defs.update({elem['name']+'.parameters.'+p:p_p})
            
        return defs

    def addBuildingBlock(self,bb_desc,storePermanently=True):
        self.bblib.addBlueprint(bb_desc,storePermanently=storePermanently)
        bb = self.getBuildingBlock(bb_desc['name'])
        if not bb_desc['properties'].get('fname'):
            bb['properties']['fname'] = self.createIcon(self.getElementForBpName(bb_desc['name']))
        self.bblib.addBlueprint(bb_desc,storePermanently=storePermanently)

    def removeBuildingBlock(self,bb_name,removePermanently=False):
        self.bblib.removeBlueprint(blueprintName=bb_name,removePermanently=removePermanently)

    def addBuildingBlockFromSeqElement(self,elem,new_name=None,icon=None,storePermanently=True):
        if not new_name:
            new_name = self.getUniqueName(elem['name'],existing=self.bblib.getAvailableBlueprints())
        elem['name'] = new_name
        desc = elem.getDescription(icon=icon)
        self.addBuildingBlock(desc,storePermanently=storePermanently)

    def removeBuildingBlockFromSeqElement(self,elem,removePermanently=True):
        self.bblib.removeBlueprint(elem['template_name'],removePermanently=removePermanently)

    def createNewSequenceBlueprint(self,*args, **kwargs):
        seqname = kwargs.get('seqname','seq')
        if not seqname:
            seqname = 'seq'
        seqname = self.getUniqueName(seqname, existing=self.lib.getAvailableBlueprints())        
        bp=self.lib.getBlueprintByName(self.default_sequenceTemplate)
        # newBp = dict(   id=kwargs.get('bpId',str(uuid4())), 
        newBp = dict(   id=str(uuid4()), 
                        name=seqname,
                        properties={'tags':['sequence','teaching']},
                        definitions = bp['definitions'])
        
        if kwargs.get('addToLib',True):
            self.lib.addBlueprint(newBp,type='../sequence')

        return newBp
        
    def getUniqueName(self,_prefix, existing=None, doNotTrim = False):
        if not doNotTrim:
            _prefix = _prefix.rstrip('0123456789')
        if not existing:
            existing = self._seq_cache.get('elements',{}).keys()
        _suffix = ''
        while _prefix+str(_suffix) in existing:
            if _suffix:
                _suffix += 1
            else:
                _suffix = 1
        return _prefix+str(_suffix)

    def getAvailableCachedSequences(self):
        return self._seq_cache.keys()
    
    def createPulseqBlueprint(self,name,script,addToLib = True,bpId=None):
        if not bpId:
            bpId = str(uuid4())
        _defs = {   'pulseq_element': {
                        'blueprint_id': '6aa187ab-7e44-4437-b766-aac0033c6c74',
                        'name':  'pulseq_element',
                        'type': 'sequence_element_definition'
                        },
                    'pulseq_element.pulseq': {
                        'name': 'pulseq_element.pulseq',
                        'script': script,
                        'sources': {},
                        'type': 'parameter_definition'
                    },
                    'pulseq_element.tstart': {
                        'name': 'pulseq_element.tstart',
                        'script': 'return 0',
                        'sources': {},
                        'type': 'parameter_definition'
                    },
                    'tstart': {
                        'name': 'tstart',
                        'script': 'return 0',
                        'sources': {
                        },
                        'type': 'parameter_definition'
                    },
                    'duration': {
                        'name': 'duration',
                        'script': 'return 0',
                        'sources': {
                        },
                        'type': 'parameter_definition'
                    },
                }
        pulseq_bp = dict(  id=bpId, 
                             name=str(name),
                             definitions = _defs,
                             properties={'tags':['pulseq','teaching','buildingBlock']})
        if addToLib:
            self.lib.addBlueprint(pulseq_bp,type='buildingBlock')
            
        return pulseq_bp

     
if __name__ == '__main__':
    mr=mrlabContext()

    # print(mr.lib.getAvailableBlueprintIds())    
    seq=mr.getSequence(autoCreate=True)
    seq.insert(mr.getElementForBpName('epi2D_RO'),0)
    seq.insert(mr.getElementForBpName('rf_ns'),0)
    seq.insert(mr.getElementForBpName('loop'),0)
    print(seq)