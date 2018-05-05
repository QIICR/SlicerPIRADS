import vtk
import slicer

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin


class Annotation(ParameterNodeObservationMixin):
  """ Base class for annotations providing a mrmlNode and visibility options

  :param volumeNode: volume that will be used as the annotation's reference volume
  """

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201
  """ This event needs to be invoked if internal data changed"""
  MRML_NODE_CLASS = None
  """ MRML_NODE_CLASS is required to be defined for mrmlNode instantiation"""

  def __init__(self, volumeNode):
    if not self.MRML_NODE_CLASS:
      raise ValueError("MRML_NODE_CLASS needs to be defined for all inheriting classes of {}".format(self.__class__.__name__))
    self._masterVolume = volumeNode
    self._initializeMRMLNode()

  def __del__(self):
    self.delete()

  def _initializeMRMLNode(self):
    self.mrmlNode = slicer.mrmlScene.AddNewNodeByClass(self.MRML_NODE_CLASS)

  def delete(self):
    """ Deletes the mrmlNode"""
    if self.mrmlNode:
      slicer.mrmlScene.RemoveNode(self.mrmlNode)
      self.mrmlNode = None

  def setVisible(self, visible):
    """ Set visibility of the mrmlNode

    :param visible: boolean setting visibility to True or False
    """
    if self.mrmlNode:
      self.mrmlNode.SetDisplayVisibility(visible)

  def cleanup(self):
    """ This method should be implemented if there is any data to cleanup at anytime"""
    pass


class Segmentation(Annotation):
  """ Annotation subclass using vtkMRMLSegmentationNode
  """

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
  """ Annotation subclass using vtkMRMLAnnotationRulerNode """

  AnnotationStartedEvent = vtk.vtkCommand.UserEvent + 202
  AnnotationFinishedEvent = vtk.vtkCommand.UserEvent + 203

  MRML_NODE_CLASS = "vtkMRMLAnnotationRulerNode"

  def __init__(self, volumeNode):
    self._annotationLogic = slicer.modules.annotations.logic()
    self.rulerObserverTag = None
    super(Ruler, self).__init__(volumeNode)

  def cleanup(self):
    self.stopPlaceMode()

  def _initializeMRMLNode(self):
    # TODO: give instructions to user
    self.mrmlNode = None
    self._addRulerObserver()
    self.startPlaceMode()
    # self.mrmlNode.AddObserver(vtkSegmentationCore.vtkSegmentation.SegmentModified, self._onRulerModified)

  def startPlaceMode(self):
    """ Starting place mode (non persistent) until user has created measurement """
    mrmlScene = self._annotationLogic.GetMRMLScene()
    selectionNode = mrmlScene.GetNthNodeByClass(0, "vtkMRMLSelectionNode")
    selectionNode.SetReferenceActivePlaceNodeClassName(self.MRML_NODE_CLASS)
    self._annotationLogic.StartPlaceMode(False)

  def stopPlaceMode(self):
    """ Stopping place mode. Observer of ruler node gets removed """
    self._removeRulerObserver()
    self._annotationLogic.StopPlaceMode(True)

  def _addRulerObserver(self):
    @vtk.calldata_type(vtk.VTK_OBJECT)
    def onNodeAdded(caller, event, calldata):
      node = calldata
      if isinstance(node, getattr(slicer, self.MRML_NODE_CLASS)):
        self.mrmlNode = node
        self._removeRulerObserver()

    self._removeRulerObserver()
    self.rulerObserverTag = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, onNodeAdded)

  def _removeRulerObserver(self):
    if self.rulerObserverTag:
      self.rulerObserverTag = slicer.mrmlScene.RemoveObserver(self.rulerObserverTag)

  def _onRulerModified(self, caller, event):
    self.invokeEvent(self.DataChangedEvent)


class AnnotationFactory(object):
  """ Provides a static method returning the annotation subclass that can handle a specific mrmlNode class """

  ANNOTATION_CLASSES = [Segmentation, Ruler]
  """ Currently available Annotation subclasses """

  @staticmethod
  def getAnnotationClassForMRMLNodeClass(mrmlNodeClass):
    """ Returns one of the registered Annotation subclasses if mrmlNodeClass can be handled by one otherwise None

    :param mrmlNodeClass: mrmlNode class to be checked for eligible Annotation subclass
    :type mrmlNodeClass: slicer.vtkMRMLNode
    :return: Annotation subclass if an eligible class was found, otherwise None
    :rtype: Annotation
    """
    for annotationClass in AnnotationFactory.ANNOTATION_CLASSES:
      if mrmlNodeClass == annotationClass.MRML_NODE_CLASS:
        return annotationClass
    return None