import asyncio

from kernel import Kernel, TaskStatus


# ==========================================================
# TEST 1 — BASIC TOOL EXECUTION
# ==========================================================

async def test_basic_tool_execution():

    print()
    print("=" * 70)
    print("TEST 1 — BASIC TOOL EXECUTION")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Turn on the bedroom light."
    )

    result = await kernel.execute_tool(
        "smart_home",
        task.task_id,
        action="turn_on",
        device="bedroom_light"
    )

    assert result.success is True
    assert result.data["device"] == "bedroom_light"
    assert result.data["state"] == "on"

    print("PASS: Smart home tool executed successfully.")


# ==========================================================
# TEST 2 — INVALID TOOL ARGUMENTS
# ==========================================================

async def test_invalid_arguments():

    print()
    print("=" * 70)
    print("TEST 2 — INVALID TOOL ARGUMENTS")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Search for a flight."
    )

    result = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru"
    )

    assert result.success is False
    assert result.retryable is False
    assert "destination" in result.error

    print("PASS: Invalid arguments handled correctly.")


# ==========================================================
# TEST 3 — RETRY / FLAKY TOOL
# ==========================================================

async def test_retry():

    print()
    print("=" * 70)
    print("TEST 3 — RETRY / FLAKY TOOL")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Find a flight from Bengaluru to Delhi."
    )

    result = await kernel.execute_tool(
        "flaky_flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert result.success is True
    assert result.data["flight"] == "SJ999"
    assert result.data["attempt"] == 3

    print(
        "PASS: Retry logic recovered from temporary failures."
    )


# ==========================================================
# TEST 4 — MULTIPLE TOOLS
# ==========================================================

async def test_multiple_tools():

    print()
    print("=" * 70)
    print("TEST 4 — MULTIPLE TOOLS")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Plan a Bengaluru to Delhi trip."
    )

    results = await kernel.execute_multiple_tools(
        task.task_id,
        [
            {
                "tool_name": "flight_search",
                "arguments": {
                    "origin": "Bengaluru",
                    "destination": "Delhi"
                }
            },
            {
                "tool_name": "hotel_search",
                "arguments": {
                    "city": "Delhi"
                }
            }
        ]
    )

    assert len(results) == 2

    assert results[
        "flight_search"
    ].success is True

    assert results[
        "hotel_search"
    ].success is True

    print(
        "PASS: Multiple tools executed successfully."
    )


# ==========================================================
# TEST 5 — CHECKPOINTS
# ==========================================================

async def test_checkpoints():

    print()
    print("=" * 70)
    print("TEST 5 — CHECKPOINTS")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Plan a trip."
    )

    flight_result = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert flight_result.success is True

    kernel.save_checkpoint(
        "flight_search_completed",
        "flight_search",
        flight=flight_result.data
    )

    assert task.current_step == 1

    assert task.checkpoint == (
        "flight_search_completed"
    )

    assert "flight" in task.slots

    hotel_result = await kernel.execute_tool(
        "hotel_search",
        task.task_id,
        city="Delhi"
    )

    assert hotel_result.success is True

    kernel.save_checkpoint(
        "hotel_search_completed",
        "hotel_search",
        hotel=hotel_result.data
    )

    assert task.current_step == 2

    assert task.checkpoint == (
        "hotel_search_completed"
    )

    assert "hotel" in task.slots

    print(
        "PASS: Checkpoints and slots persisted correctly."
    )


# ==========================================================
# TEST 6 — CANCELLATION
# ==========================================================

async def test_cancellation():

    print()
    print("=" * 70)
    print("TEST 6 — CANCELLATION")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Search for flights."
    )

    running_task = asyncio.create_task(
        kernel.execute_tool(
            "flight_search",
            task.task_id,
            origin="Bengaluru",
            destination="Delhi"
        )
    )

    await asyncio.sleep(0.1)

    kernel.cancel_current_task()

    try:

        await running_task

    except asyncio.CancelledError:

        pass

    assert task.status == (
        TaskStatus.CANCELLED
    )

    print(
        "PASS: Running task cancelled successfully."
    )


