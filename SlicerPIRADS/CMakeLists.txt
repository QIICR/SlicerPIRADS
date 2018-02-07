#-----------------------------------------------------------------------------

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  SlicerPIRADSLogic/__init__.py
  SlicerPIRADSLogic/FormGenerator.py
  SlicerPIRADSLogic/FormGeneratorFactory.py
  SlicerPIRADSLogic/JSONFormGenerator.py
  )

set(MODULE_PYTHON_RESOURCES
)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)

#-----------------------------------------------------------------------------