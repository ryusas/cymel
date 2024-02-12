# Add cymel plugin path to SafeModeAllowedlistPaths when in Maya 2022 or later UI mode.
# In userSetup.py, this can be done without going through user verification.
# If such rudeness is not allowed, please do not use this userSetup.py.
# The proper way is for each user to allow it on the UI.
try:
    import cymel.initmaya
    cymel.initmaya.addCymelPluginsPathToAllowedlist()
except:
    pass
