from .FormGenerator import *
import json
from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers


class JSONFormGenerator(FormGenerator):

  CustomFrameClass = GeneratedFrame

  def generate(self):
    with open(self.filePath) as data_file:
      data = json.load(data_file)
      return self._generate(data)

  def _generate(self, data):
    form = self._initializeCustomForm()
    form.layout().addWidget(self.generateUIElement(data))
    return form

  @staticmethod
  def generateUIElement(data):
    if data.has_key('type'):
      dataType = data.pop('type')
      if dataType == "object":
        return JSONFormGenerator.generateObjectUIElement(data['properties'])
      else:
        if dataType == "string":
          return JSONFormGenerator.generateStringUIElement(data)
        elif dataType == "integer":
          return JSONFormGenerator.generateIntegerUIElement(data)
        elif dataType == "array":
          return JSONFormGenerator.generateArrayUIElement(data)
    else:
      form = JSONFormGenerator._initializeCustomForm()
      for title, elem in data.iteritems():
        form.layout().addRow(title, JSONFormGenerator.generateUIElement(elem))
      return form

    return None

  @staticmethod
  def generateObjectUIElement(data):
    groupBox = qt.QGroupBox()
    groupBox.setLayout(qt.QFormlayout())
    # keywords to handle: required, properties
    for title, elem in data.iteritems():
      groupBox.layout().addRow(title, JSONFormGenerator.generateUIElement(elem))
    return groupBox

  @staticmethod
  def generateStringUIElement(data):
    if data.has_key("enum"):
      # maybe default?
      elem = qt.QButtonGroup()
      elem.setExclusive(True)
      for e in data["enum"]:
        b = UICreationHelpers.createRadioButton(e)
        elem.addButton(b)
    else:
      elem = qt.QLineEdit()
      # minLength
      # has pattern?
      if data.has_key("maxLength"):
        elem.setMaxLength(data["maxLength"])
      if data.has_key("default"):
        elem.setText(data["default"])

    if data.has_key("description"):
      elem.setToolTip(data["description"])

    return elem

  @staticmethod
  def generateArrayUIElement(data):
    if data.has_key("enum"):
      # maybe default?
      # has pattern?
      pass
    else:
      pass
      # minLength
      # maxLength
      # pattern
    pass

  @staticmethod
  def generateIntegerUIElement(data):
    elem = qt.QSpinBox()
    if data.has_key("default"):
      elem.setValue(data["default"])
    if data.has_key("minimum"):
      elem.setMinimum(data["minimum"])
    if data.has_key("maximum"):
      elem.setMaximum(data["maximum"])
    if data.has_key("description"):
      elem.setToolTip(data["description"])
    return elem