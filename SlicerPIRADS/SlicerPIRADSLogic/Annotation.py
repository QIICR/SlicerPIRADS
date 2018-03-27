import vtk
import slicer

from SlicerDevelopmentToolboxUtils.mixins import ParameterNodeObservationMixin


class AnnotationFactory(object):

  @staticmethod
  def getAnnotationClassForMRMLNodeClass(mrmlNodeClass):
    if mrmlNodeClass == "vtkMRMLSegmentationNode":
      return Segmentation
    return None


class Annotation(ParameterNodeObservationMixin):

  DataChangedEvent = vtk.vtkCommand.UserEvent + 201
  MRML_NODE_CLASS = None

  def __init__(self, volumeNode):
    if not self.MRML_NODE_CLASS:
      raise ValueError("MRML_NODE_CLASS needs to be defined for all inheriting classes of {}".format(self.__class__.__name__))
    self._masterVolume = volumeNode
    self._mrmlNode = slicer.mrmlScene.AddNewNodeByClass(self.MRML_NODE_CLASS)

  def delete(self):
    if self._mrmlNode:
      slicer.mrmlScene.RemoveNode(self._mrmlNode)


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