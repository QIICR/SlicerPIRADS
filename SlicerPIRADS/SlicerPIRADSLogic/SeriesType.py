from abc import ABCMeta
import os
import re


class SeriesType(object):

  __metaclass__ = ABCMeta

  @classmethod
  def canHandle(cls, obj):
    if type(obj) in [str, unicode]:
      return cls.canHandleFile(obj)
    else:
      #TODO: check if volumeNode
      return cls.canHandleVolumeNode(obj)

  @classmethod
  def getName(cls):
    return cls.__name__

  @staticmethod
  def canHandleFile(filename):
    raise NotImplementedError

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    raise NotImplementedError

  def __init__(self, volume):
    self._volume = volume

  def getVolume(self):
    return self._volume


class T2a(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    description = volumeNode.GetName().lower()
    return all(term in description for term in ['ax', 't2'])


class T2s(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    description = volumeNode.GetName().lower()
    return all(term in description for term in ['sag', 't2'])


class T2c(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    description = volumeNode.GetName().lower()
    return all(term in description for term in ['cor', 't2'])


class ADC(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    return 'apparent diffusion coeff' in volumeNode.GetName().lower()


class DCE(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    pass


class SUB(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    description = volumeNode.GetName()
    return re.search(r'[a-zA-Z]', description) is None


class DWIb(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    pass

  @classmethod
  def getName(cls):
    return "DWI-b"


class DCE(SeriesType):

  @staticmethod
  def canHandleFile(filename):
    assert os.path.exists(filename)

  @staticmethod
  def canHandleVolumeNode(volumeNode):
    pass

  @classmethod
  def getName(cls):
    return "DCE enhanced"


class SeriesTypeFactory(object):

  SERIES_TYPE_CLASSES = [T2a, T2s, T2c, ADC, DWIb, SUB, DCE]

  @staticmethod
  def getSeriesType(obj):
    for seriesTypeClass in SeriesTypeFactory.SERIES_TYPE_CLASSES:
      if seriesTypeClass.canHandle(obj):
        return seriesTypeClass
    return None