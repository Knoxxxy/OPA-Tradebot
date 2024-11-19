# app/models.py

from pydantic import BaseModel, Field
from bson import ObjectId
from database import PyObjectId

class OHLCDataModel(BaseModel):
      
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    count: int
    taker_buy_base_volume: float
    taker_buy_quote_volume: float

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = False
        json_encoders = {ObjectId: str}

class ScriptArgs(BaseModel):
    args: list[str]  # This will hold the list of arguments to pass to the script
