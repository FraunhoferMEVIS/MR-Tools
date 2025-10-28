#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 13:26:19 2024

@author: mague
"""
from mrlabContext import mrlabContext

from pathlib import Path as FilePath
import shutil
import pypulseq as pp

import numpy as np
import json

import mrlab_utils as utils

def getUniqueName(_prefix, existing=None, doNotTrim = False):
        if not doNotTrim:
            _prefix = _prefix.rstrip('0123456789')
        _suffix = ''
        while _prefix+str(_suffix) in existing:
            if _suffix:
                _suffix += 1
            else:
                _suffix = 1
        return _prefix+str(_suffix)
import sys

# from generate_parametrized_pulseq import generate_pulseq_template
# generate_pulseq_template()

blueprintIds = dict()
bbDir = (FilePath.cwd().parent/'MevisMrLab'/'buildingBlock')
bbDir = FilePath('.')/'buildingBlock'
scannerTypes = [f.name for f in bbDir.glob('*/')][1:]
mr = mrlabContext()
for scannerType in scannerTypes:
    mr.reset(scannerType=scannerType)
    mr.createBlueprintsFromPulseqFile()

    seqDir = bbDir.parent/'blueprints' / 'sequence'
    seqsToDelete = [f for f in seqDir.glob('**/*.json') if f.stem != "Empty sequence"]
    seqDir = bbDir.parent/'blueprints' / scannerType / 'buildingBlock'
    seqsToDelete.extend([f for f in seqDir.glob('**/*.json')])
    for f in seqsToDelete:
        print('deleting',f)
        f.unlink()
        
    pulseqDir = bbDir / scannerType
    existingBBsTodelete = list([f for f in pulseqDir.glob('*.json')])
    existingBBsTodelete.extend([f for f in pulseqDir.glob('*.svg')])
    for f in existingBBsTodelete:
        print('deleting',f)
        f.unlink()

    src_dir =  bbDir.parent/'presets'/'buildingBlock'/scannerType
    dst_dir = bbDir/scannerType
    filesToCopy = list(src_dir.glob('*.json'))
    filesToCopy.extend(list(src_dir.glob('*.svg')))
    for json_file in filesToCopy:
        shutil.copy2(json_file, dst_dir / json_file.name)
     
    flist = list(pulseqDir.glob('**/*.seq'))
    flist.extend( list(pulseqDir.glob('**/*.pulseq')))
    flist = set([f for f in list(flist)]) - set(list(pulseqDir.glob('**/pulseq_storage/*.seq')))
    for fname in list(flist):
        with open(fname, "r") as file1:
            print(fname)
            tags = set(fname.parent.parts)-set(pulseqDir.parent.parts)
            bbType = list(tags - {scannerType,'pulseq','_sliceSelective'})[0]
            tags = list(tags)
            bbName = fname.stem.replace('_'+scannerType,'')
            print(fname.stem,bbName)
            # tags.append(bbName)
            # gs.reset()
            seq_dump = file1.read() 
            seq_dump.replace('\nName \n', '\nName '+bbName.replace(' ','_')+' \n')
            
            param_desc = utils.extract_parameters_form_pulseq(fname)
            param_values = {p:param_desc[p]['pulseq_value'] for p in param_desc}
            fname_parsed = str(fname)+'parsed'
            utils.update_pulseqfile(fname,fname_parsed,param_values)
            
            # let's see whether we already created an id for this bbName
            # if yes, use that otherwise create a new one. By this, we can change between scanners more easily
            bp = mr.createPulseqBlueprint(bbName,seq_dump,True,bpId = blueprintIds.get(bbName))
            blueprintIds.update({bbName:bp['id']})
            
            # let's calculate the plots via pypulseq
            _pulseq = pp.Sequence(mr.systems[scannerType]['system'])
            _pulseq.read(fname_parsed,detect_rf_use=False)
            pulseqData = utils.waveforms_export(_pulseq)
            labels={'grx':'gx','gry':'gy','grz':'gz','rf_am':'rf','adc':'adc'}
            desc = dict(name = bbName, id=bp['id'],
                        properties = dict(fname = str(pulseqDir/(bbName+'.svg')),
                                          pulseqFile = str(fname),
                                          param_desc = param_desc,
                                          parameters = {p:param_desc[p]['pulseq_value'] for p in param_desc},
                                          type = bbType, tags=list(tags), 
                                          NPhase = 64, NRead = 64, 
                                          duration = _pulseq.duration()[0], scannerType = scannerType)
                    )
            showInfoBlock = len(param_desc)>0
            desc['properties']['fname'] = utils.make_icon(None,bbName,pulseqData,
                                        {p:param_desc[p]['default'] for p in param_desc},_type=bbType,
                                        showInfoBlock=showInfoBlock,_dir=pulseqDir)

            fsave = str(pulseqDir/(bbName+'.json'))
            with open(fsave, "w") as file1:
                print('saving',desc['name'],desc['id'])
                json.dump({'blueprints':{desc['id']:desc}},file1)

mr.reset()


def getBuildingBlockDescriptions():
    blocks = []

    for fa in [10,45,90,135,180]:
        bb_info = dict(name=f"FA{fa:03d}_ns", id = "rf_ns", 
                       properties = dict(parameter_units='metric',
                                         param_desc={"rf_phase", "rf_freq"},
                                         parameters={"rf_amp": float(fa),
                             			},
                            		    type = "rfpulse",
                            		    tags = ["rfpulse", "basic"]
                                         ))
        blocks.append(bb_info)

    for g in ["X","Y","Z"]:
        param={"gradX_amp":0,"gradY_amp":0,"gradZ_amp":0,}
        param.update({f"grad{g}_amp": 10,"grad_flat": 0,"grad_ramp": 200})
        blocks.append(dict(name=f"grad{g}", id = "gradient", 
                       properties = dict(parameter_units='metric',
                                         param_desc=[f"grad{g}_amp", "grad_flat","grad_ramp"],
                                         parameters=param,
                            		    type = "preparation",
                            		    tags = ["gradient", "basic"]
                                         ))
                      )
 
    for g in ["X","Y","Z"]:
        param={"gradX_amp":0,"gradY_amp":0,"gradZ_amp":0,}
        param.update({f"grad{g}_amp": "(seq_loop_counter-seq_loop_length/2)/seq_loop_length*3", "grad_flat": 200,"grad_ramp": 200})
        blocks.append(dict(name=f"table{g}", id = "gradient", 
                       properties = dict(parameter_units='metric',
                                         param_desc=[f"grad{g}_amp", "grad_flat","grad_ramp"],
                                         parameters=param,
                            		    type = "preparation",
                            		    tags = ["gradient", "extended", "variable"]
                                         ))
                      )
 
    return blocks

# from generate_parametrized_pulseq import generate_pulseq_template
# generate_pulseq_template()

bbDir = FilePath('.')/'buildingBlock'
scannerTypes = [f.name for f in bbDir.glob('*/')][1:]
mr = mrlabContext()

general_tags = []
for scannerType in scannerTypes:
    mr.reset(scannerType=scannerType)

    blocks = getBuildingBlockDescriptions()
    
    for info in blocks:
        bpId  = info["id"]
        bp = mr.getBlueprint(bpId)

        prop = info['properties']
        elem = mr.getElementForBpName(bp['name'],param_values=prop["parameters"],param_units=prop.get("parameter_units","pulseq"),checkCompleteLib=True)
        elem['name'] = info.get("name", "")
        elem['type'] = prop.get("type", "")
        tags = prop.get("tags", [])
        tags.extend(general_tags)
        elem['tags'] = tags
        old_bp = mr.getBuildingBlock(info['name'])
        if old_bp:
            elem['id']=old_bp['id']
        param_desc = elem['param_desc']
        if 'param_desc' in prop.keys():
            new_param_desc = {}
            for p in prop.get('param_desc',None):
                new_param_desc.update({p:param_desc[p]})
                elem['param_desc']=new_param_desc
        mr.addBuildingBlockFromSeqElement(elem,storePermanently=True)
        

mr.reset()
