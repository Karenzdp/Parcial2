from sqlmodel import Session, create_engine, SQLModel
from fastapi import Depends
from typing import Annotated

engine = create_engine('sqlite:///Universidad.db', connect_args={"check_same_thread": False})

def create_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
