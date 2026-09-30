import asyncio

from event_dispatcher import EventDispatcher
from kernel_events import (
    EventStream,
    KernelEventType,
    create_event,
)


async def main():

    print("=" * 70)
    print("EVENT DISPATCHER FAILURE ISOLATION TEST")
    print("=" * 70)

    event_stream = EventStream()
    dispatcher = EventDispatcher(event_stream)

    dispatcher.attach()

    received_events = []

    # --------------------------------------------------
    # GOOD HANDLER
    # --------------------------------------------------

    def good_handler(event):

        received_events.append(
            event.event_type
        )

        print(
            f"[GOOD HANDLER] Received: "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # FAILING HANDLER
    # --------------------------------------------------

    def failing_handler(event):

        print(
            f"[FAILING HANDLER] Received: "
            f"{event.event_type.value}"
        )

        raise RuntimeError(
            "Intentional dispatcher handler failure."
        )

    # --------------------------------------------------
    # SECOND GOOD HANDLER
    # --------------------------------------------------

    def second_good_handler(event):

        received_events.append(
            event.event_type
        )

        print(
            f"[SECOND GOOD HANDLER] Received: "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # REGISTER HANDLERS
    # --------------------------------------------------

    dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        failing_handler
    )

    dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        good_handler
    )

    dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        second_good_handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TASK_STARTED
        )
        == 3
    )

    # --------------------------------------------------
    # CREATE EVENT
    # --------------------------------------------------

    event = create_event(
        KernelEventType.TASK_STARTED,
        task_id="failure-test-task"
    )

    # --------------------------------------------------
    # DISPATCH EVENT
    # --------------------------------------------------

    event_stream.emit(event)

    # Allow async dispatcher work to settle.
    await asyncio.sleep(0.1)

    # --------------------------------------------------
    # VERIFY FAILURE ISOLATION
    # --------------------------------------------------

    assert received_events == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_STARTED,
    ]

    # The failing handler must not prevent the
    # other handlers from receiving the event.

    assert (
        dispatcher.handler_count(
            KernelEventType.TASK_STARTED
        )
        == 3
    )

    # --------------------------------------------------
    # VERIFY DISPATCHER IS STILL FUNCTIONAL
    # --------------------------------------------------

    received_events.clear()

    second_event = create_event(
        KernelEventType.TASK_STARTED,
        task_id="failure-test-task-2"
    )

    event_stream.emit(second_event)

    await asyncio.sleep(0.1)

    assert received_events == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_STARTED,
    ]

    # --------------------------------------------------
    # CLEAN UP
    # --------------------------------------------------

    dispatcher.detach()

    assert dispatcher._attached is False

    print()
    print(
        "Failing handler was isolated successfully."
    )

    print(
        "Other handlers continued receiving events."
    )

    print(
        "Dispatcher remained functional after failure."
    )

    print()
    print(
        "EVENT DISPATCHER FAILURE ISOLATION "
        "TEST PASSED"
    )


if __name__ == "__main__":

    asyncio.run(main())