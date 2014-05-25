# coding=utf-8
"""InaSAFE Disaster risk tool by Australian Aid - modified Hackathon entry for flood
assessment

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
from itertools import count

__author__ = 'maul'

import csv
import os

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
from safe.common.utilities import OrderedDict, round_as_million, format_decimal
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
    :modified Rizky Maulana Nugraha

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

        for row in vulnerability_file:
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

        I = assign_hazard_values_to_exposure_data(
            my_hazard, my_exposure)

        attribute_names = I.get_attribute_names()
        attributes = I.get_data()
        N = len(attributes)

        question = get_question(
            my_hazard.get_name(),
            my_exposure.get_name(),
            self)

        # create report matrix
        report_matrix = {
            'All': {
                'Number of Flooded': 0,
                'Estimated Loss': 0,
                'Total Building': 0,
                'Total Building Value': 0,
                'Percentage of Loss': 0}}

        for key in vulnerability.keys():
            report_matrix[key] = {
                'Number of Flooded': 0,
                'Estimated Loss': 0,
                'Total Building': 0,
                'Total Building Value': 0,
                'Percentage of Loss': 0}

        # fix inconsistent attribute letter cases issues
        for key in attribute_names[:]:
            if not key.lower() in attribute_names:
                attribute_names.append(key.lower())
            if not key.upper() in attribute_names:
                attribute_names.append(key.upper())

        for i in range(N):
            # Use interpolated polygon attribute
            atts = attributes[i]

            # fix lower case uppercase issues
            for key in attributes[i].keys()[:]:
                if not key.lower() in attributes[i].keys():
                    attributes[i][key.lower()] = attributes[i][key]
                if not key.upper() in attributes[i].keys():
                    attributes[i][key.upper()] = attributes[i][key]

            # FIXME (Ole): Need to agree whether to use one or the
            # other as this can be very confusing!
            # For now look for 'affected' first
            if 'affected' in atts:
                # E.g. from flood forecast
                # Assume that building is wet if inside polygon
                # as flagged by attribute Flooded
                res = atts['affected']
                if res is None:
                    x = False
                else:
                    x = bool(res)

            elif 'FLOODPRONE' in atts:
                res = atts['FLOODPRONE']
                if res is None:
                    x = False
                else:
                    x = res.lower() == 'yes'
            elif DEFAULT_ATTRIBUTE in atts:
                # Check the default attribute assigned for points
                # covered by a polygon
                res = atts[DEFAULT_ATTRIBUTE]
                if res is None:
                    x = False
                else:
                    x = res
            else:
                # there is no flood related attribute
                msg = ('No flood related attribute found in %s. '
                       'I was looking for either "affected", "FLOODPRONE" '
                       'or "inapolygon". The latter should have been '
                       'automatically set by call to '
                       'assign_hazard_values_to_exposure_data(). '
                       'Sorry I can\'t help more.')
                raise Exception(msg)

            # Count affected buildings by usage type if available
            if 'type' in attribute_names:
                usage = atts['type']
                usage = self.handle_malformed(usage, vulnerability.keys())
            elif 'TYPE' in attribute_names:
                usage = atts['TYPE']
                usage = self.handle_malformed(usage, vulnerability.keys())
            else:
                usage = None

            if 'amenity' in attribute_names and (usage is None or usage == 0):
                usage = atts['amenity']
                usage = self.handle_malformed(usage, vulnerability.keys())
            if 'building_t' in attribute_names and (usage is None
                                                    or usage == 0):
                usage = atts['building_t']
                usage = self.handle_malformed(usage, vulnerability.keys())
            if 'office' in attribute_names and (usage is None or usage == 0):
                usage = atts['office']
                usage = self.handle_malformed(usage, vulnerability.keys())
            if 'tourism' in attribute_names and (usage is None or usage == 0):
                usage = atts['tourism']
                usage = self.handle_malformed(usage, vulnerability.keys())
            if 'leisure' in attribute_names and (usage is None or usage == 0):
                usage = atts['leisure']
                usage = self.handle_malformed(usage, vulnerability.keys())
            if 'building' in attribute_names and (usage is None or usage == 0):
                usage = atts['building']
                if usage == 'yes':
                    usage = 'building'
                    usage = self.handle_malformed(usage, vulnerability.keys())

            if usage is not None and usage != 0:
                usage = usage.lower().replace('_', '')
                if usage in vulnerability.keys():
                    key = usage
                elif usage == 'supermarket':
                    key = 'commercial'
                else:
                    key = 'other'
            else:
                key = 'other'

            # the building was flooded
            category = atts['CATEGORY']
            if category is not None:
                # add number of flooded buildings
                report_matrix[key]['Number of Flooded'] += 1
                # add estimated loss
                # 1. get default price of the chosen_type
                # 2. get category factor of the chosen_type
                price = vulnerability[key]['PRICE']
                factor = vulnerability[key][category]
                report_matrix[key]['Estimated Loss'] += price * factor
                # add total number of building
                report_matrix[key]['Total Building'] += 1
                # add total number of building value
                report_matrix[key]['Total Building Value'] += price
            else:
                # add estimated value
                # 1. get default price of the chosen_type
                # 2. get category factor of the chosen_type
                price = vulnerability[key]['PRICE']

                # add total number of building
                report_matrix[key]['Total Building'] += 1
                # add total number of building value
                report_matrix[key]['Total Building Value'] += price

            attributes[i][self.target_field] = int(x)

        # aggregate all the results to 'All' keys
        for key in report_matrix.keys():
            if not key == 'All':
                for column in report_matrix[key].keys():
                    if not column == 'Percentage of Loss':
                        report_matrix['All'][column] += report_matrix[key][column]
                    else:
                        loss = report_matrix[key]['Estimated Loss']
                        total_value = report_matrix[key]['Total Building Value']
                        if total_value > 0.0:
                            report_matrix[key][column] = loss * 100.0 / total_value
        else:
            loss = report_matrix['All']['Estimated Loss']
            total_value = report_matrix['All']['Total Building Value']
            report_matrix['All']['Percentage of Loss'] = loss * 100.0 / total_value

        # Generate simple impact report
        table_body = [
            question,
            TableRow([
                tr('Building Type'),
                tr('Number of Flooded'),
                tr('Estimated Loss (in million Rupiah)'),
                tr('Total Building'),
                tr('Total Building Value (in million Rupiah))'),
                tr('Percentage of Loss (%)')], header=True),
            TableRow([
                tr('All'),
                format_int(report_matrix['All']['Number of Flooded']),
                format_int(round_as_million(report_matrix['All']['Estimated Loss'])),
                format_int(report_matrix['All']['Total Building']),
                format_int(round_as_million(report_matrix['All']['Total Building Value'])),
                format_decimal(0.12, report_matrix['All']['Percentage of Loss'])])]

        # Generate break down by building usage type is available
        if len(vulnerability.keys()) > 0:
            # Make list of building types
            building_list = []
            for usage in vulnerability.keys():
                building_type = usage.replace('_', ' ')

                # Lookup internationalised value if available
                building_type = tr(building_type)
                building_list.append([
                    building_type.capitalize(),
                    format_int(report_matrix[usage]['Number of Flooded']),
                    format_int(round_as_million(report_matrix[usage]['Estimated Loss'])),
                    format_int(report_matrix[usage]['Total Building']),
                    format_int(round_as_million(report_matrix[usage]['Total Building Value'])),
                    format_int(report_matrix[usage]['Percentage of Loss'])])

            table_body.append(TableRow(tr('Breakdown by building type'),
                                       header=True))
            for row in building_list:
                s = TableRow(row)
                table_body.append(s)

        # Result
        impact_summary = Table(table_body).toNewlineFreeString()
        impact_table = impact_summary

        # Create style
        style_classes = [dict(label=tr('Not Inundated'), value=0,
                              colour='#1EFC7C', transparency=0, size=1),
                         dict(label=tr('Inundated'), value=1,
                              colour='#F31A1C', transparency=0, size=1)]
        style_info = dict(target_field=self.target_field,
                          style_classes=style_classes,
                          style_type='categorizedSymbol')

        # For printing map purpose
        map_title = tr('Buildings inundated')
        legend_units = tr('(inundated or not inundated)')
        legend_title = tr('Structure inundated status')

        # Create vector layer and return
        V = Vector(data=attributes,
                   projection=I.get_projection(),
                   geometry=I.get_geometry(),
                   name=tr('Estimated buildings affected'),
                   keywords={'impact_summary': impact_summary,
                             'impact_table': impact_table,
                             'target_field': self.target_field,
                             'map_title': map_title,
                             'legend_units': legend_units,
                             'legend_title': legend_title,
                             'buildings_total': report_matrix['All']['Total Building'],
                             'buildings_affected': report_matrix['All']['Number of Flooded']},
                   style_info=style_info)
        return V

    @staticmethod
    def handle_malformed(usage, lookup):
        # handle lettercases and underscore
        if usage is None:
            return None
        usage = usage.lower().replace('_', '')
        if usage in lookup:
            return usage
        # handle substring
        key_in_usage = [key for key in lookup if key in usage]
        if len(key_in_usage) == 1:
            return key_in_usage[0]
        # if there is more than one key in the usage, decide in the next attributes
        return None