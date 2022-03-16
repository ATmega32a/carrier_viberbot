from datetime import datetime
from pathlib import Path

from django.db import models

from carrier_viberbot.settings import MEDIA_ROOT
from customer.models import Subscriber


class Order(models.Model):
    order_id = models.CharField("id заказа", max_length=10, default="")
    owner = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Клиент")
    service = models.CharField("Сервис", max_length=100, default="")
    tariff = models.CharField("Тариф", max_length=300, default="")
    from_location = models.CharField("Откуда", max_length=300, default="")
    to_location = models.CharField("Куда", max_length=300, default="")
    order_cost = models.IntegerField("Стоимость заказа, руб. ", default=0)
    comment = models.CharField("Комментарий", max_length=300, default="")
    ord_success = models.BooleanField("Заказ принят водителем", default=False)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class Questionnaire(models.Model):
    applicant = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Соискатель")
    city = models.CharField("Город", max_length=100, default="")
    name = models.CharField("Имя и фамилия", max_length=100, default="")
    phone = models.CharField("Номер телефона", max_length=50, default="")
    car_number = models.CharField("Госномер", max_length=20, default="")
    car_model = models.CharField("Марка и модель", max_length=50, default="")
    number_of_seats = models.CharField("Кол-во посадочных мест", max_length=50, default="")
    car_year_made = models.CharField("Год выпуска", max_length=20, default="")
    car_type = models.CharField("Тип кузова", max_length=50, default="")
    car_color = models.CharField("Тип кузова", max_length=50, default="")

    class Meta:
        verbose_name = "Анкета"
        verbose_name_plural = "Анкеты"


class LicensingQuestionnaire(models.Model):
    applicant = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Водитель")
    name = models.CharField("Имя", max_length=100, default="")
    surname = models.CharField("Фамилия", max_length=100, default="")
    phone = models.CharField("Номер телефона", max_length=50, default="")
    car_number = models.CharField("Госномер", max_length=20, default="")
    car_brand = models.CharField("Марка автомобиля", max_length=50, default="")
    car_model = models.CharField("Модель автомобиля", max_length=50, default="")
    # photo_passport_first = models.ImageField("Первая страница паспорта", default="Нет фото первой страницы паспорта")
    # photo_passport_reg = models.ImageField("Прописка", default="Нет фото прописки")
    # photo_sts_front_side = models.ImageField("СТС передняя сторона", default="Нет фото передней стороны СТС",)
    # photo_sts_back_side = models.ImageField("СТС задняя сторона", default="Нет фото задней стороны СТС")
    photo_passport_first_path = models.CharField("Первая страница паспорта", max_length=512,
                                                 default=str(Path(MEDIA_ROOT)) + "\\no_photo.png")
    photo_passport_reg_path = models.CharField("Прописка", max_length=512,
                                               default=str(Path(MEDIA_ROOT)) + "\\no_file.jpg")
    photo_sts_front_side_path = models.CharField("СТС передняя сторона", max_length=512,
                                                 default=str(Path(MEDIA_ROOT)) + "\\no_photo.png", )
    photo_sts_back_side_path = models.CharField("СТС задняя сторона", max_length=512,
                                                default=str(Path(MEDIA_ROOT)) + "\\no_photo.png")

    license_number = models.CharField("Номер лицензии", max_length=30, default="Номер лицензии не указан")

    # def image_passport_first(self):
    #     if self.photo_passport_first:
    #         from django.utils.safestring import mark_safe
    #         return mark_safe("<img src = "%s" width="30"/>" % self.photo_passport_first)
    #     else:
    #         return "Нет фото 1-й стр. паспорта"
    #
    # def image_passport_reg(self):
    #     if self.photo_passport_reg:
    #         from django.utils.safestring import mark_safe
    #         return mark_safe("<img src = "%s" width="30"/>" % self.photo_passport_reg)
    #     else:
    #         return "Нет фото паспорта (прописки)"
    #
    # def image_sts_front_side(self):
    #     if self.photo_sts_front_side:
    #         from django.utils.safestring import mark_safe
    #         return mark_safe("<img src = "%s" width="30"/>" % self.photo_sts_front_side)
    #     else:
    #         return "Нет фото передней стороны СТС"
    #
    # def image_sts_back_side(self):
    #     if self.photo_sts_back_side:
    #         from django.utils.safestring import mark_safe
    #         return mark_safe("<img src = "%s" width="30"/>" % self.photo_sts_back_side)
    #     else:
    #         return "Нет фото задней стороны СТС"
    #
    # image_passport_first.short_description = "Первая страница паспорта"
    # image_passport_first.allow_tags = True
    # image_passport_reg.short_description = "Паспорт (прописка)"
    # image_passport_reg.allow_tags = True
    # image_sts_front_side.short_description = "СТС передняя сторона"
    # image_sts_front_side.allow_tags = True
    # image_sts_back_side.short_description = "СТС задняя сторона"
    # image_sts_back_side.allow_tags = True

    class Meta:
        verbose_name = "Анкета лицензирования"
        verbose_name_plural = "Анкеты лицензирования"


