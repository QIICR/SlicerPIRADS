import qt
import ctk
import slicer
import inspect
import sys
import logging

from SlicerPIRADSLogic.JSONFormGenerator import *
from SlicerPIRADSLogic.FormGeneratorFactory import FormGeneratorFactory

from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest, ScriptedLoadableModuleWidget


__all__ = ['FormGeneratorFactoryTest', 'JSONFormGeneratorTest'] #'SlicerPIRADSTest',


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


class PIRADSModuleTestsBase(ScriptedLoadableModuleTest):

  def runTest(self):
    self.delayDisplay('Starting %s' % self.__class__.__name__)
    for testName in [f for f in self.__class__.__dict__.keys() if f.startswith('test_')]:
      getattr(self, testName)()
    self.delayDisplay('Test passed!')


class FormGeneratorFactoryTest(PIRADSModuleTestsBase):

  def test_right_generator(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    formGenerator = FormGeneratorFactory.getFormGenerator("/foo/bar/schema.json")
    self.assertIsInstance(formGenerator, JSONFormGenerator)

  def test_file_extension_not_supported(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    with self.assertRaises(ValueError):
      FormGeneratorFactory.getFormGenerator("/foo/bar/schema.xyz")


class JSONFormGeneratorTest(PIRADSModuleTestsBase):

  def test_json_form_generator_string_field(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    elem = JSONStringField("name", {
        "type": "string",
        "description": "First and Last name",
        "minLength": 4,
        "default": "John Doe"
      })
    self.assertDictEqual(elem.getData(), {"name": "John Doe"})

  def test_json_form_generator_enum(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    elem = JSONEnumField("Field of MRI scanner", {
        "type": "string",
        "enum": [
          "1.5T",
          "3T"
        ]
      })
    self.assertIsInstance(elem.getElement(), qt.QComboBox)

    elem = JSONEnumField("Field of MRI scanner", {
        "type": "string",
        "ui:widget": "combo",
        "enum": [
          "1.5T",
          "3T"
        ]
      })
    self.assertIsInstance(elem.getElement(), qt.QComboBox)

    elem = JSONEnumField("Field of MRI scanner", {
        "type": "string",
        "ui:widget": "radio",
        "enum": [
            "1.5T",
            "3T"
          ]
      })
    self.assertIsInstance(elem.getElement(), qt.QFrame)

  def test_json_form_generator_integer_type(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    elem = JSONIntegerField("age", {
        "type": "integer",
        "default": 25,
        "minimum": 18,
        "maximum": 99
      })

    self.assertDictEqual(elem.getData(), {"age": 25})
    self.assertEqual(elem._validator.bottom, 18)
    self.assertEqual(elem._validator.top, 99)

  def test_json_form_generator_object_field(self):
    logging.info('Starting %s' % inspect.stack()[0][3])

    import os
    path = os.path.join(os.path.dirname(os.path.normpath(os.path.dirname(inspect.getfile(FormGeneratorFactory)))),
                        "test_schema.json")

    formGenerator = FormGeneratorFactory.getFormGenerator(path)
    form = formGenerator.generate()
    dataPath = os.path.join(os.path.dirname(os.path.normpath(os.path.dirname(inspect.getfile(FormGeneratorFactory)))),
                            "test_data.json")
    with open(dataPath) as data_file:
      import json
      expected = json.load(data_file)
      self.maxDiff = None
      self.assertDictEqual(form.getData(), expected)


class SlicerPIRADSTest(ScriptedLoadableModuleTest):

  def runTest(self):
    pass

