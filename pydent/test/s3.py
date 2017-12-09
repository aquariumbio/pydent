import aq

aq.login()

u = aq.Upload.find(15641)
print(u.temp_url)

file = open("testfile.jpg", 'bw+')
data = u.data
file.write(data)
file.close()
