import asyncio

from kernel import Kernel, TaskStatus
from kernel_events import KernelEventType


# ==========================================================
# TEST 1 — TASK STARTED EVENT
# ==========================================================

def test_task_started_event():

    print()
    print("=" * 70)
    print("TEST 1 — TASK STARTED EVENT")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Test task"
    )

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    assert len(events) == 1

    assert (
        events[0].event_type
        == KernelEventType.TASK_STARTED
    )

    assert (
        events[0].task_id
        == task.task_id
    )

    print(
        "PASS: TASK_STARTED event emitted."
    )


# ==========================================================
# TEST 2 — TOOL EVENTS
# ==========================================================

async def test_tool_events():

    print()
    print("=" * 70)
    print("TEST 2 — TOOL STARTED + COMPLETED EVENTS")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Turn on bedroom light."
    )

    result = await kernel.execute_tool(
        tool_name="smart_home",
        task_id=task.task_id,
        action="turn_on",
        device="bedroom_light"
    )

    assert result.success

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        KernelEventType.TASK_STARTED
        in event_types
    )

    assert (
        KernelEventType.TOOL_STARTED
        in event_types
    )

    assert (
        KernelEventType.TOOL_COMPLETED
        in event_types
    )

    print(
        "PASS: Tool lifecycle events emitted."
    )


# ==========================================================
# TEST 3 — CHECKPOINT EVENT
# ==========================================================

def test_checkpoint_event():

    print()
    print("=" * 70)
    print("TEST 3 — CHECKPOINT EVENT")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Checkpoint test."
    )

    kernel.save_checkpoint(
        checkpoint="test_checkpoint",
        step_name="test_step",
        value="hello"
    )

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    checkpoint_events = [
        event
        for event in events
        if (
            event.event_type
            == KernelEventType.CHECKPOINT_SAVED
        )
    ]

    assert len(
        checkpoint_events
    ) == 1

    event = checkpoint_events[0]

    assert (
        event.checkpoint
        == "test_checkpoint"
    )

    assert (
        event.step_name
        == "test_step"
    )

    assert (
        event.data["value"]
        == "hello"
    )

    print(
        "PASS: CHECKPOINT_SAVED event emitted."
    )


# ==========================================================
# TEST 4 — CANCELLATION EVENT
# ==========================================================

def test_cancellation_event():

    print()
    print("=" * 70)
    print("TEST 4 — TASK CANCELLATION EVENT")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Cancellation test."
    )

    kernel.cancel_current_task()

    assert (
        task.status
        == TaskStatus.CANCELLED
    )

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        KernelEventType.TASK_CANCELLED
        in event_types
    )

    print(
        "PASS: TASK_CANCELLED event emitted."
    )


# ==========================================================
# TEST 5 — COMPLETION EVENT
# ==========================================================

def test_completion_event():

    print()
    print("=" * 70)
    print("TEST 5 — TASK COMPLETION EVENT")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Completion test."
    )

    kernel.complete_current_task()

    assert (
        task.status
        == TaskStatus.DONE
    )

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        KernelEventType.TASK_COMPLETED
        in event_types
    )

    print(
        "PASS: TASK_COMPLETED event emitted."
    )


# ==========================================================
# TEST 6 — FAILURE EVENT
# ==========================================================

def test_failure_event():

    print()
    print("=" * 70)
    print("TEST 6 — TASK FAILURE EVENT")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Failure test."
    )

    kernel.fail_current_task()

    assert (
        task.status
        == TaskStatus.FAILED
    )

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        KernelEventType.TASK_FAILED
        in event_types
    )

    print(
        "PASS: TASK_FAILED event emitted."
    )


# ==========================================================
# TEST 7 — MULTI-STEP EVENT ORDER
# ==========================================================

async def test_multi_step_event_order():

    print()
    print("=" * 70)
    print("TEST 7 — MULTI-STEP EVENT ORDER")
    print("=" * 70)

    kernel = Kernel()

    task = kernel.start_task(
        "Plan a trip from Bengaluru to Delhi."
    )

    flight_result = await kernel.execute_tool(
        tool_name="flight_search",
        task_id=task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert flight_result.success

    kernel.save_checkpoint(
        checkpoint="flight_search_completed",
        step_name="flight_search",
        flight=flight_result.data
    )

    hotel_result = await kernel.execute_tool(
        tool_name="hotel_search",
        task_id=task.task_id,
        city="Delhi"
    )

    assert hotel_result.success

    kernel.save_checkpoint(
        checkpoint="hotel_search_completed",
        step_name="hotel_search",
        hotel=hotel_result.data
    )

    kernel.complete_current_task()

    events = (
        kernel.event_stream
        .get_task_events(task.task_id)
    )

    event_types = [
        event.event_type
        for event in events
    ]

    expected = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.CHECKPOINT_SAVED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.CHECKPOINT_SAVED,
        KernelEventType.TASK_COMPLETED,
    ]

    assert (
        event_types
        == expected
    )

    print()
    print(
        "Event sequence:"
    )

    for event in events:

        print(
            f"  → "
            f"{event.event_type.value}"
        )

    print(
        "PASS: Multi-step event order is correct."
    )


# ==========================================================
# RUN ALL TESTS
# ==========================================================

async def main():

    print()
    print("#" * 70)
    print(
        "#       SAMSUNG AI KERNEL"
    )
    print(
        "#       EVENT INTEGRATION TESTS"
    )
    print("#" * 70)

    test_task_started_event()

    await test_tool_events()

    test_checkpoint_event()

    test_cancellation_event()

    test_completion_event()

    test_failure_event()

    await test_multi_step_event_order()

    print()
    print("#" * 70)
    print(
        "#   EVENT TESTS PASSED: 7/7"
    )
    print("#" * 70)

    print()
    print(
        "ALL KERNEL EVENT TESTS PASSED"
    )


if __name__ == "__main__":

    asyncio.run(main())