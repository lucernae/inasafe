# coding=utf-8
"""
Flood Assessment Dialog used to join flood data in the area of a layer

"""
import csv
import logging
import os
from PyQt4.QtCore import pyqtSignature, QVariant
from PyQt4.QtGui import QDialogButtonBox, QFileDialog
from qgis.core import (
    QgsVectorLayer,
    QgsVectorDataProvider,
    QgsField,
    QgsVectorFileWriter,
    QgsMapLayerRegistry)
from safe_qgis.exceptions import NoKeywordsFoundError, KeywordNotFoundError
from safe_qgis.safe_interface import styles
from safe_qgis.utilities.keyword_io import KeywordIO
from safe_qgis.utilities.utilities import html_header, html_footer
from safe_qgis.safe_interface import messaging as m

__author__ = 'maul'

from PyQt4 import QtGui
from safe_qgis.ui.flood_assessment_dialog_base import Ui_FloodAssessmentDialogBase

INFO_STYLE = styles.INFO_STYLE
LOGGER = logging.getLogger('InaSAFE')

class FloodAssessmentDialog(QtGui.QDialog, Ui_FloodAssessmentDialogBase):
    """Flood Assessment dialog for the InaSAFE plugin."""

    def __init__(self, parent=None):
        """Constructor for the dialog.

        :param parent: Parent widget of this dialog
        :type parent: QWidget
        """

        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(self.tr('Flood Assessment Dialog'))
        self.parent = parent
        self.warning_text = set()
        self.on_dim_path_textChanged()
        self.on_output_path_textChanged()
        # Keyword_io will be used to fetch hazard layer
        self.keyword_io = KeywordIO()
        self.update_warning()

        # Set up listeners
        self.same_dir_checkbox.toggled.connect(
            self.get_output_dir)
        self.dim_path.textChanged.connect(self.on_dim_path_textChanged)
        self.output_path.textChanged.connect(self.on_output_path_textChanged)

        # Get all current project layers for combo box
        self.get_project_layers()
        self.show_info()

    def update_warning(self):
        """Update warning message and enable/disable Ok button."""
        if len(self.warning_text) == 0:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            return

        header = html_header()
        footer = html_footer()
        string = header
        heading = m.Heading(self.tr('Flood Assessment Converter'), **INFO_STYLE)
        tips = m.BulletedList()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        message = m.Message()
        message.add(heading)
        for warning in self.warning_text:
            tips.add(warning)

        message.add(tips)
        string += message.to_html()
        string += footer
        self.webView.setHtml(string)

    def show_info(self):
        """Show usage text to the user."""
        header = html_header()
        footer = html_footer()
        string = header

        heading = m.Heading(self.tr('Flood Assessment Converter'), **INFO_STYLE)
        body = self.tr(
            'This tool receives DIM csv file as input and then merges it with'
            'a flood hazard layer. The output of this tool is shapefile that'
            'that contains the category of the flood disaster level for each '
            'area in the shapefile. The output of the file can be used as a hazard'
            'layer for analysis'
        )
        tips = m.BulletedList()
        tips.add(self.tr(
            'Select a *.csv file for the DIM input.'))
        tips.add(self.tr(
            'Choose where to write the output layer to (shapefile).'
        ))
        message = m.Message()
        message.add(heading)
        message.add(body)
        message.add(tips)
        string += message.to_html()
        string += footer

        self.webView.setHtml(string)

    def get_output_dir(self):
        """Create default output location based on input location.
        """
        input_path = self.dim_path.text()
        if self.same_dir_checkbox.isChecked():
            if input_path.endswith('.csv'):
                output_path = input_path[:-3] + 'shp'
            elif input_path == '':
                output_path = ''
            else:
                last_dot = input_path.rfind('.')
                if last_dot == -1:
                    output_path = ''
                else:
                    output_path = input_path[:last_dot + 1] + 'shp'
            self.output_path.setText(output_path)

    def accept(self):
        """Merge the data from DIM file and selected layer of flood hazard.
        """
        # Get all the input from dialog
        dim_path = self.dim_path.text()
        layer = self.hazard_layer_combo.itemData(self.hazard_layer_combo.currentIndex())
        output_path = self.output_path.text()
        is_load_result = self.load_result_checkbox.isChecked()

        # Load the input as list
        dim_data = []
        dim_file = csv.DictReader(open(dim_path))

        for row in dim_file:
            # store the following information:
            # ID_RWKEL, KETINGGIAN, DURASI
            # categorizes the depth to 3 category
            ketinggian = int(row['KETINGGIAN'])
            id_rwkel = int(row['ID_RWKEL'])
            if ketinggian <= 70:
                depth = 0
            elif ketinggian <= 150:
                depth = 1
            else:
                depth = 2

            # find if already in the list
            for added_row in dim_data:
                if added_row['ID_RWKEL'] == id_rwkel \
                        and added_row['KETINGGIAN'] == depth:
                    added_row['DURASI'] += 1
                    break
            else:
                entry = {
                    'ID_RWKEL': id_rwkel,
                    'KETINGGIAN': depth,
                    'DURASI': 1}
                dim_data.append(entry)

        # second pass: aggregate the result based on category matrix
        # define category matrix
        # row represents depth, column represents duration
        category_matrix = [
            ['A1', 'B1', 'C1'],
            ['A2', 'B2', 'C2'],
            ['A3', 'B3', 'C3']]

        for row in dim_data:
            if row['DURASI'] < 2:
                duration = 0
            elif row['DURASI'] <= 6:
                duration = 1
            else:
                self.warning_text.add('{0}'.format(row['ID_RWKEL']))
                duration = 2
            row['CATEGORY'] = category_matrix[row['KETINGGIAN']][duration]

        self.update_warning()
        # third and final pass, choose the worst results
        # rank the category with first priority rule
        category_rank = ['C3', 'C2', 'B3', 'B2', 'C1', 'A3', 'B1', 'A2', 'A1']
        final_dim_data = []
        for row in dim_data:
            for added_row in final_dim_data:
                # if the ID is already added
                if added_row['ID_RWKEL'] == row['ID_RWKEL']:
                    # check if the new data is a higher priority
                    if category_rank.index(row['CATEGORY']) < category_rank.index(added_row['CATEGORY']):
                        # update the category to worst case scenario
                        added_row['CATEGORY'] = row['CATEGORY']
            else:
                final_dim_data.append({'ID_RWKEL': row['ID_RWKEL'],
                                       'CATEGORY': row['CATEGORY']})

        # copy layer
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, 'CP1250', None, 'ESRI Shapefile')
        # load the new layer
        new_layer = QgsVectorLayer(output_path, '{0} with flood category'.format(layer.name()), 'ogr')
        # Iterate all the features in the shape file and do join
        # add two new attributes, category and affected
        new_layer.startEditing()
        provider = new_layer.dataProvider()
        capabilities = provider.capabilities()

        if capabilities & QgsVectorDataProvider.AddAttributes:
            provider.addAttributes([QgsField('affected', QVariant.Int)])
            provider.addAttributes([QgsField('CATEGORY', QVariant.String)])
        new_layer.commitChanges()

        # join the category from final_dim_data
        new_layer.startEditing()
        if capabilities & QgsVectorDataProvider.ChangeAttributeValues:
            for feature in new_layer.getFeatures():
                for row in final_dim_data:
                    # if '{0}'.format(feature['ID_RWKEL']) == '{0}'.format(row['ID_RWKEL']):
                    if feature['ID_RWKEL'] == row['ID_RWKEL']:
                        attributes = {provider.fieldNameIndex('affected'): 1,
                                      provider.fieldNameIndex('CATEGORY'): row['CATEGORY']}
                        provider.changeAttributeValues({feature.id(): attributes})
                        break
                else:
                    attributes = {provider.fieldNameIndex('affected'): 0}
                    provider.changeAttributeValues({feature.id(): attributes})

        new_layer.commitChanges()

        # write the resulting layer
        QgsVectorFileWriter.writeAsVectorFormat(new_layer, output_path, 'CP1250', None, 'ESRI Shapefile')

        # check if it had to automatically added to the layers list
        if is_load_result:
            QgsMapLayerRegistry.instance().addMapLayer(new_layer)

        # self.done(self.Accepted)

    def cancel_operation(self):
        self.close()

    def on_dim_path_textChanged(self):
        """Action when input file name is changed.
        """
        input_path = str(self.dim_path.text())
        input_not_exist_msg = str(self.tr('input file is not existed'))
        input_not_csv_msg = str(self.tr('input file is not .csv'))

        if not input_path.endswith('.csv'):
            self.warning_text.add(input_not_csv_msg)
        elif input_not_csv_msg in self.warning_text:
            self.warning_text.remove(input_not_csv_msg)

        if not os.path.isfile(input_path):
            self.warning_text.add(input_not_exist_msg)
        elif input_not_exist_msg in self.warning_text:
            self.warning_text.remove(input_not_exist_msg)

        if self.same_dir_checkbox.isChecked():
            self.get_output_dir()
        self.update_warning()

    def on_output_path_textChanged(self):
        """Action when output file name is changed.
        """
        output_path = str(self.output_path.text())
        output_not_shp_msg = str(self.tr('output file is not .shp'))
        if not output_path.endswith('.shp'):
            self.warning_text.add(output_not_shp_msg)
        elif output_not_shp_msg in self.warning_text:
            self.warning_text.remove(output_not_shp_msg)
        self.update_warning()

    @pyqtSignature('')  # prevents actions being handled twice
    def on_open_dim_tool_clicked(self):
        """Autoconnect slot activated when open input tool button is clicked.
        """
        # noinspection PyCallByClass,PyTypeChecker
        filename = QFileDialog.getOpenFileName(
            self, self.tr('Input DIM file'), '*.csv',
            self.tr('DIM file(*.csv)'))
        self.dim_path.setText(filename)

    @pyqtSignature('')  # prevents actions being handled twice
    def on_open_output_tool_clicked(self):
        """Autoconnect slot activated when open output tool button is clicked.
        """
        # noinspection PyCallByClass,PyTypeChecker
        filename = QFileDialog.getSaveFileName(
            self, self.tr('Output file'), '*.shp',
            self.tr('Shapefile(*.shp)'))
        self.output_path.setText(filename)

    def get_project_layers(self):
        """Get impact layers and aggregation layer currently loaded in QGIS."""
        registry = QgsMapLayerRegistry.instance()

        # MapLayers returns a QMap<QString id, QgsMapLayer layer>
        layers = registry.mapLayers().values()

        if len(layers) == 0:
            return

        # Clear the combo box at first time
        self.hazard_layer_combo.clear()

        for layer in layers:
            try:
                keywords = self.keyword_io.read_keywords(layer)
                if layer.isValid() and keywords['category'] == 'hazard' and keywords['subcategory'] == 'flood':
                    self.hazard_layer_combo.addItem(keywords['title'], layer)
            except (NoKeywordsFoundError, KeywordNotFoundError, KeyError):
                # Just continue if it doesn't have the keyword
                continue