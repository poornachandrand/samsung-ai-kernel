from event_dispatcher import EventDispatcher
from kernel_events import (
    EventStream,
    KernelEventType,
    create_event,
)


def main():

    print("=" * 70)
    print("EVENT DISPATCHER LIFECYCLE TEST")
    print("=" * 70)

    event_stream = EventStream()
    dispatcher = EventDispatcher(event_stream)

    received_events = []

    def handler(event):
        received_events.append(event.event_type)

        print(
            f"[HANDLER] Received: "
            f"{event.event_type.value}"
        )

    # --------------------------------------------------
    # INITIAL STATE
    # --------------------------------------------------

    assert dispatcher._attached is False
    assert dispatcher.handler_count() == 0

    # --------------------------------------------------
    # ATTACH
    # --------------------------------------------------

    dispatcher.attach()

    assert dispatcher._attached is True

    # Calling attach again must not create
    # duplicate EventStream subscriptions.

    dispatcher.attach()

    assert dispatcher._attached is True
    assert event_stream.subscriber_count() == 1

    # --------------------------------------------------
    # SUBSCRIBE
    # --------------------------------------------------

    dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TASK_STARTED
        )
        == 1
    )

    # --------------------------------------------------
    # EMIT EVENT
    # --------------------------------------------------

    event = create_event(
        KernelEventType.TASK_STARTED,
        task_id="lifecycle-task"
    )

    event_stream.emit(event)

    assert received_events == [
        KernelEventType.TASK_STARTED
    ]

    # --------------------------------------------------
    # UNSUBSCRIBE
    # --------------------------------------------------

    dispatcher.unsubscribe(
        KernelEventType.TASK_STARTED,
        handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TASK_STARTED
        )
        == 0
    )

    # Emit again. Handler must NOT receive it.

    event_stream.emit(
        create_event(
            KernelEventType.TASK_STARTED,
            task_id="lifecycle-task-2"
        )
    )

    assert received_events == [
        KernelEventType.TASK_STARTED
    ]

    # --------------------------------------------------
    # RESUBSCRIBE
    # --------------------------------------------------

    dispatcher.subscribe(
        KernelEventType.TASK_STARTED,
        handler
    )

    assert (
        dispatcher.handler_count(
            KernelEventType.TASK_STARTED
        )
        == 1
    )

    event_stream.emit(
        create_event(
            KernelEventType.TASK_STARTED,
            task_id="lifecycle-task-3"
        )
    )

    assert received_events == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_STARTED,
    ]

    # --------------------------------------------------
    # DETACH
    # --------------------------------------------------

    dispatcher.detach()

    assert dispatcher._attached is False
    assert event_stream.subscriber_count() == 0

    # Event must no longer reach dispatcher.

    event_stream.emit(
        create_event(
            KernelEventType.TASK_STARTED,
            task_id="lifecycle-task-4"
        )
    )

    assert received_events == [
        KernelEventType.TASK_STARTED,
        KernelEventType.TASK_STARTED,
    ]

    # --------------------------------------------------
    # DOUBLE DETACH
    # --------------------------------------------------

    dispatcher.detach()

    assert dispatcher._attached is False
    assert event_stream.subscriber_count() == 0

    print()
    print("Attach is idempotent.")
    print("Unsubscribe removes handlers correctly.")
    print("Detach removes the EventStream subscription.")
    print("Double detach is safe.")
    print()
    print(
        "EVENT DISPATCHER LIFECYCLE TEST PASSED"
    )


if __name__ == "__main__":
    main()