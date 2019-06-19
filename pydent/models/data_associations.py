"""
Models related to data associations
"""

import os
import shutil

import requests

from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.relationships import HasOne, JSON
from pydent.utils import make_async
from pydent.models.crud_mixin import JSONDeleteMixin, JSONSaveMixin
import json


class DataAssociatorMixin:
    """
    Mixin for handling data associations
    """

    def associate(self, key, value, upload=None):
        """
        Adds a data association with the key and value to this object.

        :param key: Key of the association
        :type key: str
        :param value: a json serializable object
        :type value: dict | str | int | float
        :param upload: optional file to upload
        :type upload: File
        :return: newly created data association
        :rtype: DataAssociation
        """
        """
        Adds a data association with the key and value to this object.
        """
        return self.session.utils.create_data_association(
            self, key, value, upload=upload
        )

    def associate_file(self, key, value, file, job_id=None):
        """
        Associate a file

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
        u.save()
        return self.associate(key, value, upload=u)

    def associate_file_from_path(self, key, value, filepath, job_id=None):
        """
        Associate a file from a filepath

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

    def get_data_associations(self, key):
        das = []
        for da in self.data_associations:
            if da.key == key:
                das.append(da)
        return das

    # TODO: DataAssociation - do we really want to have this return either a list or single value? How are people using this?
    def get(self, key):
        val = []
        for da in self.get_data_associations(key):
            val.append(da.value)
        if len(val) == 1:
            return val[0]
        elif len(val) == 0:
            return None
        return val


@add_schema
class DataAssociation(JSONDeleteMixin, ModelBase):
    """A DataAssociation model"""

    fields = dict(object=JSON(), upload=HasOne("Upload"))

    @property
    def value(self):
        return self.object.get(self.key, None)

    def __str__(self):
        return self._to_str("id", "object")


@add_schema
class Upload(ModelBase):
    """
    An Upload model
    """

    fields = dict(job=HasOne("Job"))

    def __init__(self, job_id=None, file=None):
        """
        Create a new upload

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
        http = self.session._AqSession__aqhttp
        return http.get("krill/uploads?job={}".format(self.job_id))["uploads"]

    def temp_url(self):
        data = self.session.Upload.where({"id": self.id}, methods=["expiring_url"])[
            0
        ].raw
        return data["expiring_url"]

    @staticmethod
    def _download_file_from_url(url, outpath):
        """
        Downloads a file from a url

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
        """
        Asynchronously downloads from list of :class:`Upload` models.

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
        """
        Downloads uploaded file from list of :class:`Upload` models.

        :param uploads: list of Uploads
        :type uploads: list
        :param outdir: path to output directory to save downloaded files (defaults to current directory)
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

    def download(self, outdir=None, filename=None, overwrite=True):
        """
        Downloads the uploaded file to the specified output directory. If
        no output directory is specified, the file will be downloaded to the
        current directory.

        :param outdir: path of directory of output file (default is current directory)
        :param outfile: filename of output file (defaults to upload_filename)
        :param overwrite: whether to overwrite file if it already exists
        :return: None
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
