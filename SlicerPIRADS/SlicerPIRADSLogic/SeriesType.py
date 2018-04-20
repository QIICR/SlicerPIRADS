from abc import ABCMeta
import os
import re
import dicom


class SeriesType(object):

  __metaclass__ = ABCMeta

  @classmethod
  def canHandle(cls, obj):
    if type(obj) in [str, unicode]:
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
      return cls._hasEligibleDescription(dataset.SeriesDescription.lower())
    except AttributeError:
      return False

  @classmethod
  def canHandleVolumeNode(cls, volumeNode):
    description = volumeNode.GetName().lower()
    return cls._hasEligibleDescription(description)

  @classmethod
  def _hasEligibleDescription(cls, description):
    raise NotImplementedError

  def __init__(self, volume):
    self._volume = volume

  def getVolume(self):
    return self._volume


class T1a(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return all(term in description for term in ['ax', 't1'])


class T2a(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return all(term in description for term in ['ax', 't2'])


class T2s(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return all(term in description for term in ['sag', 't2'])


class T2c(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return all(term in description for term in ['cor', 't2'])


class ADC(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return 'apparent diffusion coeff' in description


class DCE(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return any(re.search(term, description) for term in [r'ax dynamic', r'3d dce'])


class SUB(SeriesType):

  @classmethod
  def _hasEligibleDescription(cls, description):
    return re.search(r'[a-zA-Z]', description) is None


class DWIb(SeriesType):
  # TODO: need more rules especially regarding b-values

  @classmethod
  def _hasEligibleDescription(cls, description):
    return re.search(r'dwi', description)


class DWI(SeriesType):
  # TODO: need more rules

  @classmethod
  def _hasEligibleDescription(cls, description):
    return re.search(r'dwi', description)


class SeriesTypeFactory(object):

  SERIES_TYPE_CLASSES = [T1a, T2a, T2s, T2c, ADC, DWI, DWIb, SUB, DCE]

  @staticmethod
  def getSeriesType(obj):
    for seriesTypeClass in SeriesTypeFactory.SERIES_TYPE_CLASSES:
      if seriesTypeClass.canHandle(obj):
        return seriesTypeClass
    return None