import asyncio
import json

from google import genai

from kernel import Kernel

from extensions.smart_home import SmartHomeTool
from extensions.employee_planner import EmployeePlannerTool
from extensions.kitchen_assistant import KitchenAssistantTool
from extensions.study_helper import StudyHelperTool
from extensions.food_ordering import FoodOrderingTool
from extensions.doctor_appointment import DoctorAppointmentTool


SMART_HOME_FUNCTION = {
    "type": "function",
    "name": "smart_home",
    "description": (
        "Control a smart home device. "
        "Use this function when the user wants to turn a device on, "
        "turn a device off, set the AC temperature, "
        "or get device status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "turn_on",
                    "turn_off",
                    "set_temperature",
                    "get_status"
                ],
                "description": "The action to perform."
            },
            "device": {
                "type": "string",
                "enum": [
                    "bedroom_light",
                    "living_room_light",
                    "bedroom_fan",
                    "living_room_fan",
                    "ac"
                ],
                "description": "The smart home device."
            },
            "temperature": {
                "type": "number",
                "description": "Temperature for the AC."
            }
        },
        "required": ["action", "device"]
    }
}


EMPLOYEE_PLANNER_FUNCTION = {
    "type": "function",
    "name": "employee_planner",
    "description": (
        "Manage employee schedules and tasks. "
        "Use this function to add a task, remove a task, "
        "get an employee schedule, or update a task status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "add_task",
                    "remove_task",
                    "get_schedule",
                    "update_status"
                ],
                "description": "The employee planner action."
            },
            "employee": {
                "type": "string",
                "description": "Employee name."
            },
            "date": {
                "type": "string",
                "description": (
                    "Date of the task, preferably in "
                    "YYYY-MM-DD format."
                )
            },
            "task": {
                "type": "string",
                "description": "Task description."
            },
            "status": {
                "type": "string",
                "description": (
                    "New status of the task, such as "
                    "pending or completed."
                )
            }
        },
        "required": ["action"]
    }
}


KITCHEN_ASSISTANT_FUNCTION = {
    "type": "function",
    "name": "kitchen_assistant",
    "description": (
        "Manage kitchen inventory and recipes. "
        "Use this function to add or remove ingredients, "
        "check inventory, add recipes, get recipes, "
        "or clear the inventory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "add_ingredient",
                    "remove_ingredient",
                    "check_inventory",
                    "add_recipe",
                    "get_recipe",
                    "clear_inventory"
                ],
                "description": "The kitchen assistant action."
            },
            "ingredient": {
                "type": "string",
                "description": "Ingredient name."
            },
            "quantity": {
                "type": "string",
                "description": "Ingredient quantity."
            },
            "recipe": {
                "type": "string",
                "description": "Recipe name."
            },
            "ingredients": {
                "type": "string",
                "description": (
                    "Ingredients required for the recipe, "
                    "separated by commas."
                )
            }
        },
        "required": ["action"]
    }
}


STUDY_HELPER_FUNCTION = {
    "type": "function",
    "name": "study_helper",
    "description": (
        "Manage a student's study plan. "
        "Use this function to add a study topic, "
        "remove a study topic, get study topics, "
        "mark a topic as completed, or clear a subject."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "add_topic",
                    "remove_topic",
                    "get_topics",
                    "mark_completed",
                    "clear_subject"
                ],
                "description": "The study helper action."
            },
            "subject": {
                "type": "string",
                "description": "Subject name, such as DSA."
            },
            "topic": {
                "type": "string",
                "description": "Study topic, such as Arrays."
            }
        },
        "required": ["action"]
    }
}


FOOD_ORDERING_FUNCTION = {
    "type": "function",
    "name": "food_ordering",
    "description": (
        "Manage food orders. "
        "Use this function to place a food order, "
        "cancel the latest order, get active orders, "
        "or clear all orders."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "place_order",
                    "cancel_order",
                    "get_orders",
                    "clear_orders"
                ],
                "description": "The food ordering action."
            },
            "item": {
                "type": "string",
                "description": "Food item to order."
            },
            "quantity": {
                "type": "integer",
                "description": "Number of items to order."
            }
        },
        "required": ["action"]
    }
}


DOCTOR_APPOINTMENT_FUNCTION = {
    "type": "function",
    "name": "doctor_appointment",
    "description": (
        "Manage doctor appointments. "
        "Use this function to book an appointment, "
        "cancel the latest appointment, "
        "get active appointments, "
        "or clear all appointments."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "book_appointment",
                    "cancel_appointment",
                    "get_appointments",
                    "clear_appointments"
                ],
                "description": "The doctor appointment action."
            },
            "doctor": {
                "type": "string",
                "description": "Doctor's name."
            },
            "date": {
                "type": "string",
                "description": (
                    "Appointment date, preferably in "
                    "YYYY-MM-DD format."
                )
            },
            "time": {
                "type": "string",
                "description": "Appointment time."
            }
        },
        "required": ["action"]
    }
}


