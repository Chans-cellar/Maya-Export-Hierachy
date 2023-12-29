import maya.cmds as cmds

import os

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from maya import OpenMayaUI
from shiboken2 import wrapInstance
from PySide2.QtGui import QPixmap
import json

# from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as omui

mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QWidget)


class ExportHierachy(QWidget):

    def __init__(self, *args, **kwargs):
        super(ExportHierachy, self).__init__(*args, **kwargs)

        self.setObjectName('ExportHierarchy')
        self.setWindowTitle('Export Hierarchy')
        self.setWindowFlags(Qt.Window)
        self.init_UI()
        self.isSkeletonUnparented = False
        self.isGeometryUnparented = False

    def init_UI(self):
        usd = cmds.internalVar(usd=True)
        UI_FILE = os.path.join(usd, 'Export_Hierachy', 'Resources', 'Export_Hierachy.ui')
        ui_file = QFile(UI_FILE)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()

        self.ui = loader.load(ui_file, parentWidget=self)
        ui_file.close()

        self.rigGroup_comboBox = self.ui.rigGroup_comboBox

        self.Face = self.ui.Face_RadioButton
        self.Beard = self.ui.Beard_RadioButton
        self.Hair = self.ui.Hair_RadioButton

        self.ui.createHierachy_Button.clicked.connect(self.createHierachy)

        self.inspectRootDAGs()

    def run_UI(self):
        self.ui.show()

    def inspectRootDAGs(self):

        self.rigGroup_comboBox.clear()

        # list the top level dag objects
        grpList = cmds.ls(assemblies=True)
        for item in grpList:

            # get the objects that endswith rig keyword and add to the dropdown
            if item.endswith('Rig'):
                self.rigGroup_comboBox.addItem(item)

        # check whether there are unparented geometry objects in top level
        if 'Geometry' or '|Geometry' in grpList:
            self.isGeometryUnparented = True
        else:
            self.isGeometryUnparented = False

        # check whether there are unparented skeleton objects in top level
        if 'DeformationSystem' in grpList:
            self.isSkeletonUnparented = True
        else:
            self.isSkeletonUnparented = False

    def createHierachy(self):

        self.inspectRootDAGs()

        # un-parent the deformation system
        if not self.isSkeletonUnparented:
            self.unparentSkeleton()

        # un-parent the geometry objects
        if self.isGeometryUnparented:
            cmds.undoInfo(closeChunk=True)
            cmds.undo()
            print("Tasks undone successfully")
        self.unparentGeometry()

    # function to un-parent the deformation system
    def unparentSkeleton(self):

        cmds.select('DeformationSystem')
        cmds.parent(w=True)
        cmds.setAttr('Main.jointVis', 1)
        self.isSkeletonUnparented = True

    # function to un-parent the Geometry
    def unparentGeometry(self):
        meshGroupName = None

        if self.Face.isChecked():
            # extract the body object name from rig names
            FaceGroupName = str(self.rigGroup_comboBox.currentText()).rsplit('Rig')[0]
            meshGroupName = FaceGroupName

        elif self.Beard.isChecked():
            meshGroupName = 'Beard'

        elif self.Hair.isChecked():
            meshGroupName = 'Hairs'

        # get the list of visible meshes in the specific group
        childList = cmds.ls(cmds.listRelatives(meshGroupName, c=True), v=True)

        # remove unwanted child meshes of the group
        for item in childList:
            removals = ['Mesh_Body', 'proxy']
            if item in removals:
                childList.remove(item)

        # select the list of objects
        cmds.select(childList)
        self.groupToGeometry()

    # function to parent the selected layers to the geometry
    def groupToGeometry(self):
        # establish the undo scope
        cmds.undoInfo(openChunk=True)

        try:
            # parent to world in the outliner
            cmds.parent(w=True)
            cmds.group()
            cmds.rename(cmds.ls(sl=True)[0], 'Geometry')
            self.isGeometryUnparented = True
        finally:
            print('chunk open')


try:
    exportHierachy.close()
    exportHierachy.deleteLater()
except:
    pass
exportHierachy = ExportHierachy()
exportHierachy.run_UI()
