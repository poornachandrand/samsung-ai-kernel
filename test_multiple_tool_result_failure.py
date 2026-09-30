import asyncio

from kernel import Kernel
from tool_interface import ToolResult


async def main():

    print("=" * 70)
    print("MULTIPLE TOOLRESULT FAILURE TEST")
    print("=" * 70)

    kernel = Kernel()

    # --------------------------------------------------
    # START TASK
    # --------------------------------------------------

    task = kernel.start_task(
        "Search for a flight and hotel."
    )

    # --------------------------------------------------
    # ONE VALID + ONE INVALID TOOL REQUEST
    # --------------------------------------------------

    tool_requests = [
        {
            "tool_name": "flight_search",
            "arguments": {
                "origin": "Bengaluru",
                "destination": "Delhi",
            },
        },
        {
            "tool_name": "hotel_search",
            "arguments": {
                # Intentionally missing "city".
            },
        },
    ]

    results = await kernel.execute_multiple_tools(
        task.task_id,
        tool_requests,
    )

    # --------------------------------------------------
    # VERIFY RESULT COLLECTION
    # --------------------------------------------------

    assert isinstance(results, dict)

    assert set(results.keys()) == {
        "flight_search",
        "hotel_search",
    }

    # --------------------------------------------------
    # SUCCESSFUL RESULT
    # --------------------------------------------------

    flight_result = results["flight_search"]

    assert isinstance(
        flight_result,
        ToolResult
    )

    assert flight_result.task_id == task.task_id

    assert (
        flight_result.tool_name
        == "flight_search"
    )

    assert flight_result.success is True

    assert flight_result.error is None

    assert flight_result.retryable is False

    assert flight_result.data is not None

    assert (
        flight_result.data["origin"]
        == "Bengaluru"
    )

    assert (
        flight_result.data["destination"]
        == "Delhi"
    )

    print("Successful ToolResult        ✓")

    # --------------------------------------------------
    # FAILED RESULT
    # --------------------------------------------------

    hotel_result = results["hotel_search"]

    assert isinstance(
        hotel_result,
        ToolResult
    )

    assert hotel_result.task_id == task.task_id

    assert (
        hotel_result.tool_name
        == "hotel_search"
    )

    assert hotel_result.success is False

    assert hotel_result.data is None

    assert hotel_result.error is not None

    assert hotel_result.retryable is False

    print("Failed ToolResult             ✓")

    # --------------------------------------------------
    # VERIFY ISOLATION
    # --------------------------------------------------

    assert (
        flight_result.success is True
        and hotel_result.success is False
    )

    assert flight_result.data is not None

    assert hotel_result.data is None

    print("Success/failure isolation     ✓")

    # --------------------------------------------------
    # VERIFY SAME TASK
    # --------------------------------------------------

    assert (
        flight_result.task_id
        == hotel_result.task_id
        == task.task_id
    )

    print("Shared task association       ✓")

    # --------------------------------------------------
    # VERIFY TOOL IDENTITY
    # --------------------------------------------------

    assert (
        flight_result.tool_name
        != hotel_result.tool_name
    )

    print("Tool identity isolation       ✓")

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print("Result dictionary              ✓")
    print("Successful result              ✓")
    print("Failed result                  ✓")
    print("Failure isolation              ✓")
    print("Task ID propagation             ✓")
    print("Tool identity                  ✓")

    print()
    print(
        "MULTIPLE TOOLRESULT FAILURE "
        "TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())