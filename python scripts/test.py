import xmltodict

with open('test.xml') as f:
    xml = file.read()

data = xmltodict.parse(xml)