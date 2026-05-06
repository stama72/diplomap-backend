import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Point, User, Country
from routers.points import PointIn

import pandas as pd

from database import get_db
from routers.countries import CountryIn
df = pd.read_csv("capital_cities_2024.csv", encoding="cp932")


# ISOコード、国名、首都の座標を抽出
df_country_capital = df[["ctry_name", "iso_a2", "ja_ctry", "x", "y"]]

print(df_country_capital)

def add_point(
    body: PointIn,
    db: Session = Depends(get_db),
):
    point = Point(
        name=body.name,
        name_ja=body.name_ja,
        lat=body.lat,
        lng=body.lng,
    )

    db.add(point)
    db.commit()
    db.refresh(point)
    print(str(point.id))
    return {
        "id": point.id,
        "name": point.name,
        "name_ja": point.name_ja,
        "lat": float(point.lat),
        "lng": float(point.lng),
    }
def add_country(
    body:         CountryIn,
    db:           Session = Depends(get_db),
):
    point = add_point(PointIn(name=body.name, name_ja=body.name_ja, lat=body.lat, lng=body.lng), db)
    country = Country(
        iso_id=body.iso_id,
        name=body.name,
        name_ja=body.name_ja,
        capital_point_id=point["id"],
        exist_from=body.exist_from if body.exist_from else datetime(1900, 1, 1),
        exist_until=body.exist_until if body.exist_until else datetime(9999, 12, 31)
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return {
        "iso_id": country.iso_id,
        "name": country.name,
        "name_ja": country.name_ja,
        "capital_point_id": country.capital_point_id,
        "exist_from": country.exist_from.isoformat() if country.exist_from else None,
        "exist_until": country.exist_until.isoformat() if country.exist_until else None
    }

db = next(get_db())

if __name__ == "__main__":
    for _, row in df_country_capital.iterrows():
        if(pd.isna(row["iso_a2"])):
            print(f"Skipping row with missing data: {row}")
            continue
        if(row["iso_a2"] == "NZ"):
            print(f"Skipping row with missing data: {row}")
            continue
        add_country(
            body=CountryIn(
                iso_id=row["iso_a2"],
                name=row["ctry_name"],
                name_ja=row["ja_ctry"],
                lat=row["y"],
                lng=row["x"],
                exist_from=datetime(1900, 1, 1),
                exist_until=datetime(9999, 12, 31)
            ),
            db=db,
        )



#ナミビアが欠損している。
#ニウエ(NU)が誤記によりNZとなり、ニュージーランド(NZ)と被りを起こしている。
