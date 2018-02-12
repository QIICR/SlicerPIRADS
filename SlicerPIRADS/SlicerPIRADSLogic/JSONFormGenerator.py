import vtk
import json
from collections import OrderedDict

from .FormGenerator import *

from SlicerDevelopmentToolboxUtils.mixins import UICreationHelpers, ParameterNodeObservationMixin


# TODO: definitions are not resolved right now


class JSONFormGenerator(FormGenerator):

  CustomFrameClass = GeneratedFrame

  def generate(self):
    with open(self.filePath) as data_file:
      data = json.load(data_file, object_pairs_hook=OrderedDict)
      return self._generate(data)

  def _generate(self, schema):
    return JSONObjectField("", schema)


class JSONFieldFactory(object):

  @staticmethod
  def getJSONFieldClass(schema):
    dataType = schema.get('type')
    if dataType == "object":
      return JSONObjectField
    else:
      if dataType == "string":
        return JSONStringField
      elif dataType == "integer":
        return JSONIntegerField
      elif dataType == "number":
        return JSONNumberField
      # elif dataType == "array":
      #   return JSONArrayField
    raise ValueError("Schema %s cannot be handled by %s" % (schema, JSONFieldFactory.__name__))


class AbstractField(ParameterNodeObservationMixin):

  UpdateEvent = vtk.vtkCommand.UserEvent + 100

  def __init__(self, title, schema):
    self.title = title
    self._schema = schema
    self._data = dict()
    self.setup()

  def setup(self):
    return NotImplementedError

  def getData(self):
    return self._data

  def setData(self, data):
    #TODO: needs to iterate trough objects etc.
    # editable?
    raise NotImplementedError

  def _updateData(self, key, value):
    self._data[key] = value
    self.invokeEvent(self.UpdateEvent, str([key, value]))


class AbstractFieldWidget(qt.QWidget, AbstractField):

  def __init__(self, title, schema, parent=None):
    qt.QWidget.__init__(self, parent)
    AbstractField.__init__(self, title, schema)


class JSONObjectField(qt.QGroupBox, AbstractField):

  def __init__(self, title, schema, parent=None):
    self.elements = []
    qt.QGroupBox.__init__(self, parent)
    AbstractField.__init__(self, title, schema)

  def setup(self):
    self.setLayout(qt.QFormLayout())
    # keywords to handle: required, properties
    # description?
    # title?
    schema = self._schema
    if self._schema.get("title"):
      self.title = self._schema.get("title")
    if self._schema.get("description"):
      self.setToolTip(self._schema["description"])
    if self._schema.get('properties'):
      schema = self._schema['properties']
    for title, elem in schema.items():
      fieldObjectClass = JSONFieldFactory.getJSONFieldClass(elem)
      self._addElement(fieldObjectClass(title, elem))

  def _addElement(self, elem):
    if isinstance(elem, JSONObjectField):
      self.layout().addWidget(elem)
    else:
      self.layout().addRow(elem.title, elem)
    self.elements.append(elem)

  def getData(self):
    for elem in self.elements:
      self._data.update(elem.getData())
    return self._data if not self.title else {self.title: self._data}


class JSONArrayField(qt.QGroupBox, AbstractField):
  # TODO implement
  pass


class JSONEnumField(AbstractFieldWidget):

  def setup(self):
    self.setLayout(qt.QFormLayout())
    if self._schema.get("enum"):
      elem = self._setupEnumField()
    else:
      elem = self._setupField()
    self.layout().addWidget(elem)

  def _setupEnumField(self):
    widgetClass = self._schema.get("ui:widget", "combo")
    if widgetClass == "radio":
      elem = self.__setupRadioButtonGroup()
    else:
      elem = self.__setupComboBox()
    if self._schema.get("description"):
      elem.setToolTip(self._schema["description"])
    return elem

  def __setupComboBox(self):
    elem = qt.QComboBox()
    elem.connect("currentIndexChanged(QString)", lambda text: self._updateData(self.title, text))
    elem.addItems(self._schema["enum"])
    return elem

  def __setupRadioButtonGroup(self):
    elem = qt.QFrame()
    elem.setLayout(qt.QVBoxLayout())
    self.__buttonGroup = qt.QButtonGroup()
    self.__buttonGroup.setExclusive(True)
    self.__buttonGroup.connect("buttonClicked(QAbstractButton*)",
                               lambda button: self._updateData(self.title, button.text))
    for e in self._schema["enum"]:
      b = UICreationHelpers.createRadioButton(e, name=e)
      elem.layout().addWidget(b)
      self.__buttonGroup.addButton(b)
    return elem

  def _setupField(self):
    raise NotImplementedError


class JSONStringField(JSONEnumField):

  def _setupField(self):
    widgetClass = self._schema.get("ui:widget", "line")
    if widgetClass == "textarea":
      elem = qt.QTextEdit()
      elem.textChanged.connect(lambda: self._updateData(self.title, elem.toPlainText()))
    else:
      # has pattern?
      elem = qt.QLineEdit()
      elem.textChanged.connect(lambda text: self._updateData(self.title, text))

    if self._schema.get("maxLength"):
      elem.setMaxLength(self._schema["maxLength"])
    if self._schema.get("default"):
      default = self._schema["default"]
      elem.setText(default)
    if self._schema.get("description"):
      elem.setToolTip(self._schema["description"])
    return elem


class JSONNumberField(JSONEnumField):

  validatorClass = qt.QDoubleValidator

  def _setupField(self):
    self._configureValidator()
    elem = qt.QLineEdit()
    self._connectField(elem)
    elem.setValidator(self._validator)
    if self._schema.get("default"):
      elem.setText(self._schema["default"])
    if self._schema.get("description"):
      elem.setToolTip(self._schema["description"])
    return elem

  def _connectField(self, elem):
    elem.textChanged.connect(lambda n: self._updateData(self.title, float(n)))

  def _configureValidator(self):
    self._validator = self.validatorClass()
    if self._schema.get("minimum"):
      self._validator.setBottom(self._schema.get("minimum"))
    if self._schema.get("maximum"):
      self._validator.setTop(self._schema.get("maximum"))
    return self._validator


class JSONIntegerField(JSONNumberField):

  validatorClass = qt.QIntValidator

  def _connectField(self, elem):
    elem.textChanged.connect(lambda n: self._updateData(self.title, int(n)))