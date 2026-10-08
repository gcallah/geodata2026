#!/usr/bin/env python3

from functools import wraps

from data.db_connect import is_db_up


STATE_CODE_LEN = 2


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
    "state_code": "TS",
    "population": 1000000,
    "capital": "Test Capital",
    "area_sq_miles": 50000,
    "name": 'Test State',
}

STATE_TEST_DATA = {
    "AL": {
        "population": 4903200,
        "capital": "Montgomery",
        "area_sq_miles": 52420,
        "name": 'Alabama',
    },
    "AK": {
        "population": 731545,
        "capital": "Juneau",
        "area_sq_miles": 665384,
        "name": 'Alaska',
    },
    "AZ": {
        "population": 7278717,
        "capital": "Phoenix",
        "area_sq_miles": 113990,
        "name": 'Arizona',
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


def check_valid_state(state_code: str, population: int, capital: str,
                      area_sq_miles: float, name: str,
                      is_update: bool = False):
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
    if (not isinstance(area_sq_miles, (int, float))
            or isinstance(area_sq_miles, bool) or area_sq_miles <= 0):
        raise ValueError("Area must be a positive number.")
    if not isinstance(name, str) or not name:
        raise ValueError("Name must be a non-empty string.")
    return True


@needs_db
def create(state_code: str, population: int, capital: str,
           area_sq_miles: float, name: str):
    """
    Create a new state entry in the test data.
    """
    # check_valid_state raises ValueError if the state is invalid, so we don't
    # need to check the return value
    check_valid_state(state_code, population, capital, area_sq_miles, name)
    STATE_TEST_DATA[state_code] = {
        "population": population,
        "capital": capital,
        "area_sq_miles": area_sq_miles,
        "name": name,
    }
    return STATE_TEST_DATA[state_code]


@needs_db
def update(state_code: str, population: int, capital: str,
           area_sq_miles: float, name: str):
    """
    Update an existing state entry in the test data.
    The state code identifies the state and cannot be changed.
    Raises ValueError if the update is invalid.
    """
    check_valid_state(state_code, population, capital, area_sq_miles, name,
                      is_update=True)
    STATE_TEST_DATA[state_code] = {
        "population": population,
        "capital": capital,
        "area_sq_miles": area_sq_miles,
        "name": name,
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
        print(f"Population: {data['population']}")
        print(f"Capital: {data['capital']}")
        print(f"Area (sq miles): {data['area_sq_miles']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
