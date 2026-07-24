import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from kerykeion import AstrologicalSubject, NatalAspects
from timezonefinder import TimezoneFinder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tf = TimezoneFinder()

_planets_cache = {"data": None, "ts": 0.0}
CACHE_TTL = 15 * 60  # 15 minutes


class NatalBody(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = 12
    minute: Optional[int] = 0
    latitude: float
    longitude: float
    name: Optional[str] = "Native"


class ChartBody(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = 12
    minute: Optional[int] = 0
    latitude: float
    longitude: float
    timezone: Optional[str] = None
    location_precision: Optional[int] = 4


def _planet_dict(p):
    return {
        "name": p.name,
        "quality": p.quality,
        "element": p.element,
        "sign": p.sign,
        "sign_num": p.sign_num,
        "position": p.position,
        "abs_pos": p.abs_pos,
        "emoji": getattr(p, "sign_emoji", ""),
        "point_type": "AstrologicalPoint",
        "house": p.house,
        "retrograde": p.retrograde,
        "speed": getattr(p, "speed", None),
        "declination": getattr(p, "declination", None),
        "magnitude": None,
    }


def _calc_planets_now():
    now = datetime.now(timezone.utc)
    s = AstrologicalSubject(
        name="Now",
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        lat=51.477928,
        lng=-0.001545,
        tz_str="Etc/UTC",
    )

    PLANET_KEYS = [
        "sun", "moon", "mercury", "venus", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto", "chiron",
    ]

    iso = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    subject: dict = {
        "name": "Now",
        "iso_formatted_utc_datetime": iso,
        "iso_formatted_local_datetime": iso,
        "zodiac_type": "Tropical",
    }

    for key in PLANET_KEYS:
        p = getattr(s, key, None)
        subject[key] = _planet_dict(p) if p is not None else None

    HOUSE_ATTRS = [
        "first_house", "second_house", "third_house", "fourth_house",
        "fifth_house", "sixth_house", "seventh_house", "eighth_house",
        "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
    ]
    houses = []
    for i, attr in enumerate(HOUSE_ATTRS, 1):
        h = getattr(s, attr)
        houses.append({"house": i, "abs_pos": h.abs_pos, "sign": h.sign, "position": h.position})
    subject["houses"] = houses
    subject["ascendant"] = {"abs_pos": s.first_house.abs_pos, "sign": s.first_house.sign, "position": s.first_house.position}
    subject["mc"] = {"abs_pos": s.tenth_house.abs_pos, "sign": s.tenth_house.sign, "position": s.tenth_house.position}

    return {"status": "OK", "subject": subject}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/planets")
def planets():
    now_ts = time.time()
    if _planets_cache["data"] is None or (now_ts - _planets_cache["ts"]) > CACHE_TTL:
        _planets_cache["data"] = _calc_planets_now()
        _planets_cache["ts"] = now_ts
    return _planets_cache["data"]


@app.post("/natal")
def natal(body: NatalBody):
    tz_str = tf.timezone_at(lat=body.latitude, lng=body.longitude) or "UTC"
    s = AstrologicalSubject(
        name=body.name,
        year=body.year,
        month=body.month,
        day=body.day,
        hour=body.hour,
        minute=body.minute,
        lat=body.latitude,
        lng=body.longitude,
        tz_str=tz_str,
    )

    HOUSE_ATTRS = [
        "first_house", "second_house", "third_house", "fourth_house",
        "fifth_house", "sixth_house", "seventh_house", "eighth_house",
        "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
    ]
    houses = []
    for i, attr in enumerate(HOUSE_ATTRS, 1):
        h = getattr(s, attr)
        houses.append({"house": i, "sign": h.sign, "position": h.position, "abs_pos": h.abs_pos})

    chiron = getattr(s, "chiron", None)
    planets_list = [s.sun, s.moon, s.mercury, s.venus, s.mars,
                    s.jupiter, s.saturn, s.uranus, s.neptune, s.pluto]
    if chiron is not None:
        planets_list.append(chiron)

    aspects = []
    for asp in NatalAspects(s).relevant_aspects:
        aspects.append({
            "p1": asp["p1_name"],
            "p2": asp["p2_name"],
            "aspect": asp["aspect"],
            "orbit": asp["orbit"],
            "aspect_degrees": asp["aspect_degrees"],
            "diff": asp["diff"],
        })

    return {
        "name": body.name,
        "datetime": f"{body.year}-{body.month:02d}-{body.day:02d} {body.hour:02d}:{body.minute:02d}",
        "latitude": body.latitude,
        "longitude": body.longitude,
        "timezone": tz_str,
        "ascendant": {
            "sign": s.first_house.sign,
            "position": s.first_house.position,
            "abs_pos": s.first_house.abs_pos,
        },
        "mc": {
            "sign": s.tenth_house.sign,
            "position": s.tenth_house.position,
            "abs_pos": s.tenth_house.abs_pos,
        },
        "planets": [_planet_dict(p) for p in planets_list],
        "houses": houses,
        "aspects": aspects,
    }


# Serve widget HTML files — must be mounted last
if os.path.isdir("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")
