#-----------------------------------------------------------------------------

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  SlicerPIRADSLogic/__init__.py
  SlicerPIRADSLogic/Configuration.py
  SlicerPIRADSWidgets/__init__.py
  SlicerPIRADSWidgets/AssessmentDialog.py
  SlicerPIRADSWidgets/DataSelectionDialog.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/default.cfg
  Resources/Forms/Clinical_Information.json
  Resources/Forms/Procedure_Information.json
  Resources/UI/AssessmentDialog.ui
  Resources/UI/DataSelectionDialog.ui
  Resources/UI/FindingItemWidget.ui
  Resources/UI/FindingsWidget.ui
  Resources/UI/MeasurementToolSelectionDialog.ui
  Resources/UI/ProstateSectorMapDialog.ui
  Resources/UI/StudyLevelAssessmentWidget.ui
)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)

#-----------------------------------------------------------------------------