import asyncio

from kernel import Kernel
from tool_interface import ToolResult


async def main():

    print("=" * 70)
    print("MULTIPLE TOOLRESULT HANDLING TEST")
    print("=" * 70)

    kernel = Kernel()

    # --------------------------------------------------
    # START TASK
    # --------------------------------------------------

    task = kernel.start_task(
        "Find a flight and hotel for Delhi."
    )

    # --------------------------------------------------
    # MULTIPLE TOOL REQUESTS
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
                "city": "Delhi",
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
    # FLIGHT RESULT
    # --------------------------------------------------

    flight_result = results["flight_search"]

    assert isinstance(
        flight_result,
        ToolResult
    )

    assert flight_result.task_id == task.task_id

    assert flight_result.tool_name == "flight_search"

    assert flight_result.success is True

    assert flight_result.error is None

    assert flight_result.retryable is False

    assert (
        flight_result.data["origin"]
        == "Bengaluru"
    )

    assert (
        flight_result.data["destination"]
        == "Delhi"
    )

    assert len(
        flight_result.data["flights"]
    ) == 2

    print("Flight ToolResult            ✓")

    # --------------------------------------------------
    # HOTEL RESULT
    # --------------------------------------------------

    hotel_result = results["hotel_search"]

    assert isinstance(
        hotel_result,
        ToolResult
    )

    assert hotel_result.task_id == task.task_id

    assert hotel_result.tool_name == "hotel_search"

    assert hotel_result.success is True

    assert hotel_result.error is None

    assert hotel_result.retryable is False

    assert (
        hotel_result.data["city"]
        == "Delhi"
    )

    assert len(
        hotel_result.data["hotels"]
    ) == 2

    print("Hotel ToolResult             ✓")

    # --------------------------------------------------
    # TASK ASSOCIATION
    # --------------------------------------------------

    assert (
        flight_result.task_id
        == hotel_result.task_id
        == task.task_id
    )

    print("Shared task association      ✓")

    # --------------------------------------------------
    # TOOL IDENTITY
    # --------------------------------------------------

    assert (
        flight_result.tool_name
        != hotel_result.tool_name
    )

    print("Tool identity isolation      ✓")

    # --------------------------------------------------
    # NO CROSS-CONTAMINATION
    # --------------------------------------------------

    assert (
        "flights"
        in flight_result.data
    )

    assert (
        "hotels"
        not in flight_result.data
    )

    assert (
        "hotels"
        in hotel_result.data
    )

    assert (
        "flights"
        not in hotel_result.data
    )

    print("Result data isolation        ✓")

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print()
    print("Result dictionary             ✓")
    print("Flight result                 ✓")
    print("Hotel result                  ✓")
    print("Task ID propagation           ✓")
    print("Tool identity                 ✓")
    print("Data isolation                ✓")

    print()
    print(
        "MULTIPLE TOOLRESULT HANDLING "
        "TEST PASSED"
    )


if __name__ == "__main__":
    asyncio.run(main())