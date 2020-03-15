"""Models related to data associations."""
import json
import os
import shutil
from typing import Union

import requests

from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.models.crud_mixin import JSONDeleteMixin
from pydent.models.crud_mixin import JSONSaveMixin
from pydent.relationships import HasOne
from pydent.relationships import JSON
from pydent.utils import make_async


# TODO: changing the value of a association (and saving it) shouldn't be difficult
class DataAssociatorMixin:
    """Mixin for handling data associations."""

    def _make_association(self, key, value, parent, upload=None):
        association = self.session.DataAssociation.new(
            object=json.dumps({key: value}),
            upload=upload,
            key=key,
            parent_id=parent.id,
            parent_class=parent.__class__.__name__,
        )
        association.parent = parent
        return association

    def associate(self, key, value, upload=None, create_new=False, save=None):
        """Adds a data association with the key and value to this object.

        :param key: Key of the association
        :type key: str
        :param value: a json serializable object
        :type value: dict | str | int | float
        :param upload: optional file to upload
        :type upload: File
        :param create_new: if True (default) will create a new association instead
            of updating the existing association.
        :tuype create_new: bool
        :return: newly created or updated data association
        :rtype: DataAssociation
        """
        if save is None:
            if self.id is None:
                save = False
            else:
                save = True
        if create_new:
            association = None
        else:
            association = self.get_data_association(key)

        if not association:
            if save:
                return self.session.utils.create_data_association(
                    self, key, value, upload=upload
                )
            else:
                association = self._make_association(key, value, self, upload)
                self.append_to_many("data_associations", association)
                return association
        else:
            association.value = value
            association.upload = upload
            association.parent_class = self.__class__.__name__
            association.parent_id = self.id
            association.parent = self
            if save:
                self._try_update_data_association(association)
            return association

    def delete_data_associations(self, key):
        associations = self.get_data_associations(key)
        for a in associations:
            if a.id:
                a.delete()
            self.data_associations.remove(a)

    def _try_update_data_association(self, association):
        upload = association.upload
        if upload and upload.id:
            association.upload_id = upload.id
        if self.id:
            if association.upload and not association.upload.id:
                association.upload.save()
                association.upload_id = association.upload.id
            association.save()
        return association

        # return self.session.utils.create_data_association(
        #     self, key, value, upload=upload
        # )
        # if unique_key:
        #     existing_associations = self.get_data_associations(key)
        #     for association in existing_associations:
        #         association.value = value
        #         association.upload = upload
        #         association.upload_id = upload.id
        #         association.save()
        # else:
        #     self.session.utils.create_data_association(
        #         self, key, value, upload=upload
        #     )

    # def save_data_associations(self):
    #     if self.is_deserialized('data_associations'):
    #

    def associate_file(self, key, value, file, job_id=None):
        """Associate a file.

        :param key: association key
        :type key: str or json
        :param value: association value
        :type value: str or json
        :param file: file to create :class:`Upload`
        :type file: file object
        :param job_id: optional job_id to associate the :class:`Upload`
        :type job_id: int
        :return: new data association
        :rtype: :class:`DataAssociation`
        """
        u = self.session.Upload.new(job_id=job_id, file=file)
        return self.associate(key, value, upload=u)

    def associate_file_from_path(self, key, value, filepath, job_id=None):
        """Associate a file from a filepath.

        :param key: association key
        :type key: str or json
        :param value: association value
        :type value: str or json
        :param filepath: path to file to create :class:`Upload`
        :type filepath: str
        :param job_id: optional job_id to associate the :class:`Upload`
        :type job_id: int
        :return: new data association
        :rtype: :class:`DataAssociation`
        """
        with open(filepath, "rb") as f:
            return self.associate_file(key, value, f, job_id=job_id)

    def get_data_association(self, key: Union[None, str]):
        das = self.get_data_associations(key)
        if das:
            return das[0]

    def get_data_associations(self, key: Union[None, str]):
        das = []
        if self.data_associations:
            for da in self.data_associations:
                if da.key == key:
                    das.append(da)
        return das

    # TODO: DataAssociation - do we really want to have this return either a list or
    #       single value? How are people using this?
    def get(self, key):
        val = []
        for da in self.get_data_associations(key):
            val.append(da.value)
        if len(val) == 1:
            return val[0]
        elif len(val) == 0:
            return None
        return val


class DataAssociationSaveContext:
    def __init__(self, model: DataAssociatorMixin):
        self.model = model
        self.data_associations = []

    def __enter__(self):
        if self.model.is_deserialized("data_associations"):
            self.data_associations = self.model.data_associations

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return
        for da in self.data_associations:
            da.parent_id = self.model.id
            self.model._try_update_data_association(da)
            assert da.id
        self.model.data_associations = self.data_associations


