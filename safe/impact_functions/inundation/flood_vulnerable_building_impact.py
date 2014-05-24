# coding=utf-8
"""InaSAFE Disaster risk tool by Australian Aid - Flood Impact on OSM
Buildings

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
import csv
import os
from qgis.core import QgsMessageLog, QgsMessageLogConsole, QgsMessageOutput

from safe.metadata import (
    hazard_flood,
    hazard_tsunami,
    unit_wetdry,
    unit_feet_depth,
    unit_metres_depth,
    layer_vector_polygon,
    layer_raster_numeric,
    exposure_structure,
    unit_building_type_type,
    hazard_definition,
    exposure_definition,
    unit_building_generic)
from safe.common.utilities import OrderedDict
from safe.impact_functions.core import (
    FunctionProvider, get_hazard_layer, get_exposure_layer, get_question)
from safe.storage.vector import Vector
from safe.storage.utilities import DEFAULT_ATTRIBUTE
from safe.common.utilities import ugettext as tr, format_int, verify
from safe.common.tables import Table, TableRow
from safe.engine.interpolation import assign_hazard_values_to_exposure_data
from safe.impact_functions.impact_function_metadata import (
    ImpactFunctionMetadata)
import logging

LOGGER = logging.getLogger('InaSAFE')

path = os.path.dirname(__file__)

class FloodVulnerableBuildingImpactFunction(FunctionProvider):
    """Inundation impact on building data.

    :author Ole Nielsen, Kristy van Putten
    # this rating below is only for testing a function, not the real one
    :rating 0
    :param requires category=='hazard' and \
                    subcategory in ['flood', 'tsunami']

    :param requires category=='exposure' and \
                    subcategory=='structure' and \
                    layertype=='vector'
    """

    class Metadata(ImpactFunctionMetadata):
        """Metadata for Flood Building Impact Function.

        .. versionadded:: 2.1

        We only need to re-implement get_metadata(), all other behaviours
        are inherited from the abstract base class.
        """

        @staticmethod
        def get_metadata():
            """Return metadata as a dictionary.

            This is a static method. You can use it to get the metadata in
            dictionary format for an impact function.

            :returns: A dictionary representing all the metadata for the
                concrete impact function.
            :rtype: dict
            """
            dict_meta = {
                'id': 'FloodVulnerableBuildingImpactFunction',
                'name': tr('Flood Vulnerable Building Impact Function'),
                'impact': tr('Be vulnerable to flood'),
                'author': ['Ole Nielsen', 'Kristy van Putten', 'maul'],
                'date_implemented': '2014/05/25',
                'overview': tr(
                    'To assess the impacts of (flood or tsunami) inundation '
                    'on building vulnerability.'),
                'categories': {
                    'hazard': {
                        'definition': hazard_definition,
                        'subcategory': [
                            hazard_flood,
                            hazard_tsunami
                        ],
                        'units': [
                            unit_wetdry,
                            unit_metres_depth,
                            unit_feet_depth],
                        'layer_constraints': [
                            layer_vector_polygon,
                        ]
                    },
                    'exposure': {
                        'definition': exposure_definition,
                        'subcategory': exposure_structure,
                        'units': [
                            unit_building_type_type,
                            unit_building_generic],
                        'layer_constraints': [layer_vector_polygon]
                    }
                }
            }
            return dict_meta

    # Function documentation
    target_field = 'INUNDATED'
    title = tr('Be vulnerable to flood')
    synopsis = tr(
        'To assess the impacts of (flood or tsunami) inundation '
        'on building vulnerability.')
    actions = tr(
        'Provide details about how much damage the flood cause')
    detailed_description = tr(
        'The inundation status is calculated for each building (using the '
        'centroid if it is a polygon) based on the hazard levels provided. if '
        'the hazard is given as a raster a threshold of 1 meter is used. This '
        'is configurable through the InaSAFE interface. If the hazard is '
        'given as a vector polygon layer buildings are considered to be '
        'impacted depending on the value of hazard attributes (in order) '
        '"affected" or "FLOODPRONE": If a building is in a region that has '
        'attribute "affected" set to True (or 1) it is impacted. If attribute '
        '"affected" does not exist but "FLOODPRONE" does, then the building '
        'is considered impacted if "FLOODPRONE" is "yes". If neither '
        '"affected" nor "FLOODPRONE" is available, a building will be '
        'impacted if it belongs to any polygon. The latter behaviour is '
        'implemented through the attribute "inapolygon" which is automatically'
        ' assigned.')
    hazard_input = tr(
        'A hazard raster layer where each cell represents flood depth (in '
        'meters), or a vector polygon layer where each polygon represents an '
        'inundated area. In the latter case, the following attributes are '
        'recognised (in order): "affected" (True or False) or "FLOODPRONE" '
        '(Yes or No). (True may be represented as 1, False as 0')
    exposure_input = tr(
        'Vector polygon layer extracted from OSM where each polygon '
        'represents the footprint of a building.')
    output = tr(
        'Vector layer contains building is estimated to be flooded and the '
        'breakdown of the building by type.')
    limitation = tr(
        'This function only flags buildings as impacted or not either based '
        'on a fixed threshold in case of raster hazard or the the attributes '
        'mentioned under input in case of vector hazard.')

    # parameters
    parameters = OrderedDict([
        ('vulnerability matrix', os.path.join(path, 'vulnerability_matrix.csv')),
        ('postprocessors', OrderedDict([('BuildingType', {'on': True})]))
    ])

    def run(self, layers):
        """Flood impact to buildings (e.g. from Open Street Map).

         :param layers: List of layers expected to contain.
                * my_hazard: Hazard layer of flood
                * my_exposure: Vector layer of structure data on
                the same grid as my_hazard
        """
        vulnerability_path = self.parameters['vulnerability matrix']

        verify(os.path.exists(vulnerability_path),
               'The path: %s did not exists' % str(vulnerability_path))

        vulnerability = {}

        vulnerability_file = csv.DictReader(open(vulnerability_path))

        # QgsMessageLogConsole.logMessage('Log Console',QgsMessageLog.INFO)
        # QgsMessageLog.logMessage('Log message',QgsMessageLog.INFO)

        for row in vulnerability_file:
            print row
            print row['TYPE']
            building_type = row['TYPE'].replace(' ', '_').lower()
            # normalize type names for matching purposes
            price = float(row['PRICE'].replace('.', ''))  # Don't forget to sanitize the string from '.'
            a1 = float(row['A1'].replace(',', '.'))
            a2 = float(row['A2'].replace(',', '.'))
            a3 = float(row['A3'].replace(',', '.'))
            b1 = float(row['B1'].replace(',', '.'))
            b2 = float(row['B2'].replace(',', '.'))
            b3 = float(row['B3'].replace(',', '.'))
            c1 = float(row['C1'].replace(',', '.'))
            c2 = float(row['C2'].replace(',', '.'))
            c3 = float(row['C3'].replace(',', '.'))
            entry = {
                'PRICE': price,
                'A1': a1,
                'A2': a2,
                'A3': a3,
                'B1': b1,
                'B2': b2,
                'B3': b3,
                'C1': c1,
                'C2': c2,
                'C3': c3}
            vulnerability[building_type] = entry

        # Extract data
        my_hazard = get_hazard_layer(layers)  # Depth
        my_exposure = get_exposure_layer(layers)  # Building locations

        question = get_question(
            my_hazard.get_name(),
            my_exposure.get_name(),
            self)

        # No need for interpolation to follow spec.
        # Just use polygon intersection

        # Extract relevant exposure data
        # There are only 2 attributes for hazard level
        attribute_index = {
            'affected': my_hazard.fieldNameIndex('affected'),
            'CATEGORY': my_hazard.fieldNameIndex('CATEGORY')}

        # create report matrix
        report_matrix = {
            'All': {
                'Number of flooded': 0,
                'Estimated Loss': 0,
                'Total Building': 0,
                'Total Building Value:': 0,
                'Percentage of Loss': 0}}

        for key in vulnerability.keys():
            report_matrix[key] = {
                'Number of Flooded': 0,
                'Estimated Loss': 0,
                'Total Building': 0,
                'Total Building Value:': 0,
                'Percentage of Loss': 0}

        # set the target metadata for building attributes
        building_attributes = set(['type', 'TYPE', 'amenity', 'building_t', 'office', 'tourism', 'leisure', 'building']) & \
            set([field.name() for field in my_exposure.pendingFields()])

        building_category = vulnerability.keys() + ['supermarket']
        # iterate the features in hazard (the flood area)
        for area in my_hazard.getFeatures():
            # select only flooded area
            # get list of features in exposure that intersects with the
            # flooded area
            if area.attributes()[attribute_index['affected']] == 1:
                intersected_buildings = [b for b in my_exposure.getFeatures() if b.geometry().intersect(area)]
                not_intersected_buildings = [b for b in my_exposure.getFeatures() if b not in intersected_buildings]

                for building in intersected_buildings:
                    # check the building type
                    # rule to choose the building type:
                    # 1. get the list of attribute value of type that is included in the building type metadata
                    # 2. choose the type in the building_types that is relevant with the vulnerability keys
                    building_types = [building.attributes()[t] for t in building_attributes
                                      if building.attributes()[t] in building_category]

                    # choose the type if any, if not just choose 'other'
                    if len(building_types) > 0:
                        chosen_type = building_types[0]
                        # the spec says this
                        if chosen_type == 'supermarket':
                            chosen_type = 'commercial'
                    else:
                        chosen_type = 'other'

                    # add number of flooded buildings
                    report_matrix[chosen_type]['Number of Flooded'] += 1
                    # add estimated loss
                    # 1. get default price of the chosen_type
                    # 2. get category factor of the chosen_type
                    price = vulnerability[chosen_type]['price']
                    factor = vulnerability[chosen_type][area.attributes()[attribute_index['CATEGORY']]]
                    report_matrix[chosen_type]['Estimated Loss'] += price * factor
                    # add total number of building
                    report_matrix[chosen_type]['Total Building'] += 1
                    # add total number of building value
                    report_matrix[chosen_type]['Total Building Value'] += price * factor

                for building in not_intersected_buildings:
                    # check the building type
                    # rule to choose the building type:
                    # 1. get the list of attribute value of type that is included in the building type metadata
                    # 2. choose the type in the building_types that is relevant with the vulnerability keys
                    building_types = [building.attributes()[t] for t in building_attributes
                                      if building.attributes()[t] in vulnerability.keys()]
                    # choose the type if any, if not just choose 'other'
                    if len(building_types) > 0:
                        chosen_type = building_types[0]
                    else:
                        chosen_type = 'other'
                    # add total number of building
                    report_matrix[chosen_type]['Total Building'] += 1
                    # add total number of building value
                    report_matrix[chosen_type]['Total Building Value'] += price * factor

        # aggregate all the results to 'All' keys
        for key in report_matrix.keys():
            if not key == 'All':
                for column in report_matrix[key].keys():
                    if not column == 'Percentage of Loss':
                        report_matrix['All'][column] += report_matrix[key][column]
                    else:
                        loss = report_matrix[key]['Estimated Loss']
                        total_value = report_matrix[key]['Total Building Value']
                        report_matrix[key][column] = loss * 100.0 / total_value
        else:
            loss = report_matrix['All']['Estimated Loss']
            total_value = report_matrix['All']['Total Building Value']
            report_matrix['All']['Percentage of Loss'] = loss * 100.0 / total_value

        # Generate simple impact report
        table_body = [question,
                      TableRow(
                          [tr('Building Type')] + [tr(key) for key in report_matrix.keys()], header=True),
                      TableRow(
                          [tr('All')] +
                          [format_int(report_matrix['All'][field]) for field in report_matrix.keys()])]

        # Generate break down by building usage type is available
        if len(building_attributes) > 0:
            # Make list of building types
            building_list = []
            for usage in vulnerability.keys():
                building_type = usage.replace('_', ' ')

                # Lookup internationalised value if available
                building_type = tr(building_type)
                building_list.append(
                    [building_type.capitalize()] +
                    [format_int(report_matrix[usage][field]) for field in report_matrix.keys()])

            # Sort alphabetically
            building_list.sort()

            table_body.append(TableRow(tr('Breakdown by building type'),
                                       header=True))
            for row in building_list:
                s = TableRow(row)
                table_body.append(s)

        return None
