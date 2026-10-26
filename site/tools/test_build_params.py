from build_params import flatten


def test_flatten():
    pdef = {"json": {"version": 0}, "ATC_": {"ATC_X": {
        "Description": "d", "DisplayName": "t", "Range": {"low": "0", "high": "1"},
        "Units": "m", "Values": {"0": "a"}, "Bitmask": {"0": "b"}, "User": "Standard"}}}
    assert flatten(pdef) == [{"n": "ATC_X", "t": "t", "d": "d", "r": ["0", "1"], "u": "m", "v": {"0": "a"}, "b": {"0": "b"}}]
