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
    self._setupConnections()

  def _configurePatientTable(self):
    self._patientTable = self.ui.findChild(qt.QTableView, "patientsTableView")
    self._patientTableModel = PatientsTableModel()
    self._patientTable.setModel(self._patientTableModel)
    self._patientTable.setSelectionBehavior(qt.QTableView.SelectRows)
    self._patientTable.setSelectionMode(qt.QTableView.SingleSelection)
    self._patientTable.verticalHeader().hide()
    self._patientTable.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
    self._patientTable.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.Stretch)
    self._patientTable.horizontalHeader().setSectionResizeMode(1, qt.QHeaderView.ResizeToContents)

  def _configureStudiesTable(self):
    self._studiesLabel = self.ui.findChild(qt.QLabel, "studiesLabel")
    self._studiesList = self.ui.findChild(qt.QTableView, "studiesTableView")
    self._studiesListModel = qt.QStandardItemModel()
    self._studiesList.setModel(self._studiesListModel)
    self._studiesList.setSelectionBehavior(qt.QTableView.SelectRows)
    self._studiesList.setSelectionMode(qt.QTableView.SingleSelection)
    self._studiesList.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
    self._studiesList.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
    self._studiesList.verticalHeader().hide()
    self._studiesList.horizontalHeader().hide()

  def _setupConnections(self):
    self._browseButton.clicked.connect(self._onBrowseButtonClicked)
    self._loadButton.clicked.connect(self._onLoadButtonClicked)
    self._patientTable.clicked.connect(self._onPatientSelected)
    self._studiesList.selectionModel().connect('currentChanged(QModelIndex, QModelIndex)', self._onStudySelected)
    self.destroyed.connect(self._cleanupConnections)

  def _cleanupConnections(self):
    self._browseButton.clicked.disconnect(self._onBrowseButtonClicked)
    self._loadButton.clicked.disconnect(self._onLoadButtonClicked)
    self._patientTable.clicked.disconnect(self._onPatientSelected)
    self._studiesList.selectionModel().disconnect('currentChanged(QModelIndex, QModelIndex)', self._onStudySelected)

  def _onPatientSelected(self, modelIndex):
    self._studiesListModel.clear()
    pid = self._patientTableModel.getPatients()[modelIndex.row()]
    studies = self._patientTableModel.getStudiesForPatient(pid)
    for study in studies:
      sItem = qt.QStandardItem(study)
      self._studiesListModel.appendRow(sItem)
    if self._studiesListModel.rowCount() == 1:
      modelIndex = self._studiesListModel.index(0,0)
      self._studiesList.selectionModel().select(modelIndex, self._studiesList.selectionModel().Select)
      self._studiesList.selectionModel().setCurrentIndex(modelIndex, self._studiesList.selectionModel().Select)
    else:
      self._loadButton.enabled = False

  def _onStudySelected(self, modelIndex):
    self._loadButton.enabled = DataSelectionLogic.isStudyPIRADSEligible(self._studiesListModel.data(modelIndex))

  def _onLoadButtonClicked(self):
    modelIndex = self._studiesList.selectionModel().currentIndex
    series = self.logic.getEligibleSeriesForStudy(self._studiesListModel.data(modelIndex))
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

  def getPatients(self):
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

  def loadStudy(self, studyID):
    pass

  def loadSeries(self, files):
    multiVolumeImporterPlugin = MultiVolumeImporterPluginClass()
    scalarVolumePlugin = DICOMScalarVolumePluginClass()
    loadables = scalarVolumePlugin.examineFiles(files) + multiVolumeImporterPlugin.examineFiles(files)
    loadables.sort(reverse=True, key=lambda loadable: loadable.confidence)
    if loadables:
      scalarVolumePlugin.load(loadables[0])