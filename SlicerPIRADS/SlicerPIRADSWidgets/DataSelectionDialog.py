import qt
import os
import slicer
import string
from MultiVolumeImporterPlugin import MultiVolumeImporterPluginClass
from DICOMScalarVolumePlugin import DICOMScalarVolumePluginClass


class DataSelectionDialog(qt.QDialog):

  def __init__(self, parent=None):
    qt.QDialog.__init__(self, parent)
    self.modulePath = os.path.dirname(slicer.util.modulePath("SlicerPIRADS"))
    self.logic = DataSelectionLogic()
    self.setup()

  def setup(self):
    path = os.path.join(self.modulePath, 'Resources', 'UI', 'DataSelectionDialog.ui')
    self.ui = slicer.util.loadUI(path)
    self._browseButton = self.ui.findChild(qt.QPushButton, "browseButton")
    self._loadButton = self.ui.findChild(qt.QPushButton, "loadButton")
    self._progress = self.ui.findChild(qt.QProgressBar, "progressBar")
    self._progress.hide()
    self._configurePatientTable()
    self._configureStudiesTable()
    self._configureCommonTableSettings()
    self._setupConnections()

  def _configurePatientTable(self):
    self._patientTable = self.ui.findChild(qt.QTableView, "patientsTableView")
    self._patientTableModel = PatientsTableModel()
    self._patientTable.setModel(self._patientTableModel)
    self._patientTable.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.Stretch)
    self._patientTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)

  def _configureStudiesTable(self):
    self._studiesLabel = self.ui.findChild(qt.QLabel, "studiesLabel")
    self._studiesTable = self.ui.findChild(qt.QTableView, "studiesTableView")
    self._studiesTableModel = qt.QStandardItemModel()
    self._studiesTable.setModel(self._studiesTableModel)
    self._studiesTable.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
    self._studiesTable.horizontalHeader().hide()

  def _configureCommonTableSettings(self):
    for table in [self._studiesTable, self._patientTable]:
      table.setSelectionBehavior(qt.QTableView.SelectRows)
      table.setSelectionMode(qt.QTableView.SingleSelection)
      table.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
      table.verticalHeader().hide()

  def _setupConnections(self):
    def setupConnections(funcName="connect"):
      getattr(self._browseButton.clicked, funcName)(self._onBrowseButtonClicked)
      getattr(self._loadButton.clicked, funcName)(self._onLoadButtonClicked)
      getattr(self._patientTable.selectionModel(), funcName)('currentChanged(QModelIndex, QModelIndex)',
                                                             self._onPatientSelected)
      getattr(self._studiesTable.selectionModel(), funcName)('currentChanged(QModelIndex, QModelIndex)',
                                                             self._onStudySelected)

    setupConnections()
    slicer.app.connect('aboutToQuit()', self.deleteLater)
    self.destroyed.connect(lambda : setupConnections(funcName="disconnect"))

  def _onPatientSelected(self, modelIndex):
    pid = self._patientTableModel.getPatients()[modelIndex.row()]
    self._fillStudiesList(pid)
    if self._studiesTableModel.rowCount() == 1:
      self._autoSelectFirstStudy()
    else:
      self._loadButton.enabled = False

  def _autoSelectFirstStudy(self):
    modelIndex = self._studiesTableModel.index(0, 0)
    self._studiesTable.selectionModel().select(modelIndex, self._studiesTable.selectionModel().Select)
    self._studiesTable.selectionModel().setCurrentIndex(modelIndex, self._studiesTable.selectionModel().Select)

  def _fillStudiesList(self, pid):
    self._studiesTableModel.clear()
    studies = self._patientTableModel.getStudiesForPatient(pid)
    for study in studies:
      sItem = qt.QStandardItem(study)
      self._studiesTableModel.appendRow(sItem)

  def _onStudySelected(self, modelIndex):
    self._loadButton.enabled = DataSelectionLogic.isStudyPIRADSEligible(self._studiesTableModel.data(modelIndex))

  def _onLoadButtonClicked(self):
    modelIndex = self._studiesTable.selectionModel().currentIndex
    series = self.logic.getEligibleSeriesForStudy(self._studiesTableModel.data(modelIndex))
    self._progress.setMaximum(len(series))
    self._progress.show()

    for idx, s in enumerate(series):
      files = slicer.dicomDatabase.filesForSeries(s)
      self._progress.setValue(idx)
      slicer.app.processEvents()
      self.logic.loadSeries(files)

    self.ui.accept()

  def _onBrowseButtonClicked(self):
    path = qt.QFileDialog.getExistingDirectory(self.window(), "Select folder")
    if len(path):
      self._patientTable.update()

  def exec_(self):
    return self.ui.exec_()


