import asyncio

from kernel import Kernel
from kernel_events import KernelEventType
from tools import SmartHomeTool


# ==========================================================
# TEST: MULTIPLE EVENT SUBSCRIBERS
# ==========================================================

async def test_multiple_subscribers():

    print()
    print("=" * 70)
    print(
        "          MULTIPLE EVENT SUBSCRIBERS TEST"
    )
    print("=" * 70)

    # ------------------------------------------------------
    # CREATE KERNEL
    # ------------------------------------------------------

    kernel = Kernel()

    # ------------------------------------------------------
    # CREATE TWO INDEPENDENT SUBSCRIBERS
    # ------------------------------------------------------

    ui_events = []

    logger_events = []

    def ui_listener(event):

        ui_events.append(event)

        print(
            f"[UI] "
            f"{event.event_type.value}"
        )

    def logger_listener(event):

        logger_events.append(event)

        print(
            f"[LOGGER] "
            f"{event.event_type.value}"
        )

    # ------------------------------------------------------
    # SUBSCRIBE BOTH
    # ------------------------------------------------------

    kernel.event_stream.subscribe(
        ui_listener
    )

    kernel.event_stream.subscribe(
        logger_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 2
    )

    # ------------------------------------------------------
    # REGISTER TOOL
    # ------------------------------------------------------

    kernel.register_tool(
        SmartHomeTool()
    )

    # ------------------------------------------------------
    # START TASK
    # ------------------------------------------------------

    task = kernel.start_task(
        "Turn on bedroom light."
    )

    # ------------------------------------------------------
    # EXECUTE TOOL
    # ------------------------------------------------------

    result = await kernel.execute_tool(
        "smart_home",
        task.task_id,
        action="turn_on",
        device="bedroom_light"
    )

    assert result.success is True

    # ------------------------------------------------------
    # COMPLETE TASK
    # ------------------------------------------------------

    kernel.complete_current_task()

    # ------------------------------------------------------
    # VERIFY BOTH RECEIVED EVERYTHING
    # ------------------------------------------------------

    ui_event_types = [
        event.event_type
        for event in ui_events
    ]

    logger_event_types = [
        event.event_type
        for event in logger_events
    ]

    expected_events = [
        KernelEventType.TASK_STARTED,
        KernelEventType.TOOL_STARTED,
        KernelEventType.TOOL_COMPLETED,
        KernelEventType.TASK_COMPLETED,
    ]

    assert (
        ui_event_types
        == expected_events
    )

    assert (
        logger_event_types
        == expected_events
    )

    # ------------------------------------------------------
    # VERIFY BOTH RECEIVED THE SAME EVENT IDS
    # ------------------------------------------------------

    ui_event_ids = [
        event.event_id
        for event in ui_events
    ]

    logger_event_ids = [
        event.event_id
        for event in logger_events
    ]

    assert (
        ui_event_ids
        == logger_event_ids
    )

    # ------------------------------------------------------
    # REMOVE ONLY UI SUBSCRIBER
    # ------------------------------------------------------

    kernel.event_stream.unsubscribe(
        ui_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 1
    )

    # ------------------------------------------------------
    # EMIT ANOTHER EVENT
    # ------------------------------------------------------

    kernel.emit_event(
        KernelEventType.CHECKPOINT_SAVED,
        task_id=task.task_id,
        checkpoint="after_ui_unsubscribe"
    )

    # ------------------------------------------------------
    # UI MUST NOT RECEIVE NEW EVENT
    # ------------------------------------------------------

    assert (
        len(ui_events)
        == 4
    )

    # ------------------------------------------------------
    # LOGGER MUST STILL RECEIVE IT
    # ------------------------------------------------------

    assert (
        len(logger_events)
        == 5
    )

    assert (
        logger_events[-1].event_type
        == KernelEventType.CHECKPOINT_SAVED
    )

    # ------------------------------------------------------
    # REMOVE LOGGER
    # ------------------------------------------------------

    kernel.event_stream.unsubscribe(
        logger_listener
    )

    assert (
        kernel.event_stream.subscriber_count()
        == 0
    )

    # ------------------------------------------------------
    # VERIFY EVENT STREAM STILL STORES EVENTS
    # ------------------------------------------------------

    stored_events = (
        kernel.event_stream.get_task_events(
            task.task_id
        )
    )

    assert (
        len(stored_events)
        == 5
    )

    # ------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------

    print()
    print(
        "UI subscriber events:",
        len(ui_events)
    )

    print(
        "Logger subscriber events:",
        len(logger_events)
    )

    print(
        "Stored events:",
        len(stored_events)
    )

    print(
        "Subscribers remaining:",
        kernel.event_stream.subscriber_count()
    )

    print()
    print(
        "MULTIPLE EVENT SUBSCRIBERS TEST PASSED"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        test_multiple_subscribers()
    )