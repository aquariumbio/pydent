from pydent import AqSession
import os


# TODO: write upload test
def test_upload():
    raise NotImplementedError("This test is not implemented. We need to write the upload test!")
    session = AqSession("vrana", "Mountain5", "http://52.27.43.242")
    here = os.path.dirname(os.path.abspath(__file__))
    p = session.Plan.find(18260)
    p.download_files(outdir=os.path.join(here, "temp"), overwrite=False)
    # from tqdm import tqdm
    # for da in tqdm(p.data_associations):
    #     if da.upload is not None:
    #         da.upload.download('temp')
    # u = session.Upload.find(24020)
    # print(u.download())
    # print(u)
    # print(u.job.uploads)

def test_get_upload_using_method():
    session = AqSession("vrana", "Mountain5", "http://52.27.43.242")

    u = session.Upload.find(25797)
    aqhttp = session._AqSession__aqhttp
    uploads = session.Upload.where({"id": u.id}, methods=["expiring_url"])
    print(uploads[0].temp_url())
    # print(uploads[0].expiring_url())