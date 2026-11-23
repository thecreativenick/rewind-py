from rewind import record


def find_last_even(values):
    found = None
    for v in values:
        if v % 2 == 0:
            found = v
    return found


def outer(n):
    total = 0
    for i in range(n):
        total += square(i)
    return total


def square(x):
    return x * x


def test_records_result_and_lines():
    result, trace = record(find_last_even, [1, 4, 7, 10, 3])
    assert result == 10
    assert len(trace) > 0
    assert all(s.function == "find_last_even" for s in trace.steps)


def test_history_of_a_variable():
    _, trace = record(find_last_even, [1, 4, 7, 10, 3])
    values = [v for _, v in trace.when_changed("found") if v is not None]
    assert values == ["None", "4", "10"]


def test_first_step_where_answers_when_question():
    _, trace = record(find_last_even, [3, 8])
    step = trace.first_step_where("found", "8")
    assert step is not None
    assert step.locals["v"] == "8"


def test_nested_calls_track_depth():
    result, trace = record(outer, 3)
    assert result == 0 + 1 + 4
    depths = {s.function: s.depth for s in trace.steps}
    assert depths["square"] == depths["outer"] + 1


def test_recording_can_run_twice():
    record(find_last_even, [2])
    _, trace = record(find_last_even, [2])
    assert len(trace) > 0
