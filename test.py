import random
f=open("thiswillwork.txt",'ab')
data = [random.randint(0,100) for i in range(500)]
channel_count = 5
data_dump = []
threshold = (float(len(data))/2) - (float(len(data))/2)%channel_count

for i in range(int(threshold)):
    if i%channel_count == 0:
        row_data = str(data[i:i+channel_count])
        data_dump.append(row_data[1:-1])
s = "\n"
f.write(s.join(data_dump)+'\n')

data_dump = []
for i in range(int(threshold),len(data)):
    if i%channel_count == 0:
        row_data = str(data[i:i+channel_count])
        data_dump.append(row_data[1:-1])
s = "\n"
f.write(s.join(data_dump)+'\n')
data[int(threshold):len(data)]

f.close
print(data)
