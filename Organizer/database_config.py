import os
from sqlalchemy import create_engine,Column, String, Float, Integer, Text, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import time

load_dotenv()

db_url = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:" f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST', "postgres")}:" f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB')}"
    )

engine = create_engine(db_url)
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Notice(Base):
    __tablename__ = "notices"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String(30), unique=True, nullable=False, index=True)
    date_of_birth = Column(String(20), nullable=True)
    distinguishing_marks = Column(Text, nullable=True)
    weight = Column(Float, nullable=True)
    nationalities = Column(JSON, nullable=True)
    eyes_colors_id = Column(JSON, nullable=True)
    sex_id = Column(String(5), nullable=False)
    place_of_birth = Column(String(200), nullable=True)
    forename = Column(String(200), nullable=True)
    arrest_warrants = Column(JSON, nullable=True)
    country_of_birth_id = Column(String(20), nullable=True)
    hairs_id = Column(JSON, nullable=True)
    name = Column(String(200), nullable=True)
    languages_spoken_ids = Column(JSON, nullable=True)
    height = Column(Float, nullable=True)

    imgs_link = Column(String(200), nullable=True)

    upload_time = Column(String(50), nullable=True)

    def __repr__(self):
        return f'<Notice(entity_id = "{self.entity_id}", name = "{self.name}", forename = "{self.forename}")>'

def db_init():
    retries = 10
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            print("Db tables created successfully!")
            return
        except Exception as e:
            retries -= 1
            time.sleep(5)
    raise Exception(f"Couldnt connect to db after {retries} retries")
