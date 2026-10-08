#!/usr/bin/env python3

import states.query as sqry
from states.query import needs_db, STATE_CODE_LEN


# Field names:
STATE_CODE = 'state_code'
NAME = 'name'
POPULATION = 'population'
AREA = 'area'
METRO_AREA = 'metro_area'


class NotFoundError(LookupError):
    """
    Raised when something a county depends on, such as its state,
    does not exist.
    """


TEST_COUNTY = {
    STATE_CODE: "AL",
    NAME: "Test County",
    POPULATION: 50000,
    AREA: 600.5,
    METRO_AREA: "Test City, AL Metropolitan Statistical Area",
}

# County names are only unique within a state, so the data is keyed
# first by state code, then by county name.
COUNTY_TEST_DATA = {
    "AL": {
        "Autauga": {
            POPULATION: 58805,
            AREA: 594.44,
            METRO_AREA: "Montgomery, AL Metropolitan Statistical Area",
        },
        "Baldwin": {
            POPULATION: 231767,
            AREA: 1589.78,
            METRO_AREA: "Daphne-Fairhope-Foley, AL Metropolitan "
                        "Statistical Area",
        },
        "Barbour": {
            POPULATION: 25223,
            AREA: 884.88,
            METRO_AREA: "Eufaula, AL-GA Micropolitan Statistical Area",
        },
        "Bullock": {
            POPULATION: 10357,
            AREA: 622.80,
            METRO_AREA: "",
        },
    },
    # Add more counties as needed
}


@needs_db
def read():
    """
    Return all counties in the test data, keyed by state code,
    then by county name.
    """
    return COUNTY_TEST_DATA


@needs_db
def exists(state_code: str, name: str):
    """
    Check if a county exists in the test data.
    """
    return name in COUNTY_TEST_DATA.get(state_code, {})


@needs_db
def has_counties(state_code: str):
    """
    Check if a state has any counties in the test data.
    """
    return bool(COUNTY_TEST_DATA.get(state_code))


def check_valid_county(state_code: str, name: str, population: int,
                       area: float, metro_area: str,
                       is_update: bool = False):
    """
    Raise ValueError if the county data is invalid.
    For a create, the state must exist (else NotFoundError is raised) and
    the county must not exist yet; for an update (is_update=True), the
    county must already exist.
    A county need not be in a metro area, so metro_area may be empty.
    """
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f"State code must be {STATE_CODE_LEN}-letter string.")
    if not isinstance(name, str) or not name:
        raise ValueError("Name must be a non-empty string.")
    if is_update:
        if not exists(state_code, name):
            raise ValueError(f"County {name}, {state_code} does not exist.")
    else:
        if not sqry.exists(state_code):
            raise NotFoundError(f"State {state_code} not found.")
        if exists(state_code, name):
            raise ValueError(f"County {name}, {state_code} already exists.")
    if (not isinstance(population, int) or isinstance(population, bool)
            or population < 0):
        raise ValueError("Population must be a non-negative integer.")
    if (not isinstance(area, (int, float))
            or isinstance(area, bool) or area <= 0):
        raise ValueError("Area must be a positive number.")
    if not isinstance(metro_area, str):
        raise ValueError("Metro area must be a string.")
    return True


@needs_db
def create(state_code: str, name: str, population: int,
           area: float, metro_area: str):
    """
    Create a new county entry in the test data.
    """
    # check_valid_county raises ValueError if the county is invalid, so we
    # don't need to check the return value
    check_valid_county(state_code, name, population, area,
                       metro_area)
    counties = COUNTY_TEST_DATA.setdefault(state_code, {})
    counties[name] = {
        POPULATION: population,
        AREA: area,
        METRO_AREA: metro_area,
    }
    return counties[name]


@needs_db
def update(state_code: str, name: str, population: int,
           area: float, metro_area: str):
    """
    Update an existing county entry in the test data.
    The state code and name identify the county and cannot be changed.
    Raises ValueError if the update is invalid.
    """
    check_valid_county(state_code, name, population, area,
                       metro_area, is_update=True)
    COUNTY_TEST_DATA[state_code][name] = {
        POPULATION: population,
        AREA: area,
        METRO_AREA: metro_area,
    }
    return COUNTY_TEST_DATA[state_code][name]


@needs_db
def delete(state_code: str, name: str):
    """
    Delete a county entry from the test data.
    Returns the deleted entry, or None if it did not exist.
    A state left with no counties is removed too.
    """
    counties = COUNTY_TEST_DATA.get(state_code)
    if counties is None:
        return None
    deleted = counties.pop(name, None)
    if not counties:
        del COUNTY_TEST_DATA[state_code]
    return deleted


def main():
    for state_code, counties in read().items():
        for name, data in counties.items():
            print(f"County: {name}, {state_code}")
            print(f"Population: {data[POPULATION]}")
            print(f"Area (sq miles): {data[AREA]}")
            print(f"Metro area: {data[METRO_AREA] or '(none)'}")
            print("-" * 40)


if __name__ == "__main__":
    main()
