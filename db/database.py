from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("postgresql://user:pass@localhost/car_ai")
Session = sessionmaker(bind=engine)
Base = declarative_base()

def save_record(vin, data):
    session = Session()
    record = ContractRecord(vin=vin, analysis=data)
    session.add(record)
    session.commit()
