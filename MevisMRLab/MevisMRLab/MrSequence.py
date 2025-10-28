#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:12:19 2024

@author: mague
"""

import mrlab_utils as utils
import pypulseq as pp
import os
from uuid import uuid4

def round_nearest(x, a=1e-5,limit=False):
    if limit:
        return max(round(x / a) * a,0)
    else:
        return round(x / a) * a

class seqElementFactory:
    _registry = {}

    @classmethod
    def register(cls, key, element_cls):
        """
        Registers an element class under the given key.
        key: str — e.g. 'standard' or 'loop'
        element_cls: class — must be a subclass of seqElement
        """

        cls._registry[key] = element_cls

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Creates and returns an instance of the class registered under `key`.
        Raises KeyError if no such class is registered.
        """
        if args[0].get('template_name').lower()=='loop' or args[0].get('type','')=='macro':
            key = 'loop'
        else:
            key = 'standard'
        try:
            element_cls = cls._registry[key]
        except KeyError:
            raise KeyError(f"No seqElement registered under key '{key}'")
        return element_cls(*args, **kwargs)

class seqElement(dict):
    def __init__(self,*args, **kwargs):
        from mrlabContext import mrlabContext
        super().__init__(*args, **kwargs)
        self._type = 'standard'

        if 'loop' not in self['name']:
            self.setDuration(self.getDuration(update=True,_globals=mrlabContext().getCounters()))

    def isNested(self):
        return False
    
    def _delete(self):
        pass
    
    def getNumberOfElements(self):
        return 1
    
    def getType(self):
        return self._type
    
    def insertChild(self,child,at):
        print('standard seqElement does not have children')
        return
    
    def getDuration(self,counter=0,update=False,_globals={}):
        from mrlabContext import mrlabContext
        if not len(_globals):
            print('no globals set!')
            _globals.update(mrlabContext().getCounters())
        if update:
            curBp = mrlabContext().getBuildingBlock(self['template_name'],checkCompleteLib=True)
            _globals.update(self['parameters'])
            _pulseq = utils.update_pulseqfile(curBp['properties']['pulseqFile'],f"temp\\{self['name']}_get_duration_dummy.seq"
                                              ,_globals,systemInfo=mrlabContext().getSystemInfo()['system'])
            return _pulseq.duration()[0]
        else:
            return self.get('duration',0.0)
   
        
    def setDuration(self,dur):
        if dur>=0:
            self['duration'] = dur
        
    def getTstart(self,counter=0,_globals={}):
        return self.get('tstart',0.0)

    def getDescription(self, **kwargs):
        from mrlabContext import mrlabContext
        icon =  kwargs.get('icon',mrlabContext().createIcon(self))
        desc = dict(name = self['name'], id=self.get('id',str(uuid4())), template_bpId=self['template_bpId'], template_name=self['template_name'], 
                    properties = dict(fname = icon,
                                      pulseqFile = self['pulseqFile'],
                                      param_desc = self['param_desc'],
                                      parameters = self['parameters'],
                                      type = self['type'], tags=list(self['tags']), 
                                      NPhase = 64, NRead = 64, 
                                      duration = self.getDuration(), scannerType = self['scannerType'])
                )
        return desc
        
    def create_plots_and_pulseq(self,_globals={}):
        from mrlabContext import mrlabContext
        # will output plots and pulseq sequence
        fname_out = f"temp\\{self['name']}_pulseq.seq"
        _globals.update(self.get('parameters',{}))
        curBp = mrlabContext().getBuildingBlock(self['template_name'])
        # let's calculate the plots via pypulseq
        _pulseq = utils.update_pulseqfile(curBp['properties']['pulseqFile'],fname_out,_globals,systemInfo=mrlabContext().getSystemInfo()['system'])
        full_data = utils.waveforms_export(_pulseq)
        self.setDuration(_pulseq.duration()[0])
        # pulseq.write(fname_out,create_signature=False)
        return full_data,_pulseq
    
    def getCounterKey(self):
        return "_"
        
