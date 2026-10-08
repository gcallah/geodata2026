"""
The data dictionary for states.
The field-description constants are copied from
backendcore/data/fields.py, so this project does not depend on it.
"""

BAR = 'bar'
CHECKBOX = 'checkbox'
CHOICES = 'choices'
CLICK = 'click'
DEC_PLACES = 'decimalPlaces'
DESCR = 'description'
DICT = 'dict'
DISP_NAME = 'name'
DSRC_LINK = 'datasources'
FLD_TYPE = 'type'
FLOAT = 'float'
GRAPH = 'graph'
HIDDEN = 'hidden'
HI_VAL = 'high_value'
HOVER = 'hover'
INT = 'int'
JUSTIFICATION = 'justification'
LEFT = 'start'
LINE = 'line'
LINK = 'link'
LINK_ACTIVATE = 'link-activate'
LINK_TYPE = 'link-type'
LIST = 'list'
LOW_VAL = 'low_value'
MAP = 'map'
MARKDOWN = 'markdown'  # field contains markdown
MAX_LEN = 'maxLen'
ORIGIN = '$ORIGIN'
# sometimes we don't want sorting on a field; set this to True:
NO_SORT = 'noSort'
RIGHT = 'end'
STR = 'string'
VAL = '$VAL'
WIDTH = 'width'

# Common field names:
CODE = 'code'
DATE = 'date'
MORE_INFO = 'more_info'
MORE_INFO_DISP_NM = 'More info'
NAME = 'name'

# Field values:
DATE_LEN = 10
STATE_CODE_LEN = 2

# State field names:
STATE_CODE = 'state_code'
POPULATION = 'population'
CAPITAL = 'capital'
AREA = 'area'

STATE_FLDS = {
    STATE_CODE: {
        DISP_NAME: 'State Code',
        DESCR: 'The two-letter postal code for the state.',
        FLD_TYPE: STR,
        MAX_LEN: STATE_CODE_LEN,
    },
    NAME: {
        DISP_NAME: 'Name',
        DESCR: 'The name of the state.',
        FLD_TYPE: STR,
    },
    CAPITAL: {
        DISP_NAME: 'Capital',
        DESCR: 'The capital city of the state.',
        FLD_TYPE: STR,
    },
    POPULATION: {
        DISP_NAME: 'Population',
        DESCR: 'The number of people living in the state.',
        FLD_TYPE: INT,
        JUSTIFICATION: RIGHT,
    },
    AREA: {
        DISP_NAME: 'Area (sq miles)',
        DESCR: 'The total area of the state in square miles.',
        FLD_TYPE: FLOAT,
        DEC_PLACES: 2,
        JUSTIFICATION: RIGHT,
    },
}
