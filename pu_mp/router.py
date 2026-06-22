"""
PU-Connect Database Router

global.db  (default)  — all data
  All apps route to the default database.
  chat_app was previously routed to user_db but cross-database FK/M2M
  (Conversation → Listing, participants → User) made queries fail silently.

user.db    (user_db)  — unused, kept for backwards compat with entrypoint migrations
"""


class PURouter:

    def db_for_read(self, model, **hints):
        return 'default'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'
