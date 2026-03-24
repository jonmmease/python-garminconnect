"""MCP tools for Garmin Connect nutrition tracking."""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)


async def get_nutrition_data(
    action: Literal[
        "summary",
        "food_logs",
        "meals",
        "settings",
        "status",
        "recent_foods",
        "search",
        "custom_foods",
        "custom_meals",
    ],
    date: str | None = None,
    end_date: str | None = None,
    search_query: str | None = None,
    meal_id: int | None = None,
    start: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """Query nutrition data from Garmin Connect.

    Args:
        action: Which nutrition data to retrieve:
            - summary: Calorie/macro summary for a date range (requires date,
              optional end_date)
            - food_logs: Detailed food logs with per-meal breakdown (requires date)
            - meals: Meal definitions with time windows and goals (requires date)
            - settings: Nutrition settings and goals (requires date)
            - status: Whether nutrition tracking is enabled
            - recent_foods: Recently logged foods for a meal (requires date and
              meal_id)
            - search: Search the FatSecret food database (requires search_query)
            - custom_foods: List/search user's custom foods (My Foods).
              Optional search_query.
            - custom_meals: List/search user's custom meals (My Meals).
              Optional search_query.
        date: Date in 'YYYY-MM-DD' format. Required for summary, food_logs,
            meals, settings, recent_foods.
        end_date: End date in 'YYYY-MM-DD' format. Only used with summary
            (defaults to date).
        search_query: Search term for search, custom_foods, or custom_meals.
        meal_id: Meal ID for recent_foods (from get_nutrition_data meals action).
        start: Pagination start index.
        limit: Maximum number of results.

    Returns:
        Dict with the requested nutrition data.

    """
    from garminconnect.mcp.server import garmin_api_call, get_garmin_client

    garmin = get_garmin_client()

    if action == "summary":
        if not date:
            return {"error": "date is required for summary"}
        return await garmin_api_call(garmin.get_nutrition_summary, date, end_date)

    if action == "food_logs":
        if not date:
            return {"error": "date is required for food_logs"}
        return await garmin_api_call(garmin.get_nutrition_food_logs, date)

    if action == "meals":
        if not date:
            return {"error": "date is required for meals"}
        return await garmin_api_call(garmin.get_nutrition_meals, date)

    if action == "settings":
        if not date:
            return {"error": "date is required for settings"}
        return await garmin_api_call(garmin.get_nutrition_settings, date)

    if action == "status":
        return await garmin_api_call(garmin.get_nutrition_status)

    if action == "recent_foods":
        if not date:
            return {"error": "date is required for recent_foods"}
        if meal_id is None:
            return {"error": "meal_id is required for recent_foods"}
        return await garmin_api_call(
            garmin.get_nutrition_recent_foods,
            date,
            meal_id,
            start=start,
            limit=limit,
        )

    if action == "search":
        if not search_query:
            return {"error": "search_query is required for search"}
        return await garmin_api_call(
            garmin.search_nutrition_foods,
            search_query,
            start=start,
            limit=limit,
        )

    if action == "custom_foods":
        return await garmin_api_call(
            garmin.get_nutrition_custom_foods,
            search=search_query or "",
            start=start,
            limit=limit,
        )

    if action == "custom_meals":
        return await garmin_api_call(
            garmin.get_nutrition_custom_meals,
            search=search_query or "",
            start=start,
            limit=limit,
        )

    return {"error": f"Unknown action: {action}"}


async def manage_nutrition(
    action: Literal[
        "create_food",
        "update_food",
        "delete_food",
        "create_meal",
        "delete_meal",
        "add_log",
        "delete_logs",
        "log_meal",
    ],
    # Common fields
    date: str | None = None,
    meal_id: int | None = None,
    # Food fields
    food_id: str | None = None,
    serving_id: str | None = None,
    food_name: str | None = None,
    serving_unit: str | None = None,
    serving_size: float | None = None,
    calories: float | None = None,
    carbs: float = 0,
    protein: float = 0,
    fat: float = 0,
    fiber: float = 0,
    sugar: float = 0,
    brand_name: str | None = None,
    added_sugars: float | None = None,
    saturated_fat: float | None = None,
    monounsaturated_fat: float | None = None,
    polyunsaturated_fat: float | None = None,
    trans_fat: float | None = None,
    cholesterol: float | None = None,
    sodium: float | None = None,
    potassium: float | None = None,
    vitamin_a: float | None = None,
    vitamin_c: float | None = None,
    vitamin_d: float | None = None,
    calcium: float | None = None,
    iron: float | None = None,
    image_token: str | None = None,
    # Food log fields
    serving_qty: float | None = None,
    source: str = "FATSECRET",
    meal_time: str | None = None,
    log_ids: list[str] | None = None,
    # Meal fields
    meal_name: str | None = None,
    foods: list[dict[str, Any]] | None = None,
    custom_meal_id: int | None = None,
) -> dict[str, Any]:
    """Create, update, or delete nutrition items on Garmin Connect.

    Args:
        action: What to do:
            - create_food: Create a custom food (My Foods). Requires food_name,
              serving_unit, serving_size, calories. Optional: carbs, protein, fat,
              fiber, sugar, brand_name, image_token, and micronutrients.
            - update_food: Update a custom food. Requires food_id, serving_id,
              food_name, serving_unit, serving_size, calories. Same optional
              fields as create_food.
            - delete_food: Delete a custom food. Requires food_id.
            - create_meal: Create a custom meal (My Meals). Requires meal_name
              and foods (list of food items). Each food item dict needs:
              food_id, serving_id, serving_qty, and source. The tool will look
              up the full food data automatically.
            - delete_meal: Delete a custom meal. Requires custom_meal_id.
            - add_log: Log a food. Requires date, meal_id, food_id, serving_id,
              serving_qty. Optional: source, meal_time.
            - delete_logs: Delete food log entries. Requires date and log_ids.
            - log_meal: Log a custom meal (all its foods). Requires date,
              meal_id, custom_meal_id. Optional: meal_time.
        date: Date in 'YYYY-MM-DD' format. Required for add_log, delete_logs,
            log_meal.
        meal_id: Meal ID (from get_nutrition_data meals). Required for add_log,
            log_meal.
        food_id: Food ID. Required for update_food, delete_food, add_log.
        serving_id: Serving ID. Required for update_food, add_log.
        food_name: Food name. Required for create_food, update_food.
        serving_unit: Serving unit (oz, g, ml, cup, etc.). Required for
            create_food, update_food.
        serving_size: Number of units per serving. Required for create_food,
            update_food.
        calories: Calories per serving. Required for create_food, update_food.
        carbs: Carbohydrates in grams.
        protein: Protein in grams.
        fat: Total fat in grams.
        fiber: Fiber in grams.
        sugar: Sugar in grams.
        brand_name: Optional brand name for custom foods.
        added_sugars: Added sugars in grams.
        saturated_fat: Saturated fat in grams.
        monounsaturated_fat: Monounsaturated fat in grams.
        polyunsaturated_fat: Polyunsaturated fat in grams.
        trans_fat: Trans fat in grams.
        cholesterol: Cholesterol in mg.
        sodium: Sodium in mg.
        potassium: Potassium in mg.
        vitamin_a: Vitamin A (% daily value).
        vitamin_c: Vitamin C (% daily value).
        vitamin_d: Vitamin D (% daily value).
        calcium: Calcium (% daily value).
        iron: Iron (% daily value).
        image_token: Upload token from request_upload for food image
            (create_food, update_food only).
        serving_qty: Number of servings. Required for add_log.
        source: Food source ("FATSECRET" or "GARMIN"). Default "FATSECRET".
        meal_time: Time in 'HH:MM:SS' format. Optional for add_log, log_meal.
        log_ids: List of log IDs to delete. Required for delete_logs.
        meal_name: Name for a custom meal. Required for create_meal.
        foods: List of food items for create_meal. Each dict should have:
            food_id (str), serving_id (str), serving_qty (float),
            source (str, default "FATSECRET").
        custom_meal_id: Custom meal ID. Required for delete_meal, log_meal.

    Returns:
        Dict with the result of the operation.

    """
    from garminconnect.mcp.server import garmin_api_call, get_garmin_client

    garmin = get_garmin_client()

    if action == "create_food":
        return await _create_food(
            garmin,
            food_name=food_name,
            serving_unit=serving_unit,
            serving_size=serving_size,
            calories=calories,
            carbs=carbs,
            protein=protein,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            brand_name=brand_name,
            added_sugars=added_sugars,
            saturated_fat=saturated_fat,
            monounsaturated_fat=monounsaturated_fat,
            polyunsaturated_fat=polyunsaturated_fat,
            trans_fat=trans_fat,
            cholesterol=cholesterol,
            sodium=sodium,
            potassium=potassium,
            vitamin_a=vitamin_a,
            vitamin_c=vitamin_c,
            vitamin_d=vitamin_d,
            calcium=calcium,
            iron=iron,
            image_token=image_token,
        )

    if action == "update_food":
        return await _update_food(
            garmin,
            food_id=food_id,
            serving_id=serving_id,
            food_name=food_name,
            serving_unit=serving_unit,
            serving_size=serving_size,
            calories=calories,
            carbs=carbs,
            protein=protein,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            brand_name=brand_name,
            added_sugars=added_sugars,
            saturated_fat=saturated_fat,
            monounsaturated_fat=monounsaturated_fat,
            polyunsaturated_fat=polyunsaturated_fat,
            trans_fat=trans_fat,
            cholesterol=cholesterol,
            sodium=sodium,
            potassium=potassium,
            vitamin_a=vitamin_a,
            vitamin_c=vitamin_c,
            vitamin_d=vitamin_d,
            calcium=calcium,
            iron=iron,
            image_token=image_token,
        )

    if action == "delete_food":
        if not food_id:
            return {"error": "food_id is required for delete_food"}
        await garmin_api_call(garmin.delete_nutrition_custom_food, food_id)
        return {"status": "deleted", "food_id": food_id}

    if action == "create_meal":
        return await _create_meal(garmin, meal_name=meal_name, foods=foods)

    if action == "delete_meal":
        if custom_meal_id is None:
            return {"error": "custom_meal_id is required for delete_meal"}
        await garmin_api_call(garmin.delete_nutrition_custom_meal, custom_meal_id)
        return {"status": "deleted", "custom_meal_id": custom_meal_id}

    if action == "add_log":
        if not date:
            return {"error": "date is required for add_log"}
        if meal_id is None:
            return {"error": "meal_id is required for add_log"}
        if not food_id:
            return {"error": "food_id is required for add_log"}
        if not serving_id:
            return {"error": "serving_id is required for add_log"}
        if serving_qty is None:
            return {"error": "serving_qty is required for add_log"}
        return await garmin_api_call(
            garmin.add_nutrition_food_log,
            date,
            meal_id,
            food_id,
            serving_id,
            serving_qty,
            source=source,
            meal_time=meal_time,
        )

    if action == "delete_logs":
        if not date:
            return {"error": "date is required for delete_logs"}
        if not log_ids:
            return {"error": "log_ids is required for delete_logs"}
        await garmin_api_call(garmin.delete_nutrition_food_logs, date, log_ids)
        return {"status": "deleted", "date": date, "log_ids": log_ids}

    if action == "log_meal":
        return await _log_meal(
            garmin,
            date=date,
            meal_id=meal_id,
            custom_meal_id=custom_meal_id,
            meal_time=meal_time,
        )

    return {"error": f"Unknown action: {action}"}


async def _resolve_image_token(image_token: str) -> str:
    """Resolve an upload token to base64-encoded image data.

    Args:
        image_token: Upload token from request_upload.

    Returns:
        Base64-encoded image data string.

    """
    import base64
    from pathlib import Path

    from jons_mcp_file_server import get_file_server

    from garminconnect.mcp.server import gcs_enabled

    server = get_file_server(backend="gcs" if gcs_enabled else "localhost")
    upload_info = server.resolve_upload(image_token)
    local_path = Path(upload_info["local_path"])

    image_base64 = base64.b64encode(local_path.read_bytes()).decode("ascii")

    server.consume_upload(image_token)
    logger.debug("Resolved image token, %d bytes of base64 data", len(image_base64))
    return image_base64


async def _create_food(
    garmin: Any,
    *,
    food_name: str | None,
    serving_unit: str | None,
    serving_size: float | None,
    calories: float | None,
    carbs: float,
    protein: float,
    fat: float,
    fiber: float,
    sugar: float,
    brand_name: str | None,
    added_sugars: float | None,
    saturated_fat: float | None,
    monounsaturated_fat: float | None,
    polyunsaturated_fat: float | None,
    trans_fat: float | None,
    cholesterol: float | None,
    sodium: float | None,
    potassium: float | None,
    vitamin_a: float | None,
    vitamin_c: float | None,
    vitamin_d: float | None,
    calcium: float | None,
    iron: float | None,
    image_token: str | None,
) -> dict[str, Any]:
    """Create a custom food, optionally with an image."""
    from garminconnect.mcp.server import garmin_api_call

    if not food_name:
        return {"error": "food_name is required for create_food"}
    if not serving_unit:
        return {"error": "serving_unit is required for create_food"}
    if serving_size is None:
        return {"error": "serving_size is required for create_food"}
    if calories is None:
        return {"error": "calories is required for create_food"}

    image_base64: str | None = None
    if image_token:
        image_base64 = await _resolve_image_token(image_token)

    return await garmin_api_call(
        garmin.create_nutrition_custom_food,
        food_name,
        serving_unit,
        serving_size,
        calories,
        carbs=carbs,
        protein=protein,
        fat=fat,
        fiber=fiber,
        sugar=sugar,
        brand_name=brand_name,
        added_sugars=added_sugars,
        saturated_fat=saturated_fat,
        monounsaturated_fat=monounsaturated_fat,
        polyunsaturated_fat=polyunsaturated_fat,
        trans_fat=trans_fat,
        cholesterol=cholesterol,
        sodium=sodium,
        potassium=potassium,
        vitamin_a=vitamin_a,
        vitamin_c=vitamin_c,
        vitamin_d=vitamin_d,
        calcium=calcium,
        iron=iron,
        image_base64=image_base64,
    )


async def _update_food(
    garmin: Any,
    *,
    food_id: str | None,
    serving_id: str | None,
    food_name: str | None,
    serving_unit: str | None,
    serving_size: float | None,
    calories: float | None,
    carbs: float,
    protein: float,
    fat: float,
    fiber: float,
    sugar: float,
    brand_name: str | None,
    added_sugars: float | None,
    saturated_fat: float | None,
    monounsaturated_fat: float | None,
    polyunsaturated_fat: float | None,
    trans_fat: float | None,
    cholesterol: float | None,
    sodium: float | None,
    potassium: float | None,
    vitamin_a: float | None,
    vitamin_c: float | None,
    vitamin_d: float | None,
    calcium: float | None,
    iron: float | None,
    image_token: str | None,
) -> dict[str, Any]:
    """Update a custom food, optionally with an image."""
    from garminconnect.mcp.server import garmin_api_call

    if not food_id:
        return {"error": "food_id is required for update_food"}
    if not serving_id:
        return {"error": "serving_id is required for update_food"}
    if not food_name:
        return {"error": "food_name is required for update_food"}
    if not serving_unit:
        return {"error": "serving_unit is required for update_food"}
    if serving_size is None:
        return {"error": "serving_size is required for update_food"}
    if calories is None:
        return {"error": "calories is required for update_food"}

    image_base64: str | None = None
    if image_token:
        image_base64 = await _resolve_image_token(image_token)

    return await garmin_api_call(
        garmin.update_nutrition_custom_food,
        food_id,
        serving_id,
        food_name,
        serving_unit,
        serving_size,
        calories,
        carbs=carbs,
        protein=protein,
        fat=fat,
        fiber=fiber,
        sugar=sugar,
        brand_name=brand_name,
        added_sugars=added_sugars,
        saturated_fat=saturated_fat,
        monounsaturated_fat=monounsaturated_fat,
        polyunsaturated_fat=polyunsaturated_fat,
        trans_fat=trans_fat,
        cholesterol=cholesterol,
        sodium=sodium,
        potassium=potassium,
        vitamin_a=vitamin_a,
        vitamin_c=vitamin_c,
        vitamin_d=vitamin_d,
        calcium=calcium,
        iron=iron,
        image_base64=image_base64,
    )


async def _create_meal(
    garmin: Any,
    *,
    meal_name: str | None,
    foods: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Create a custom meal by looking up food data from simplified input.

    The foods list accepts dicts with: food_id, serving_id, serving_qty, source.
    The tool fetches the full food data needed by the API.
    """
    from garminconnect.mcp.server import garmin_api_call

    if not meal_name:
        return {"error": "meal_name is required for create_meal"}
    if not foods:
        return {"error": "foods list is required for create_meal"}

    # Look up full food data for each item
    food_tuples: list[tuple[dict[str, Any], str, float]] = []

    for item in foods:
        item_food_id = item.get("food_id")
        item_serving_id = item.get("serving_id")
        item_serving_qty = item.get("serving_qty", 1.0)
        item_source = item.get("source", "FATSECRET")

        if not item_food_id:
            return {"error": "Each food item requires a food_id"}
        if not item_serving_id:
            return {"error": "Each food item requires a serving_id"}

        # Search for the food to get the full food dict
        if item_source == "GARMIN":
            # Custom food - search custom foods
            results = await garmin_api_call(
                garmin.get_nutrition_custom_foods, search=""
            )
            food_dict = None
            for cf in results.get("customFoods", []):
                if cf.get("foodMetaData", {}).get("foodId") == item_food_id:
                    food_dict = cf
                    break
        else:
            # FatSecret food - search by food ID isn't directly possible,
            # so we construct a minimal food dict that the API accepts
            food_dict = None
            # Try searching recent/custom first, fall back to constructing
            results = await garmin_api_call(garmin.search_nutrition_foods, item_food_id)
            for r in results.get("results", []):
                if r.get("foodMetaData", {}).get("foodId") == item_food_id:
                    food_dict = r
                    break

        if food_dict is None:
            return {
                "error": f"Could not find food with ID '{item_food_id}'. "
                "Provide the full food dict from a previous search or "
                "custom_foods query."
            }

        food_tuples.append((food_dict, item_serving_id, float(item_serving_qty)))

    return await garmin_api_call(
        garmin.create_nutrition_custom_meal,
        meal_name,
        food_tuples,
    )


async def _log_meal(
    garmin: Any,
    *,
    date: str | None,
    meal_id: int | None,
    custom_meal_id: int | None,
    meal_time: str | None,
) -> dict[str, Any]:
    """Log a custom meal (all its foods) to the food log."""
    from garminconnect.mcp.server import garmin_api_call

    if not date:
        return {"error": "date is required for log_meal"}
    if meal_id is None:
        return {"error": "meal_id is required for log_meal"}
    if custom_meal_id is None:
        return {"error": "custom_meal_id is required for log_meal"}

    # Fetch the custom meal data
    meals_data = await garmin_api_call(garmin.get_nutrition_custom_meals)
    custom_meal = None
    for meal in meals_data.get("customMeals", []):
        if meal.get("customMealId") == custom_meal_id:
            custom_meal = meal
            break

    if custom_meal is None:
        return {"error": f"Custom meal with ID {custom_meal_id} not found"}

    return await garmin_api_call(
        garmin.add_nutrition_custom_meal_log,
        date,
        meal_id,
        custom_meal,
        meal_time=meal_time,
    )
