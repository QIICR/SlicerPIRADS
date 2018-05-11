#-----------------------------------------------------------------------------

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  SlicerPIRADSLogic/__init__.py
  SlicerPIRADSLogic/Configuration.py
  SlicerPIRADSLogic/Annotation.py
  SlicerPIRADSLogic/Exception.py
  SlicerPIRADSLogic/Finding.py
  SlicerPIRADSLogic/HangingProtocol.py
  SlicerPIRADSLogic/SeriesType.py
  SlicerPIRADSLogic/LesionAssessmentRules.py
  SlicerPIRADSLogic/Constants.py
  SlicerPIRADSLogic/PIRADSAssessmentCategory.py
  SlicerPIRADSWidgets/__init__.py
  SlicerPIRADSWidgets/AnnotationWidget.py
  SlicerPIRADSWidgets/FindingsWidget.py
  SlicerPIRADSWidgets/AssessmentWidget.py
  SlicerPIRADSWidgets/ProstateSectorMapDialog.py
  SlicerPIRADSWidgets/DataSelectionDialog.py
  SlicerPIRADSWidgets/ProstateWidget.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/default.cfg
  Resources/Forms/Imaging_Study_Information.json
  Resources/Forms/Patient_Clinical_Information.json
  Resources/UI/AnnotationItemWidget.ui
  Resources/UI/DataSelectionDialog.ui
  Resources/UI/FindingsWidget.ui
  Resources/UI/FindingInformationWidget.ui
  Resources/UI/ProstateSectorMapDialog.ui
  Resources/UI/AssessmentWidget.ui
  Resources/Icons/Fiducials.png
  Resources/Icons/ProstateMap.png
  Resources/Icons/Ruler.png
  Resources/Icons/SegmentEditor.png
  Resources/Images/prostate_sector_map.png
)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)

#-----------------------------------------------------------------------------