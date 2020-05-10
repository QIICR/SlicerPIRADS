from abc import ABCMeta
import slicer
from SlicerDevelopmentToolboxUtils.decorators import singleton

from SlicerPIRADSLogic.SeriesType import *


class HangingProtocolFactory(object):

  @staticmethod
  def getHangingProtocol(volumeNodes):
    if len(volumeNodes) <= 4:
      return PIRADSHangingProtocolP1
    elif 4 < len(volumeNodes) < 7:
      return PIRADSHangingProtocolP2
    else:
      return PIRADSHangingProtocolP3


class HangingProtocol(object):

  __metaclass__ = ABCMeta

  SERIES_TYPES = None
  LAYOUT = None

  def __init__(self, volumeNodes):
    if not self.SERIES_TYPES or not self.LAYOUT:
      raise NotImplementedError
    self._volumeNodes = volumeNodes

  def canHandle(self, seriesTypes):
    pass


class PIRADSHangingProtocolP1(HangingProtocol):

  SERIES_TYPES = [T2a, ADC, DWIb, SUB]
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutTwoOverTwoView


class PIRADSHangingProtocolP2(HangingProtocol):

  SERIES_TYPES = [T2a, T2s, T2c, ADC, DWIb, SUB]
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutThreeOverThreeView


class PIRADSHangingProtocolP3(HangingProtocol):

  SERIES_TYPES = [T2a, T2s, T2c, ADC, DWIb, SUB, DCE] # TODO: add , "curve"]
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutThreeByThreeSliceView


@singleton
class FocussedSliceWidget:

  def __init__(self):
    pass

