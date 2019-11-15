"Base document saver context classes."

import copy

import flask

from . import constants
from . import utils


class BaseSaver:
    "Base document saver context."

    DOCTYPE = None
    HIDDEN_FIELDS = []

    def __init__(self, doc=None):
        if doc is None:
            self.original = {}
            self.doc = {'_id': utils.get_iuid(),
                        'created': utils.get_time()}
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
        self.doc['doctype'] = self.DOCTYPE
        self.doc['modified'] = utils.get_time()
        flask.g.db.put(self.doc)
        self.add_log()

    def __getitem__(self, key):
        return self.doc[key]

    def __setitem__(self, key, value):
        self.doc[key] = value

    def initialize(self):
        "Initialize the new document."
        pass

    def prepare(self):
        "Preparations before making any changes."
        pass

    def finalize(self):
        "Final operations and checks on the document."
        pass

    def add_log(self):
        """Add a log entry recording the the difference betweens the current and
        the original document, hiding values of specified keys.
        'added': list of keys for items added in the current.
        'updated': dictionary of items updated; original values.
        'removed': dictionary of items removed; original values.
        """
        added = list(set(self.doc).difference(self.original or {}))
        updated = dict([(k, self.original[k])
                        for k in set(self.doc).intersection(self.original or {})
                        if self.doc[k] != self.original[k]])
        removed = dict([(k, self.original[k])
                        for k in set(self.original or {}).difference(self.doc)])
        for key in ['_id', '_rev', 'modified']:
            try:
                added.remove(key)
            except ValueError:
                pass
        updated.pop('_rev', None)
        updated.pop('modified', None)
        for key in self.HIDDEN_FIELDS:
            if key in updated:
                updated[key] = '***'
            if key in removed:
                removed[key] = '***'
        entry = {'_id': utils.get_iuid(),
                 'doctype': constants.DOCTYPE_LOG,
                 'docid': self.doc['_id'],
                 'added': added,
                 'updated': updated,
                 'removed': removed,
                 'timestamp': utils.get_time()}
        if hasattr(flask.g, 'current_user') and flask.g.current_user:
            entry['username'] = flask.g.current_user['username']
        else:
            entry['username'] = None
        if flask.has_request_context():
            entry['remote_addr'] = str(flask.request.remote_addr)
            entry['user_agent'] = str(flask.request.user_agent)
        else:
            entry['remote_addr'] = None
            entry['user_agent'] = None
        flask.g.db.put(entry)


class AttachmentsSaver(BaseSaver):
    "Document saver context handling attachments."

    def prepare(self):
        self._delete_attachments = set()
        self._add_attachments = []

    def finish(self):
        """Delete any specified attachments.
        Store the input files as attachments.
        Must be done after document is saved.
        """
        for filename in self._delete_attachments:
            rev = flask.g.db.delete_attachment(self.doc, filename)
            self.doc['_rev'] = rev
        for attachment in self._add_attachments:
            flask.g.db.put_attachment(self.doc,
                                      attachment['content'],
                                      filename=attachment['filename'],
                                      content_type=attachment['mimetype'])

    def add_attachment(self, filename, content, mimetype):
        self._add_attachments.append({'filename': filename,
                                      'content': content,
                                      'mimetype': mimetype})

    def delete_attachment(self, filename):
        self._delete_attachments.add(filename)