@add_schema
class DataAssociation(JSONDeleteMixin, JSONSaveMixin, ModelBase):
    """A DataAssociation model."""

    fields = dict(object=JSON(), upload=HasOne("Upload"))

    @property
    def value(self):
        return self.object.get(self.key, None)

    @value.setter
    def value(self, new_value):
        self.object = {self.key: new_value}

    # def save(self):
    #     if self.upload and not self.upload_id:
    #         self.upload.save()
    #         self.upload_id = self.upload_id
    #     super().save()
    #
    #     data_association = self.parent.session.DataAssociation.find(self.id)
    #     if data_association.id not in [da.id for da in self.parent.data_associations]:
    #         self.parent.data_associations.append(data_association)
    #         return data_association
    #     else:
    #         for da in self.parent.data_associations:
    #             if da.id == data_association.id:
    #                 return da

    def save(self):
        if self.parent_id is None:
            raise ValueError("Cannot save DataAssociation. `parent_id` cannot be None")
        if self.parent_class is None:
            raise ValueError(
                "Cannot save DataAssociation. `parent_class` cannot be None"
            )
        super().save(do_reload=True)

    def __str__(self):
        return self._to_str("id", "object")


@add_schema
class Upload(ModelBase):
    """An Upload model."""

    fields = dict(job=HasOne("Job"))

    def __init__(self, job_id=None, file=None):
        """Create a new upload.

        :param job_id: job id to associate the upload to
        :type job_id: int
        :param file: file to upload
        :type file: file object
        """
        super().__init__(job_id=job_id)
        self.file = file

    query_hook = dict(methods=["size", "name", "job"])

    # def _get_uploads_from_job_id(self, job_id):

    def _get_uploads_from_job(self):
        http = self.session._http
        return http.get("krill/uploads?job={}".format(self.job_id))["uploads"]

    def temp_url(self):
        data = self.session.Upload.where({"id": self.id}, methods=["expiring_url"])[
            0
        ].raw
        return data["expiring_url"]

    @staticmethod
    def _download_file_from_url(url, outpath):
        """Downloads a file from a url.

        :param url: url of file
        :type url: str
        :param outpath: filepath of out file
        :type outpath: str
        :return: http response
        :rtype: str
        """
        response = requests.get(url, stream=True)
        with open(outpath, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return response.raw

    @staticmethod
    @make_async(1)
    def async_download(uploads, outdir=None, overwrite=True):
        """Asynchronously downloads from list of :class:`Upload` models.

        :param uploads: list of Uploads
        :type uploads: list
        :param outdir: path to output directory to save downloaded files
        :type outdir: str
        :param overwrite: if True, will overwrite existing files
        :type overwrite: bool
        :return: list of filepaths
        :rtype: list
        """
        return Upload._download_files(uploads, outdir, overwrite)

    @staticmethod
    def _download_files(uploads, outdir, overwrite):
        """Downloads uploaded file from list of :class:`Upload` models.

        :param uploads: list of Uploads
        :type uploads: list
        :param outdir: path to output directory to save downloaded files (defaults to
            current directory)
        :type outdir: str
        :param overwrite: if True, will overwrite existing files (default: True)
        :type overwrite: bool
        :return: list of filepaths
        :rtype: list
        """
        filepaths = []
        for upload in uploads:
            filepath = upload.download(outdir=outdir, overwrite=overwrite)
            filepaths.append(filepath)
        return filepaths

    def fetch(self, outdir: str = None, filename: str = None, overwrite: bool = True):
        """Alias for `download`

        :param outdir: path of directory of output file (default is current directory)
        :param outfile: filename of output file (defaults to upload_filename)
        :param overwrite: whether to overwrite file if it already exists
        :return: filepath of the downloaded file
        """
        return self.download(outdir=outdir, filename=filename, overwrite=overwrite)

    def download(
        self, outdir: str = None, filename: str = None, overwrite: bool = True
    ):
        """Downloads the uploaded file to the specified output directory. If no
        output directory is specified, the file will be downloaded to the
        current directory.

        :param outdir: path of directory of output file (default is current directory)
        :param outfile: filename of output file (defaults to upload_filename)
        :param overwrite: whether to overwrite file if it already exists
        :return: filepath of the downloaded file
        """
        if outdir is None:
            outdir = "."
        if filename is None:
            filename = "{}_{}".format(self.id, self.upload_file_name)
        filepath = os.path.join(outdir, filename)
        if not os.path.exists(filepath) or overwrite:
            self._download_file_from_url(self.temp_url(), filepath)
        return filepath

    @property
    def data(self):
        """Return the data associated with the upload."""
        result = requests.get(self.temp_url())
        return result.content

    def create(self):
        """Save the upload to the server."""
        return self.session.utils.create_upload(self)

    def save(self):
        return self.create()
