from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	password = Column(String(250), nullable = False)

class Category(Base):
	__tablename__ = 'category'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)

	@property
	def serialize(self):
	    return {
	    	'id' : self.id,
	    	'name' : self.name,
	    }
	

class Item(Base):
	__tablename__ = 'item'
	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	description = Column(String(500), nullable = False)
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)

	@property
	def serialize(self):
	    return {
	    	'id' : self.id,
	    	'description' : self.description,
	    	'category_id' : self.category_id,
	    }

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.create_all(engine)
	