# ==========================================================
# TEST 7 — USER CORRECTION
# ==========================================================

async def test_user_correction():

    print()
    print("=" * 70)
    print("TEST 7 — USER CORRECTION")
    print("=" * 70)

    kernel = Kernel()

    original_task = kernel.start_task(
        "Find flights from Bengaluru to Delhi."
    )

    original_task_id = (
        original_task.task_id
    )

    new_task = kernel.handle_user_correction(
        "Actually, find flights from Bengaluru to Mumbai."
    )

    assert original_task.status == (
        TaskStatus.CANCELLED
    )

    assert new_task.task_id != (
        original_task_id
    )

    assert new_task.goal == (
        "Actually, find flights from Bengaluru to Mumbai."
    )

    result = await kernel.execute_tool(
        "flight_search",
        new_task.task_id,
        origin="Bengaluru",
        destination="Mumbai"
    )

    assert result.success is True

    assert result.data[
        "destination"
    ] == "Mumbai"

    print(
        "PASS: User correction created a new active task."
    )


# ==========================================================
# TEST 8 — LATE RESULT PROTECTION
# ==========================================================

async def test_late_result_protection():

    print()
    print("=" * 70)
    print("TEST 8 — LATE RESULT PROTECTION")
    print("=" * 70)

    kernel = Kernel()

    # ------------------------------------------------------
    # CREATE TASK A
    # ------------------------------------------------------

    task_a = kernel.start_task(
        "Find flights from Bengaluru to Delhi."
    )

    task_a_id = task_a.task_id

    # ------------------------------------------------------
    # CANCEL TASK A
    # ------------------------------------------------------

    kernel.cancel_current_task()

    assert task_a.status == (
        TaskStatus.CANCELLED
    )

    # ------------------------------------------------------
    # CREATE TASK B
    # ------------------------------------------------------

    task_b = kernel.start_task(
        "Find flights from Bengaluru to Mumbai."
    )

    # ------------------------------------------------------
    # TASK B MUST WORK
    # ------------------------------------------------------

    result_b = await kernel.execute_tool(
        "flight_search",
        task_b.task_id,
        origin="Bengaluru",
        destination="Mumbai"
    )

    assert result_b.success is True

    assert result_b.data[
        "destination"
    ] == "Mumbai"

    # ------------------------------------------------------
    # SIMULATE LATE RESULT FROM TASK A
    #
    # The Kernel should reject this before the tool
    # can modify the active task.
    # ------------------------------------------------------

    late_result_rejected = False

    try:

        await kernel.execute_tool(
            "flight_search",
            task_a_id,
            origin="Bengaluru",
            destination="Delhi"
        )

    except RuntimeError as error:

        late_result_rejected = True

        print()
        print(
            "Expected stale-task rejection:"
        )

        print(error)

    assert late_result_rejected is True

    # ------------------------------------------------------
    # VERIFY TASK B WAS NOT CORRUPTED
    # ------------------------------------------------------

    assert task_b.results[
        "flight_search"
    ].data[
        "destination"
    ] == "Mumbai"

    assert task_b.status == (
        TaskStatus.RUNNING
    )

    assert task_a.status == (
        TaskStatus.CANCELLED
    )

    print(
        "PASS: Late result from old task was rejected."
    )


# ==========================================================
# TEST 9 — DUPLICATE RESULT PROTECTION
# ==========================================================

async def test_duplicate_result_protection():

    print()
    print("=" * 70)
    print("TEST 9 — DUPLICATE RESULT PROTECTION")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Find a flight from Bengaluru to Delhi."
    )

    first_result = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert first_result.success is True

    original_data = task.results[
        "flight_search"
    ]

    duplicate_result = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert duplicate_result.success is True

    assert task.results[
        "flight_search"
    ] == original_data

    print(
        "PASS: Duplicate result did not corrupt task state."
    )


# ==========================================================
# TEST 10 — TASK ISOLATION
# ==========================================================

