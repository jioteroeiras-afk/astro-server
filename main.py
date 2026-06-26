import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from kerykeion import AstrologicalSubject
from timezonefinder import TimezoneFinder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "astrologer.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY or "",
}

tf = TimezoneFinder()


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


class NatalBody(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = 12
    minute: Optional[int] = 0
    latitude: float
    longitude: float
    name: Optional[str] = "Native"


def planet_to_dict(p):
    return {
        "name": p.name,
        "sign": p.sign,
        "sign_num": p.sign_num,
        "position": p.position,
        "abs_pos": p.abs_pos,
        "emoji": p.sign_emoji if hasattr(p, "sign_emoji") else "",
        "house": p.house,
        "retrograde": p.retrograde,
        "element": p.element,
        "quality": p.quality,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/planets")
async def planets():
    if not RAPIDAPI_KEY:
        raise HTTPException(500, "RAPIDAPI_KEY no configurada")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://astrologer.p.rapidapi.com/api/v5/now/context",
            headers=RAPIDAPI_HEADERS,
            json={},
        )
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()


@app.post("/chart")
async def chart(body: ChartBody):
    if not RAPIDAPI_KEY:
        raise HTTPException(500, "RAPIDAPI_KEY no configurada")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://astrologer.p.rapidapi.com/api/v5/moon-phase/context",
            headers=RAPIDAPI_HEADERS,
            json=body.model_dump(exclude_none=True),
        )
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()


@app.post("/natal")
def natal(body: NatalBody):
    tz_str = tf.timezone_at(lat=body.latitude, lng=body.longitude)
    if not tz_str:
        tz_str = "UTC"

    subject = AstrologicalSubject(
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

    planets_list = [
        subject.sun,
        subject.moon,
        subject.mercury,
        subject.venus,
        subject.mars,
        subject.jupiter,
        subject.saturn,
        subject.uranus,
        subject.neptune,
        subject.pluto,
    ]

    houses = []
    for i in range(1, 13):
        h = getattr(subject, f"first_house" if i == 1 else
                    f"second_house" if i == 2 else
                    f"third_house" if i == 3 else
                    f"fourth_house" if i == 4 else
                    f"fifth_house" if i == 5 else
                    f"sixth_house" if i == 6 else
                    f"seventh_house" if i == 7 else
                    f"eighth_house" if i == 8 else
                    f"ninth_house" if i == 9 else
                    f"tenth_house" if i == 10 else
                    f"eleventh_house" if i == 11 else
                    f"twelfth_house")
        houses.append({
            "house": i,
            "sign": h.sign,
            "position": h.position,
            "abs_pos": h.abs_pos,
        })

    aspects = []
    if hasattr(subject, "aspects_list"):
        for asp in subject.aspects_list:
            aspects.append({
                "p1": asp.p1_name,
                "p2": asp.p2_name,
                "aspect": asp.aspect,
                "orbit": asp.orbit,
                "aspect_degrees": asp.aspect_degrees,
                "diff": asp.diff,
            })

    return {
        "name": body.name,
        "datetime": f"{body.year}-{body.month:02d}-{body.day:02d} {body.hour:02d}:{body.minute:02d}",
        "latitude": body.latitude,
        "longitude": body.longitude,
        "timezone": tz_str,
        "ascendant": {
            "sign": subject.first_house.sign,
            "position": subject.first_house.position,
            "abs_pos": subject.first_house.abs_pos,
        },
        "mc": {
            "sign": subject.tenth_house.sign,
            "position": subject.tenth_house.position,
            "abs_pos": subject.tenth_house.abs_pos,
        },
        "planets": [planet_to_dict(p) for p in planets_list],
        "houses": houses,
        "aspects": aspects,
    }
