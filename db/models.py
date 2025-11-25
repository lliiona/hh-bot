from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(255))
    city = Column(String(255))
    desired_position = Column(String(255))
    skills = Column(Text)
    base_resume = Column(Text)

class SearchSettings(Base):
    __tablename__ = 'search_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    position = Column(String(255))
    city = Column(String(255))
    min_salary = Column(Integer)
    metro_stations = Column(JSON)  # list of stations
    freshness = Column(Integer)  # days
    employment_type = Column(String(50))  # full, part, remote
    experience = Column(String(50))  # no_exp, 1-3, 3-6, 6+
    company_filters = Column(JSON)  # dict with filters

    user = relationship("User")

class LLMSettings(Base):
    __tablename__ = 'llm_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    base_url = Column(String(500))
    api_key = Column(String(500))
    model = Column(String(100))

    user = relationship("User")

class Vacancy(Base):
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True)
    hh_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500))
    company = Column(String(255))
    city = Column(String(255))
    salary = Column(String(255))
    url = Column(String(500))
    description = Column(Text)

class UserVacancy(Base):
    __tablename__ = 'user_vacancies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    vacancy = relationship("Vacancy")

class GeneratedDocument(Base):
    __tablename__ = 'generated_documents'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=False)
    doc_type = Column(String(20))  # resume or cover
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    vacancy = relationship("Vacancy")