import pytest

import states.fields as flds
import states.query as qry


def test_fields_match_test_state():
    """
    The data dictionary and the test state must describe the same fields.
    """
    assert set(flds.STATE_FLDS) == set(qry.TEST_STATE)


def test_fields_match_state_data():
    """
    Every stored state has exactly the non-key fields in the dictionary.
    """
    non_key_flds = set(flds.STATE_FLDS) - {flds.STATE_CODE}
    for data in qry.STATE_TEST_DATA.values():
        assert set(data) == non_key_flds


@pytest.mark.parametrize('fld_nm', list(flds.STATE_FLDS))
def test_field_is_described(fld_nm):
    fld = flds.STATE_FLDS[fld_nm]
    assert fld[flds.DISP_NAME]
    assert fld[flds.DESCR]
    assert fld[flds.FLD_TYPE] in (flds.STR, flds.INT, flds.FLOAT)


def test_state_code_max_len():
    state_code = flds.STATE_FLDS[flds.STATE_CODE]
    assert state_code[flds.MAX_LEN] == flds.STATE_CODE_LEN


def test_query_uses_fields_constants():
    assert qry.STATE_CODE is flds.STATE_CODE
    assert qry.STATE_CODE_LEN == flds.STATE_CODE_LEN


def test_get_flds():
    assert flds.get_flds() is flds.STATE_FLDS
