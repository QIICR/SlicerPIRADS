import qt
import ctk
import slicer
import sys


from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest, ScriptedLoadableModuleWidget


__all__ = ['SlicerPIRADSTest']


class SlicerPIRADSTests:

  def __init__(self, parent):
    parent.title = "Slicer PIRADS Tests"
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = ["SlicerPIRADS"]
    parent.contributors = ["Christian Herz (SPL, BWH), Andrey Fedorov (SPL, BWH)"]
    parent.helpText = """
    """
    parent.acknowledgementText = """Surgical Planning Laboratory, Brigham and Women's Hospital, Harvard
                                    Medical School, Boston, USA This work was supported in part by the National
                                    Institutes of Health through grants U24 CA180918,
                                    R01 CA111288 and P41 EB015898."""
    self.parent = parent

    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['SlicerPIRADS'] = self.runTest

  def runTest(self):
    tester = SlicerPIRADSTest()
    tester.runTest()


class SlicerPIRADSTestsWidget(ScriptedLoadableModuleWidget):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.testsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.testsCollapsibleButton.setLayout(qt.QFormLayout())
    self.testsCollapsibleButton.text = "Slicer PIRADS Tests"
    self.layout.addWidget(self.testsCollapsibleButton)
    self.generateButtons()

  def generateButtons(self):

    def onButtonPressed(button):
      tester = getattr(sys.modules[__name__], button.name)()
      tester.runTest()

    buttons = []
    for testName in __all__:
      b = qt.QPushButton(testName)
      b.name = testName
      self.testsCollapsibleButton.layout().addWidget(b)
      buttons.append(b)

    map(lambda b: b.clicked.connect(lambda clicked: onButtonPressed(b)), buttons)


class SlicerPIRADSTest(ScriptedLoadableModuleTest):
  # TODO: this is meant to be the test for going trough the workflows

  def runTest(self):
    self.delayDisplay('Starting %s' % self.__class__.__name__)
    for testName in [f for f in self.__class__.__dict__.keys() if f.startswith('test_')]:
      getattr(self, testName)()
    self.delayDisplay('Test passed!')

