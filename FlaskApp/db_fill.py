from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Categories
category1 = Category(name="Electric Guitars")
session.add(category1)
session.commit()

category2 = Category(name="Acoustic Guitars")
session.add(category2)
session.commit()

category3 = Category(name="Bass Guitars")
session.add(category3)
session.commit()

category4 = Category(name="Drum Kits")
session.add(category4)
session.commit()

category5 = Category(name="Accessories")
session.add(category5)
session.commit()

# Items

item1 = Item(name="Fender Guitar", description="A very fine Fender Guitar",
             category=category1)
session.add(item1)
session.commit()

print("added items!")
