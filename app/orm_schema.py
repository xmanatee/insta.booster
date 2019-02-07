from sqlalchemy import Column, DateTime, String, Integer, Float, ForeignKey, func
from sqlalchemy.orm import relationship, backref, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import UniqueConstraint


Base = declarative_base()


class InstaUser(Base):
    __tablename__ = 'insta_user'

    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)

    followers_count = Column(Integer)
    following_count = Column(Integer)
    media_count = Column(Integer)

    # followers_count_deriv = Column(Float, default=0)
    # following_count_deriv = Column(Float, default=0)
    # media_count_deriv = Column(Float, default=0)

    added_on = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<InstaUser(id={id}, user_name={user_name}, full_name={full_name}, followers_count={followers_count}, following_count={following_count}, media_count={media_count})>".format(
            id=self.id,
            user_name=self.user_name,
            full_name=self.full_name,
            followers_count=self.followers_count,
            following_count=self.following_count,
            media_count=self.media_count,
        )


class InstaFollow(Base):
    __tablename__ = 'insta_follow'
    __table_args__ = (UniqueConstraint('from_id', 'to_id', name='_insta_follow'),)

    entry_id = Column(Integer, primary_key=True, autoincrement=True)
    from_id = Column(Integer, ForeignKey('insta_user.id'))
    to_id = Column(Integer, ForeignKey('insta_user.id'))

    added_on = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<InstaFollow(from_id={from_id}, to_id={to_id})>".format(
            from_id=self.from_id,
            to_id=self.to_id,
        )


class WorthyUserId(Base):
    __tablename__ = 'worthy_user_id'

    id = Column(Integer, primary_key=True)
    status = Column(Integer)

    added_on = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<WorthyUserId(id={id}, status={status})>".format(
            id=self.id,
            status=self.status,
        )


class QueueUserId(Base):
    __tablename__ = 'queue_user_id'

    # entry_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer, primary_key=True)
    processed_on = Column(DateTime, nullable=True)

    added_on = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<QueueUserId(id={id}, processed_on={processed_on})>".format(
            id=self.id,
            processed_on=self.processed_on,
        )


def get_session(orm_path):
    engine = create_engine(orm_path)
    Session = scoped_session(sessionmaker(bind=engine))
    Base.metadata.create_all(engine)
    session = Session()
    return session
