"""Nutrition commands for garminconnect CLI."""

import json

import click

from garminconnect.cli.formatters import format_output
from garminconnect.cli.utils import handle_api_error, parse_date, require_auth


@click.group()
def nutrition() -> None:
    """Nutrition tracking commands."""


@nutrition.command()
@click.argument("date_input", default="today")
@click.option(
    "--period",
    type=click.Choice(["day", "week", "month"]),
    default="day",
    help="Period for summary (day/week/month)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def summary(ctx: click.Context, date_input: str, period: str, as_json: bool) -> None:
    """Get nutrition summary for a date/period.

    DATE defaults to 'today'. Accepts: today, yesterday, -N (days ago), YYYY-MM-DD
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)

        # Calculate date range based on period
        if period == "day":
            start_date = target_date
            end_date = target_date
        elif period == "week":
            # Week starting from target date going back 6 days
            from datetime import datetime, timedelta

            dt = datetime.strptime(target_date, "%Y-%m-%d")
            start_dt = dt - timedelta(days=6)
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = target_date
        else:  # month
            # Month containing target date
            from datetime import datetime

            dt = datetime.strptime(target_date, "%Y-%m-%d")
            start_date = dt.replace(day=1).strftime("%Y-%m-%d")
            # Last day of month
            if dt.month == 12:
                next_month = dt.replace(year=dt.year + 1, month=1, day=1)
            else:
                next_month = dt.replace(month=dt.month + 1, day=1)
            from datetime import timedelta

            end_date = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")

        data = client.get_nutrition_summary(start_date, end_date)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("date_input", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def logs(ctx: click.Context, date_input: str, as_json: bool) -> None:
    """Get detailed food logs for a date.

    DATE defaults to 'today'. Accepts: today, yesterday, -N (days ago), YYYY-MM-DD
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)
        data = client.get_nutrition_food_logs(target_date)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("date_input", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def meals(ctx: click.Context, date_input: str, as_json: bool) -> None:
    """Get meal definitions with time windows and goals.

    DATE defaults to 'today'. Accepts: today, yesterday, -N (days ago), YYYY-MM-DD
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)
        data = client.get_nutrition_meals(target_date)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("date_input", default="today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def settings(ctx: click.Context, date_input: str, as_json: bool) -> None:
    """Get nutrition settings and goals for a date.

    DATE defaults to 'today'. Accepts: today, yesterday, -N (days ago), YYYY-MM-DD
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)
        data = client.get_nutrition_settings(target_date)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def status(ctx: click.Context, as_json: bool) -> None:
    """Get nutrition tracking status."""
    client = ctx.obj["client"]
    try:
        data = client.get_nutrition_status()
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def recent(ctx: click.Context, as_json: bool) -> None:
    """Get recently logged nutrition foods."""
    client = ctx.obj["client"]
    try:
        data = client.get_nutrition_recent_foods()
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("query")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def search(ctx: click.Context, query: str, as_json: bool) -> None:
    """Search nutrition foods in FatSecret database.

    QUERY: Search term (e.g., 'apple', 'chicken breast')
    """
    client = ctx.obj["client"]
    try:
        data = client.search_nutrition_foods(query)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.option("--limit", type=int, help="Maximum number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def custom_foods(ctx: click.Context, limit: int | None, as_json: bool) -> None:
    """Get user's custom nutrition foods."""
    client = ctx.obj["client"]
    try:
        data = client.get_nutrition_custom_foods(limit=limit)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("name")
@click.argument("serving_unit")
@click.argument("serving_size", type=float)
@click.argument("calories", type=float)
@click.option("--carbs", type=float, default=0, help="Carbohydrates in grams")
@click.option("--protein", type=float, default=0, help="Protein in grams")
@click.option("--fat", type=float, default=0, help="Fat in grams")
@click.option("--fiber", type=float, default=0, help="Fiber in grams")
@click.option("--sugar", type=float, default=0, help="Sugar in grams")
@click.option("--brand", help="Brand name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def add_custom_food(
    ctx: click.Context,
    name: str,
    serving_unit: str,
    serving_size: float,
    calories: float,
    carbs: float,
    protein: float,
    fat: float,
    fiber: float,
    sugar: float,
    brand: str | None,
    as_json: bool,
) -> None:
    """Add a custom nutrition food.

    NAME: Food name (required)
    SERVING_UNIT: Unit (e.g., 'g', 'oz', 'cup') (required)
    SERVING_SIZE: Amount per serving (required)
    CALORIES: Calories per serving (required)
    """
    client = ctx.obj["client"]
    try:
        data = client.create_nutrition_custom_food(
            food_name=name,
            serving_unit=serving_unit,
            serving_size=serving_size,
            calories=calories,
            carbs=carbs,
            protein=protein,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            brand_name=brand,
        )
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("food_id")
@click.argument("serving_id")
@click.argument("name")
@click.argument("serving_unit")
@click.argument("serving_size", type=float)
@click.argument("calories", type=float)
@click.option("--carbs", type=float, default=0, help="Carbohydrates in grams")
@click.option("--protein", type=float, default=0, help="Protein in grams")
@click.option("--fat", type=float, default=0, help="Fat in grams")
@click.option("--fiber", type=float, default=0, help="Fiber in grams")
@click.option("--sugar", type=float, default=0, help="Sugar in grams")
@click.option("--brand", help="Brand name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def update_custom_food(
    ctx: click.Context,
    food_id: str,
    serving_id: str,
    name: str,
    serving_unit: str,
    serving_size: float,
    calories: float,
    carbs: float,
    protein: float,
    fat: float,
    fiber: float,
    sugar: float,
    brand: str | None,
    as_json: bool,
) -> None:
    """Update a custom nutrition food.

    FOOD_ID: ID of the custom food to update
    SERVING_ID: ID of the serving to update
    NAME: Updated food name
    SERVING_UNIT: Updated unit (e.g., 'g', 'oz', 'cup')
    SERVING_SIZE: Updated amount per serving
    CALORIES: Updated calories per serving
    """
    client = ctx.obj["client"]
    try:
        data = client.update_nutrition_custom_food(
            food_id=food_id,
            serving_id=serving_id,
            food_name=name,
            serving_unit=serving_unit,
            serving_size=serving_size,
            calories=calories,
            carbs=carbs,
            protein=protein,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            brand_name=brand,
        )
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("food_id")
@click.pass_context
@require_auth
def delete_custom_food(ctx: click.Context, food_id: str) -> None:
    """Delete a custom nutrition food.

    FOOD_ID: ID of the custom food to delete
    """
    client = ctx.obj["client"]
    try:
        client.delete_nutrition_custom_food(food_id)
        click.echo(f"Custom food {food_id} deleted successfully")
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.option("--limit", type=int, help="Maximum number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def custom_meals(ctx: click.Context, limit: int | None, as_json: bool) -> None:
    """Get user's custom nutrition meals."""
    client = ctx.obj["client"]
    try:
        data = client.get_nutrition_custom_meals(limit=limit)
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("name")
@click.argument("foods_json")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def add_custom_meal(
    ctx: click.Context, name: str, foods_json: str, as_json: bool
) -> None:
    """Add a custom nutrition meal.

    NAME: Meal name (required)
    FOODS_JSON: JSON array of food dicts with serving_id and quantity, e.g.:
    '[{"food": {...full food dict...}, "serving_id": "123", "quantity": 1.5}]'

    Note: This command requires complex food dict structures. Use custom-foods
    or search commands first to get full food objects, then construct the JSON.
    """
    client = ctx.obj["client"]
    try:
        foods_data = json.loads(foods_json)

        # Convert from CLI format to API format (list of tuples)
        foods_list = []
        for item in foods_data:
            if not all(k in item for k in ["food", "serving_id", "quantity"]):
                raise click.ClickException(
                    "Each food entry must have 'food', 'serving_id', and 'quantity'"
                )
            foods_list.append((item["food"], item["serving_id"], item["quantity"]))

        data = client.create_nutrition_custom_meal(meal_name=name, foods=foods_list)
        click.echo(format_output(data, as_json=as_json))
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON for foods: {e}") from e
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("meal_id", type=int)
@click.pass_context
@require_auth
def delete_custom_meal(ctx: click.Context, meal_id: int) -> None:
    """Delete a custom nutrition meal.

    MEAL_ID: ID of the custom meal to delete
    """
    client = ctx.obj["client"]
    try:
        client.delete_nutrition_custom_meal(meal_id)
        click.echo(f"Custom meal {meal_id} deleted successfully")
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("date_input")
@click.argument("meal_id", type=int)
@click.argument("food_id")
@click.argument("serving_id")
@click.argument("quantity", type=float)
@click.option("--source", default="FATSECRET", help="Food source (default: FATSECRET)")
@click.option("--meal-time", help="Time in HH:MM:SS format (default: current time)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def add_log(
    ctx: click.Context,
    date_input: str,
    meal_id: int,
    food_id: str,
    serving_id: str,
    quantity: float,
    source: str,
    meal_time: str | None,
    as_json: bool,
) -> None:
    """Log a nutrition food for a date.

    DATE: Date to log food (today, yesterday, -N, YYYY-MM-DD)
    MEAL_ID: Meal ID (from get_nutrition_meals, e.g., 205461 for breakfast)
    FOOD_ID: ID of the food to log
    SERVING_ID: Serving size ID
    QUANTITY: Quantity/servings to log
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)
        data = client.add_nutrition_food_log(
            cdate=target_date,
            meal_id=meal_id,
            food_id=food_id,
            serving_id=serving_id,
            serving_qty=quantity,
            source=source,
            meal_time=meal_time,
        )
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("date_input")
@click.argument("log_ids")
@click.pass_context
@require_auth
def delete_logs(ctx: click.Context, date_input: str, log_ids: str) -> None:
    """Delete nutrition food logs for a date.

    DATE: Date of logs to delete (today, yesterday, -N, YYYY-MM-DD)
    LOG_IDS: Comma-separated list of log IDs to delete
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)
        ids = [log_id.strip() for log_id in log_ids.split(",")]
        client.delete_nutrition_food_logs(target_date, ids)
        click.echo(f"Deleted {len(ids)} nutrition log(s) for {target_date}")
    except Exception as e:
        handle_api_error(e)


@nutrition.command()
@click.argument("date_input")
@click.argument("meal_id", type=int)
@click.argument("custom_meal_id", type=int)
@click.option("--meal-time", help="Time in HH:MM:SS format (default: current time)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
@require_auth
def add_meal_log(
    ctx: click.Context,
    date_input: str,
    meal_id: int,
    custom_meal_id: int,
    meal_time: str | None,
    as_json: bool,
) -> None:
    """Log a custom meal (all its foods) for a date.

    DATE: Date to log meal (today, yesterday, -N, YYYY-MM-DD)
    MEAL_ID: Meal slot ID (from 'nutrition meals', e.g., breakfast/lunch/dinner)
    CUSTOM_MEAL_ID: ID of custom meal (from 'nutrition custom-meals')

    Example workflow:
      1. garmin nutrition custom-meals --json  # Get custom meal IDs
      2. garmin nutrition meals today --json   # Get meal slot IDs
      3. garmin nutrition add-meal-log today <meal_id> <custom_meal_id>
    """
    client = ctx.obj["client"]
    try:
        target_date = parse_date(date_input)

        # Fetch custom meals to get the full meal dict
        meals_response = client.get_nutrition_custom_meals()
        custom_meals = meals_response.get("customMeals", [])
        custom_meal = next(
            (m for m in custom_meals if m["customMealId"] == custom_meal_id),
            None,
        )
        if not custom_meal:
            raise click.ClickException(
                f"Custom meal {custom_meal_id} not found. "
                "Use 'nutrition custom-meals --json' to list available meals."
            )

        data = client.add_nutrition_custom_meal_log(
            cdate=target_date,
            meal_id=meal_id,
            custom_meal=custom_meal,
            meal_time=meal_time,
        )
        click.echo(format_output(data, as_json=as_json))
    except Exception as e:
        handle_api_error(e)
