import slicer
import os
import qt
from slicer.ScriptedLoadableModule import *

from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, GeneralModuleMixin, ModuleLogicMixin
from SlicerPIRADSLogic.Configuration import SlicerPIRADSConfiguration
from SlicerPIRADSWidgets.AssessmentDialog import AssessmentDialog


class SlicerPIRADS(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Slicer PIRADS"
    self.parent.categories = ["Informatics", "Quantification", "Segmentation"]
    self.parent.dependencies = ["SlicerDevelopmentToolbox"]
    self.parent.contributors = ["Christian Herz (SPL, BWH)", "Andrey Fedorov (SPL, BWH)"]
    self.parent.helpText = """
      
    """
    self.parent.acknowledgementText = """ 
      Surgical Planning Laboratory, Brigham and Women's Hospital, Harvard 
      Medical School, Boston, USA This work was supported in part by the 
      National Institutes of Health through grants U24 CA180918,
      R01 CA111288 and P41 EB015898.
    """


class SlicerPIRADSWidget(ScriptedLoadableModuleWidget, GeneralModuleMixin):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath(self.moduleName))
    SlicerPIRADSConfiguration(self.moduleName, os.path.join(self.modulePath, 'Resources', "default.cfg"))

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self._studyAssessmentWidget = SlicerPIRADSStudyLevelAssessmentWidget()
    self._findingsWidget = SlicerPIRADSSFindingsWidget()
    self.layout.addWidget(self._studyAssessmentWidget)
    self.layout.addWidget(self._findingsWidget)
    self.layout.addStretch(1)


class SlicerPIRADSStudyLevelAssessmentWidget(qt.QWidget, GeneralModuleMixin):

  def __init__(self, parent=None):
    qt.QWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()
    self.setupConnections()

  def setup(self):
    self._assessmentFormWidget = None

    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'StudyLevelAssessmentWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._studyLevelAssessmentButton = self.ui.findChild(qt.QPushButton, "studyLevelAssessmentButton")
    self._studyAssessmentListView = self.ui.findChild(qt.QListView, "studyAssessmentView")

  def setupConnections(self):
    self._studyLevelAssessmentButton.clicked.connect(self._onStudyAssessmentButtonClicked)

  def _onStudyAssessmentButtonClicked(self):
    if self._studyAssessmentListView.count != 0:
      self._studyAssessmentListView.clear()
      self._studyLevelAssessmentButton.icon = qt.QIcon(":/Icons/Add.png")
    else:
      # TODO: take care of situations when number of forms get changed in between
      if not self._assessmentFormWidget:
        forms = GeneralModuleMixin.getSetting(self, "Study_Assessment_Forms", moduleName="SlicerPIRADS")
        if forms:
          forms = [os.path.join(self.modulePath, 'Resources', 'Forms', f) for f in forms.split(" ")]
          self._assessmentFormWidget = AssessmentDialog(forms)
      self._assessmentFormWidget.exec_()
      print self._assessmentFormWidget.getData()
      # TODO: if item added, change icon and react
      self._studyAssessmentListView.addItem(self._assessmentFormWidget.getData())
      self._studyLevelAssessmentButton.icon = qt.QIcon(":/Icons/Remove.png")


