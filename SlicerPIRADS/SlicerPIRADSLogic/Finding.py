import vtk
from .Annotation import AnnotationFactory
from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin


class Finding(ParameterNodeObservationMixin):

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201

  def __init__(self, name):
    self._name = name
    self._assessment = None
    self._sectors = []
    self._annotations = dict()

  def __del__(self):
    for seriesType, annotations in self._annotations.items():
      for annotation in annotations.values():
        annotation.delete()

  def setName(self, name):
    self._name = name
    self.invokeEvent(self.DataChangedEvent)

  def getName(self):
    return self._name

  def getOrCreateAnnotation(self, seriesType, mrmlNodeClass):
    try:
      annotation = self._annotations[seriesType][mrmlNodeClass]
    except KeyError:
      volumeNode = seriesType.getVolume()
      annotation = AnnotationFactory.getAnnotationClassForMRMLNodeClass(mrmlNodeClass)(volumeNode)
      if not self._annotations.has_key(seriesType):
        self._annotations[seriesType] = dict()
      self._annotations[seriesType][mrmlNodeClass] = annotation
    return annotation

  def getSectors(self):
    return self._sectors

  def setSectors(self, sectors):
    self._sectors = sectors
    self.invokeEvent(self.DataChangedEvent)


class FindingAssessment(object):

  def __init__(self):
    self._location = None
    self._score = None

  def getLocation(self):
    return self._location

  def getScore(self):
    return self._score