import datetime
import pytz
import swisseph as swe
import requests
import os

# Get bot token and chat ID from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN and CHAT_ID must be set as environment variables")

# Timezones
tehran_tz = pytz.timezone('Asia/Tehran')
london_tz = pytz.timezone('Europe/London')
ny_tz = pytz.timezone('America/New_York')

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

ASPECTS = {
    0: "Con",
    60: "Sxt",
    90: "Sqr",
    120: "Tri",
    180: "Opp"
}

MAX_ORB_LONGITUDE = 6.0
MAX_ORB_LATITUDE = 1.0

def normalize_angle(angle):
    return angle % 360

def angle_difference(a1, a2):
    diff = abs(a1 - a2)
    return min(diff, 360 - diff)

def get_planet_positions(jd):
    positions = {}
    for name, pid in PLANETS.items():
        res = swe.calc_ut(jd, pid)
        if len(res) < 2:
            continue
        lon, lat = res[0][0], res[0][1]  # [0][0] is longitude, [0][1] is latitude
        positions[name] = (lon, lat)
    return positions

def find_longitude_aspects(positions):
    aspects_found = []
    planet_names = list(positions.keys())
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]
            lon1, _ = positions[p1]
            lon2, _ = positions[p2]
            for angle, abbr in ASPECTS.items():
                diff = angle_difference(lon1, lon2)
                orb = abs(diff - angle)
                if orb <= MAX_ORB_LONGITUDE:
                    aspects_found.append({
                        "type": "longitude",
                        "p1": p1,
                        "p2": p2,
                        "aspect": abbr,
                        "orb": orb,
                        "angle": diff
                    })
    return aspects_found

def find_latitude_aspects(positions):
    parallels = []
    planet_names = list(positions.keys())
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]
            _, lat1 = positions[p1]
            _, lat2 = positions[p2]
            orb = abs(abs(lat1) - abs(lat2))
            if orb <= MAX_ORB_LATITUDE:
                aspect_type = "Par" if (lat1 * lat2) > 0 else "CPar"
                parallels.append({
                    "type": "latitude",
                    "p1": p1,
                    "p2": p2,
                    "aspect": aspect_type,
                    "orb": orb
                })
    return parallels

def format_aspect(aspect):
    p1 = f"<b>{aspect['p1']}</b>"
    p2 = f"<b>{aspect['p2']}</b>"
    asp = f"<i>{aspect['aspect']}</i>"
    orb = f"{aspect['orb']:.2f}°"
    return f"{p1} {asp} {p2} (orb: {orb})"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    max_len = 4000
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]
    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML"
        }
        resp = requests.post(url, data=payload)
        if not resp.ok:
            print(f"Telegram send error: {resp.text}")

def main():
    now_utc = datetime.datetime.utcnow()
    jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                    now_utc.hour + now_utc.minute / 60 + now_utc.second / 3600)

    positions = get_planet_positions(jd)
    long_aspects = find_longitude_aspects(positions)
    lat_aspects = find_latitude_aspects(positions)

    now_tehran = now_utc.replace(tzinfo=pytz.utc).astimezone(tehran_tz)
    now_london = now_utc.replace(tzinfo=pytz.utc).astimezone(london_tz)
    now_ny = now_utc.replace(tzinfo=pytz.utc).astimezone(ny_tz)

    header = (
        f"🔮 Astrological Aspects for {now_tehran.strftime('%Y-%m-%d')}\n"
        f"Times: Tehran: {now_tehran.strftime('%Y-%m-%d %H:%M %Z')} | "
        f"London: {now_london.strftime('%Y-%m-%d %H:%M %Z')} | "
        f"New York: {now_ny.strftime('%Y-%m-%d %H:%M %Z')}\n\n"
    )

    messages = [header]

    for asp in long_aspects:
        messages.append(format_aspect(asp))

    for asp in lat_aspects:
        messages.append(format_aspect(asp))

    if len(messages) == 1:
        messages.append("📭 No major aspects found today.")

    full_message = "<b>Longitude and Latitude Aspects:</b>\n" + "\n".join(messages[1:])
    send_telegram_message(header + full_message)

if __name__ == "__main__":
    main()

