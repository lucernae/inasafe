"""Definitions relating to default value."""

from safe.utilities.i18n import tr

__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'

vulnerability_score_default_value = {
    'key': 'vulnerability_score_default_value',
    'name': tr('Vulnerability Score Global Default'),
    'default_value': 0,
    # 0 means not vulnerable
    # In impact layer, affected exposure but not vulnerable just generally means
    # the exposure is indeed affected but not necessarily considered vulnerable.
    'min_value': 0,
    'max_value': 1000000000,
    'increment': 1,
    'description': tr(
        'Default vulnerability score assigned for each exposed feature.')
}