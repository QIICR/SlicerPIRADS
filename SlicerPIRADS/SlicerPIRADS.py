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
    self._assessmentFormWidget = None

    self.setLayout(qt.QGridLayout())
    self._loadUI()
    self.layout().addWidget(self.ui)

  def _loadUI(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'FindingsWidget.ui')
    self.ui = slicer.util.loadUI(path)
    self._findingsButton = self.ui.findChild(qt.QPushButton, "findingsButton")
    self._findingsListView = self.ui.findChild(qt.QListView, "findingsListView")

  def setupConnections(self):
    self._findingsButton.clicked.connect(self._onStudyAssessmentButtonClicked)

  def _onStudyAssessmentButtonClicked(self):
    # TODO: findings assessment
    # TODO: add segmentation and enable editor
    pass


class FindingsModel(qt.QAbstractListModel):

  def __init__(self):
    pass

  def rowCount(self):
    # TODO: implement
    pass

  def data(self):
    # TODO: implement
    pass

  def addFinding(self, finding):
    pass

  def removeFinding(self, finding):
    pass


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

