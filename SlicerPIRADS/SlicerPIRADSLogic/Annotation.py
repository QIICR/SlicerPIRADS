import vtk
import slicer

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin


class Annotation(ParameterNodeObservationMixin):

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201
  MRML_NODE_CLASS = None

  def __init__(self, volumeNode):
    if not self.MRML_NODE_CLASS:
      raise ValueError("MRML_NODE_CLASS needs to be defined for all inheriting classes of {}".format(self.__class__.__name__))
    self._masterVolume = volumeNode
    self._initializeMRMLNode()

  def _initializeMRMLNode(self):
    self.mrmlNode = slicer.mrmlScene.AddNewNodeByClass(self.MRML_NODE_CLASS)

  def delete(self):
    if self.mrmlNode:
      slicer.mrmlScene.RemoveNode(self.mrmlNode)

  def cleanup(self):
    pass


class Segmentation(Annotation):

  MRML_NODE_CLASS = "vtkMRMLSegmentationNode"

  def __init__(self, volumeNode):
    super(Segmentation, self).__init__(volumeNode)
    self._createAndObserveSegment()

  def _createAndObserveSegment(self):
    import vtkSegmentationCorePython as vtkSegmentationCore
    segment = vtkSegmentationCore.vtkSegment()
    segment.SetName(self._masterVolume.GetName())
    # TODO need to think about the reference more in detail. After loading the volume nodes don't occupy the same address
    self.mrmlNode.SetReferenceImageGeometryParameterFromVolumeNode(self._masterVolume)
    self.mrmlNode.GetSegmentation().AddSegment(segment)
    self.mrmlNode.AddObserver(vtkSegmentationCore.vtkSegmentation.SegmentModified, self._onSegmentModified)

  def _onSegmentModified(self, caller, event):
    self.invokeEvent(self.DataChangedEvent)


class Ruler(Annotation):

  AnnotationStartedEvent = vtk.vtkCommand.UserEvent + 202
  AnnotationFinishedEvent = vtk.vtkCommand.UserEvent + 203

  MRML_NODE_CLASS = "vtkMRMLAnnotationRulerNode"

  def __init__(self, volumeNode):
    self.annotationLogic = slicer.modules.annotations.logic()
    self.rulerObserverTag = None
    super(Ruler, self).__init__(volumeNode)

  def cleanup(self):
    self.stopPlaceMode()

  def _initializeMRMLNode(self):
    # TODO: give instructions to user
    self.mrmlNode = None
    self.addRulerObserver()
    mrmlScene = self.annotationLogic.GetMRMLScene()
    selectionNode = mrmlScene.GetNthNodeByClass(0, "vtkMRMLSelectionNode")
    selectionNode.SetReferenceActivePlaceNodeClassName(self.MRML_NODE_CLASS)
    self.annotationLogic.StartPlaceMode(False)
    # self.mrmlNode.AddObserver(vtkSegmentationCore.vtkSegmentation.SegmentModified, self._onRulerModified)

  def stopPlaceMode(self):
    self.removeRulerObserver()
    self.annotationLogic.StopPlaceMode(True)

  def addRulerObserver(self):
    @vtk.calldata_type(vtk.VTK_OBJECT)
    def onNodeAdded(caller, event, calldata):
      node = calldata
      if isinstance(node, getattr(slicer, self.MRML_NODE_CLASS)):
        # fire created event and
        self.mrmlNode = node
        self.removeRulerObserver()

    self.removeRulerObserver()
    self.rulerObserverTag = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, onNodeAdded)

  def removeRulerObserver(self):
    if self.rulerObserverTag:
      self.rulerObserverTag = slicer.mrmlScene.RemoveObserver(self.rulerObserverTag)

  def _onRulerModified(self, caller, event):
    self.invokeEvent(self.DataChangedEvent)


class AnnotationFactory(object):

  ANNOTATION_CLASSES = [Segmentation, Ruler]

  @staticmethod
  def getAnnotationClassForMRMLNodeClass(mrmlNodeClass):
    for annotationClass in AnnotationFactory.ANNOTATION_CLASSES:
      if mrmlNodeClass == annotationClass.MRML_NODE_CLASS:
        return annotationClass
    return None