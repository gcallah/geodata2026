#!/usr/bin/env python3

from functools import wraps

from data.db_connect import is_db_up
from states.fields import (
    AREA,
    CAPITAL,
    LATITUDE,
    LONGITUDE,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    NAME,
    POPULATION,
    STATE_CODE,
    STATE_CODE_LEN,
)


def needs_db(fn):
    """
    Decorate any function that needs the database: if the DB is down,
    print a message and return None instead of calling the function.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_db_up():
            print("Database is down.")
            return None
        return fn(*args, **kwargs)
    return wrapper


TEST_STATE = {
    STATE_CODE: "TS",
    POPULATION: 1000000,
    CAPITAL: "Test Capital",
    AREA: 50000,
    NAME: 'Test State',
    LATITUDE: 40.0,
    LONGITUDE: -100.0,
}

STATE_TEST_DATA = {
    "AL": {
        POPULATION: 4903200,
        CAPITAL: "Montgomery",
        AREA: 52420,
        NAME: 'Alabama',
        LATITUDE: 32.318231,
        LONGITUDE: -86.902298,
    },
    "AK": {
        POPULATION: 731545,
        CAPITAL: "Juneau",
        AREA: 665384,
        NAME: 'Alaska',
        LATITUDE: 63.588753,
        LONGITUDE: -154.493062,
    },
    "AZ": {
        POPULATION: 7278717,
        CAPITAL: "Phoenix",
        AREA: 113990,
        NAME: 'Arizona',
        LATITUDE: 34.048928,
        LONGITUDE: -111.093731,
    },
    # Add more states as needed
}


@needs_db
def read():
    """
    Return a list of all states in the test data.
    """
    return STATE_TEST_DATA


@needs_db
def exists(state_code: str):
    """
    Check if a state exists in the test data.
    """
    return state_code in STATE_TEST_DATA


def is_number(val) -> bool:
    """
    True if val is an int or float (but not a bool, which Python
    counts as an int).
    """
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def check_valid_state(state_code: str, population: int, capital: str,
                      area: float, name: str, latitude: float,
                      longitude: float, is_update: bool = False):
    """
    Raise ValueError if the state data is invalid.
    For a create, the state code must not exist yet; for an update
    (is_update=True), it must already exist.
    """
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f"State code must be {STATE_CODE_LEN}-letter string.")
    if is_update:
        if not exists(state_code):
            raise ValueError(f"State code {state_code} does not exist.")
    elif exists(state_code):
        raise ValueError(f"State code {state_code} already exists.")
    if not isinstance(population, int) or population < 0:
        raise ValueError("Population must be a non-negative integer.")
    if not isinstance(capital, str) or not capital:
        raise ValueError("Capital must be a non-empty string.")
    if not is_number(area) or area <= 0:
        raise ValueError("Area must be a positive number.")
    if not isinstance(name, str) or not name:
        raise ValueError("Name must be a non-empty string.")
    if (not is_number(latitude)
            or not MIN_LATITUDE <= latitude <= MAX_LATITUDE):
        raise ValueError(f"Latitude must be a number from {MIN_LATITUDE} "
                         + f"to {MAX_LATITUDE}.")
    if (not is_number(longitude)
            or not MIN_LONGITUDE <= longitude <= MAX_LONGITUDE):
        raise ValueError(f"Longitude must be a number from {MIN_LONGITUDE} "
                         + f"to {MAX_LONGITUDE}.")
    return True


@needs_db
def create(state_code: str, population: int, capital: str,
           area: float, name: str, latitude: float, longitude: float):
    """
    Create a new state entry in the test data.
    """
    # check_valid_state raises ValueError if the state is invalid, so we don't
    # need to check the return value
    check_valid_state(state_code, population, capital, area, name,
                      latitude, longitude)
    STATE_TEST_DATA[state_code] = {
        POPULATION: population,
        CAPITAL: capital,
        AREA: area,
        NAME: name,
        LATITUDE: latitude,
        LONGITUDE: longitude,
    }
    return STATE_TEST_DATA[state_code]


@needs_db
def update(state_code: str, population: int, capital: str,
           area: float, name: str, latitude: float, longitude: float):
    """
    Update an existing state entry in the test data.
    The state code identifies the state and cannot be changed.
    Raises ValueError if the update is invalid.
    """
    check_valid_state(state_code, population, capital, area, name,
                      latitude, longitude, is_update=True)
    STATE_TEST_DATA[state_code] = {
        POPULATION: population,
        CAPITAL: capital,
        AREA: area,
        NAME: name,
        LATITUDE: latitude,
        LONGITUDE: longitude,
    }
    return STATE_TEST_DATA[state_code]


@needs_db
def delete(state_code: str):
    """
    Delete a state entry from the test data.
    Returns the deleted entry, or None if it did not exist.
    Raises ValueError if the state still has counties.
    """
    # Imported here because counties.query imports this module.
    import counties.query as cqry
    if cqry.has_counties(state_code):
        raise ValueError(f"State {state_code} still has counties.")
    return STATE_TEST_DATA.pop(state_code, None)


def main():
    states = read()
    for state, data in states.items():
        print(f"State: {state}")
        print(f"Population: {data[POPULATION]}")
        print(f"Capital: {data[CAPITAL]}")
        print(f"Area (sq miles): {data[AREA]}")
        print("-" * 40)


if __name__ == "__main__":
    main()
