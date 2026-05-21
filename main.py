import os

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Weather condition code mapping (WMO Weather interpretation codes)
WMO_CODES = {
    0: ("☀️", "Clear sky"),
    1: ("🌤️", "Mainly clear"),
    2: ("⛅", "Partly cloudy"),
    3: ("☁️", "Overcast"),
    45: ("🌫️", "Foggy"),
    48: ("🌫️", "Icy fog"),
    51: ("🌦️", "Light drizzle"),
    53: ("🌦️", "Moderate drizzle"),
    55: ("🌧️", "Dense drizzle"),
    61: ("🌧️", "Slight rain"),
    63: ("🌧️", "Moderate rain"),
    65: ("🌧️", "Heavy rain"),
    71: ("🌨️", "Slight snow"),
    73: ("🌨️", "Moderate snow"),
    75: ("❄️", "Heavy snow"),
    77: ("🌨️", "Snow grains"),
    80: ("🌦️", "Slight showers"),
    81: ("🌧️", "Moderate showers"),
    82: ("⛈️", "Violent showers"),
    85: ("🌨️", "Slight snow showers"),
    86: ("🌨️", "Heavy snow showers"),
    95: ("⛈️", "Thunderstorm"),
    96: ("⛈️", "Thunderstorm with hail"),
    99: ("⛈️", "Thunderstorm with heavy hail"),
}


def geocode_city(city: str) -> tuple[float, float, str] | None:
    """Resolve a city name to (latitude, longitude, display_name) via Open-Meteo geocoding."""
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results")
        if not results:
            return None
        r = results[0]
        display = r.get("name", city)
        country = r.get("country", "")
        if country:
            display = f"{display}, {country}"
        return r["latitude"], r["longitude"], display
    except Exception:
        return None


def fetch_weather(lat: float, lon: float) -> dict | None:
    """Fetch current weather from Open-Meteo for the given coordinates."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ],
                "wind_speed_unit": "kmh",
                "timezone": "auto",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def wind_direction_label(degrees: float) -> str:
    """Convert wind direction in degrees to a compass label."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = round(degrees / 45) % 8
    return directions[idx]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 机器人部署成功！\n\n"
        "可用命令：\n"
        "/start — 显示此帮助信息\n"
        "/weather <城市> — 查询实时天气\n\n"
        "示例：/weather Beijing"
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weather <city> command."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ 请提供城市名称。\n用法：/weather <城市>\n示例：/weather Beijing"
        )
        return

    city = " ".join(context.args)
    await update.message.reply_text(f"🔍 正在查询 {city} 的天气，请稍候…")

    # Step 1: Geocode the city
    geo = geocode_city(city)
    if geo is None:
        await update.message.reply_text(
            f"❌ 找不到城市「{city}」，请检查拼写后重试。"
        )
        return

    lat, lon, display_name = geo

    # Step 2: Fetch weather data
    data = fetch_weather(lat, lon)
    if data is None:
        await update.message.reply_text("❌ 天气数据获取失败，请稍后再试。")
        return

    current = data.get("current", {})
    temp = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind_speed = current.get("wind_speed_10m")
    wind_dir = current.get("wind_direction_10m")
    code = current.get("weather_code", 0)

    emoji, condition = WMO_CODES.get(code, ("🌡️", "Unknown"))
    wind_label = wind_direction_label(wind_dir) if wind_dir is not None else "N/A"

    message = (
        f"{emoji} *{display_name} 天气*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌡️ 温度：{temp}°C（体感 {feels_like}°C）\n"
        f"🌈 天气：{condition}\n"
        f"💧 湿度：{humidity}%\n"
        f"💨 风速：{wind_speed} km/h {wind_label}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📍 坐标：{lat:.2f}°N, {lon:.2f}°E"
    )

    await update.message.reply_text(message, parse_mode="Markdown")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo any plain text message back to the user."""
    await update.message.reply_text(update.message.text)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()


if __name__ == "__main__":
    main()
