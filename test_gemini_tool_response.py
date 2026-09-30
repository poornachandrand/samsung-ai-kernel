from gemini_kernel import GeminiKernelBridge
from tool_interface import ToolResult


def main():

    print("=" * 70)
    print("GEMINI TOOL-RESPONSE CONTRACT TEST")
    print("=" * 70)

    bridge = GeminiKernelBridge()

    # ------------------------------------------------------------
    # SUCCESSFUL TOOL RESULT
    # ------------------------------------------------------------

    success_result = ToolResult(
        task_id="task-001",
        tool_name="flight_search",
        success=True,
        data={
            "origin": "Bengaluru",
            "destination": "Delhi",
            "flight": "SJ101"
        }
    )

    response = bridge.build_function_response(
        "flight_search",
        success_result
    )

    assert response is not None
    assert response.role == "user"
    assert len(response.parts) == 1

    print("Successful ToolResult converted     ✓")
    print("Correct Gemini content role         ✓")
    print("Function response part created      ✓")

    # ------------------------------------------------------------
    # VERIFY FUNCTION RESPONSE CONTENT
    # ------------------------------------------------------------

    part = response.parts[0]

    assert part.function_response is not None
    assert part.function_response.name == "flight_search"

    print("Tool name propagated                ✓")

    function_response = part.function_response.response

    assert function_response["success"] is True
    assert function_response["data"]["flight"] == "SJ101"
    assert function_response["error"] is None

    print("Success status propagated            ✓")
    print("Tool data propagated                 ✓")
    print("Error field correctly empty         ✓")

    # ------------------------------------------------------------
    # FAILED TOOL RESULT
    # ------------------------------------------------------------

    failed_result = ToolResult(
        task_id="task-002",
        tool_name="hotel_search",
        success=False,
        data=None,
        error="The 'city' argument is required.",
        retryable=False
    )

    failed_response = bridge.build_function_response(
        "hotel_search",
        failed_result
    )

    assert failed_response is not None
    assert failed_response.role == "user"
    assert len(failed_response.parts) == 1

    failed_part = failed_response.parts[0]

    assert failed_part.function_response is not None
    assert failed_part.function_response.name == "hotel_search"

    failed_function_response = (
        failed_part.function_response.response
    )

    assert failed_function_response["success"] is False
    assert failed_function_response["data"] is None
    assert (
        failed_function_response["error"]
        == "The 'city' argument is required."
    )

    print("Failed ToolResult converted          ✓")
    print("Failure status propagated             ✓")
    print("Failure error propagated              ✓")
    print("Failure data remains None             ✓")

    print()
    print("GEMINI TOOL-RESPONSE CONTRACT TEST PASSED")


if __name__ == "__main__":
    main()