class loop_seqElement(seqElement):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self._type = 'loop'
        from mrlabContext import mrlabContext
        seqname = mrlabContext().currentSequenceName or 'seq' +'.'+self.get('name','loop')
        seqname = self.get('name','loop')
        self.internal_seq = mrlabContext().getSequence(seqname=seqname,activate=False,uniqueKey=True)
        mrlabContext().globalsChanged.connect(self.updateCounter)
        self.setCounter(0)
        children = args[0].get('sequence')
        if children:
            for child in children:
                self.internal_seq.append(mrlabContext().getElementFromBpDescription(child))

    def _delete(self):
        from mrlabContext import mrlabContext
        mrlabContext().removeSequence(self.internal_seq.name)
        
    def getNumberOfElements(self):
        return len(self.internal_seq.getSortedElements())
    
    def getDescription(self, **kwargs):
        desc = super().getDescription(**kwargs)
        desc['template_bpId']=self['template_bpId']
        desc['template_name']=self['template_name']
        desc['properties'].update({'duration':self.getDuration()})
        desc['properties'].update({'type':kwargs.get('type','macro')})
        desc['sequence'] = [c.getDescription() for c in self.internal_seq.getSortedElements()]
        return desc
        
    
    def setCounter(self,counter=0):
        from mrlabContext import mrlabContext
        if counter>=0 and counter<self.getLoopLength():
            self.counter = counter
            mrlabContext().updateCounters({self.getCounterKey():0})
            return True
        return False
        
    def updateCounter(self,_globalCounters = {}):
        self.counter = _globalCounters.get(self.getCounterKey(),0)
        _globalCounters.update({self.getCounterKey():self.counter})
        _globalCounters.update({self.getLengthKey():self.getLoopLength()})
        # _ = self.getInternalSequence(_globals=_globalCounters)
        
    def getCounterKey(self):
        return f"{self['name']}.counter".replace('.','_')
    def getLengthKey(self):
        return f"{self['name']}.length".replace('.','_')
    
    def getLoopLength(self):
        return self.get('parameters').get('loopLength',1)    
    
    def setLoopLength(self, maxCount):
        if maxCount>=0:
            self['parameters']['loopLength'] = maxCount
    
    def isNested(self):
        return True

    def getInternalSequence(self,_globals={}):
        # Prevent re-entrant refreshes
        if getattr(self, '_refreshing', False):
            return self.internal_seq

        self._refreshing = True
        try:
            self.internal_seq._refresh(_globals)
        finally:
            self._refreshing = False
        return self.internal_seq    

    def appendElement(self,elem,name=None):
        from mrlabContext import mrlabContext
        if not name:
            name = self.get('name')+'.'+elem.get('name').split('.')[-1]
        elem['name'] = name
        return self.getInternalSequence().insert(elem,self.getInternalSequence().getDuration(),uniqueKey=True)
         
    def removeElement(self,elem):
        return self.internal_seq.remove(elem['name'])
         
    def remove(self,name):
        return self.internal_seq.remove(name)
         
    def shiftElement(self,name,to=0):
        return self.internal_seq.shiftElement(name,to)

    def getDuration(self,counter=-1,update=True,_globals={}):
        # ─── skip empty loop ───────────────────────────────────────────────────
        if not self.internal_seq.getSortedElements():
            return 0

        # ─── prime globals with any outside counters ─────────────────────────
        from mrlabContext import mrlabContext
        _globals.update(mrlabContext().getCounters())

        # ─── single‐iteration override ────────────────────────────────────────
        if counter >= 0:
            if not self.setCounter(counter):
                return 0
            return self.getInternalSequence(_globals=_globals).getDuration()

        # ─── guard against re-entrant getDuration ────────────────────────────
        if getattr(self, '_computingDuration', False):
            return 0
        self._computingDuration = True
        try:
            dur = 0
            for _c in range(self.getLoopLength()):
                # update the correct counter each pass
                _globals[self.getCounterKey()] = _c
                dur += self.getInternalSequence(_globals=_globals).getDuration()
            return dur
        finally:
            self._computingDuration = False
            
    def create_plots_and_pulseq(self,_globals={}):
        from mrlabContext import mrlabContext
        _globals.update({self.getLengthKey():self.getLoopLength()})

        fname_out = f"temp\\{self['name']}_pulseq.seq"
        pulseq = None
        curT = 0
        if not len(self.internal_seq.getSortedElements()):
            return {},None
        
        pulseq = pp.Sequence(mrlabContext().getSystemInfo()['system'])
        full_data={'grx':{'t':[],'v':[]}, 
                   'gry':{'t':[],'v':[]}, 
                   'grz':{'t':[],'v':[]}, 
                   'rf':{'t':[],'v':[]}, 
                   'rf_am':{'t':[],'v':[]}, 
                   'adc':{'t':[],'v':[]}, 
                  }
        for counter in range(self.getLoopLength()):
            key = self.getCounterKey()
            _globals.update({key:counter})
            dataToAdd,pulseqToAdd = self.getInternalSequence(_globals=_globals).getPlotsAndPulseq(mrlabContext().getSystemInfo()['system'])
            
            for d in dataToAdd.keys():
                t = full_data.get(d,dict(t=[],v=[]))['t']
                t.extend([_t+curT for _t in dataToAdd[d]['t']])
                v = full_data.get(d,dict(t=[],v=[]))['v']
                v.extend(dataToAdd[d]['v'])
                full_data[d] = dict(t=t,v=v)
                
            if pulseqToAdd:
                for i in range(len(pulseqToAdd.block_events)):
                    pulseq.add_block(pulseqToAdd.get_block(i+1))
                curT += round_nearest(pulseqToAdd.duration()[0])

        # pulseq.write(fname_out,create_signature=False)
        return full_data,pulseq
    
        
