from safe.definitions import qvariant_numbers, default_field_length
from safe.definitions.fbf.default_values import vulnerability_score_default_value
from safe.utilities.i18n import tr

__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'

# Exposure_vulnerability_score_count_field
# Naming convention is used to make the field treated as _exposure_count_field
vulnerability_score_exposure_count_field = {
    'key': 'vulnerability_score_exposure_count_field',
    'name': tr('Exposure Vulnerability Score'),
    'field_name': 'vulnerability_score_exposure_count',
    'type': qvariant_numbers,
    'length': default_field_length,
    'precision': 2,
    'description': tr(  # Short description
        'Vulnerability score associated with each exposure feature. '
        'This number is treated like a count field.'),
    'help_text': tr(
        'Vulnerability score is a value that represents how vulnerable '
        'this exposure is to a hazard. '
        'Typical values can range from 0 to 1 to represent percentage or weight.'),
    'citations': [
        {
            'text': None,
            'link': None
        }
    ],
    # Null value can be replaced by default or not
    'replace_null': True,
    'default_value': vulnerability_score_default_value
}

# Exposure vulnerability score
exposed_vulnerability_score_count_field = {
    'key': 'exposed_vulnerability_score_count_field',
    'name': tr('Exposed Vulnerability Score'),
    'field_name': 'exposed_vulnerability_score',
    'type': qvariant_numbers,
    'length': default_field_length,
    'precision': 2,
    'description': tr(  # Short description
        'Summary field of total vulnerability score of exposed exposure feature. '
        'This number is treated like a count field.'),
    'help_text': tr(
        'Vulnerability score is a value that represents how vulnerable '
        'this exposure is to a hazard. '
        'Typical values can range from 0 to 1 to represent percentage or weight. '
        'In a summary layer, this value means the total vulnerability score of each exposed feature '
        'in that aggregated feature.'),
    'citations': [
        {
            'text': None,
            'link': None
        }
    ],
    # Null value can be replaced by default or not
    'replace_null': False
}


fbf_count_fields = [
    vulnerability_score_exposure_count_field
]
