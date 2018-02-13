#-----------------------------------------------------------------------------

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  SlicerPIRADSLogic/__init__.py
  SlicerPIRADSLogic/FormGenerator.py
  SlicerPIRADSLogic/FormGeneratorFactory.py
  SlicerPIRADSLogic/JSONFormGenerator.py
  SlicerPIRADSLogic/Configuration.py
  SlicerPIRADSWidgets/__init__.py
  SlicerPIRADSWidgets/AssessmentWidget.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/default.cfg
  Resources/Forms/Clinical_Information.json
  Resources/Forms/Procedure_Information.json
)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)

#-----------------------------------------------------------------------------