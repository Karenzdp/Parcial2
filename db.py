from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from typing import Annotated


db_name = "universidad.db"
db_url = f"sqlite:///{db_name}"

engine = create_engine(db_url, echo=True, connect_args={"check_same_thread": False})


def init_db(app: FastAPI):
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]