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
        self.isSkeletonParentTo_W = False
        self.isGeometryParentTo_W = False
        self.fullRigFlag = False

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
        self.FullRig = self.ui.FullRig_RadioButton

        self.ui.createHierachy_Button.clicked.connect(self.createHierachy)
        self.ui.refImport_Button.clicked.connect(self.load_Reference)
        self.ui.extractLayers_Button.clicked.connect(self.create_AnimExports)
        # self.ui.
        self.loadRigName()

    def run_UI(self):
        self.ui.show()

    # ----------------RIG EXPORT FUNCTIONS-----------------

    def loadRigName(self):
        self.rigGroup_comboBox.clear()

        # list the top level dag objects
        grpList = cmds.ls(assemblies=True)
        for item in grpList:
            # get the objects that endswith rig keyword and add to the dropdown
            if item.endswith('Rig'):
                self.rigGroup_comboBox.addItem(item)

    def inspectRootDAGs(self):

        # list the top level dag objects
        grpList = cmds.ls(assemblies=True)

        geoNames = ['Geometry', '|Geometry']
        # check whether there are unparented geometry objects in top level
        if any(grp in geoNames for grp in grpList):
            self.isGeometryParentTo_W = True
        else:
            self.isGeometryParentTo_W = False

        # check whether there are unparented skeleton objects in top level
        if 'DeformationSystem' in grpList:
            self.isSkeletonParentTo_W = True
        else:
            self.isSkeletonParentTo_W = False

    def createHierachy(self):

        self.inspectRootDAGs()

        # un-parent the deformation system
        if not self.isSkeletonParentTo_W:
            self.unparentSkeleton()

        # un-parent the geometry objects
        if self.isGeometryParentTo_W:
            cmds.undoInfo(closeChunk=True)
            cmds.undo()
            print("Tasks undone successfully")
        self.unparentGeometry()

    # function to un-parent the deformation system
    def unparentSkeleton(self):


        cmds.select('DeformationSystem')
        cmds.parent(w=True)
        self.isSkeletonParentTo_W = True
        cmds.setAttr('Main.jointVis', 1)

        # get level2 grandchildren of the deformation system
        childJoints = cmds.listRelatives(cmds.listRelatives(cmds.ls(sl=True)[0], c=True), c=True, type='joint',
                                         fullPath=True)
        for joint in childJoints:
            # select the bat_jnt and rename
            if joint.endswith('bat_jnt'):
                cmds.select(joint)
                cmds.rename('BatOffset_1')
                print('renamed successfully')

    # function to un-parent the Geometry
    def unparentGeometry(self):

        if self.FullRig.isChecked():
            FaceGroupName = str(self.rigGroup_comboBox.currentText()).rsplit('Rig')[0]
            meshGroupNameList = ['Body', 'HandTech', 'Shoes', 'HandGloves', 'LegGuards', 'Trousers',
                                 'Tshirts', 'Beards', 'Hairs', 'Caps', 'EarPieces', 'HeadGears']
            print('fullRig')
            self.fullRigFlag = True

            self.selectMultipleMeshGroups(meshGroupNameList)

        else:
            self.fullRigFlag = False
            meshGroupName = None
            if self.Face.isChecked():
                # extract the body object name from rig names
                # FaceGroupName = str(self.rigGroup_comboBox.currentText()).rsplit('Rig')[0]
                meshGroupName = 'Body'


            elif self.Beard.isChecked():
                meshGroupName = 'Beards'

            elif self.Hair.isChecked():
                meshGroupName = 'Hairs'

            self.selectSingleMeshGroup(meshGroupName)

    def selectSingleMeshGroup(self, meshGroupName):
        # get the list of visible meshes in the specific group
        try:
            childList = cmds.ls(cmds.listRelatives(meshGroupName, c=True), v=True)
        except ValueError:
            print(meshGroupName + ' not found')

        # remove unwanted child meshes of the group
        cleanedChildList = []
        if len(childList) > 0:
            for item in childList:
                removals = ['Mesh_Body', 'proxy', 'Mesh_HairBack_1', 'Mesh_HairBack']
                if item not in removals:
                    cleanedChildList.append(item)
        else:
            print('No such mesh')

        # select the list of objects
        cmds.select(cleanedChildList)
        self.group_ToGeometry()

    def selectMultipleMeshGroups(self, meshGroupNameList):
        cmds.select(clear=True)
        for meshGroupName in meshGroupNameList:
            try:
                cmds.select(meshGroupName, af=True)
            except:
                pass
        self.group_ToGeometry()

    def cleanFullRig(self):
        FaceGroupName = str(self.rigGroup_comboBox.currentText()).rsplit('Rig')[0]

        geoChildList = cmds.listRelatives(cmds.ls(sl=True)[0], c=True)

        for geoChild in geoChildList:

            geoGrandChildList = cmds.listRelatives(geoChild, c=True)
            if len(geoGrandChildList) > 0:
                for geoGrandChild in geoGrandChildList:
                    visibility_value = cmds.getAttr(geoGrandChild + ".visibility")

                    removals = ['proxy']
                    if (geoGrandChild in removals) or visibility_value == 0:
                        cmds.delete(geoGrandChild)

            if geoChild == FaceGroupName:
                cmds.rename(geoChild, 'Body')

    # function to parent the selected layers to the geometry
    def group_ToGeometry(self):
        # begin the undo scope
        cmds.undoInfo(openChunk=True)

        try:
            # parent to world in the outliner
            cmds.parent(w=True)
            cmds.group()
            cmds.rename(cmds.ls(sl=True)[0], 'Geometry')
            self.isGeometryParentTo_W = True
            if self.fullRigFlag:
                self.cleanFullRig()

        finally:
            print('chunk open')

    # ---------------ANIMATION EXPORT FUNCTIONS-------------------------------
    def load_Reference(self):
        all_ref_paths = cmds.file(q=True, reference=True) or []  # Get a list of all top-level references in the scene.

        for ref_path in all_ref_paths:
            if cmds.referenceQuery(ref_path, isLoaded=True):
                cmds.file(ref_path, importReference=True)  # Import the reference.
                print('object imported from reference')

        self.remove_Namespaces()

    def remove_Namespaces(self):
        defaults = ['UI', 'shared']
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        filtered_Namespaces = [i for i in namespaces if i not in defaults]  # Remove default namespaces from namespaces
        for ns in filtered_Namespaces:
            cmds.namespace(removeNamespace=ns, mergeNamespaceWithParent=True)
            print('Namespace ' + ns + ' Removed')

    def merge_AnimLayers(self):
        animation_layers = cmds.ls(type='animLayer')
        cmds.select(animation_layers)
        print(animation_layers)

    def create_AnimExports(self):
        self.fullRigFlag = False
        animExportMeshList = ['Body', 'Beards']
        self.unparentSkeleton()
        self.selectMultipleMeshGroups(animExportMeshList)


try:
    exportHierachy.close()
    exportHierachy.deleteLater()
except:
    pass
exportHierachy = ExportHierachy()
exportHierachy.run_UI()
