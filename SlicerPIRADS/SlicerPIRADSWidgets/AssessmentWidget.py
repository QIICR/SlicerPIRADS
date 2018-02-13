import qt
import logging

from SlicerPIRADSLogic.FormGeneratorFactory import FormGeneratorFactory
from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, GeneralModuleMixin


class AssessmentWidget(qt.QDialog):

  def __init__(self, schemaFiles, parent=None):
    qt.QDialog.__init__(self, parent)
    self.standardButtons = None
    self.clickedButton = None

    self.logic = AssessmentLogic(schemaFiles)

    self.formWidgets = []
    self.setup()
    self.setupConnections()

  def setup(self):
    self.setLayout(qt.QGridLayout())

    self.generateFormWidgets()

    self.tabWidget = AssessmentTabWidget(self.formWidgets)

    self.buttonBox = qt.QDialogButtonBox()
    self.buttonBox.standardButtons = self.standardButtons if getattr(self, "standardButtons") else \
      qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel

    self.layout().addWidget(self.tabWidget, 0, 0)
    self.layout().addWidget(UICreationHelpers.createHLayout(self.buttonBox.buttons()), 1, 0)

  def setupConnections(self):
    self.buttonBox.accepted.connect(lambda: self.accept())
    self.buttonBox.rejected.connect(lambda: self.reject())
    self.buttonBox.clicked.connect(lambda b: setattr(self, "clickedButton", self.buttonBox.standardButton(b)))

  def generateFormWidgets(self):
    for form in self.logic.schemaFiles:
      gen = FormGeneratorFactory.getFormGenerator(form)
      formWidget = gen.generate()
      self.formWidgets.append(formWidget)

  def getData(self):
    data = dict()
    for form in self.formWidgets:
      data.update(form.getData())
    return data


class AssessmentLogic(object):

  @property
  def schemaFiles(self):
    return self._schemaFiles

  @schemaFiles.setter
  def schemaFiles(self, schemaFiles):
    if type(schemaFiles) is str:
      schemaFiles = [schemaFiles]
    elif type(schemaFiles) is list:
      pass
    else:
      raise ValueError("Value %s is not valid for schema files. It has to be either a list or a string" % schemaFiles)
    self._schemaFiles = schemaFiles

  def __init__(self, schemaFiles):
    self.schemaFiles = schemaFiles


class AssessmentTabWidget(qt.QTabWidget):

  def __init__(self, formWidgets):
    super(AssessmentTabWidget, self).__init__()
    self._createTabs(formWidgets)
    self.currentChanged.connect(self.onCurrentTabChanged)
    self.onCurrentTabChanged(0)

  def _createTabs(self, formWidgets):
    for widget in formWidgets:
      logging.debug("Adding tab for %s step" % widget.title)
      self.addTab(widget, widget.title)

  def hideTabs(self):
    self.tabBar().hide()

  def onCurrentTabChanged(self, index):
    pass