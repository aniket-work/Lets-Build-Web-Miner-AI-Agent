from pydantic import BaseModel


class Car(BaseModel):
    """
    Represents the data structure of a Car.
    """
    year: int
    name: str
    kilometers: str
    price: str
