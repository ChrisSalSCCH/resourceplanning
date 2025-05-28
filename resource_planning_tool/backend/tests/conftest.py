import pytest
import os
from resource_planning_tool.backend.app import app as flask_app, db as sqlalchemy_db
from resource_planning_tool.backend.models import Person, Project, Assignment # Ensure all models are imported

@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # In-memory SQLite database for tests
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False, # Disable CSRF for simpler form testing if applicable
        "DEBUG": False
    })
    return flask_app

@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='session')
def _db(app): # Renamed to _db to avoid conflict with db_session if it were named 'db'
    """
    Session-wide database setup. Initializes the database schema once per session.
    Yields the SQLAlchemy db object associated with the app.
    """
    with app.app_context():
        sqlalchemy_db.create_all()
        yield sqlalchemy_db # This is the SQLAlchemy extension instance
        sqlalchemy_db.drop_all()

@pytest.fixture(scope='function')
def db_session(_db):
    """
    Provides a transactional scope around a test function using the app's db object.
    Ensures that the database is clean for each test by rolling back transactions.
    Yields the SQLAlchemy session from the app's db object.
    """
    # The _db fixture ensures create_all() has been called.
    # We use the session from the Flask-SQLAlchemy instance (_db.session).
    # This session is typically a scoped_session that manages sessions per thread/context.
    
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    # Bind the app's db.session to this connection for the duration of the test
    # This is a way to make the global 'db.session' use this specific transaction
    # However, for Flask-SQLAlchemy, db.session is a scoped_session.
    # We need to ensure operations within this scope use our transaction.
    # A common pattern is to begin a nested transaction on the existing session if possible,
    # or ensure the existing session uses our connection.

    # Forcing the scoped_session to use our connection and transaction
    # This is somewhat advanced. A simpler way if models allow passing session:
    # session = _db.create_session(options={'bind': connection, 'binds': {}})
    
    # Let's try ensuring the global session uses our connection.
    # This is tricky because db.session is a proxy.
    # The most robust way is often to use a SAVEPOINT (nested transaction)
    # if the database and SQLAlchemy driver support it. SQLite does.
    
    # Start a SAVEPOINT
    _db.session.begin_nested()

    @_db.event.listens_for(_db.session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        # If the main transaction is still active (which it should be in our test case)
        # and the just-ended transaction was our savepoint (is_active will be false for it)
        # then restart the savepoint. This handles cases where app code might commit the savepoint.
        if transaction.parent is not None: # Check if it was a nested transaction
             session.begin_nested()

    yield _db.session # Tests will use the app's global db.session

    # Rollback the SAVEPOINT
    _db.session.rollback() # Rolls back to the state before begin_nested()
    
    # Clean up listener to avoid side effects on other sessions/tests if any
    # This is tricky; typically, event listeners are module/class level.
    # For simplicity here, we assume this listener is fine for the test function's scope.
    # A more complex setup might involve removing the listener.

    # The main transaction on the connection will be rolled back by pytest-flask-sqlalchemy or similar,
    # or would need explicit rollback if we managed the connection directly without such a plugin.
    # For now, relying on the nested transaction rollback for test isolation.
    # The outer transaction on 'connection' is not committed here.
    # If the 'connection' and 'transaction' were created here, they should be closed/rolled back.
    # However, the global _db.session will manage its own connection lifecycle usually.
    # The initial `connection` and `transaction` are not used if we only use `_db.session.begin_nested()`.

    # Let's simplify: the goal is that any commit inside a test is rolled back.
    # Flask-SQLAlchemy's session is a scoped_session. We want to ensure it rolls back.
    # The `_db.session.remove()` can be called to ensure the session is reset,
    # and `_db.engine.dispose()` if we want to clear all connections.
    # However, for test-by-test isolation, rolling back the transaction is key.
    # The current approach with begin_nested() and rollback() on _db.session is standard.

    # The previous code with `sqlalchemy_db_global.session = session` was problematic.
    # Let's stick to manipulating the existing `_db.session` (which is `sqlalchemy_db.session`).
    # The `_db` fixture already provides the app's db context.
    # The issue might be that the session used by `Model.query` is not the one we are controlling.

    # Reverting to a simpler model that relies on Flask-SQLAlchemy's session management
    # within a transaction for each test.
    # The `_db` fixture gives us the `SQLAlchemy` instance. `_db.session` is the scoped session.
    # We just need to ensure this session's changes are rolled back.

    # No, the previous `db_session` was closer for raw SQLAlchemy with Pytest.
    # For Flask-SQLAlchemy, the `db.session` object within the app context is the one to use.
    # The issue is ensuring this `db.session` is properly isolated.
    # `db.create_all()` and `db.drop_all()` in `_db` are correct for session-wide setup.
    # The `TypeError: 'Session' object is not callable` is the primary clue.
    # It happens here: `cls, session=cls.__fsa__.session()`.
    # This means `cls.__fsa__.session` (which should be `db.session_factory`) is an actual session instance.
    # This happens if `SQLAlchemy(app)` was called *after* `SQLAlchemy()` was initialized without an app.
    # Or, if `db.init_app(app)` was not correctly setting up the session factory.

    # The `conftest.py` from Subtask 7, Turn 2 was:
    # sqlalchemy_db.session.configure(bind=connection)
    # This was causing SAWarning.

    # Let's ensure that the app context is active when db operations occur via client.
    # The `_db` fixture handles app_context for create_all/drop_all.
    # Test functions using `client` operate within an app context pushed by the test client.
    # The `db_session` fixture should provide the session that the app uses.
    
    # The error `TypeError: 'Session' object is not callable` in `flask_sqlalchemy/model.py`
    # `cls, session=cls.__fsa__.session()` suggests `cls.__fsa__.session` is not the session factory.
    # `__fsa__` is `app.extensions['sqlalchemy']`. So it's `app.extensions['sqlalchemy'].session`.
    # This should be the `scoped_session` instance itself, not its factory.
    # The `scoped_session` is callable to get the actual session. So `db.session()` gives current session.
    # The error implies that `db.session` itself (the scoped_session proxy) has been replaced by a raw Session instance.
    # This was exactly what my `conftest.py` from Subtask 7, Turn 5 was doing:
    # `sqlalchemy_db_global.session = session` (where `session` was a newly created raw session).
    # That was a mistake. We must not replace the `scoped_session` proxy.

    # The `db_session` from Subtask 7, Turn 2 was:
    # yield db.session
    # db.session.rollback()
    # This is simpler and relies on the global `db.session` (scoped_session) being correctly managed.
    # The key is that the scoped_session needs to use the test transaction.

    # Let's try to use the connection from the engine and start a transaction on it,
    # then make the scoped_session use this connection.
    # This ensures all operations via db.session in app code use this transaction.
    
    # This is the setup that usually works for Flask-SQLAlchemy:
    # 1. `_db` fixture creates tables once per session.
    # 2. `db_session` (function-scoped):
    #    - `_db.session.begin_nested()`  (starts a SAVEPOINT)
    #    - `yield _db.session`
    #    - `_db.session.rollback()` (rolls back the SAVEPOINT)
    # This structure was present in my `tests/test_person_api.py` which had fewer failures.
    # The issue might be the interaction of this with how `Model.query` gets the session.
    # Flask-SQLAlchemy v3+ changed how `Model.query` works; it uses `db.session` directly.
    # The error `TypeError: 'Session' object is not callable` means that `db.session` (the scoped_session)
    # is being expected to be called like `db.session()` to get the actual session instance,
    # but it's already a session instance. This is highly indicative of the `db.session`
    # (the scoped_session proxy itself) being overwritten by a direct session object.

    # The `conftest.py` from Subtask 7, Turn 5:
    # sqlalchemy_db_global.session = session # THIS WAS THE BUG.
    # yield session
    # sqlalchemy_db_global.session = original_session

    # The correct way is to *not* replace `sqlalchemy_db_global.session`.
    # Instead, ensure the operations within the test run in a transaction that gets rolled back.
    # The `db.session.begin_nested()` and `db.session.rollback()` is the right pattern for this
    # if `db.session` is the standard Flask-SQLAlchemy scoped_session.

    # Let's revert conftest.py to a known good state for Flask-SQLAlchemy testing,
    # which focuses on using nested transactions for test isolation.
    # The one from Subtask 7, Turn 2, but with explicit transaction management for the test.
    # No, that one was also problematic.

    # The simplest function-scoped fixture for Flask-SQLAlchemy:
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    # This forces the session to use this connection for the current scope
    # However, this is not how a scoped_session is typically handled.
    # _db.session.configure(bind=connection) # This caused warnings.

    # The most straightforward approach for Flask-SQLAlchemy is to use its session directly
    # and manage transactions on it.
    
    # Start a new transaction (SAVEPOINT)
    _db.session.begin_nested()
    
    yield _db.session # The test uses the app's session

    # Rollback the transaction
    _db.session.rollback()
    # If db.session.remove() is called, it detaches the session, and a new one is created on next access.
    # This can be useful for true isolation if tests might leave session in a bad state.
    _db.session.remove() # Ensure session is clean for the next test.
    
    # No need to manage connection or transaction on connection directly here,
    # as Flask-SQLAlchemy's scoped_session handles that. We are just managing
    # the outermost test transaction on that session.

@pytest.fixture
def fresh_db_session(app, _db):
    """
    This fixture provides a completely clean database for specific tests
    by dropping and recreating all tables. Use sparingly.
    """
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.create_all()
    return _db.session
