from classiq_gaussian_state_preparation import create_solution


def test_create_solution_returns_callable():
    fn = create_solution(8)
    assert callable(fn)
