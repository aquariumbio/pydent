class CreateMixin(object):

    def create(self):
        data = self._get_create_json()
        params = self._get_create_params()
        name = self.get_tableized_name()
        result = self.session.utils.model_create(name, data, params=params)
        self.reload(result)
        return self

    def _get_create_json(self):
        return self.dump()

    def _get_create_params(self):
        return None


class UpdateMixin(object):

    def update(self):
        data = self._get_create_json()
        params = self._get_update_params()
        name = self.get_tableized_name()
        result = self.session.utils.model_update(name, self.id, data, params=params)
        self.reload(result)
        return self

    def _get_update_json(self):
        return self.dump()

    def _get_update_params(self):
        return None


class SaveMixin(UpdateMixin, CreateMixin):

    def save(self):
        if self.id:
            self.update()
        else:
            self.create()


class DeleteMixin(object):

    def delete(self):
        name = self.get_tableized_name()
        params = self._get_delete_params()
        result = self.session.utils.model_delete(name, self.id, params=params)
        return result

    def _get_delete_params(self):
        return None