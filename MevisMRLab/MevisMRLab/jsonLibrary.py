# -*- coding: utf-8 -*-
# Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
# **InsertLicense** code

import logging
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

def flatten(matrix):
    return [item for row in matrix for item in row]


logger = logging.getLogger(__name__)


class JSONLibrary:
  """Read blueprit library from a single JSON file."""

  def __init__(self, filepath: Path):
    """Instantiate library.

    :param filepath: Path to blueprint library
    :type filepath: Path
    :return: None
    :rtype: None
    """
    self.full_library = dict()
    self.library = dict()
    self.filterTags = []
    self.filepath = filepath
    for file in self.filepath.glob("**/*.json"):
        print('reading',file)
        with open(file, "r", encoding="utf-8") as _f:
            self.full_library.update(json.load(_f)['blueprints'])
    if (self.filepath.parent/'sequence').is_dir():
        for file in (self.filepath.parent/'sequence').glob("**/*.json"):
            with open(file, "r", encoding="utf-8") as _f:
                self.full_library.update(json.load(_f)['blueprints'])
    self.applyFilterTags()
    
  def applyFilterTags(self):
      self.setFilterTags(self.filterTags)

  def setFilterTags(self,filter_tags=[],doNotStore=False):
      if not doNotStore:
          self.filterTags = filter_tags
      self.library = { key: val for key, val in self.full_library.items()
                          if any(tag in filter_tags for tag in val['properties'].get('tags', [])) or not len(filter_tags)
                      }
      
  def addBlueprint(self, blueprint: dict, **kwargs):
    """Add blueprint to library. Missing ID is generated
     
    :param blueprint: Dictionary of blueprint
    :type blueprint: dict[str,Any]
    :return: None
    :rtype: None
    """
    import shutil
    import os
    base_folder = os.path.dirname(os.path.abspath(__file__))

    blueprintId = blueprint.get('id',str(uuid4()))
    blueprint.update({'id':blueprintId})
    self.full_library.update({blueprintId:blueprint})
    if kwargs.get('storePermanently',True):
        addToSavePath = kwargs.get('type','')
        print('storing blueprint',blueprint.get('name'),' permanently')
        src = blueprint['properties'].get('fname')
        if src and os.path.isfile(src):
            filename = os.path.basename(src)
            dst = os.path.join(self.filepath/addToSavePath, filename)
            if not shutil._samefile(src, dst):
                shutil.copy(src, dst)
            blueprint['properties']['fname'] = os.path.relpath(dst, start=base_folder)
        src=blueprint['properties'].get('pulseqFile')
        if src and os.path.isfile(src):
            filename = blueprint.get('name')+'_pulseq.seq'
            dst = os.path.join(self.filepath/addToSavePath/'pulseq_storage', filename)
            if not shutil._samefile(src, dst):
                shutil.copy(src, dst)
            blueprint['properties']['pulseqFile'] = os.path.relpath(dst, start=base_folder)

        self.saveBlueprintsToIndividualFiles(self.filepath/addToSavePath,{blueprintId:blueprint})
    if kwargs.get('copyToDir'):
        self.exportBlueprint(blueprintId,**kwargs)
    self.applyFilterTags()

  def exportBlueprint(self,blueprintName, **kwargs):
    blueprintId = self.getBlueprintIdByName(blueprintName)
    listOfIds = [blueprintId]
    if kwargs.get('exportAll'):
        # sequence_elements will also by saved
        bp = self.getBlueprintById(blueprintId)
        se_d=[d['blueprint_id'] for k,d in bp['definitions'].items() 
              if d['type']=='sequence_element_definition' and len(d['blueprint_id'])>10]
        listOfIds.extend(se_d)
    self.saveBlueprintsToIndividualFiles(Path(kwargs.get('dirName')),
             self.getBlueprintsByIds(listOfIds))
      
  def removeBlueprint(self, blueprintName="", bpId=None, removePermanently=False):
      if not bpId:
          bpId = self.getBlueprintIdByName(blueprintName)
      if bpId:
          # print('lib: now removing',blueprintName,bpId)
          self.full_library.pop(bpId)
      if removePermanently:
          for _path in self.filepath.glob('**/'+blueprintName+'.json'):
              Path.unlink(_path)
      self.applyFilterTags()
            
  def getBlueprintById(self, blueprintId: str) -> dict[str, Any]:
    """Get blueprint from library identified by its ID.

    :param blueprintId: ID of requested blueprint
    :type blueprintId: str
    :return: Dictionary of blueprint
    :rtype: dict[str, Any]
    """
    blueprint = self.library.get(blueprintId, None)
    if not blueprint:
      logger.error(f"Blueprint ID {blueprintId} not available.")
      return None
    return dict(blueprint)

  def getBlueprintIdByName(self, blueprintName: str) -> dict[str, Any]:
    """Get blueprint from library identified by its ID.

    :param blueprintName: name of requested blueprint
    :type blueprintName: str
    :return: Dictionary of blueprint
    :rtype: dict[str, Any]
    """
    blueprintId = None
    for key, val in self.library.items():
      if val['name'] == blueprintName:
        blueprintId = key
        break

    if not blueprintId:
      logger.error(f"Blueprint {blueprintName} not available.")
    return blueprintId

  def getAvailableBlueprints(self) -> list[dict[[str, str]]]:
    """Get a list of all available blueprints.

    :return: List of all blueprint ids and their names.
    :rtype: list[dict[str, str]]
    """
    blueprints = []
    for bid, b in self.library.items():
      blueprints.append(b['name'])
    return blueprints

  def getAvailableSequences(self) -> list[str]:
    """Get a list of all available sequences.

    :return: List of blueprint names.
    :rtype: list[str]
    """
    return self.getBlueprintsByTag("sequence")

  def getBlueprintsByTag(self, tag: str) -> list[str]:
    """Get a list of all blueprints with a given tag.

    :param tag: Tag to search for.
    :type tag: str
    :return: List of blueprint names.
    :rtype: list[str]
    """
    blueprints = []
    for bid, b in self.library.items():
      properties = b.get("properties", {})
      if tag in properties.get("tags", []):
        blueprints.append(b['name'])
    return blueprints

  def getBlueprintsByType(self, _type: str) -> list[str]:
    """Get a list of all blueprints with a given type.

    :param tag: Tag to search for.
    :type tag: str
    :return: List of blueprint names.
    :rtype: list[str]
    """
    blueprints = []
    for bid, b in self.library.items():
      properties = b.get("properties", {})
      if _type in properties.get("type", []):
        blueprints.append(b['name'])
    return blueprints

  def getAvailableBlueprintIds(self):
        return self.getBlueprintIdsByNames(self.getAvailableBlueprints())
    
  def getBlueprintByName(self,_name):
      return self.getBlueprintById(self.getBlueprintIdByName(_name))
    
  def getBlueprintsByIds(self,Ids):
        _dict = dict()
        if not isinstance(Ids,list):
            Ids = [Ids]
        for _id in Ids:
            _dict.update({_id:self.getBlueprintById(_id)})
        return _dict
    
  def getBlueprintIdsByNames(self,bpNames):
        _list = list()
        if not isinstance(bpNames,list):
            bpNames = [bpNames]
        for bpname in bpNames:
            _list.append(self.getBlueprintIdByName(bpname))
        return _list
    
  def getBlueprintsByNames(self,bpNames):
        _dict = dict()
        if not isinstance(bpNames,list):
            bpNames = [bpNames]
        for bpname in bpNames:
            bpId = self.getBlueprintIdsByNames(bpname)[0]
            _dict.update({bpname:self.getBlueprintById(bpId)})
        return _dict
    
  def getAvailableBlueprintTags(self):
        bps = self.getBlueprintsByNames(self.getAvailableBlueprints())
        l=[_v['properties'].get('tags',[]) for _v in bps.values()]
        l = list(set(flatten(l)))
        l.sort()
        return l
    
  def getAvailableBlueprintTypes(self):
        bps = self.getBlueprintsByNames(self.getAvailableBlueprints())
        l=[_v['properties'].get('type',[]) for _v in bps.values()]
        l = list(set(l))
        l.sort()
        return l
    
  def getBlueprintNamesByTags(self,tags):
        _list = list()
        if isinstance(tags,list):
            for tag in tags:
                _list.append(self.getBlueprintsByTag(tag))
                l = flatten(_list)
                l.sort()
            return l
        else:
          return self.getBlueprintsByTag(tags)
        
  def getBlueprintIdsByTags(self,tags):
        return self.getBlueprintIdsByNames(self.getBlueprintNamesByTags(tags))
        
  def getBlueprintsByTags(self,tags):
        return self.getBlueprintsByNames(self.getBlueprintNamesByTags(tags))

  def getBlueprintNamesByTypes(self,_type):
        _list = list()
        if isinstance(_type,list):
            for _t in _type:
                _list.append(self.getBlueprintsByType(_t))
                l = flatten(_list)
                l.sort()
            return l
        else:
          return self.getBlueprintsByType(_type)
        
  def getBlueprintIdsByTypes(self,_type):
        return self.getBlueprintIdsByNames(self.getBlueprintNamesByTypes(_type))
        
  def getBlueprintsByTypes(self,_type):
        return self.getBlueprintsByNames(self.getBlueprintNamesByTypes(_type))

    
  def saveBlueprintsToIndividualFiles(self,_path,bps=None):
     if not bps:
         bps = self.library
     for bpId,bp in bps.items():
        fname = bp['name'].replace('/','-')+'.json'
        with open(_path/fname, 'w') as f:
            json.dump({'blueprints':{bpId:bp}}, f)
