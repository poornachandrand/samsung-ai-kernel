import asyncio

from kernel import Kernel
from kernel_events import KernelEventType
from tools import FlightSearchTool, HotelSearchTool


# ==========================================================
# TEST: MULTI-STEP EVENT SUBSCRIBERS
# ==========================================================

async def test_multistep_event_subscribers():

    print()
    print("=" * 70)
    print(
        "       MULTI-STEP EVENT SUBSCRIBERS TEST"
    )
    print("=" * 70)

    # ------------------------------------------------------
    # CREATE KERNEL
    # ------------------------------------------------------

    kernel = Kernel()

    sync_events = []

    async_events = []

    # ------------------------------------------------------
    # SYNCHRONOUS SUBSCRIBER
    # ------------------------------------------------------

    def sync_listener(event):

        sync_events.append(event)

        print(
            f"[SYNC] "
            f"{event.event_type.value}"
        )

    # ------------------------------------------------------
    # ASYNCHRONOUS SUBSCRIBER
    # ------------------------------------------------------

    async def async_listener(event):

        await asyncio.sleep(0.01)

        async_events.append(event)

        print(
            f"[ASYNC] "
            f"{event.event_type.value}"
        )

    # ------------------------------------------------------
    # SUBSCRIBE BOTH
    # ------------------------------------------------------

    kernel.event_stream.subscribe(
        sync_listener
    )

    kernel.event_stream.subscribe(
        async_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 2
    )

    # ------------------------------------------------------
    # REGISTER TOOLS
    # ------------------------------------------------------

    kernel.register_tool(
        FlightSearchTool()
    )

    kernel.register_tool(
        HotelSearchTool()
    )

    # ------------------------------------------------------
    # START TASK
    # ------------------------------------------------------

    task = kernel.start_task(
        "Plan a Bengaluru to Delhi trip."
    )

    # ------------------------------------------------------
    # STEP 1 — FLIGHT
    # ------------------------------------------------------

    flight_result = await kernel.execute_tool(
        "flight_search",
        task.task_id,
        origin="Bengaluru",
        destination="Delhi"
    )

    assert flight_result.success is True

    # ------------------------------------------------------
    # SAVE CHECKPOINT 1
    # ------------------------------------------------------

    kernel.save_checkpoint(
        "flight_search",
        "flight_search_completed"
    )

    # ------------------------------------------------------
    # STEP 2 — HOTEL
    # ------------------------------------------------------

    hotel_result = await kernel.execute_tool(
        "hotel_search",
        task.task_id,
        city="Delhi"
    )

    assert hotel_result.success is True

    # ------------------------------------------------------
    # SAVE CHECKPOINT 2
    # ------------------------------------------------------

    kernel.save_checkpoint(
        "hotel_search",
        "hotel_search_completed"
    )

    # ------------------------------------------------------
    # COMPLETE TASK
    # ------------------------------------------------------

    kernel.complete_current_task()

    # ------------------------------------------------------
    # WAIT FOR ASYNC SUBSCRIBER
    # ------------------------------------------------------

    await asyncio.sleep(
        0.2
    )

    # ------------------------------------------------------
    # EXPECTED EVENT SEQUENCE
    # ------------------------------------------------------

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.CHECKPOINT_SAVED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.CHECKPOINT_SAVED,
        KernelEventType.TASK_COMPLETED,
    ]

    # ------------------------------------------------------
    # EXTRACT EVENT TYPES
    # ------------------------------------------------------

    sync_event_types = [
        event.event_type
        for event in sync_events
    ]

    async_event_types = [
        event.event_type
        for event in async_events
    ]

    # ------------------------------------------------------
    # PRINT EVENTS
    # ------------------------------------------------------

    print()
    print(
        "Synchronous subscriber events:"
    )

    for event_type in sync_event_types:

        print(
            f"- {event_type.value}"
        )

    print()
    print(
        "Asynchronous subscriber events:"
    )

    for event_type in async_event_types:

        print(
            f"- {event_type.value}"
        )

    # ------------------------------------------------------
    # VERIFY SYNC EVENTS
    # ------------------------------------------------------

    assert (
        sync_event_types
        == expected_events
    )

    # ------------------------------------------------------
    # VERIFY ASYNC EVENTS
    # ------------------------------------------------------

    assert (
        async_event_types
        == expected_events
    )

    # ------------------------------------------------------
    # VERIFY EVENT IDS MATCH
    # ------------------------------------------------------

    sync_event_ids = [
        event.event_id
        for event in sync_events
    ]

    async_event_ids = [
        event.event_id
        for event in async_events
    ]

    assert (
        sync_event_ids
        == async_event_ids
    )

    # ------------------------------------------------------
    # VERIFY TASK EVENT HISTORY
    # ------------------------------------------------------

    stored_events = (
        kernel.event_stream.get_task_events(
            task.task_id
        )
    )

    assert (
        len(stored_events)
        == 8
    )

    stored_event_types = [
        event.event_type
        for event in stored_events
    ]

    assert (
        stored_event_types
        == expected_events
    )

    # ------------------------------------------------------
    # VERIFY CHECKPOINTS
    # ------------------------------------------------------

    checkpoint_events = [
        event
        for event in stored_events
        if event.event_type
        == KernelEventType.CHECKPOINT_SAVED
    ]

    assert (
        len(checkpoint_events)
        == 2
    )

    # The Kernel stores the checkpoint name
    # in the "checkpoint" field and the step
    # name in the "step_name" field.

    assert (
        checkpoint_events[0].checkpoint
        == "flight_search"
    )

    assert (
        checkpoint_events[0].step_name
        == "flight_search_completed"
    )

    assert (
        checkpoint_events[1].checkpoint
        == "hotel_search"
    )

    assert (
        checkpoint_events[1].step_name
        == "hotel_search_completed"
    )

    # ------------------------------------------------------
    # UNSUBSCRIBE
    # ------------------------------------------------------

    kernel.event_stream.unsubscribe(
        sync_listener
    )

    kernel.event_stream.unsubscribe(
        async_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 0
    )

    # ------------------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------------------

    print()
    print(
        "Sync events:",
        len(sync_events)
    )

    print(
        "Async events:",
        len(async_events)
    )

    print(
        "Stored events:",
        len(stored_events)
    )

    print(
        "Checkpoint events:",
        len(checkpoint_events)
    )

    print(
        "Subscribers remaining:",
        kernel.event_stream.subscriber_count()
    )

    print()
    print(
        "MULTI-STEP EVENT SUBSCRIBERS TEST PASSED"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        test_multistep_event_subscribers()
    )