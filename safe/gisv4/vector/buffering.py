# coding=utf-8
"""
InaSAFE Disaster risk assessment tool developed by AusAid -

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

Issue https://github.com/inasafe/inasafe/issues/3185

"""

from qgis.core import (
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsFeature,
    QGis,
    QgsField,
)

from safe.common.exceptions import KeywordNotFoundError
from safe.common.utilities import get_utm_epsg
from safe.gisv4.vector.tools import create_memory_layer
from safe.definitionsv4.fields import hazard_value_field
from safe.utilities.i18n import tr


def buffering(layer, radii, callback=None):
    """
    Buffer a vector point or line layer into polygons.

    This processing algorithm will keep the original attribute table and
    will add a new one for the hazard class name according to
    safe.definitionsv4.fields.hazard_value_field.

    radii = OrderedDict()
    radii[500] = 'high'
    radii[1000] = 'medium'
    radii[2000] = 'low'

    Issue https://github.com/inasafe/inasafe/issues/3185

    :param layer: The layer to polygonize.
    :type layer: QgsVectorLayer

    :param radii: A dictionary of radius.
    :type radii: OrderedDict

    :param callback: A function to all to indicate progress. The function
        should accept params 'current' (int), 'maximum' (int) and 'step' (str).
        Defaults to None.
    :type callback: function

    :return: The buffered vector layer.
    :rtype: QgsVectorLayer
    """

    # Layer output
    output_layer_name = 'buffer'
    processing_step = tr('Buffer')

    input_crs = layer.crs()
    feature_count = layer.featureCount()

    # Set the new hazard value field
    fields = layer.fields()
    type_field = hazard_value_field['type'][0]
    name_field = hazard_value_field['key']
    new_field = QgsField(name_field, type_field)
    fields.append(new_field)

    buffered = create_memory_layer(
        output_layer_name, QGis.Polygon, input_crs, fields)
    data_provider = buffered.dataProvider()

    # Reproject features if needed into UTM if the layer is in 4326.
    if layer.crs().authid() == 'EPSG:4326':
        center = layer.extent().center()
        utm = QgsCoordinateReferenceSystem(
            get_utm_epsg(center.x(), center.y(), input_crs))
        transform = QgsCoordinateTransform(layer.crs(), utm)
        reverse_transform = QgsCoordinateTransform(utm, layer.crs())
    else:
        transform = None
        reverse_transform = None

    for i, feature in enumerate(layer.getFeatures()):
        geom = QgsGeometry(feature.geometry())

        if transform:
            geom.transform(transform)

        inner_ring = None

        for radius in radii:
            attributes = feature.attributes()

            # We add the hazard value name to the attribute table.
            attributes.append(radii[radius])

            circle = geom.buffer(radius, 30)

            if inner_ring:
                circle.addRing(inner_ring)

            inner_ring = circle.asPolygon()[0]

            new_feature = QgsFeature()
            if reverse_transform:
                circle.transform(reverse_transform)

            new_feature.setGeometry(circle)
            new_feature.setAttributes(attributes)

            data_provider.addFeatures([new_feature])

        if callback:
            callback(current=i, maximum=feature_count, step=processing_step)

    # We transfer keywords to the output.
    try:
        buffered.keywords = layer.keywords
        buffered.keywords['layer_geometry'] = 'polygon'
        buffered.keywords['attribute_field'] = name_field
    except AttributeError:
        raise KeywordNotFoundError

    return buffered