class WaybillEntry(models.Model):
    applicant = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Заявитель")
    number = models.PositiveIntegerField("Номер путевого листа", default=0)
    id_client = models.PositiveIntegerField("Гаражный номер", default=0)
    surname = models.CharField("Фамилия", max_length=50, default="")  # Фамилия водителя
    name = models.CharField("Имя", max_length=50, default="")  # Имя водителя
    patronymic = models.CharField("Отчество", max_length=50, default="")  # Отчество водителя
    ser_doc = models.CharField("Серия удостоверения", max_length=10, default="")  # Серия удостоверения
    num_doc = models.CharField("Номер удостоверения", max_length=10, default="")  # Номер удостоверения
    kod_org_doc = models.CharField("Класс ТС", max_length=2, default="")  # Класс ТС A,B,C ...
    tr_reg_num = models.CharField("Гос. номер ТС", max_length=12, default="")  # Гос. номер ТС
    tr_mark = models.CharField("Марка ТС", max_length=50, default="")  # Марка ТС
    odometer_value = models.CharField("Показание одометра при выезде", max_length=8, default="")  # Показание одометра
    time_zone = models.CharField("Часовой пояс", max_length=2, default="3")
    date = models.CharField("Дата выезда", max_length=10, default="")
    time = models.CharField("Время выезда", max_length=5, default="")

    class Meta:
        verbose_name = "Регистрационные данные для путёвки"
        verbose_name_plural = "Регистрационные данные для путёвок"


class WaybillNote(models.Model):
    applicant = models.CharField("Заявитель", max_length=30, default="")
    number = models.PositiveIntegerField("Номер путевого листа", default=0)
    id_client = models.PositiveIntegerField("Гаражный номер", default=0)
    surname = models.CharField("Фамилия", max_length=50, default="")  # Фамилия водителя
    name = models.CharField("Имя", max_length=50, default="")  # Имя водителя
    patronymic = models.CharField("Отчество", max_length=50, default="")  # Отчество водителя
    ser_doc = models.CharField("Серия удостоверения", max_length=10, default="")  # Серия удостоверения
    num_doc = models.CharField("Номер удостоверения", max_length=10, default="")  # Номер удостоверения
    kod_org_doc = models.CharField("Класс ТС", max_length=2, default="")  # Класс ТС A,B,C ...
    tr_reg_num = models.CharField("Гос. номер ТС", max_length=12, default="")  # Гос. номер ТС
    tr_mark = models.CharField("Марка ТС", max_length=50, default="")  # Марка ТС
    odometer_value = models.CharField("Показание одометра при выезде", max_length=8, default="")  # Показание одометра
    date = models.CharField("Дата выезда", max_length=10, default="")
    time = models.CharField("Время выезда", max_length=5, default="")
    time_zone = models.CharField("Часовой пояс", max_length=2, default="3")
    arrival_time = models.CharField("Время возвращения", max_length=5, default="", blank=True)
    start_tech_state = models.CharField("Тех.состояние ТС и прицепа в момент выезда", max_length=10,
                                        default="Исправен", blank=True)
    finish_tech_state = models.CharField("Тех.состояние ТС и прицепа по возвращению", max_length=10,
                                         default="", blank=True)
    final_odometer_value = models.CharField("Показание одометра при возвращении", max_length=8,
                                            default="", blank=True)  # Показание одометра
    fuel_residue = models.CharField("Остаток горючего", max_length=3, default="", blank=True)
    special_marks = models.CharField("Особые отметки", max_length=50, default="", blank=True)
    mechanic_signature = models.CharField("Подпись механика", max_length=25, default="", blank=True)
    driver_signature = models.CharField("Подпись водителя", max_length=25, default="", blank=True)

    def fio_driver(self):
        return str(self.surname) + " " + str(self.name[:1]) + "." + str(self.patronymic[:1]) + "."

    def __str__(self):
        return self.applicant

    def dep_time(self):
        return str(self.time)

    class Meta:
        verbose_name = "Запись в журнале"
        verbose_name_plural = "Записи в журнале"


class WaybillJournal(models.Model):
    journal_counter = models.PositiveIntegerField("Количество путевых листов", default=0)

    class Meta:
        verbose_name = "Регистрация путевого листа"
        verbose_name_plural = "Регистрации путевых листов"


class Car(models.Model):
    car_owner = models.ForeignKey(Subscriber, verbose_name='Владелец автомобиля', on_delete=models.CASCADE)
    car_brand = models.CharField(max_length=50, default='Модель не указана')
    car_model = models.CharField(max_length=50, default='Модель не указана')
    car_number = models.CharField(max_length=50, default='Номер не указан')

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"