seqElementFactory.register('standard', seqElement)
seqElementFactory.register('loop',     loop_seqElement)
    
class MrSequence(dict):
    def __init__(self,*args, **kwargs):
        super(MrSequence, self).__init__(*args, **kwargs)
        self.name = kwargs.get('name','')
        self._globals = {}
        
        if not kwargs.get('elements'):
            self['elements'] = {}
    
    def updateSeqElement(self, elem):
        existing = self.get('elements').keys()
        name = elem.get('name')
        if name in existing:
            if not isinstance(elem, seqElement):
                elem = seqElementFactory.create(elem)
            else:
                if 'loopLength' in elem.get('parameters',{}).keys():
                    elem.setLoopLength(elem.get('parameters',{}).get('loopLength',1))
            self['elements'][name] = elem

    def uniqueKey(self,_prefix):
        _prefix = _prefix.rstrip('0123456789')
        existing = self.get('elements').keys()
        _suffix = ''
        while _prefix+str(_suffix) in existing:
            if _suffix:
                _suffix += 1
            else:
                _suffix = 1
        return _prefix+str(_suffix)

    def append(self,elem,uniqueKey=True):
        elem['name'] = self.name + '.' + elem['name'].split('.')[-1]
        if not isinstance(elem, seqElement):
            elem=seqElementFactory.create(elem)

        _elems = self.getSortedElements()
        if len(_elems):
            insertTime = self.getDuration()
        else:
            insertTime = 0
        if uniqueKey:
            elem['name'] = self.uniqueKey(elem['name'])
        self.get('elements')[elem['name']]=elem
        self.get('elements')[elem['name']]['tstart'] = round_nearest(insertTime)
        self.repairTiming()
        return elem['name']
    
    def insert(self,elem,wantedInsertTime,uniqueKey=True):
        elem['name'] = self.name + '.' + elem['name'].split('.')[-1]
        if not isinstance(elem, seqElement):
            elem=seqElementFactory.create(elem)
        # find element currently located at wantedInsertTime (if any)
        wantedInsertTime = round_nearest(wantedInsertTime)
        realInsertTime = 0
        if wantedInsertTime<0:
            wantedInsertTime = 0
        if uniqueKey:
            elem['name'] = self.uniqueKey(elem['name'])
        _c = [e for k,e in self.get('elements',{}).items() 
                    if (wantedInsertTime-e.getTstart())<e.getDuration() and e.getTstart()<wantedInsertTime]
        if _c:
            # elem exists
            _c=_c[0]
            _side = (wantedInsertTime-_c.getTstart()-_c.getDuration()/2.0)
            if _side<=0:
                realInsertTime = _c.getTstart()-1e-4
            else:
                realInsertTime = _c.getTstart()+_c.getDuration()
        else:
            # no element exists (simple case)
            realInsertTime = wantedInsertTime

        self.get('elements')[elem['name']]=elem
        self.get('elements')[elem['name']]['tstart'] = round_nearest(realInsertTime)
        self.repairTiming()
        return elem['name']

    def setGlobals(self,_globals={}):
        self._globals.update(_globals)
            
    def getGlobals(self):
        return self._globals
            
    def _refresh(self,_globals={}):
        if not len(_globals):
            _globals = self._globals
        self.setGlobals(_globals)
        elems = self.getSortedElements()
        for i,e in enumerate(elems):
            e.getDuration(update=True,_globals=_globals)
        self.squeezeTiming()
        
    def shiftElement(self,name,newT):
        if name in self.get('elements').keys():
            self['elements'][name]['tstart'] = round_nearest(newT)
            self.repairTiming()

    def repairTiming(self):
        elems = self.getSortedElements()
        earliestAvailableTime = 0
        if elems:
            elems[0]['tstart'] = 0
        for i,e in enumerate(elems):
            if e.getTstart()<earliestAvailableTime:
                elems[i]['tstart']=earliestAvailableTime
            earliestAvailableTime = round_nearest(elems[i].getTstart()+e.getDuration())
        self['elements'] = {e['name']:e for e in elems}
        
    def squeezeTiming(self):
        elems = self.getSortedElements()
        earliestAvailableTime = 0
        if elems:
            elems[0]['tstart']  = 0
        for i,e in enumerate(elems):
            elems[i]['tstart']=earliestAvailableTime
            earliestAvailableTime = round_nearest(elems[i].getTstart(_globals=self.getGlobals())+e.getDuration(_globals=self.getGlobals()))
        self['elements'] = {e['name']:e for e in elems}
        
    def getSortedElements(self):
        _sorted = list(self.get('elements').values())
        _sorted.sort(key=lambda x:x.getTstart())
        return _sorted

    def getElementByName(self,name):
        hits = [self['elements'][e] for e in self.get('elements').keys() if e==name]
        if len(hits)==1:
            return hits[0]
        else:
            print('Element',name,'not identified under available elements',[e for e in self.get('elements')])
            return None
        
    def getDuration(self):
        elems = self.getSortedElements()
        if len(elems):
            return elems[-1].getTstart() + elems[-1].getDuration(_globals=self.getGlobals())
        else:
            return 0

    def _remove(self,name,shift=False):
        if name not in self.get('elements').keys():
            name = self.name+'.'+name
        if name in self.get('elements').keys():
            _data = self.get('elements').pop(name)
            if shift:
                _dur = _data.getDuration()
                _t = _data.getTstart()
                for e in self.get('elements'):
                    if _t<=self['elements'][e].getTstart():
                        self['elements'][e]['tstart'] -= _dur
                        
            _data._delete()
            return True
        else:
            print('not finding',name,'in',self.get('elements').keys() )
            return False
        
    def remove(self,name,shift=False):
        new_n = name.removeprefix(self.name).strip('.')
        s = new_n.split('.')
        if not self._remove(name) and len(s)>1:
            loop = self.getElementByName(s[0])
            if not loop:
                return
            loop.remove(name)
            return
                    
    def removeAll(self):
        for name in self['elements'].copy():
            self._remove(name, shift=False)
        self['elements'] = {}

    def getGammaStarBlueprint(self) :
        print('not implemented, yet!')

    def getSequenceBlueprint(self,seq,*args, **kwargs):
        from mrlabContext import mrlabContext
        seq.remove('bpId')
        bp = mrlabContext().createNewSequenceBlueprint(seqname=kwargs.get('seqname',seq['name']),addToLib=False)
        for name,elem in seq['elements'].items():
            bp['definitions'].update({**self.getDefinitions(elem)})
        tags=set(bp['properties'].get('tags',[]))
        tags.add('sequence')
        bp['properties']['tags'] = list(tags)

        return bp
        
    def getDescription(self):
        return [c.getDescription() for c in self.getSortedElements()]

    def getPlotsAndPulseq(self,systemInfo=None,_globals={}):
        curT = 0
        full_data={'grx':{'t':[],'v':[]}, 
                   'gry':{'t':[],'v':[]}, 
                   'grz':{'t':[],'v':[]}, 
                   'rf':{'t':[],'v':[]}, 
                   'rf_am':{'t':[],'v':[]}, 
                   'adc':{'t':[],'v':[]}, 
                  }
        if not systemInfo:
            print('systemInfo is missing!')
        pulseq = pp.Sequence(systemInfo)
        self.setGlobals(_globals)
        for elem in self.getSortedElements():
            dataToAdd,pulseqToAdd = elem.create_plots_and_pulseq(_globals=self.getGlobals())
            for d in dataToAdd.keys():
                t = full_data.get(d,dict(t=[],v=[]))['t']
                t.extend([_t+elem.getTstart() for _t in dataToAdd[d]['t']])
                v = full_data.get(d,dict(t=[],v=[]))['v']
                v.extend(dataToAdd[d]['v'])
                full_data[d] = dict(t=t,v=v)
            if pulseqToAdd:
                _delay = round_nearest(elem.getTstart() - curT,limit=True)
                if _delay:
                    pulseq.add_block(pp.make_delay(_delay))
                    curT += round_nearest(elem.getTstart(),limit=True)
                for i in range(len(pulseqToAdd.block_events)):
                    pulseq.add_block(pulseqToAdd.get_block(i+1))
                curT += round_nearest(pulseqToAdd.duration()[0],limit=True)

                
        return full_data,pulseq
        
    def __str__(self):
        _sorted = list(self.get('elements').values())
        _sorted.sort(key=lambda x:x.getTstart())
        return ' - '.join([str(int(e.getTstart()*1e4)/10)+'('+str(e['name'])+')'+str(int((e.getTstart()+e.getDuration())*1e4)/10) for e in _sorted])

if __name__ == '__main__':
    from mrlabContext import mrlabContext
    # from PyQt5.QtWidgets import QApplication
    # from Plot import Plot
    # qapp = QApplication.instance()
    mr = mrlabContext()
    seq=mr.getSequence()
    seq.append(mr.getElementForBpName('gradient'))
    seq.append(mr.getElementForBpName('gradient',param_values=dict(grad_flat=2000,gradX_amp=20000.0,gradY_amp=0,gradZ_amp=0)))
    seq.append(mr.getElementForBpName('rf_ns'))
    loop = mr.getElementForBpName('loop')
    loop.setLoopLength(2)
    loop.appendElement(mr.getElementForBpName('rf_ss_sym',param_values=dict(delay='loop_counter*2000+100')))
    seq.append(loop)
    print(seq)
    # plot = Plot()
    # plot.show()
    # qapp.exec()

