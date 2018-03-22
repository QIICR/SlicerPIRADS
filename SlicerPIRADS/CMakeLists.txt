#-----------------------------------------------------------------------------

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  SlicerPIRADSLogic/__init__.py
  SlicerPIRADSLogic/Configuration.py
  SlicerPIRADSLogic/Annotation.py
  SlicerPIRADSLogic/Finding.py
  SlicerPIRADSLogic/HangingProtocol.py
  SlicerPIRADSLogic/SeriesType.py
  SlicerPIRADSWidgets/__init__.py
  SlicerPIRADSWidgets/AssessmentDialog.py
  SlicerPIRADSWidgets/AnnotationWidget.py
  SlicerPIRADSWidgets/FindingsWidget.py
  SlicerPIRADSWidgets/ProstateSectorMapDialog.py
  SlicerPIRADSWidgets/DataSelectionDialog.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/default.cfg
  Resources/Forms/Clinical_Information.json
  Resources/Forms/Procedure_Information.json
  Resources/UI/AssessmentDialog.ui
  Resources/UI/DataSelectionDialog.ui
  Resources/UI/AnnotationItemWidget.ui
  Resources/UI/FindingsWidget.ui
  Resources/UI/FindingInformationWidget.ui
  Resources/UI/AnnotationItemWidget.ui
  Resources/UI/ProstateSectorMapDialog.ui
  Resources/UI/StudyLevelAssessmentWidget.ui
  Resources/Icons/Fiducials.png
  Resources/Icons/ProstateMap.png
  Resources/Icons/Ruler.png
  Resources/Icons/SegmentEditor.png
)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)

#-----------------------------------------------------------------------------