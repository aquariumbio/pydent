from pydent.interfaces import SessionInterface, ModelInterfaceABC, CRUDInterface
from pydent.marshaller import ModelRegistry


class BrowserInterface(ModelInterfaceABC, SessionInterface):
    __slots__ = ["aqhttp", "session", "model", "__dict__"]
    MERGE = ["methods"]
    DEFAULT_OFFSET = -1
    DEFAULT_REVERSE = False
    DEFAULT_LIMIT = -1

    # TODO: browser should use standard session
    def __init__(self, model_name, aqhttp, session):
        super().__init__(aqhttp, session)
        self.crud = CRUDInterface(aqhttp, session)
        self.model = ModelRegistry.get_model(model_name)
        self._do_load = True

    @property
    def browser(self):
        return self.session.browser

    def find(self, id):
        return self.browser.find(id, model_class=self.model_name)

    def find_by_name(self, name):
        return self.bowser.find_by_name(name, model_class=self.model_name)

    def where(self, criteria, methods=None, opts=None):
        return self.browser.where(criteria, model_class=self.model_name, methods=methods, opts=opts)

    def one(self, query=None, first=False, opts=None):
        return self.browser.one(model_class=self.model_name, query=query, opts=opts)

    def first(self, num=1, query=None, opts=None):
        return self.browser.first(num, model_class=self.model_name, query=query)

    def last(self, num=1, query=None, opts=None):
        return self.browser.last(num, model_class=self.model_name, query=query)

    def new(self, *args, **kwargs):
        instance = self.model.__new__(self.model, *args, session=self.session, **kwargs)
        self.model.__init__(instance, *args, **kwargs)
        self.browser.update_cache([instance])
        return instance

    def all(self, opts=None):
        return self.browser.all(model_class=self.model_name, opts=opts)

    # TODO: load_from using new session
    def load(self, post_response):
        """
        Loads model instance(s) from data.
        Model instances will be of class defined by self.model.
        If data is a list, will return a list of model instances.
        """
        models = self.model.load_from(post_response, self.session)
        return models