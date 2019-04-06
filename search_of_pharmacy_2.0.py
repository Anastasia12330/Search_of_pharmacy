import sys, math
import requests
import pygame, os
from distance import lonlat_distance

# запрос к геокодеру формируется следующим образом:
toponym_to_find = " ".join(sys.argv[1:])

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
geocoder_params = {"geocode": toponym_to_find, "format": "json"}
response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    # обработка ошибочной ситуации
    print("Ошибка выполнения запроса:")
    print(geocoder_api_server)
    print("Http статус:", response.status_code, "(", response.reason, ")")

# Преобразуем ответ в json-объект
json_response = response.json()
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

# Собираем параметры для запроса к StaticMapsAPI:

search_api_server = "https://search-maps.yandex.ru/v1/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

address_ll = ",".join([toponym_longitude, toponym_lattitude])

search_params = {
    "apikey": api_key,
    "text": "аптека",
    "lang": "ru_RU",
    "ll": address_ll,
    "type": "biz",
}

response = requests.get(search_api_server, params=search_params)

# Преобразуем ответ в json-объект
json_response = response.json()
organization1 = json_response["features"]

minimum = 100000000
for i in range(len(organization1)):
    # Получаем первую найденную организацию.
    organization = json_response["features"][i]
    # Название организации.
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    # Адрес организации.
    org_address = organization["properties"]["CompanyMetaData"]["address"]
    point = organization["geometry"]["coordinates"]

    S = int(lonlat_distance([float(toponym_longitude), float(toponym_lattitude)], [float(point[0]), float(point[1])]))
    if minimum > S:
        minimum = S
        apothecary_address = org_address
        apothecary_name = org_name
        apothecary_time_open = \
            organization["properties"]["CompanyMetaData"]["Hours"]['Availabilities'][0]['Intervals'][0]['from']
        apothecary_time_close = \
            organization["properties"]["CompanyMetaData"]["Hours"]['Availabilities'][0]['Intervals'][0]['to']
        apothecary_org_point = "{0},{1}".format(point[0], point[1])
        S_apothecary = str(S)

# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    # Воспользуйтесь автоматическим позиционированием карты
    "l": "map",
    "pl": "{0},{1}".format(apothecary_org_point, address_ll),
    # добавим точку, чтобы указать найденную аптеку
    "pt": "{0},pm2dgl~{1},pm2dgl".format(apothecary_org_point, address_ll)
}

map_api_server = "http://static-maps.yandex.ru/1.x/"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)

# Запишем полученное изображение в файл.
map_file = "map.png"
try:
    with open(map_file, "wb") as file:
        file.write(response.content)
except IOError as ex:
    print("Ошибка записи временного файла:", ex)
    sys.exit(2)

# Инициализируем pygame
pygame.init()
screen = pygame.display.set_mode((600, 450))
# Рисуем картинку, загружаемую из только что созданного файла.
screen.blit(pygame.image.load(map_file), (0, 0))

intro_text = [apothecary_address,
              apothecary_name,
              apothecary_time_open + " - " + apothecary_time_close,
              "Расстояние :  " + S_apothecary]

font = pygame.font.Font(None, 30)
text_coord = 5
for line in intro_text:
    string_rendered = font.render(line, 1, pygame.Color('black'))
    intro_rect = string_rendered.get_rect()
    text_coord += 10
    intro_rect.top = text_coord
    intro_rect.x = 10
    text_coord += intro_rect.height
    screen.blit(string_rendered, intro_rect)

# Переключаем экран и ждем закрытия окна.
pygame.display.flip()
while pygame.event.wait().type != pygame.QUIT:
    pass
pygame.quit()

# Удаляем за собой файл с изображением.
os.remove(map_file)
