from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Session
import random

Base = declarative_base()

LEVEL_MAP = {
    "начинающий": "новичок",
    "продвинутый": "профи",
    "продолжающий": "продолжающий",
    "неважно": "неважно"
}

class YogaVideo(Base):
    __tablename__ = "yoga_videos"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    duration_label = Column(String)
    level = Column(String)

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    video_id = Column(Integer, ForeignKey("yoga_videos.id"))
    video = relationship("YogaVideo")

def get_random_video(session: Session, filters: dict):
    query = session.query(YogaVideo)
    if "duration" in filters:
        query = query.filter(YogaVideo.duration_label == filters["duration"])
    if "level" in filters:
        mapped_level = LEVEL_MAP.get(filters["level"], filters["level"])
        if mapped_level != "неважно":
            query = query.filter(YogaVideo.level == mapped_level)
    videos = query.all()
    return random.choice(videos) if videos else None

def get_favorite_videos(session: Session, user_id: int):
    return session.query(YogaVideo).join(UserFavorite).filter(UserFavorite.user_id == user_id).all()

def add_favorite(session: Session, user_id: int, video_id: int):
    fav = UserFavorite(user_id=user_id, video_id=video_id)
    session.add(fav)
    session.commit()

def is_favorite(session: Session, user_id: int, video_id: int):
    return session.query(UserFavorite).filter_by(user_id=user_id, video_id=video_id).first() is not None