class PatientsTableModel(qt.QAbstractTableModel):

  COLUMN_NAME = 'Patient Name'
  COLUMN_DOB = 'Date of Birth'

  headers = [COLUMN_NAME, COLUMN_DOB]

  @property
  def db(self):
    return slicer.dicomDatabase

  def __init__(self, parent=None, *args):
    qt.QAbstractTableModel.__init__(self, parent, *args)
    self._datasets = dict()

  def rowCount(self):
    return len(self.getPatients())

  def columnCount(self):
    return len(self.headers)

  def headerData(self, col, orientation, role):
    if orientation == qt.Qt.Horizontal and role in [qt.Qt.DisplayRole, qt.Qt.ToolTipRole]:
        return self.headers[col]
    return None

  def data(self, index, role):
    if role != qt.Qt.DisplayRole:
      return None

    col = index.column()

    pid = self.getPatients()[index.row()]

    if col == 0:
      return self._getPatientName(pid)
    elif col == 1:
      return self._getPatientBirthDate(pid)

  def getPatients(self):
    return self.db.patients()

  def _getPatientName(self, pid):
    return slicer.dicomDatabase.fileValue(self._getDataset(pid), "0010,0010")

  def _getPatientBirthDate(self, pid):
    return slicer.dicomDatabase.fileValue(self._getDataset(pid), "0010,0030")

  def _getDataset(self, pid):
    try:
      return self._datasets[pid]
    except KeyError:
      studies = self.getStudiesForPatient(pid)
      series = self.db.seriesForStudy(studies[0])
      self._datasets[pid] = self.db.filesForSeries(series[0])[0]
    return self._datasets[pid]

  def getStudiesForPatient(self, pid):
    return self.db.studiesForPatient(pid)


class DataSelectionLogic(object):

  def __init__(self):
    pass

  @staticmethod
  def isStudyPIRADSEligible(studyID):
    return len(DataSelectionLogic.getEligibleSeriesForStudy(studyID)) > 3

  @staticmethod
  def getEligibleSeriesForStudy(study):
    db = slicer.dicomDatabase
    series = db.seriesForStudy(study)
    validSeries = []
    for s in series:
      f = db.filesForSeries(s)[0]
      if DataSelectionLogic.isSeriesOfInterest(f):
        validSeries.append(s)
    return validSeries

  @staticmethod
  def isSeriesOfInterest(dcmFile):
    db = slicer.dicomDatabase
    modality = db.fileValue(dcmFile, "0008,0060")
    if modality != "MR":
      return False

    description = db.fileValue(dcmFile, "0008,103E")

    discardThose = ['SAG', 'COR', 'PURE', 'mapping', 'DWI',
                    'breath', '3D DCE', 'loc', 'Expo', 'Map',
                    'MAP', 'POST', 'ThreeParameter', 'AutoAIF',
                    'BAT', '-Slope', 'PkRsqr', 'Loc', 'Cal', 'Body']
    for d in discardThose:
      if string.find(description, d) >= 0:
        return False
    return True

  def loadSeries(self, files):
    scalarVolumePlugin = DICOMScalarVolumePluginClass()
    scalarLoadables = scalarVolumePlugin.examineFiles(files)

    multiVolumeImporterPlugin = MultiVolumeImporterPluginClass()
    multiVolumeLoadables = multiVolumeImporterPlugin.examineFiles(files)

    if multiVolumeLoadables and multiVolumeLoadables[0].confidence >= scalarLoadables[0].confidence:
      multiVolumeImporterPlugin.load(multiVolumeLoadables[0])
    else:
      scalarVolumePlugin.load(scalarLoadables[0])