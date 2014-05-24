# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'flood_assessment_dialog_base.ui'
#
# Created: Sat May 24 14:08:15 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_FloodAssessmentDialogBase(object):
    def setupUi(self, FloodAssessmentDialogBase):
        FloodAssessmentDialogBase.setObjectName(_fromUtf8("FloodAssessmentDialogBase"))
        FloodAssessmentDialogBase.resize(525, 635)
        self.groupBox_2 = QtGui.QGroupBox(FloodAssessmentDialogBase)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 128, 508, 200))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_7 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.label_5 = QtGui.QLabel(self.groupBox_2)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout_7.addWidget(self.label_5, 0, 0, 1, 1)
        self.hazard_layer_combo = QtGui.QComboBox(self.groupBox_2)
        self.hazard_layer_combo.setObjectName(_fromUtf8("hazard_layer_combo"))
        self.gridLayout_7.addWidget(self.hazard_layer_combo, 3, 0, 1, 1)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.dim_path = QtGui.QLineEdit(self.groupBox_2)
        self.dim_path.setEnabled(True)
        self.dim_path.setObjectName(_fromUtf8("dim_path"))
        self.horizontalLayout_5.addWidget(self.dim_path)
        self.open_dim_tool = QtGui.QToolButton(self.groupBox_2)
        self.open_dim_tool.setEnabled(True)
        self.open_dim_tool.setObjectName(_fromUtf8("open_dim_tool"))
        self.horizontalLayout_5.addWidget(self.open_dim_tool)
        self.gridLayout_7.addLayout(self.horizontalLayout_5, 1, 0, 1, 1)
        self.label_title_3 = QtGui.QLabel(self.groupBox_2)
        self.label_title_3.setObjectName(_fromUtf8("label_title_3"))
        self.gridLayout_7.addWidget(self.label_title_3, 2, 0, 1, 1)
        self.button_box = QtGui.QDialogButtonBox(FloodAssessmentDialogBase)
        self.button_box.setGeometry(QtCore.QRect(10, 602, 508, 27))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.button_box.setObjectName(_fromUtf8("button_box"))
        self.groupBox_3 = QtGui.QGroupBox(FloodAssessmentDialogBase)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 334, 508, 144))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout_8 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_8.setObjectName(_fromUtf8("gridLayout_8"))
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.output_path = QtGui.QLineEdit(self.groupBox_3)
        self.output_path.setEnabled(False)
        self.output_path.setObjectName(_fromUtf8("output_path"))
        self.horizontalLayout_6.addWidget(self.output_path)
        self.open_output_tool = QtGui.QToolButton(self.groupBox_3)
        self.open_output_tool.setEnabled(False)
        self.open_output_tool.setObjectName(_fromUtf8("open_output_tool"))
        self.horizontalLayout_6.addWidget(self.open_output_tool)
        self.gridLayout_8.addLayout(self.horizontalLayout_6, 1, 0, 1, 1)
        self.label_6 = QtGui.QLabel(self.groupBox_3)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout_8.addWidget(self.label_6, 2, 0, 1, 1)
        self.same_dir_checkbox = QtGui.QCheckBox(self.groupBox_3)
        self.same_dir_checkbox.setChecked(True)
        self.same_dir_checkbox.setObjectName(_fromUtf8("same_dir_checkbox"))
        self.gridLayout_8.addWidget(self.same_dir_checkbox, 0, 0, 1, 1)
        self.load_result_checkbox = QtGui.QCheckBox(self.groupBox_3)
        self.load_result_checkbox.setEnabled(True)
        self.load_result_checkbox.setChecked(True)
        self.load_result_checkbox.setObjectName(_fromUtf8("load_result_checkbox"))
        self.gridLayout_8.addWidget(self.load_result_checkbox, 3, 0, 1, 1)
        self.webView = QtWebKit.QWebView(FloodAssessmentDialogBase)
        self.webView.setGeometry(QtCore.QRect(10, 10, 508, 112))
        self.webView.setProperty("url", QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setObjectName(_fromUtf8("webView"))

        self.retranslateUi(FloodAssessmentDialogBase)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("accepted()")), FloodAssessmentDialogBase.accept)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("rejected()")), FloodAssessmentDialogBase.close)
        QtCore.QMetaObject.connectSlotsByName(FloodAssessmentDialogBase)

    def retranslateUi(self, FloodAssessmentDialogBase):
        FloodAssessmentDialogBase.setWindowTitle(_translate("FloodAssessmentDialogBase", "Dialog", None))
        self.groupBox_2.setTitle(_translate("FloodAssessmentDialogBase", "Input", None))
        self.label_5.setText(_translate("FloodAssessmentDialogBase", "Data Kejadian Banjir / DIM (*.csv)", None))
        self.open_dim_tool.setText(_translate("FloodAssessmentDialogBase", "...", None))
        self.label_title_3.setText(_translate("FloodAssessmentDialogBase", "Hazard Layer (flood)", None))
        self.groupBox_3.setTitle(_translate("FloodAssessmentDialogBase", "Output", None))
        self.open_output_tool.setText(_translate("FloodAssessmentDialogBase", "...", None))
        self.label_6.setText(_translate("FloodAssessmentDialogBase", "The output will be a .shp shape file", None))
        self.same_dir_checkbox.setText(_translate("FloodAssessmentDialogBase", "Same directory as input file", None))
        self.load_result_checkbox.setText(_translate("FloodAssessmentDialogBase", "Add output layer to QGIS project", None))

from PyQt4 import QtWebKit
