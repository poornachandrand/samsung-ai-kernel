import asyncio

from kernel import Kernel
from kernel_events import KernelEventType
from tools import SmartHomeTool


# ==========================================================
# TEST: SUBSCRIBER FAILURE ISOLATION
# ==========================================================

async def test_subscriber_failure_isolation():

    print()
    print("=" * 70)
    print(
        "          SUBSCRIBER FAILURE ISOLATION TEST"
    )
    print("=" * 70)

    # ------------------------------------------------------
    # CREATE KERNEL
    # ------------------------------------------------------

    kernel = Kernel()

    healthy_events = []

    failing_events = []

    # ------------------------------------------------------
    # HEALTHY SUBSCRIBER
    # ------------------------------------------------------

    def healthy_listener(event):

        healthy_events.append(event)

        print(
            f"[HEALTHY] "
            f"{event.event_type.value}"
        )

    # ------------------------------------------------------
    # FAILING SUBSCRIBER
    # ------------------------------------------------------

    def failing_listener(event):

        failing_events.append(event)

        print(
            f"[FAILING] "
            f"{event.event_type.value}"
        )

        raise RuntimeError(
            "Simulated subscriber failure."
        )

    # ------------------------------------------------------
    # SUBSCRIBE BOTH
    # ------------------------------------------------------

    kernel.event_stream.subscribe(
        healthy_listener
    )

    kernel.event_stream.subscribe(
        failing_listener
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

    # ------------------------------------------------------
    # THE TEST EXPECTS THE KERNEL TO SURVIVE
    # ------------------------------------------------------

    assert result.success is True

    # ------------------------------------------------------
    # COMPLETE TASK
    # ------------------------------------------------------

    kernel.complete_current_task()

    # ------------------------------------------------------
    # VERIFY HEALTHY SUBSCRIBER
    # ------------------------------------------------------

    healthy_event_types = [
        event.event_type
        for event in healthy_events
    ]

    assert (
        KernelEventType.TASK_STARTED
        in healthy_event_types
    )

    assert (
        KernelEventType.TOOL_STARTED
        in healthy_event_types
    )

    assert (
        KernelEventType.TOOL_COMPLETED
        in healthy_event_types
    )

    assert (
        KernelEventType.TASK_COMPLETED
        in healthy_event_types
    )

    # ------------------------------------------------------
    # VERIFY FAILING SUBSCRIBER WAS CALLED
    # ------------------------------------------------------

    assert len(
        failing_events
    ) >= 1

    # ------------------------------------------------------
    # VERIFY EVENT STORAGE
    # ------------------------------------------------------

    stored_events = (
        kernel.event_stream.get_task_events(
            task.task_id
        )
    )

    assert len(
        stored_events
    ) == 4

    # ------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------

    print()
    print(
        "Healthy subscriber events:",
        len(healthy_events)
    )

    print(
        "Failing subscriber events:",
        len(failing_events)
    )

    print(
        "Stored events:",
        len(stored_events)
    )

    print()
    print(
        "SUBSCRIBER FAILURE ISOLATION TEST PASSED"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    asyncio.run(
        test_subscriber_failure_isolation()
    )
