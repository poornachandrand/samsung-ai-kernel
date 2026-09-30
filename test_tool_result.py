import asyncio

from kernel import Kernel
from tool_interface import ToolResult


async def main():

    print("=" * 70)
    print("TOOLRESULT HANDLING TEST")
    print("=" * 70)

    kernel = Kernel()

    # --------------------------------------------------
    # SUCCESSFUL TOOL RESULT
    # --------------------------------------------------

    task = kernel.start_task(
        "Turn on the bedroom light."
    )

    result = await kernel.execute_tool(
        "smart_home",
        task.task_id,
        action="turn_on",
        device="bedroom_light",
    )

    assert isinstance(result, ToolResult)

    assert result.task_id == task.task_id

    assert result.tool_name == "smart_home"

    assert result.success is True

    assert result.error is None

    assert result.retryable is False

    assert result.data == {
        "device": "bedroom_light",
        "state": "on",
    }

    print("Successful ToolResult      ✓")

    # --------------------------------------------------
    # PERMANENT FAILURE RESULT
    # --------------------------------------------------

    failed_task = kernel.start_task(
        "Turn on the bedroom light."
    )

    failed_result = await kernel.execute_tool(
        "smart_home",
        failed_task.task_id,
        action="turn_on",
    )

    assert isinstance(
        failed_result,
        ToolResult
    )

    assert (
        failed_result.task_id
        == failed_task.task_id
    )

    assert (
        failed_result.tool_name
        == "smart_home"
    )

    assert failed_result.success is False

    assert failed_result.data is None

    assert failed_result.error is not None

    assert failed_result.retryable is False

    print("Permanent failure ToolResult ✓")

    # --------------------------------------------------
    # RETRY / RECOVERY RESULT
    # --------------------------------------------------

    retry_task = kernel.start_task(
        "Find a flight from Bengaluru to Delhi."
    )

    retry_result = await kernel.execute_tool(
        "flaky_flight_search",
        retry_task.task_id,
        origin="Bengaluru",
        destination="Delhi",
    )

    # The Kernel automatically retries the tool.
    # The first two attempts fail with retryable=True.
    # The third attempt succeeds.
    #
    # Therefore execute_tool() returns the final
    # successful ToolResult.

    assert isinstance(
        retry_result,
        ToolResult
    )

    assert retry_result.task_id == retry_task.task_id

    assert (
        retry_result.tool_name
        == "flaky_flight_search"
    )

    assert retry_result.success is True

    assert retry_result.error is None

    assert retry_result.retryable is False

    assert retry_result.data is not None

    assert (
        retry_result.data["attempt"]
        == 3
    )

    print("Retry/recovery ToolResult    ✓")

    # --------------------------------------------------
    # VERIFY FINAL DATA
    # --------------------------------------------------

    assert (
        retry_result.data["origin"]
        == "Bengaluru"
    )

    assert (
        retry_result.data["destination"]
        == "Delhi"
    )

    assert (
        retry_result.data["status"]
        == "available"
    )

    print("Recovered result data        ✓")

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print("Task ID propagation          ✓")
    print("Tool name propagation       ✓")
    print("Success contract             ✓")
    print("Permanent failure contract   ✓")
    print("Automatic retry recovery     ✓")
    print("Final data propagation       ✓")

    print()
    print(
        "TOOLRESULT HANDLING TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())