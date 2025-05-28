"""
Defines the SQLAlchemy data models for the Resource Planning Tool.

This module includes models for Person, Project, and Assignment,
detailing their attributes, relationships, and helper methods for serialization.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship

# Initialize SQLAlchemy extension object.
# This object will be further configured and registered with the Flask app
# in app.py via db.init_app(app).
db = SQLAlchemy()

class Person(db.Model):
    """
    Represents a person in the system who can be assigned to projects
    or manage projects.
    """
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Unique identifier for the person.")
    name = Column(String(255), nullable=False, comment="Name of the person.")
    working_hours = Column(Integer, nullable=True, comment="Nominal working hours per week for the person, if specified.")

    # Relationship for projects managed by this person (one-to-many: Person to Project)
    # 'back_populates' links this to the 'project_manager' attribute in the Project model.
    managed_projects = relationship("Project", back_populates="project_manager", lazy='dynamic')
    
    # Relationship for assignments this person has (one-to-many: Person to Assignment)
    # 'back_populates' links this to the 'person' attribute in the Assignment model.
    assignments = relationship("Assignment", back_populates="person", lazy='dynamic')

    def __repr__(self):
        """Provides a developer-friendly string representation of the Person object."""
        return f"<Person {self.name}>"

    def to_dict(self):
        """
        Serializes the Person object to a dictionary.

        Returns:
            dict: A dictionary representation of the person's attributes.
        """
        return {
            'id': self.id,
            'name': self.name,
            'working_hours': self.working_hours
        }

class Project(db.Model):
    """
    Represents a project in the system. Each project has a manager and can have
    multiple persons assigned to it through assignments.
    """
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Unique identifier for the project.")
    name = Column(String(255), nullable=False, comment="Name of the project.")
    project_manager_id = Column(Integer, ForeignKey('persons.id'), nullable=False, comment="Foreign key linking to the person managing this project.")
    budget = Column(Numeric(10, 2), nullable=True, comment="Allocated budget for the project (e.g., 10 digits, 2 decimal places).") # Example precision

    # Relationship to the Person who is the project manager (many-to-one: Project to Person)
    # 'back_populates' links this to the 'managed_projects' attribute in the Person model.
    project_manager = relationship("Person", back_populates="managed_projects")
    
    # Relationship for assignments under this project (one-to-many: Project to Assignment)
    # 'back_populates' links this to the 'project' attribute in the Assignment model.
    assignments = relationship("Assignment", back_populates="project", lazy='dynamic')

    def __repr__(self):
        """Provides a developer-friendly string representation of the Project object."""
        return f"<Project {self.name}>"

    def to_dict(self):
        """
        Serializes the Project object to a dictionary.

        Includes the project manager's name and formats the budget as a string.

        Returns:
            dict: A dictionary representation of the project's attributes.
        """
        return {
            'id': self.id,
            'name': self.name,
            'project_manager_id': self.project_manager_id,
            'project_manager_name': self.project_manager.name if self.project_manager else None,
            'budget': str(self.budget) if self.budget is not None else None  # Convert Decimal to string for JSON
        }

class Assignment(db.Model):
    """
    Represents an assignment of a person to a project for a certain number of hours
    within a specific timeline. This acts as a link between Persons and Projects.
    """
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Unique identifier for the assignment.")
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment="Foreign key linking to the project.")
    person_id = Column(Integer, ForeignKey('persons.id'), nullable=False, comment="Foreign key linking to the person assigned.")
    assigned_hours = Column(Integer, nullable=False, comment="Number of hours allocated for this person on this project.")
    timeline_start = Column(Date, nullable=True, comment="Start date of the assignment.")
    timeline_end = Column(Date, nullable=True, comment="End date of the assignment.")

    # Relationship to the Project (many-to-one: Assignment to Project)
    # 'back_populates' links this to the 'assignments' attribute in the Project model.
    project = relationship("Project", back_populates="assignments")
    
    # Relationship to the Person (many-to-one: Assignment to Person)
    # 'back_populates' links this to the 'assignments' attribute in the Person model.
    person = relationship("Person", back_populates="assignments")

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the Assignment object.
        Handles cases where related person or project might not be loaded.
        """
        person_name = self.person.name if self.person else 'N/A'
        project_name = self.project.name if self.project else 'N/A'
        return f"<Assignment of {self.assigned_hours} hours for {person_name} on {project_name}>"

    def to_dict(self):
        """
        Serializes the Assignment object to a dictionary.

        Includes related project and person names, and formats dates as ISO strings.

        Returns:
            dict: A dictionary representation of the assignment's attributes.
        """
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'person_id': self.person_id,
            'person_name': self.person.name if self.person else None,
            'assigned_hours': self.assigned_hours,
            'timeline_start': self.timeline_start.isoformat() if self.timeline_start else None,
            'timeline_end': self.timeline_end.isoformat() if self.timeline_end else None
        }
