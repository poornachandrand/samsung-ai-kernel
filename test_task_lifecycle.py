import asyncio

from kernel import Kernel, TaskStatus


async def main():

    print("=" * 70)
    print("TASK LIFECYCLE STATE TEST")
    print("=" * 70)

    kernel = Kernel()

    # --------------------------------------------------
    # START TASK
    # --------------------------------------------------

    task = kernel.start_task(
        "Turn on the bedroom light."
    )

    assert task is not None

    assert kernel.get_current_task() is task

    assert task.status == TaskStatus.RUNNING

    assert (
        kernel.get_task_status()
        == TaskStatus.RUNNING
    )

    print("Task created               ✓")
    print("Current task               ✓")
    print("RUNNING state              ✓")

    # --------------------------------------------------
    # INITIAL TASK DATA
    # --------------------------------------------------

    assert task.goal == (
        "Turn on the bedroom light."
    )

    assert task.task_id is not None

    assert task.results == {}

    assert task.completed_steps == []

    print("Task goal                  ✓")
    print("Task ID                    ✓")
    print("Initial results            ✓")
    print("Initial completed steps    ✓")

    # --------------------------------------------------
    # COMPLETE TASK
    # --------------------------------------------------

    kernel.complete_current_task()

    await asyncio.sleep(0.05)

    # --------------------------------------------------
    # VERIFY COMPLETED STATE
    # --------------------------------------------------

    assert task.status == TaskStatus.DONE

    assert (
        kernel.get_task_status()
        == TaskStatus.DONE
    )

    # The current Kernel implementation retains
    # the completed task as the current task.

    assert (
        kernel.get_current_task()
        is task
    )

    print("DONE state                 ✓")
    print("Completed task retained    ✓")

    # --------------------------------------------------
    # START SECOND TASK
    # --------------------------------------------------

    second_task = kernel.start_task(
        "Search for a flight from Bengaluru to Delhi."
    )

    assert second_task is not task

    assert (
        second_task.task_id
        != task.task_id
    )

    assert (
        second_task.status
        == TaskStatus.RUNNING
    )

    assert (
        kernel.get_current_task()
        is second_task
    )

    print("New task isolation         ✓")
    print("Second task RUNNING        ✓")

    # --------------------------------------------------
    # CANCEL SECOND TASK
    # --------------------------------------------------

    kernel.cancel_current_task()

    await asyncio.sleep(0.05)

    # --------------------------------------------------
    # VERIFY CANCELLED STATE
    # --------------------------------------------------

    assert (
        second_task.status
        == TaskStatus.CANCELLED
    )

    # Current Kernel retains the cancelled task
    # as the current task.

    assert (
        kernel.get_current_task()
        is second_task
    )

    assert (
        kernel.get_task_status()
        == TaskStatus.CANCELLED
    )

    print("CANCELLED state            ✓")
    print("Cancelled task retained    ✓")

    # --------------------------------------------------
    # START THIRD TASK
    # --------------------------------------------------

    third_task = kernel.start_task(
        "Find a hotel in Delhi."
    )

    assert (
        third_task.status
        == TaskStatus.RUNNING
    )

    assert (
        kernel.get_current_task()
        is third_task
    )

    print("Third task RUNNING         ✓")

    # --------------------------------------------------
    # FAIL THIRD TASK
    # --------------------------------------------------

    kernel.fail_current_task()

    await asyncio.sleep(0.05)

    # --------------------------------------------------
    # VERIFY FAILED STATE
    # --------------------------------------------------

    assert (
        third_task.status
        == TaskStatus.FAILED
    )

    assert (
        kernel.get_current_task()
        is third_task
    )

    assert (
        kernel.get_task_status()
        == TaskStatus.FAILED
    )

    print("FAILED state               ✓")
    print("Failed task retained       ✓")

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print("RUNNING → DONE             ✓")
    print("RUNNING → CANCELLED        ✓")
    print("RUNNING → FAILED           ✓")
    print("Task isolation             ✓")
    print("Current task management    ✓")
    print()
    print(
        "TASK LIFECYCLE STATE TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())