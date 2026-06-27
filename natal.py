#!/usr/bin/env python3
import sys
import json
from kerykeion import AstrologicalSubject
from timezonefinder import TimezoneFinder

def planet_to_dict(p):
    return {
        "name": p.name,
        "sign": p.sign,
        "sign_num": p.sign_num,
        "position": p.position,
        "abs_pos": p.abs_pos,
        "house": p.house,
        "retrograde": p.retrograde,
        "element": p.element,
        "quality": p.quality,
    }

def main():
    data = json.loads(sys.stdin.read())
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=data["latitude"], lng=data["longitude"]) or "UTC"

    s = AstrologicalSubject(
        name=data.get("name", "Native"),
        year=data["year"],
        month=data["month"],
        day=data["day"],
        hour=data.get("hour", 12),
        minute=data.get("minute", 0),
        lat=data["latitude"],
        lng=data["longitude"],
        tz_str=tz_str,
    )

    house_attrs = [
        "first_house","second_house","third_house","fourth_house",
        "fifth_house","sixth_house","seventh_house","eighth_house",
        "ninth_house","tenth_house","eleventh_house","twelfth_house",
    ]
    houses = []
    for i, attr in enumerate(house_attrs, 1):
        h = getattr(s, attr)
        houses.append({"house": i, "sign": h.sign, "position": h.position, "abs_pos": h.abs_pos})

    planets = [s.sun, s.moon, s.mercury, s.venus, s.mars,
               s.jupiter, s.saturn, s.uranus, s.neptune, s.pluto]

    aspects = []
    if hasattr(s, "aspects_list"):
        for asp in s.aspects_list:
            aspects.append({
                "p1": asp.p1_name,
                "p2": asp.p2_name,
                "aspect": asp.aspect,
                "orbit": asp.orbit,
                "aspect_degrees": asp.aspect_degrees,
                "diff": asp.diff,
            })

    result = {
        "name": data.get("name", "Native"),
        "datetime": f"{data['year']}-{data['month']:02d}-{data['day']:02d} {data.get('hour',12):02d}:{data.get('minute',0):02d}",
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "timezone": tz_str,
        "ascendant": {"sign": s.first_house.sign, "position": s.first_house.position, "abs_pos": s.first_house.abs_pos},
        "mc": {"sign": s.tenth_house.sign, "position": s.tenth_house.position, "abs_pos": s.tenth_house.abs_pos},
        "planets": [planet_to_dict(p) for p in planets],
        "houses": houses,
        "aspects": aspects,
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
