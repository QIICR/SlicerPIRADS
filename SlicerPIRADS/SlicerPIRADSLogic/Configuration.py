import ConfigParser
from SlicerDevelopmentToolboxUtils.mixins import GeneralModuleMixin


class SlicerPIRADSConfiguration(GeneralModuleMixin):

  def __init__(self, moduleName, configFile):
    self.moduleName = moduleName
    self.configFile = configFile
    self.loadConfiguration()

  def loadConfiguration(self):

    config = ConfigParser.RawConfigParser()
    config.read(self.configFile)

    self.setSetting("Study_Assessment_Forms", config.get('Study Assessment Forms', 'schema_files'))