async def test_task_isolation():

    print()
    print("=" * 70)
    print("TEST 10 — TASK ISOLATION")
    print("=" * 70)

    kernel = Kernel()

    task_a = kernel.start_task(
        "Find flights from Bengaluru to Delhi."
    )

    task_a_id = task_a.task_id

    kernel.cancel_current_task()

    task_b = kernel.start_task(
        "Find flights from Bengaluru to Mumbai."
    )

    old_result_rejected = False

    try:

        await kernel.execute_tool(
            "flight_search",
            task_a_id,
            origin="Bengaluru",
            destination="Delhi"
        )

    except RuntimeError as error:

        old_result_rejected = True

        print()
        print(
            "Expected old-task rejection:"
        )

        print(error)

    assert old_result_rejected is True

    assert task_b.task_id != (
        task_a_id
    )

    assert (
        task_b.results.get(
            "flight_search"
        )
        is None
    )

    assert task_a.status == (
        TaskStatus.CANCELLED
    )

    assert task_b.status == (
        TaskStatus.RUNNING
    )

    print(
        "PASS: Old task cannot modify new task state."
    )


# ==========================================================
# TEST 11 — MULTI-STEP WORKFLOW
# ==========================================================

async def test_multi_step_workflow():

    print()
    print("=" * 70)
    print("TEST 11 — MULTI-STEP WORKFLOW")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Plan a trip from Bengaluru to Delhi."
    )

    # ------------------------------------------------------
    # STEP 1 — FLIGHT
    # ------------------------------------------------------

    flight = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert flight.success is True

    kernel.save_checkpoint(
        "flight_search_completed",
        "flight_search",
        flight=flight.data
    )

    # ------------------------------------------------------
    # STEP 2 — HOTEL
    # ------------------------------------------------------

    hotel = await kernel.execute_tool(
        "hotel_search",
        task.task_id,
        city="Delhi"
    )

    assert hotel.success is True

    kernel.save_checkpoint(
        "hotel_search_completed",
        "hotel_search",
        hotel=hotel.data
    )

    # ------------------------------------------------------
    # STEP 3 — FINALIZE
    # ------------------------------------------------------

    kernel.save_checkpoint(
        "workflow_ready",
        "finalization"
    )

    kernel.complete_current_task()

    # ------------------------------------------------------
    # VERIFY
    # ------------------------------------------------------

    assert task.status == (
        TaskStatus.DONE
    )

    assert task.current_step == 3

    assert task.checkpoint == (
        "task_completed"
    )

    assert len(
        task.completed_steps
    ) == 3

    assert "flight" in task.slots

    assert "hotel" in task.slots

    print(
        "PASS: Multi-step workflow completed."
    )


# ==========================================================
# FULL REGRESSION SUITE
# ==========================================================

async def run_all_tests():

    print()
    print()
    print("#" * 70)
    print("#")
    print("#       SAMSUNG AI KERNEL")
    print("#       END-TO-END REGRESSION SUITE")
    print("#")
    print("#" * 70)

    tests = [
        test_basic_tool_execution,
        test_invalid_arguments,
        test_retry,
        test_multiple_tools,
        test_checkpoints,
        test_cancellation,
        test_user_correction,
        test_late_result_protection,
        test_duplicate_result_protection,
        test_task_isolation,
        test_multi_step_workflow
    ]

    passed = 0

    for test in tests:

        try:

            await test()

            passed += 1

        except AssertionError as error:

            print()
            print(
                f"FAILED: {test.__name__}"
            )

            print(
                f"Assertion error: {error}"
            )

            raise

        except Exception as error:

            print()
            print(
                f"ERROR: {test.__name__}"
            )

            print(error)

            raise

    print()
    print()
    print("#" * 70)
    print(
        f"#   TESTS PASSED: "
        f"{passed}/{len(tests)}"
    )
    print("#" * 70)

    print()
    print(
        "ALL KERNEL REGRESSION TESTS PASSED"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        run_all_tests()
    )