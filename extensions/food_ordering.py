from tool_base import BaseTool
from tool_interface import ToolResult


class FoodOrderingTool(BaseTool):

    @property
    def name(self):
        return "food_ordering"

    def __init__(self):
        self.orders = []

    async def run(self, task_id: str, **kwargs):

        action = kwargs.get("action")

        # ====================================================
        # PLACE ORDER
        # ====================================================

        if action == "place_order":

            item = kwargs.get("item")
            quantity = kwargs.get("quantity", 1)

            if not item:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error="Food item is required.",
                    retryable=False
                )

            order = {
                "item": item,
                "quantity": quantity,
                "status": "placed"
            }

            self.orders.append(order)

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "order": order,
                    "message": (
                        f"{quantity} x {item} order placed successfully."
                    )
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # CANCEL ORDER
        # ====================================================

        elif action == "cancel_order":

            if not self.orders:
                return ToolResult(
                    task_id=task_id,
                    tool_name=self.name,
                    success=False,
                    error="No active orders to cancel.",
                    retryable=False
                )

            order = self.orders.pop()

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "cancelled_order": order,
                    "message": (
                        f"Order for {order['item']} cancelled."
                    )
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # GET ORDERS
        # ====================================================

        elif action == "get_orders":

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "orders": self.orders,
                    "message": f"{len(self.orders)} active order(s)."
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # CLEAR ORDERS
        # ====================================================

        elif action == "clear_orders":

            self.orders.clear()

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=True,
                data={
                    "orders": [],
                    "message": "All orders cleared."
                },
                error=None,
                retryable=False
            )

        # ====================================================
        # UNKNOWN ACTION
        # ====================================================

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=False,
            error=f"Unknown food ordering action: {action}",
            retryable=False
        )