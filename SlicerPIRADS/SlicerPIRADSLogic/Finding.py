import vtk
from .Annotation import AnnotationFactory
from .LesionAssessmentRules import LesionAssessmentRuleFactory

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin


class Finding(ParameterNodeObservationMixin):

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201
  RuleChangedEvent = vtk.vtkCommand.UserEvent + 202
  SectorSelectionChangedEvent = vtk.vtkCommand.UserEvent + 203
  AssessmentScoreChanged = vtk.vtkCommand.UserEvent + 204

  def __init__(self, name):
    self._name = name
    self._assessmentRule = None
    self._assessmentScores = dict()
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
      annotation.addEventObserver(self.DataChangedEvent, lambda caller, event: self.invokeEvent(event))
      if not self._annotations.has_key(seriesType):
        self._annotations[seriesType] = dict()
      self._annotations[seriesType][mrmlNodeClass] = annotation
    return annotation

  def deleteAnnotation(self, seriesType, mrmlNodeClass):
    try:
      annotation = self._annotations[seriesType][mrmlNodeClass]
      annotation.cleanup()
      del self._annotations[seriesType][mrmlNodeClass]
    except Exception:
      pass

  def getSectors(self):
    return self._sectors

  def setSectors(self, sectors):
    self._sectors = sectors
    self._assessmentRule = LesionAssessmentRuleFactory.getEligibleLesionAssessmentRule(sectors)
    self.invokeEvent(self.SectorSelectionChangedEvent)

  def setAllVisible(self, visible):
    for seriesType in self._annotations.keys():
      self.setSeriesTypeVisible(seriesType, visible)

  def setSeriesTypeVisible(self, seriesType, visible):
    try:
      for annotationClass, annotation in self._annotations[seriesType].items():
        if annotation.mrmlNode:
          annotation.setVisible(visible)
    except KeyError:
      pass

  def getPickList(self, seriesType):
    if not self._assessmentRule: # TODO: think about situations where rule is not set but sectors are...
      return []
    return self._assessmentRule.getPickList(seriesType)

  def getPickListTooltip(self, seriesType):
    if not self._assessmentRule: # TODO: think about situations where rule is not set but sectors are...
      return []
    return self._assessmentRule.getPickListTooltip(seriesType)

  def setScore(self, seriesType, score):
    self._assessmentScores[seriesType] = score
    self.invokeEvent(self.AssessmentScoreChanged)

  def getScore(self, seriesType):
    try:
      return self._assessmentScores[seriesType]
    except KeyError:
      return None

  def removeScore(self, seriesType):
    try:
      del self._assessmentScores[seriesType]
    except KeyError:
      pass
    self.invokeEvent(self.AssessmentScoreChanged)

  def getAssessmentScores(self):
    return self._assessmentScores

class FindingAssessment(object):
  # TODO: make use of this class

  def __init__(self):
    self._location = None
    self._score = None

  def getLocation(self):
    return self._location

  def getScore(self):
    return self._score