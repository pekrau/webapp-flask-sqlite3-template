"Base entity saver context class."

import copy
import json
import os.path
import sys

import flask

from webapp import constants
from webapp import utils


class BaseSaver:
    "Base entity saver context."

    EXCLUDE_PATHS = [["modified"]]
    HIDDEN_VALUE_PATHS = []

    def __init__(self, doc=None):
        if doc is None:
            self.original = {}
            self.doc = {"iuid": utils.get_iuid(),
                        "created": utils.get_time()}
            self.initialize()
        else:
            self.original = copy.deepcopy(doc)
            self.doc = doc
        self.prepare()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        self.finalize()
        self.doc["modified"] = utils.get_time()
        self.upsert()
        self.add_log()

    def __getitem__(self, key):
        return self.doc[key]

    def __setitem__(self, key, value):
        self.doc[key] = value

    def initialize(self):
        "Initialize the new entity."
        pass

    def prepare(self):
        "Preparations before making any changes."
        pass

    def finalize(self):
        "Final operations and checks on the entity."
        pass

    def upsert(self):
        "Actually insert or update the entity in the database."
        raise NotImplementedError

    def add_log(self):
        """Add a log entry recording the the difference betweens the current
        and the original entity.
        """
        self.stack = []
        diff = self.diff(self.original, self.doc)
        entry = {"diff": diff,
                 "timestamp": utils.get_time()}
        values = [utils.get_iuid(),
                  self.doc["iuid"],
                  json.dumps(diff),
                  utils.get_time()]
        if hasattr(flask.g, "current_user") and flask.g.current_user:
            values.append(flask.g.current_user["username"])
        else:
            values.append(None)
        if flask.has_request_context():
            values.append(str(flask.request.remote_addr))
            values.append(str(flask.request.user_agent))
        else:
            values.append(None)
            values.append(os.path.basename(sys.argv[0]))
        with flask.g.db:
            flask.g.db.execute("INSERT INTO logs "
                               " ('iuid', 'docid', 'diff',"
                               "  'timestamp', 'username',"
                               " 'remote_addr', 'user_agent')"
                               " VALUES (?,?,?,?,?,?,?)", values)

    def diff(self, old, new):
        """Find the differences between the old and the new documents.
        Uses a fairly simple algorithm which is OK for shallow hierarchies.
        """
        added = {}
        removed = {}
        updated = {}
        new_keys = set(new.keys())
        old_keys = set(old.keys())
        for key in new_keys.difference(old_keys):
            self.stack.append(key)
            if self.stack not in self.EXCLUDE_PATHS:
                if self.stack in self.HIDDEN_VALUE_PATHS:
                    added[key] = "<hidden>"
                else:
                    added[key] = new[key]
            self.stack.pop()
        for key in old_keys.difference(new_keys):
            self.stack.append(key)
            if self.stack not in self.EXCLUDE_PATHS:
                if self.stack in self.HIDDEN_VALUE_PATHS:
                    removed[key] = "<hidden>"
                else:
                    removed[key] = old[key]
            self.stack.pop()
        for key in new_keys.intersection(old_keys):
            self.stack.append(key)
            if self.stack not in self.EXCLUDE_PATHS:
                new_value = new[key]
                old_value = old[key]
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    changes = self.diff(old_value, new_value)
                    if changes:
                        if self.stack in self.HIDDEN_VALUE_PATHS:
                            updated[key] = "<hidden>"
                        else:
                            updated[key] = changes
                elif new_value != old_value:
                    if self.stack in self.HIDDEN_VALUE_PATHS:
                        updated[key]= dict(new_value="<hidden>",
                                           old_value="<hidden>")
                    else:
                        updated[key]= dict(new_value= new_value,
                                           old_value=old_value)
            self.stack.pop()
        result = {}
        if added:
            result['added'] = added
        if removed:
            result['removed'] = removed
        if updated:
            result['updated'] = updated
        return result
