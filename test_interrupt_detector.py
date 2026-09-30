from interrupt_detector import InterruptDetector


detector = InterruptDetector()


def test_normal_request():
    result = detector.classify_interruption(
        "",
        "Book a flight from Bangalore to Delhi tomorrow",
    )

    assert result.interrupted is False
    assert result.interruption_type == "none"
    assert result.slots["origin"] == "Bangalore"
    assert result.slots["destination"] == "Delhi"
    assert result.slots["date"] == "tomorrow"


def test_destination_correction():
    result = detector.classify_interruption(
        "Book a flight from Bangalore to Delhi",
        "Actually, make that Mumbai",
    )

    assert result.interrupted is True
    assert result.interruption_type == "correction"
    assert result.changed_slots["destination"] == "Mumbai"


def test_date_correction():
    result = detector.classify_interruption(
        "Book a flight from Bangalore to Delhi tomorrow",
        "Actually, make it Friday",
    )

    assert result.interrupted is True
    assert result.interruption_type == "correction"
    assert result.changed_slots["date"] == "friday"


def test_multiple_corrections():
    result = detector.classify_interruption(
        "Book a flight from Bangalore to Delhi tomorrow",
        "Wait, from Bangalore to Mumbai on Friday",
    )

    assert result.interrupted is True
    assert result.interruption_type == "correction"

    assert result.changed_slots["destination"] == "Mumbai"
    assert result.changed_slots["date"] == "friday"


def test_additional_constraint():
    result = detector.classify_interruption(
        "Book a flight from Bangalore to Delhi",
        "Also, I need a return flight",
    )

    assert result.interrupted is False
    assert result.interruption_type == "constraint"


def test_noisy_correction():
    result = detector.classify_interruption(
        "Book a flight from Bangalore to Delhi",
        "uh wait no actually make that Mumbai",
    )

    assert result.interrupted is True
    assert result.interruption_type == "correction"
    assert result.changed_slots["destination"] == "Mumbai"


def test_return_flight():
    result = detector.classify_interruption(
        "",
        "Book a return flight from Bangalore to Mumbai",
    )

    assert result.slots["origin"] == "Bangalore"
    assert result.slots["destination"] == "Mumbai"
    assert result.slots["trip_type"] == "return"


def test_result_to_dict():
    result = detector.classify_interruption(
        "Book Bangalore to Delhi",
        "Actually make that Mumbai",
    )

    data = result.to_dict()

    assert isinstance(data, dict)
    assert "interrupted" in data
    assert "changed_slots" in data
    assert "new_goal" in data


if __name__ == "__main__":
    tests = [
        test_normal_request,
        test_destination_correction,
        test_date_correction,
        test_multiple_corrections,
        test_additional_constraint,
        test_noisy_correction,
        test_return_flight,
        test_result_to_dict,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("\nAll Person B tests passed.")