class CreateMixin(object):

    def create(self):
        data = self._get_create_json()
        name = self.get_tableized_name()
        result = self.session.utils.create(name, data)
        self.reload(result)
        return self

    def _get_create_json(self):
        return self.dump()


class UpdateMixin(object):

    def update(self):
        data = self._get_create_json()
        name = self.get_tableized_name()
        result = self.session.utils.update(name, self.id, data)
        self.reload(result)
        return self

    def _get_update_json(self):
        return self.dump()


class SaveMixin(UpdateMixin, CreateMixin):

    def save(self):
        if self.id:
            self.update()
        else:
            self.create()


class DeleteMixin(object):

    def delete(self):
        pass