ALL_FUNCTIONS = [
    SMART_HOME_FUNCTION,
    EMPLOYEE_PLANNER_FUNCTION,
    KITCHEN_ASSISTANT_FUNCTION,
    STUDY_HELPER_FUNCTION,
    FOOD_ORDERING_FUNCTION,
    DOCTOR_APPOINTMENT_FUNCTION
]


def main():

    client = genai.Client(
        http_options={"api_version": "v1"}
    )

    kernel = Kernel()

    smart_home = SmartHomeTool()
    employee_planner = EmployeePlannerTool()
    kitchen_assistant = KitchenAssistantTool()
    study_helper = StudyHelperTool()
    food_ordering = FoodOrderingTool()
    doctor_appointment = DoctorAppointmentTool()

    kernel.register_tool(smart_home)
    kernel.register_tool(employee_planner)
    kernel.register_tool(kitchen_assistant)
    kernel.register_tool(study_helper)
    kernel.register_tool(food_ordering)
    kernel.register_tool(doctor_appointment)

    task = kernel.start_task(
        "User request"
    )

    user_command = input("You: ")

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=user_command,
        tools=ALL_FUNCTIONS
    )

    print("\nGemini steps:")

    for step in interaction.steps:

        if step.type != "function_call":
            continue

        print("Function called:", step.name)
        print("Arguments:", step.arguments)

        arguments = step.arguments

        # ====================================================
        # SMART HOME
        # ====================================================

        if step.name == "smart_home":

            tool_arguments = {
                "action": arguments.get("action"),
                "device": arguments.get("device")
            }

            if "temperature" in arguments:
                tool_arguments["temperature"] = arguments["temperature"]

        # ====================================================
        # EMPLOYEE PLANNER
        # ====================================================

        elif step.name == "employee_planner":

            tool_arguments = {
                "action": arguments.get("action")
            }

            if "employee" in arguments:
                tool_arguments["employee"] = arguments["employee"]

            if "date" in arguments:
                tool_arguments["date"] = arguments["date"]

            if "task" in arguments:
                tool_arguments["task"] = arguments["task"]

            if "status" in arguments:
                tool_arguments["status"] = arguments["status"]

        # ====================================================
        # KITCHEN ASSISTANT
        # ====================================================

        elif step.name == "kitchen_assistant":

            tool_arguments = {
                "action": arguments.get("action")
            }

            if "ingredient" in arguments:
                tool_arguments["ingredient"] = arguments["ingredient"]

            if "quantity" in arguments:
                tool_arguments["quantity"] = arguments["quantity"]

            if "recipe" in arguments:
                tool_arguments["recipe"] = arguments["recipe"]

            if "ingredients" in arguments:
                tool_arguments["ingredients"] = arguments["ingredients"]

        # ====================================================
        # STUDY HELPER
        # ====================================================

        elif step.name == "study_helper":

            tool_arguments = {
                "action": arguments.get("action")
            }

            if "subject" in arguments:
                tool_arguments["subject"] = arguments["subject"]

            if "topic" in arguments:
                tool_arguments["topic"] = arguments["topic"]

        # ====================================================
        # FOOD ORDERING
        # ====================================================

        elif step.name == "food_ordering":

            tool_arguments = {
                "action": arguments.get("action")
            }

            if "item" in arguments:
                tool_arguments["item"] = arguments["item"]

            if "quantity" in arguments:
                tool_arguments["quantity"] = arguments["quantity"]

        # ====================================================
        # DOCTOR APPOINTMENT
        # ====================================================

        elif step.name == "doctor_appointment":

            tool_arguments = {
                "action": arguments.get("action")
            }

            if "doctor" in arguments:
                tool_arguments["doctor"] = arguments["doctor"]

            if "date" in arguments:
                tool_arguments["date"] = arguments["date"]

            if "time" in arguments:
                tool_arguments["time"] = arguments["time"]

        else:

            print(
                f"Unknown function returned by Gemini: "
                f"{step.name}"
            )

            continue

        # ====================================================
        # EXECUTE TOOL THROUGH KERNEL
        # ====================================================

        result = asyncio.run(
            kernel.execute_tool(
                step.name,
                task.task_id,
                **tool_arguments
            )
        )

        print("\nKernel ToolResult:")
        print(result)

        # ====================================================
        # SEND RESULT BACK TO GEMINI
        # ====================================================

        final_interaction = client.interactions.create(
            model="gemini-3.6-flash",
            previous_interaction_id=interaction.id,
            input=[
                {
                    "type": "function_result",
                    "name": step.name,
                    "call_id": step.id,
                    "result": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": result.success,
                                "data": result.data,
                                "error": result.error
                            })
                        }
                    ]
                }
            ]
        )

        print("\nFinal Gemini response:")
        print(final_interaction.output_text)

        return

    print("\nGemini response:")
    print(interaction.output_text)


if __name__ == "__main__":
    main()