class SlicerPIRADSSFindingsWidget(qt.QWidget, GeneralModuleMixin):

  def __init__(self, parent=None):
    qt.QWidget.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.setup()
    self.setupConnections()

  def setup(self):
    self._findingsModel = FindingsModel()

    self._assessmentFormWidget = None

    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'FindingsWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._addFindingsButton = self.ui.findChild(qt.QPushButton, "addFindingsButton")
    self._removeFindingsButton = self.ui.findChild(qt.QPushButton, "removeFindingsButton")
    self._findingsListWidget = self.ui.findChild(qt.QListView, "findingsListView")
    self._findingsListWidget.setModel(self._findingsModel)
    self.updateButtons()

  def setupConnections(self):
    self._addFindingsButton.clicked.connect(self._onAddFindingsButtonClicked)
    self._removeFindingsButton.clicked.connect(self._onRemoveFindingsButtonClicked)

  def _onAddFindingsButtonClicked(self):
    # TODO: findings assessment
    # TODO: add segmentation and enable editor
    measurementSelector = MeasurementToolSelectionDialog()
    if measurementSelector.exec_():
      # show widget and activate tool
      import random
      finding = Finding("Finding %s" %random.randint(0,10))
      finding.createLesion(measurementSelector.getSelectedMRMLNodeClass())
      self._findingsModel.addFinding(finding)
      findings = self._findingsModel.findings
      self._findingsListWidget.selectionModel().clear()
      self._findingsListWidget.selectionModel().setCurrentIndex(self._findingsModel.index(len(findings)-1, 0),
                                                                qt.QItemSelectionModel.Select)

      self.updateButtons()

  def _onRemoveFindingsButtonClicked(self):
    # TODO: if finding is selected, for now only removing last one
    index = self._findingsListWidget.selectionModel().selectedIndexes()
    self._findingsModel.removeFinding(self._findingsModel.findings[index[0].row()])
    self.updateButtons()

  def onSelectionChanged(self):
    self.updateButtons()

  def updateButtons(self):
    self._removeFindingsButton.setEnabled(self._findingsListWidget.selectedIndexes())


class FindingsModel(qt.QAbstractListModel):

  def __init__(self, parent=None, *args):
    qt.QAbstractListModel.__init__(self, parent, *args)
    self.findings = []

  def rowCount(self):
    return len(self.findings)

  def insertRows(self, row, count, parent=qt.QModelIndex()):
    self.beginInsertRows(parent, row, count)
    self.endInsertRows()

  def removeRows(self, row, count, parent=qt.QModelIndex()):
    self.beginRemoveRows(parent, row, count)
    self.endRemoveRows()

  def data(self, index, role=qt.Qt.DisplayRole):
    if index.isValid() and role == qt.Qt.DisplayRole:
      return self.findings[index.row()].getName()
    elif role == qt.Qt.DecorationRole:
      # TODO: add custom icon depending on what tool for segmentation was used
      return self.findings[index.row()].getLesion().getIcon()
    else:
      return None

  def addFinding(self, finding):
    self.findings.append(finding)
    # TODO: connect to finding events so that the model can be updated on finding changes
    self.insertRows(len(self.findings) - 1, 1)

  def getFinding(self, row):
    try:
      return self.findings[row]
    except IndexError:
      return None

  def removeFinding(self, finding):
    self.removeRows(self.findings.index(finding), 1)
    self.findings.pop(self.findings.index(finding))


class Finding(object):

  def __init__(self, name):
    self._name = name
    self._assessment = None
    # TODO: assessment holds data like location and score

  def __del__(self):
    # remove lesion
    # if self._lesion:
    #   slicer.mrmlScene.RemoveNode(self._lesion)
    pass

  def setName(self, name):
    self._name = name

  def getName(self):
    return self._name

  def createLesion(self, mrmlNodeClass):
    self._lesion = Lesion(mrmlNodeClass)

  def getLesion(self):
    return self._lesion


class Lesion(object):
  # maybe even subclass the specific types

  def __init__(self, mrmlNodeClass):
    self.mrmlNodeClass = mrmlNodeClass
    self._icon = MeasurementToolSelectionDialog.getIconFromMRMLNodeClass(mrmlNodeClass)

  def getIcon(self):
    return self._icon


class MeasurementToolSelectionDialog(object):

  ICON_MAP = {"slicer.vtkMRMLSegmentationNode": "SegmentEditor.png",
              "slicer.vtkMRMLAnnotationRulerNode": "Ruler.png",
              "slicer.vtkMRMLAnnotationRulerNode": "Fiducials.png"}

  def __init__(self):
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self._selectedMRMLNodeClass = None
    self.setup()

  def setup(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'MeasurementToolSelectionDialog.ui')
    self.ui = slicer.util.loadUI(path)

    for bName in ["segmentationButton", "rulerButton", "fiducialButton"]:
      button = self.ui.findChild(qt.QPushButton, bName)
      button.setIcon(self.getIconFromMRMLNodeClass(button.property("MRML_NODE_CLASS")))
      self._connectButton(button)

  def _connectButton(self, button):
    button.clicked.connect(lambda: setattr(self, "_selectedMRMLNodeClass", button.property("MRML_NODE_CLASS")))

  def exec_(self):
    return self.ui.exec_()

  @staticmethod
  def getIconFromMRMLNodeClass(name):
    modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    return qt.QIcon(os.path.join(modulePath, 'Resources', 'Icons', MeasurementToolSelectionDialog.ICON_MAP[name]))

  def getSelectedMRMLNodeClass(self):
    return self._selectedMRMLNodeClass

