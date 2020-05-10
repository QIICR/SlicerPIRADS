import configparser
from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin


class SlicerPIRADSConfiguration(GeneralModuleMixin):

  def __init__(self, moduleName, configFile):
    self.moduleName = moduleName
    self.configFile = configFile
    self.loadConfiguration()

  def loadConfiguration(self):
    config = configparser.RawConfigParser()
    config.read(self.configFile)

    self.setSetting("Study_Assessment_Forms", config.get('Assessment Forms', 'study_schema_files'))
    self.setSetting("Patient_Assessment_Forms", config.get('Assessment Forms', 'patient_schema_files'))
