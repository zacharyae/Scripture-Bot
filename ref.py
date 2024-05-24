import json

text = ''

with open ('reference.txt', 'r+') as ref:
    text += ref.read()

with open("doctrine-and-covenants.json", "r") as f:
    data = json.load(f)


dataList = data["sections"]
for sections in dataList:
    for section in sections["verses"]:
        print(section["reference"])
        text += f'{section["reference"]}, '

with open ('reference.txt', 'w') as ref:
    ref.write(text)

    
            
            


  