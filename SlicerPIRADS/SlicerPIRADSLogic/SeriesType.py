from abc import ABCMeta
import os
import re
import dicom
import vtk
import slicer
from collections import OrderedDict

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin
from SlicerDevelopmentToolboxUtils.decorators import singleton


class SeriesType(object):

  __metaclass__ = ABCMeta

  @classmethod
  def canHandle(cls, obj):
    if type(obj) is str:
      assert os.path.exists(obj)
      return cls.canHandleFile(obj)
    else:
      #TODO: check if volumeNode
      return cls.canHandleVolumeNode(obj)

  @classmethod
  def getName(cls):
    return cls.__name__

  @classmethod
  def canHandleFile(cls, filename):
    try:
      # TODO: if is imported in DICOMDatabase, use database mechanism for checking tag else use dicom
      dataset = dicom.read_file(filename)
      return cls.hasEligibleDescription(dataset.SeriesDescription.lower())
    except AttributeError:
      return False

  @classmethod
  def canHandleVolumeNode(cls, volumeNode):
    description = volumeNode.GetName().lower()
    return cls.hasEligibleDescription(description)

  @classmethod
  def hasEligibleDescription(cls, description):
    raise NotImplementedError

  def __init__(self, volume):
    self._volume = volume

  def getVolume(self):
    return self._volume


class T2BasedSeriesType(SeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return 't2' in description


class DiffusionBasedSeriesType(SeriesType):
  pass


class DCEBasedSeriesType(SeriesType):
  pass


class T1a(SeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return all(term in description for term in ['ax', 't1'])


class T2a(T2BasedSeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return T2BasedSeriesType.hasEligibleDescription(description) and 'ax' in description


class T2s(T2BasedSeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return T2BasedSeriesType.hasEligibleDescription(description) and 'sag' in description


class T2c(T2BasedSeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return T2BasedSeriesType.hasEligibleDescription(description) and 'cor' in description


class ADC(DiffusionBasedSeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return 'apparent diffusion coeff' in description


class DWIb(DiffusionBasedSeriesType):
  # TODO: need more rules especially regarding b-values

  @classmethod
  def hasEligibleDescription(cls, description):
    return re.search(r'dwi', description)


class DWI(DiffusionBasedSeriesType):
  # TODO: need more rules

  @classmethod
  def hasEligibleDescription(cls, description):
    return re.search(r'dwi', description)


class DCE(DCEBasedSeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return any(re.search(term, description) for term in [r'ax dynamic', r'3d dce'])


class SUB(DCEBasedSeriesType):

  @classmethod
  def hasEligibleDescription(cls, description):
    return re.search(r'[a-zA-Z]', description) is None


class SeriesTypeFactory(object):

  SERIES_TYPE_CLASSES = [T1a, T2a, T2s, T2c, ADC, DWI, DWIb, SUB, DCE]

  @staticmethod
  def getSeriesType(obj):
    for seriesTypeClass in SeriesTypeFactory.SERIES_TYPE_CLASSES:
      if seriesTypeClass.canHandle(obj):
        return seriesTypeClass
    return None


@singleton
class VolumeSeriesTypeSceneObserver(ParameterNodeObservationMixin):
  """ This class keeps track of all volume nodes that have been added to the mrmlScene classifying each one with a
      a SeriesType if possible
  """

  @property
  def volumeSeriesTypes(self):
    return self._volumeSeriesTypes

  def __init__(self):
    self._volumeSeriesTypes = dict()
    self._nodeAddedObserver = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent,
                                                           self._onVolumeNodeAdded)
    self._nodeRemovedObserver = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeRemovedEvent,
                                                             self._onVolumeNodeRemoved)

  def __del__(self):
    slicer.mrmlScene.RemoveObserver(self._nodeAddedObserver)
    slicer.mrmlScene.RemoveObserver(self._nodeRemovedObserver)

  def reset(self):
    self._volumeSeriesTypes = dict()

  def refresh(self):
    loadedVolumeNodes = OrderedDict({volume: volume for volume
                                     in slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')})
    for volume in loadedVolumeNodes:
      try:
        self._volumeSeriesTypes[volume]
      except KeyError:
        seriesTypeClass = SeriesTypeFactory.getSeriesType(volume)
        if seriesTypeClass:
          seriesType = seriesTypeClass(volume)
          self._volumeSeriesTypes[volume] = seriesType

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def _onVolumeNodeAdded(self, caller, event, callData):
    if isinstance(callData, slicer.vtkMRMLScalarVolumeNode):
      seriesTypeClass = SeriesTypeFactory.getSeriesType(callData)
      if seriesTypeClass:
        seriesType = seriesTypeClass(callData)
        self._volumeSeriesTypes[callData] = seriesType

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def _onVolumeNodeRemoved(self, caller, event, callData):
    if isinstance(callData, slicer.vtkMRMLScalarVolumeNode):
      try:
        del self._volumeSeriesTypes[callData]
      except KeyError:
        pass