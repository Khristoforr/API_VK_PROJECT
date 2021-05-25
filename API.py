import requests
import json
import time
import os
YA_DISK_TOKEN = ''
VK_TOKEN = ""

def menu():
    print("МЕНЮ")
    print("Список доступных команд:")
    print('d - скачать фотографии пользователя на Я.Диск')
    print('j - скомпилировать json файл')
    print('c - ввести нового пользователя')
    print('exit - выйти из программы')
    user = VKuser(input('Введите id пользователя: '))
    print(user.represent())
    choise = 0
    while choise != exit:
        choise = input('Введите необходимую команду: ').lower()
        if choise == 'd':
            user.upload_on_ya_disk()
        elif choise == 'j':
            user.create_json()
        elif choise == 'c':
            user = VKuser(input('Введите id нового пользователя: '))
        elif choise == 'exit':
            print("Выход из программы...")
            break
        else:
            print("Попробуйте еще раз")

class VKuser:
    def __init__(self, vk_id):
        self.vk_id = vk_id

    # функция для презентации пользователя
    def represent(self):
        url = 'https://api.vk.com/method/users.get'
        params = {
            'user_id': self.vk_id,
            'access_token': VK_TOKEN,
            'v': '5.130',
        }
        response = requests.get(url, params=params).json()
        name = f"Имя: {response['response'][0]['first_name']}\nФамилия: {response['response'][0]['last_name']}"
        return name

    # основная функция, выполняющая запрос API VK
    def make_a_responce(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': self.vk_id,
            'access_token': VK_TOKEN,
            'v': '5.130',
            'album_id': 'profile',
            'photo_sizes': '1',
            'extended': '1'
            }
        response = requests.get(url, params=params).json()
        return response

    # функция для авторизации на Я.Диске
    def get_headers_ya_disk(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {YA_DISK_TOKEN}'}

    # функция для создания папки на Я.Диске с названием - id пользователя
    def create_folder(self):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path' : f'/{self.vk_id}'}
        response = requests.put(url,params=params, headers=self.get_headers_ya_disk())
        if response.status_code == 201:
            print (f"Папка с фото пользователя {self.vk_id} создана успешно")
        else:
            print("Ошибка создания папки, возможно, папка с таким именем уже существует")

    # функция для создания json файла
    def create_json(self):
        list1 = []
        response = self.make_a_responce()
        total_profile_photos = len(response['response']['items'])
        for photo in range(total_profile_photos):
            time.sleep(1)
            list1.append(dict(size=response['response']['items'][photo]['sizes'][self.get_max_size(photo)]['type'],
                              file_name=str(response['response']['items'][photo]['likes']['count'])+'.jpg'))
        file_path = os.path.join(os.getcwd(), f'id{self.vk_id}.json')
        with open(file_path,'w') as f:
            json.dump(list1,f)
        print('JSON файл создан')

    # функция для определения URL фото с максимальным разрешением
    def get_max_size(self, photo):
        list_of_sizes = []
        response = self.make_a_responce()
        time.sleep(0.1)
        total = len(response['response']['items'][photo]['sizes'])
        for i in range(total):
            height = response['response']['items'][photo]['sizes'][i]['height']
            width = response['response']['items'][photo]['sizes'][i]['width']
            list_of_sizes.append(height * width)
        # добавим проверку, т.к. на некоторых фото запрос возвращает все значения height и width равными 0
        if 0 in list_of_sizes:
            return -1
        else:
            return list_of_sizes.index(max(list_of_sizes))

    # функция, для получения ссылок на фото в профиле пользователя ВК
    def get_profile_photos_url(self):
        photos_url = []
        likes_per_photo = []
        date_upload = []
        response = self.make_a_responce()
        total_profile_photos = len(response['response']['items'])
        time.sleep(0.1)
        for photo in range(total_profile_photos):
            # для получения ссылки на фото в максимальном разрешении воспользуемся функцией get_max_size
            photos_url.append(response['response']['items'][photo]['sizes'][self.get_max_size(photo)]['url'])
            likes_per_photo.append(response['response']['items'][photo]['likes']['count'])
            date_upload.append(response['response']['items'][photo]['date'])
        # функция возращает список кортежей с URL, кол-вом лайков, и датой загрузки фото
        return list(zip(photos_url,likes_per_photo,date_upload))

    # функция для залива фото на Я.Диск
    def upload_on_ya_disk(self):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        # создадим список для проверки фотографии на одинаковое кол-во лайков
        list_of_likes = []
        self.create_folder()
        # проитерируемся по всему списку фото, полученному из функции get_profile_photos
        for photo in range(len(self.get_profile_photos_url())):
            # проверка на кол-во лайков для выбора названия фото на Я.Диске
            if self.get_profile_photos_url()[photo][1] in list_of_likes:
                # слэш приходится менять на точку для того, чтобы имя файла было допустимым
                print(time.strftime("%D", (time.localtime(self.get_profile_photos_url()[photo][2]))).replace("/","."))
                # параметры, если кол-во лайков совпадает
                params = {'url': f'{self.get_profile_photos_url()[photo][0]}',
                          'path': f'/{self.vk_id}/{time.strftime("%D", (time.localtime(self.get_profile_photos_url()[photo][2]))).replace("/",".")}.jpeg'}
                list_of_likes.append(self.get_profile_photos_url()[photo][1])
            else:
                # параметры, если кол-во лайков не совпадает
                params = {'url' : f'{self.get_profile_photos_url()[photo][0]}',
                          'path': f'/{self.vk_id}/{self.get_profile_photos_url()[photo][1]}.jpeg'}
                list_of_likes.append(self.get_profile_photos_url()[photo][1])
            print(f"Идет загрузка фотографии {photo + 1} с количеством лайков "
                  f"{self.get_profile_photos_url()[photo][1]}...")
            response = requests.post(upload_url, params=params, headers = self.get_headers_ya_disk())
            if response.status_code == 202:
                print("Загрузка выполнена успешно.")
                print()
            else:
                print("Ошибка")
                print()

menu()