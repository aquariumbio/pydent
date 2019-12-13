"""The create, read, update, destroy (CRUD) mixins used for some models."""
from retry import retry


class CreateMixin:
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


class UpdateFailed(Exception):
    pass


class UpdateMixin:
    @retry(UpdateFailed, tries=3, delay=0.1, backoff=0.25, max_delay=1.0)
    def update(self):
        data = self._get_create_json()
        params = self._get_update_params()
        name = self.get_tableized_name()
        result = self.session.utils.model_update(name, self.id, data, params=params)
        self.reload(result)
        if not self.id:
            raise UpdateFailed
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


class DeleteMixin:
    def delete(self):
        name = self.get_tableized_name()
        params = self._get_delete_params()
        result = self.session.utils.model_delete(name, self.id, params=params)
        return result

    def _get_delete_params(self):
        return None


class JSONSaveMixin:
    def save(self, do_reload=True):
        name = self.get_server_model_name()
        data = self._get_save_json()
        result = self.session.utils.json_save(name, data)
        if do_reload:
            self.reload(result)
        return result

    # TODO: add update to JSONMixin?
    # def update(self):
    #     self.save()

    def _get_save_json(self):
        return self.dump()


class JSONDeleteMixin:
    def delete(self):
        name = self.get_server_model_name()
        data = self._get_delete_json()
        return self.session.utils.json_delete(name, data)

    def _get_delete_json(self):
        return self.dump()
