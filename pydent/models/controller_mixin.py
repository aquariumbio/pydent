from typing import Union


class ControllerMixin:
    def controller_method(
        self,
        controller_method: str,
        table: str,
        model_id: Union[str, int, None],
        data: Union[None, dict],
        params=None,
    ) -> dict:
        """Method for create, updating, and deleting models.

        :param controller_method: Name of the controller method
        :param table: Table name of model (e.g. 'samples' or 'data_associations')
        :param model_id: Optional model_id (not required for 'post')
        :param data: data
        :param params: controller parameters
        :return: json formatted server response
        :rtype: dict
        """

        if model_id:
            url = "{}/{}/{}".format(table, model_id, controller_method)
        else:
            url = "{}/{}".format(table, controller_method)

        result = self.aqhttp.request("post", url, json=data, params=params)
        return result
