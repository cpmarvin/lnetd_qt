# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/edit_label.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ChangeName(object):

    def change_name(self):
        #check if node name not in used
        new_label = self.lineEdit.text()
        node_labels = [ node.get_label() for node in self.graph.nodes ]
        if new_label in node_labels:
            #raise Exception
            QtWidgets.QMessageBox.critical(
                    self.horizontalLayoutWidget, "Error!", "There is a node with this name already !!!"
                )
        else:
            self.node.label = self.lineEdit.text()
            self.graph.redeploy_demands()

    def setupUi(self, EditLabel, node, graph):
        self.node = node
        self.graph = graph
        EditLabel.setObjectName("EditLabel")
        EditLabel.resize(281, 138)
        self.horizontalLayoutWidget = QtWidgets.QWidget(EditLabel)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(60, 40, 161, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.LabelLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.LabelLayout.setContentsMargins(0, 0, 0, 0)
        self.LabelLayout.setObjectName("LabelLayout")
        self.Label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.Label.setObjectName("Label")
        self.LabelLayout.addWidget(self.Label)
        self.lineEdit = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.lineEdit.setObjectName("lineEdit")
        self.LabelLayout.addWidget(self.lineEdit)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.LabelLayout.addItem(spacerItem)
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(EditLabel)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(60, 71, 161, 31))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.Save_btn = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.Save_btn.setObjectName("Save_btn")

        self.Save_btn.clicked.connect(self.change_name)

        self.horizontalLayout_2.addWidget(self.Save_btn)
        '''
        self.Cancel_btn = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.Cancel_btn.setObjectName("Cancel_btn")
        self.horizontalLayout_2.addWidget(self.Cancel_btn)
        '''

        self.retranslateUi(EditLabel)
        QtCore.QMetaObject.connectSlotsByName(EditLabel)

    def retranslateUi(self, EditLabel):
        _translate = QtCore.QCoreApplication.translate
        EditLabel.setWindowTitle(_translate("EditLabel", "Node Change Name"))
        self.Label.setText(_translate("EditLabel", "Name: "))
        self.Save_btn.setText(_translate("EditLabel", "Save"))
        '''
        self.Cancel_btn.setText(_translate("EditLabel", "Cancel"))
        '''
        self.lineEdit.setText(str(self.node.label))



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    EditLabel = QtWidgets.QWidget()
    ui = Ui_EditLabel()
    ui.setupUi(EditLabel)
    EditLabel.show()
    sys.exit(app.exec_())

