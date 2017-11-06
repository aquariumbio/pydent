from pydent import *

AqSession.create_from_config_file("secrets/config.json")

u = aq.Upload.find(1000)
print(u.temp_url)

file = open("testfile.jpg", 'bw+')
data = u.data
file.write(data)
file.close()
