import pickle

from peak.api import *
from peak.storage.files import EditableFile

from magot.model import *


class AccountDM(storage.EntityDM):

    defaultClass = DetailAccount

    filename = binding.Obtain(PropertyName('magot.accountfile'))
    file = binding.Make(lambda self: EditableFile(filename=self.filename))
   
    def root(self):
        text = self.file.text
        root = pickle.loads(text)
        return root
    root = binding.Make(root)

    def _load(self, oid, ob):
        return self.get(oid)

    def _new(self, ob):
        self._save(ob)
        return ob.name

    def _save(self, ob):
        pass

    def flush(self, ob=None):
        super(AccountDM, self).flush(ob)
        self.file.text = pickle.dumps(self.root)

    def get(self, oid, default=None):
        if oid in self.cache:
            return self.cache[oid]
        else:
            account = self._findAccount(oid, self.root)
            if account is None:
                raise exceptions.NameNotFound('Account ' +oid+' not found')
            self.register(account)
            self.cache[oid] = account
            return account
        
        return default
   
    def _findAccount(self, oid, parent):
        if isinstance(parent, SummaryAccount):
            for account in parent.subAccounts:
                if oid == account.name:
                    return account
            for account in parent.subAccounts:
                acc = self._findAccount(oid, account)
                if acc is not None:
                    return acc
    
    def abortTransaction(self, ob):
        self._delBinding("root")
        super(AccountDM, self).abortTransaction(ob)
