from fastapi.templating import Jinja2Templates


def format_price(value):
    if value is None:
        return "0"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    return f"{value:,.0f}".replace(",", " ")


templates = Jinja2Templates(directory="templates")
templates.env.filters["price"] = format_price