class MeasurementWidgetFactory(object):
  # TODO: write test
  # helper class for delivering widget to user with tools
  def getMeasurementWidget(self, mrmlNodeClass):
    if mrmlNodeClass is slicer.vtkMRMLSegmentationNode:
      return CustomSegmentEditorWidget()
    return None


class CustomSegmentEditorWidget(object):

  def __init__(self):
    pass


class LesionAssessment(object):

  def __init__(self):
    self._location = None
    self._score = None

  def getLocation(self):
    return self._location

  def getScore(self):
    return self._score


class SlicerPIRADSLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)


class SlicerPIRADSSlicelet(qt.QWidget):

  def __init__(self):
    qt.QWidget.__init__(self)
    self.mainWidget = qt.QWidget()
    self.mainWidget.objectName = "qSlicerAppMainWindow"
    self.mainWidget.setLayout(qt.QHBoxLayout())

    self.setupLayoutWidget()

    self.moduleFrame = qt.QWidget()
    self.moduleFrame.setLayout(qt.QVBoxLayout())
    self.widget = SlicerPIRADSWidget(self.moduleFrame)
    self.widget.setup()

    self.scrollArea = qt.QScrollArea()
    self.scrollArea.setWidget(self.widget.parent)
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.setMinimumWidth(self.widget.parent.minimumSizeHint.width())

    self.splitter = qt.QSplitter()
    self.splitter.setOrientation(qt.Qt.Horizontal)
    self.splitter.addWidget(self.scrollArea)
    self.splitter.addWidget(self.layoutWidget)
    self.splitter.splitterMoved.connect(self.onSplitterMoved)

    self.splitter.setStretchFactor(0, 0)
    self.splitter.setStretchFactor(1, 1)
    self.splitter.handle(1).installEventFilter(self)

    self.mainWidget.layout().addWidget(self.splitter)
    self.mainWidget.show()
    self.configureStyle()

  def configureStyle(self):
    slicer.app.setStyleSheet("""
      QWidget{
        background-color: #555555;
        color: white;
      }
    """)

  def setupLayoutWidget(self):
    # TODO: configurable ...
    self.layoutWidget = qt.QWidget()
    self.layoutWidget.setLayout(qt.QHBoxLayout())
    layoutWidget = slicer.qMRMLLayoutWidget()
    layoutManager = slicer.qSlicerLayoutManager()
    layoutManager.setMRMLScene(slicer.mrmlScene)
    layoutManager.setScriptedDisplayableManagerDirectory(slicer.app.slicerHome + "/bin/Python/mrmlDisplayableManager")
    layoutWidget.setLayoutManager(layoutManager)
    slicer.app.setLayoutManager(layoutManager)
    layoutWidget.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.layoutWidget.layout().addWidget(layoutWidget)

  def eventFilter(self, obj, event):
    if event.type() == qt.QEvent.MouseButtonDblClick:
      self.onSplitterClick()

  def onSplitterMoved(self, pos, index):
    vScroll = self.scrollArea.verticalScrollBar()
    vScrollbarWidth = 4 if not vScroll.isVisible() else vScroll.width + 4
    if self.scrollArea.minimumWidth != self.widget.parent.minimumSizeHint.width() + vScrollbarWidth:
      self.scrollArea.setMinimumWidth(self.widget.parent.minimumSizeHint.width() + vScrollbarWidth)

  def onSplitterClick(self):
    if self.splitter.sizes()[0] > 0:
      self.splitter.setSizes([0, self.splitter.sizes()[1]])
    else:
      minimumWidth = self.widget.parent.minimumSizeHint.width()
      self.splitter.setSizes([minimumWidth, self.splitter.sizes()[1] - minimumWidth])


if __name__ == "SlicerPIRADSSlicelet":
  slicelet = SlicerPIRADSSlicelet()

