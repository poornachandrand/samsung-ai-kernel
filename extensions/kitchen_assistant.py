from typing import Any

from tool_base import BaseTool
from tool_interface import ToolResult


class KitchenAssistantTool(BaseTool):

    def __init__(self):
        self.inventory = {}
        self.recipes = {}

    @property
    def name(self) -> str:
        return "kitchen_assistant"

    async def run(
        self,
        task_id: str,
        **kwargs: Any
    ) -> ToolResult:

        action = kwargs.get("action")

        try:

            if action == "add_ingredient":
                return self._add_ingredient(
                    task_id,
                    kwargs.get("ingredient"),
                    kwargs.get("quantity")
                )

            if action == "remove_ingredient":
                return self._remove_ingredient(
                    task_id,
                    kwargs.get("ingredient")
                )

            if action == "check_inventory":
                return self._check_inventory(task_id)

            if action == "add_recipe":
                return self._add_recipe(
                    task_id,
                    kwargs.get("recipe"),
                    kwargs.get("ingredients")
                )

            if action == "get_recipe":
                return self._get_recipe(
                    task_id,
                    kwargs.get("recipe")
                )

            if action == "clear_inventory":
                return self._clear_inventory(task_id)

            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=f"Unknown action: {action}",
                retryable=False,
            )

        except Exception as exc:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=str(exc),
                retryable=False,
            )

    def _add_ingredient(
        self,
        task_id: str,
        ingredient: str,
        quantity: Any
    ) -> ToolResult:

        if not ingredient or quantity is None:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Ingredient and quantity are required.",
                retryable=False,
            )

        ingredient = ingredient.strip().lower()

        self.inventory[ingredient] = quantity

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "ingredient": ingredient,
                "quantity": quantity,
                "message": (
                    f"{quantity} of {ingredient} "
                    f"added to inventory."
                ),
            },
        )

    def _remove_ingredient(
        self,
        task_id: str,
        ingredient: str
    ) -> ToolResult:

        if not ingredient:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Ingredient is required.",
                retryable=False,
            )

        ingredient = ingredient.strip().lower()

        if ingredient not in self.inventory:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=(
                    f"{ingredient} is not in the inventory."
                ),
                retryable=False,
            )

        quantity = self.inventory.pop(ingredient)

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "ingredient": ingredient,
                "quantity": quantity,
                "message": (
                    f"{ingredient} removed from inventory."
                ),
            },
        )

    def _check_inventory(
        self,
        task_id: str
    ) -> ToolResult:

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "inventory": self.inventory.copy()
            },
        )

    def _add_recipe(
        self,
        task_id: str,
        recipe: str,
        ingredients: Any
    ) -> ToolResult:

        if not recipe or not ingredients:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Recipe and ingredients are required.",
                retryable=False,
            )

        recipe = recipe.strip().lower()

        if isinstance(ingredients, str):
            ingredients = [
                item.strip()
                for item in ingredients.split(",")
                if item.strip()
            ]

        self.recipes[recipe] = ingredients

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "recipe": recipe,
                "ingredients": ingredients,
                "message": (
                    f"Recipe '{recipe}' added."
                ),
            },
        )

    def _get_recipe(
        self,
        task_id: str,
        recipe: str
    ) -> ToolResult:

        if not recipe:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error="Recipe name is required.",
                retryable=False,
            )

        recipe = recipe.strip().lower()

        if recipe not in self.recipes:
            return ToolResult(
                task_id=task_id,
                tool_name=self.name,
                success=False,
                error=(
                    f"Recipe '{recipe}' not found."
                ),
                retryable=False,
            )

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "recipe": recipe,
                "ingredients": self.recipes[recipe]
            },
        )

    def _clear_inventory(
        self,
        task_id: str
    ) -> ToolResult:

        self.inventory.clear()

        return ToolResult(
            task_id=task_id,
            tool_name=self.name,
            success=True,
            data={
                "inventory": {},
                "message": "Kitchen inventory cleared."
            },
        )


if __name__ == "__main__":
    import asyncio

    async def main():

        tool = KitchenAssistantTool()

        task_id = "demo-task"

        # Add ingredients
        result = await tool.run(
            task_id,
            action="add_ingredient",
            ingredient="Tomatoes",
            quantity="5"
        )
        print(result)

        result = await tool.run(
            task_id,
            action="add_ingredient",
            ingredient="Rice",
            quantity="2 kg"
        )
        print(result)

        # Check inventory
        result = await tool.run(
            task_id,
            action="check_inventory"
        )
        print(result)

        # Add recipe
        result = await tool.run(
            task_id,
            action="add_recipe",
            recipe="Tomato Rice",
            ingredients=(
                "rice, tomatoes, onion, spices"
            )
        )
        print(result)

        # Get recipe
        result = await tool.run(
            task_id,
            action="get_recipe",
            recipe="Tomato Rice"
        )
        print(result)

        # Remove ingredient
        result = await tool.run(
            task_id,
            action="remove_ingredient",
            ingredient="Rice"
        )
        print(result)

        # Clear inventory
        result = await tool.run(
            task_id,
            action="clear_inventory"
        )
        print(result)

    asyncio.run(main())