import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Thread

import requests

from viberbot.api.messages import TextMessage, KeyboardMessage

import order
from botviber.bot_config import viber
from botviber.buttons.buttons import choice_service, info, from_address, to_address, get_phone, \
    comment, order_kb, return_to_menu_rich, job_application_form, choice_evacuator_tariff, choice_cargo_tariff, \
    cancel_order_or_menu_rich, order_buttons, take_order_or_not_rich, driver_arrival_interval, \
    accept_the_order_or_cancel_kb, to_menu_rich, after_take_driver_kb, call_or_cancel_kb, arrival_or_cancel_kb, \
    after_accept_arrival_kb, start_trip_or_cancel_kb, finish_trip_kb, call_or_cancel_in_arrival_moment_kb, \
    show_all_orders_or_less_remote_locations_kb, driver_location_kb, balance_kb, license_form, choice_region_kb, \
    send_request_or_come_back, get_phone_for_letter, waybill_form, return_waybill_document, \
    download_waybill_or_edit_kb, is_exists_waybill_buttons, back_or_main_menu, access_denied, payment_for_services, \
    test_kb, cars, my_cars, list_of_cars, create_car_form
from botviber.models import QuestionnaireButtons, ConditionsForRegions, WaybillQuestionnaireButtons, \
    LicensingQuestionnaireButtons, CarQuestionnaireButtons
from carrier_viberbot.cancel_order import cancel
from carrier_viberbot.osm import get_address, coordinates_from_address
from carrier_viberbot.send_email import send_email
from carrier_viberbot.send_order import send_order
from carrier_viberbot.get_distance import distance
from carrier_viberbot.settings import MEDIA_ROOT, MEDIA_URL
from carrier_viberbot.waybill import render_pdf_template
from customer.models import Subscriber
from order.models import Questionnaire, Order, LicensingQuestionnaire, WaybillEntry, WaybillJournal, WaybillNote, Car
from properties import server_url

services = {"4": "evacuator", "5": "cargo"}
tariffs = {"4": "Эвакуатор до 2000 кг.", "5": "Эвакуатор до 3000 кг.", "6": "Эвакуатор до 3500 кг.",
           "7": "Эвакуатор до 4000 кг.", "8": "Грузовой 1,5т"}
names_for_files = {"6": "passport_first_page", "7": "passport_registration", "8": "sts_front_side",
                   "9": "sts_back_side"}
local_storage = {}

time_zones = {
    -12: "в формате UTC-12",
    -11: "на Паго-Паго",
    -10: "на Гаваях",
    -9: "на Аляске",
    -8: "в США и Канаде (Тихоокеанское время)",
    -7: "в США и Канаде (Горное время)",
    -6: "в США и Канаде (Центральное время)",
    -5: "в США и Канаде (Восточное время)",
    -4: "в Каракасе",
    -3: "в Сальвадоре",
    -2: "в формате UTC-02",
    -1: "в Кабо-Верде",
    0: "в Лондоне",
    1: "в Париже",
    2: "в Калининграде",
    3: "в Москве",
    4: "в Самаре",
    5: "в Екатеринбурге",
    6: "в Омске",
    7: "в Красноярске",
    8: "в Иркутске",
    9: "в Якутске",
    10: "во Владивостоке",
    11: "в Магадане",
    12: "на Камчатке",
    13: "на островах Феникс",
    14: "на островах Лайн",
}


def get_files(path):
    files = []

    directory = os.listdir(path)
    directory.sort(reverse=True)

    for file in directory:
        if file.startswith('Путевой лист'):
            files.append(file)
    return files


def remove_old_files(path):
    max_files = 5
    files = get_files(path)
    if len(files) < max_files:
        return
    i = 0
    for f in files:
        i += 1
        if i > max_files:
            os.remove(os.path.join(path, f))


def is_exists_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not Questionnaire.objects.filter(applicant=s).exists():
        Questionnaire.objects.create(applicant=s)


def is_exists_car(vid):
    s = Subscriber.objects.get(user=vid)
    if not Car.objects.filter(car_owner=s).exists():
        print("Re")
        # Car.objects.create(car_brand="", car_model="", car_number="new")
        # car = Car.objects.get()


def is_exists_licensing_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not LicensingQuestionnaire.objects.filter(applicant=s).exists():
        LicensingQuestionnaire.objects.create(applicant=s)


def is_exists_waybill_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not WaybillEntry.objects.filter(applicant=s).exists():
        WaybillEntry.objects.create(applicant=s, phone=s.phone)


def set_answer(vid, data, item):
    is_exists_questionnaire(vid)
    s = Subscriber.objects.get(user=vid)
    questionnaire = Questionnaire.objects.get(applicant=s)
    if item == "0":
        questionnaire.city = data
        questionnaire.save()
    elif item == "1":
        questionnaire.name = data
        questionnaire.save()
    elif item == "2":
        questionnaire.phone = data
        questionnaire.save()
    elif item == "3":
        questionnaire.car_number = data
        questionnaire.save()
    elif item == "4":
        questionnaire.car_model = data
        questionnaire.save()
    elif item == "5":
        questionnaire.number_of_seats = data
        questionnaire.save()
    elif item == "6":
        questionnaire.car_year_made = data
        questionnaire.save()
    elif item == "7":
        questionnaire.car_type = data
        questionnaire.save()
    elif item == "8":
        questionnaire.car_color = data
        questionnaire.save()


def set_answer_licensing_question(vid, data, item):
    is_exists_licensing_questionnaire(vid)
    s = Subscriber.objects.get(user=vid)
    licensing_questionnaire = LicensingQuestionnaire.objects.get(applicant=s)
    is_exists_car(vid)
    car = Car.objects.get(car_owner=s)
    if item == "0":
        licensing_questionnaire.name = data
        licensing_questionnaire.save()
    elif item == "1":
        licensing_questionnaire.surname = data
        licensing_questionnaire.save()
    elif item == "2":
        licensing_questionnaire.phone = data
        licensing_questionnaire.save()
    elif item == "3":
        licensing_questionnaire.car_number = data
        licensing_questionnaire.save()
        car.car_number = data
        car.save()
    elif item == "4":
        licensing_questionnaire.car_brand = data
        licensing_questionnaire.save()
        car.car_brand = data
        car.save()
    elif item == "5":
        licensing_questionnaire.car_model = data
        licensing_questionnaire.save()
        car.car_model = data
        car.save()
    elif item == "6":
        licensing_questionnaire.photo_passport_first_path = str(data)
        licensing_questionnaire.save()
    elif item == "7":
        licensing_questionnaire.photo_passport_reg_path = str(data)
        licensing_questionnaire.save()
    elif item == "8":
        licensing_questionnaire.photo_sts_front_side_path = str(data)
        licensing_questionnaire.save()
    elif item == "9":
        licensing_questionnaire.photo_sts_back_side_path = str(data)
        licensing_questionnaire.save()


def set_answer_waybill_question(vid, data, item):
    is_exists_waybill_questionnaire(vid)
    subscriber = Subscriber.objects.get(user=vid)
    waybill_questionnaire = WaybillEntry.objects.get(applicant=subscriber)
    if item == "0":
        waybill_questionnaire.surname = data
        waybill_questionnaire.save()
    elif item == "1":
        waybill_questionnaire.name = data
        waybill_questionnaire.save()
    elif item == "2":
        waybill_questionnaire.patronymic = data
        waybill_questionnaire.save()
    elif item == "3":
        waybill_questionnaire.ser_doc = data
        waybill_questionnaire.save()
    elif item == "4":
        waybill_questionnaire.num_doc = data
        waybill_questionnaire.save()
    elif item == "5":
        waybill_questionnaire.num_lic = data
        waybill_questionnaire.save()
    elif item == "6":
        waybill_questionnaire.kod_org_doc = data
        waybill_questionnaire.save()
    elif item == "7":
        waybill_questionnaire.tr_reg_num = data
        waybill_questionnaire.save()
    elif item == "8":
        waybill_questionnaire.tr_mark = data
        waybill_questionnaire.save()
    elif item == "9":
        waybill_questionnaire.tr_model = data
        waybill_questionnaire.save()
    elif item == "10":
        waybill_questionnaire.odometer_value = data
        waybill_questionnaire.save()
    elif item == "11":
        if validate_time_format(data):
            time_zone = set_tz(data)
            waybill_questionnaire.time_zone = time_zone
            waybill_questionnaire.save()
            tz = int(time_zone)
            sign = '+' if tz >= 0 else ''
            try:
                text = "Ваше время соответствует времени " + time_zones[tz] + ". Ваш часовой пояс - UTC" + sign + \
                       str(waybill_questionnaire.time_zone) + "."
                viber.send_messages(vid, [TextMessage(text=text, min_api_version=6)])
            except KeyError:
                text = "Вы, вероятно, ошиблись при вводе времени! Пожалуйста, напишите время в формате Часы-Минуты, " \
                       "например: 12-45"
                return "retry_10_" + text
        else:
            text = "Ваш ввод не соответствует формату времени, пожалуйста, напишите время в формате Часы-Минуты, " \
                   "например: 12-45"
            return "retry_10_" + text


def set_value_car(vid, data, item):
    local_storage.update({item + vid: data})
    s = Subscriber.objects.get(user=vid)
    car_num_filter = s.cars.filter(car_number="?")
    car_brand_filter = s.cars.filter(car_brand="?")
    car_model_filter = s.cars.filter(car_model="?")

    if not car_num_filter.exists() and not car_brand_filter.exists() and not car_model_filter:
        s.cars.create(car_brand="?", car_model="?", car_number="?")
    try:
        car = s.cars.get(car_number="?")
    except order.models.Car.DoesNotExist:
        car = s.cars.get(car_number=local_storage["2" + vid])
    if item == "0":
        car.car_brand = data
        car.save()
    elif item == "1":
        car.car_model = data
        car.save()
    elif item == "2":
        car.car_number = data
        car.save()


def is_exists_order(vid):
    s = Subscriber.objects.get(user=vid)
    if not Order.objects.filter(owner=s).exists():
        Order.objects.create(owner=s)


def get_answer_string(vid):
    s = Subscriber.objects.get(user=vid)
    questionnaire = Questionnaire.objects.get(applicant=s)
    answer_string = "Город: " + questionnaire.city + "\n" + \
                    "Фамилия, имя: " + questionnaire.name + "\n" + \
                    "Телефон: " + questionnaire.phone + "\n" + \
                    "Госномер: " + questionnaire.car_number + "\n" + \
                    "Марка/Модель: " + questionnaire.car_model + "\n" + \
                    "Количество мест: " + questionnaire.number_of_seats + "\n" + \
                    "Год выпуска: " + questionnaire.car_year_made + "\n" + \
                    "Тип кузова/грузоподъёмность: " + questionnaire.car_type + "\n" + \
                    "Цвет: " + questionnaire.car_color + "\n"
    return answer_string


def get_licensing_answer_string(vid):
    s = Subscriber.objects.get(user=vid)
    licensing_questionnaire = LicensingQuestionnaire.objects.get(applicant=s)
    answer_string = "Имя: " + licensing_questionnaire.name + "\n" + \
                    "Фамилия: " + licensing_questionnaire.surname + "\n" + \
                    "Телефон: " + licensing_questionnaire.phone + "\n" + \
                    "Госномер: " + licensing_questionnaire.car_number + "\n" + \
                    "Марка: " + licensing_questionnaire.car_brand + "\n" + \
                    "Модель: " + licensing_questionnaire.car_model + "\n"
    return answer_string


def get_waybill_answer_string(vid, odometer_value=None):
    s = Subscriber.objects.get(user=vid)
    wq = WaybillEntry.objects.get(applicant=s)
    if odometer_value is not None:
        odometer_val = odometer_value
    else:
        odometer_val = wq.odometer_value
    answer_string = \
        "ФИО: " + wq.surname + " " + wq.name[:1] + "." + wq.patronymic[:1] + ".\n" + \
        "Номер путёвки: " + str(wq.number) + "\n" + \
        "Гаражный номер: " + str(wq.id_client) + "\n" + \
        "Дата: " + str(wq.date) + "\n" \
                                  "Время: " + str(wq.time) + "\n" \
                                                             "Время отправления: " + str(wq.time) + "\n" \
                                                                                                    "Серия удостоверения: " + str(
            wq.ser_doc) + "\n" + \
        "Номер удостоверения: " + str(wq.num_doc) + "\n" + \
        "Номер лицензии: " + str(wq.num_lic) + "\n" + \
        "Класс ТС: " + str(wq.kod_org_doc) + "\n" + \
        "Госномер: " + str(wq.tr_reg_num) + "\n" + \
        "Марка ТС: " + str(wq.tr_mark) + "\n" + \
        "Модель ТС: " + str(wq.tr_model) + "\n" + \
        "Показание одометра: " + str(odometer_val) + "\n" + \
        "Контроль технического состояния пройден, выпуск на линию разрешён. " \
        "Контролёр технического состояния " \
        "автотранспортных средств : Рыбников Алексей Иванович.\n" + "" \
                                                                    "Прошёл предрейсовый медицинский осмотр, к исполнению трудовых обязанностей допущен. " \
                                                                    "Фельдшер: Дуткина Яна Андреевна."
    return answer_string


def get_order_string(vid):
    s = Subscriber.objects.get(user=vid)
    ordering = Order.objects.get(owner=s)
    order_string = "Сервис: " + ordering.service.split("_")[0] + "\n" + \
                   "Тариф: " + tariffs[ordering.tariff] + "\n" + \
                   "Откуда: " + ordering.from_location.split("#")[0] + "\n" + \
                   "Куда: " + ordering.to_location.split("#")[0] + "\n" + \
                   "Стоимость: " + str(ordering.order_cost) + " руб.\n" + \
                   "Комментарий: " + ordering.comment + "\n"
    return order_string


def get_creating_car_string(vid):
    s = Subscriber.objects.get(user=vid)
    car_questionnaire_buttons = CarQuestionnaireButtons.objects.get(user=s)
    creating_car_string = \
        "Марка: " + car_questionnaire_buttons.car_brand + "\n" + \
        "Модель: " + car_questionnaire_buttons.car_model + "\n" + \
        "Номер: " + car_questionnaire_buttons.car_number + "\n"
    return creating_car_string


def conditions(region):
    return ConditionsForRegions.objects.filter(region_name=region).get().condition


def validate_time_format(time):
    pattern = re.compile(r'^([0-1]?[0-9]|2[0-3])\s*[:,.\-_\s]\s*([0-9]|[0-5][0-9])$')
    return True if re.search(pattern, time) else False


def message_handler(viber_request):
    vid = viber_request.sender.id
    name = viber_request.sender.name
    action_body = str(viber_request.message.text)
    tracking_data = str(viber_request.message.tracking_data)
    subscriber = Subscriber.objects.get(user=vid)

    if not subscriber.is_enable:
        if action_body == "payment_for_services":
            return viber.send_messages(vid, [payment_for_services()])
        if action_body == "menu":
            return
        else:
            print("Блокирован")
            return viber.send_messages(vid, [access_denied()])

    is_exists_order(vid)
    ordering = Order.objects.get(owner=subscriber)

    if tracking_data.startswith("job-app-form"):
        id_number = tracking_data.split('_')[1]
        n = id_number if id_number != "" else None
        count = QuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
        answered = True if count == 10 else False
        if not action_body.startswith("job_") and not action_body.startswith("c") and not action_body == "menu":
            set_answer(vid, action_body, id_number)
        viber.send_messages(vid,
                            [job_application_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])
    elif tracking_data.startswith("license-app-form"):
        id_number = tracking_data.split('_')[1]
        n = id_number if id_number != "" else None
        count = LicensingQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
        answered = True if count == 11 else False
        if not action_body.startswith("license_") and not action_body.startswith("send_") and not action_body == "menu":
            set_answer_licensing_question(vid, action_body, id_number)
        viber.send_messages(vid, [license_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])
    elif tracking_data.startswith("waybill-app-form") or tracking_data.startswith('kb-waybill-app-form'):
        id_number = tracking_data.split("_")[1]
        n = id_number if id_number != "" else None
        if WaybillQuestionnaireButtons.objects.get(user=subscriber).edit:
            if not action_body.startswith("waybill_") and not action_body.startswith("send_") \
                    and not action_body == "for-drivers":
                res = set_answer_waybill_question(vid, action_body, id_number)
                if str(res).startswith("retry"):
                    number_retry = res.split("_")[1]

                    text = res.split("_")[2]
                    viber.send_messages(vid,
                                        [waybill_form(vid=vid, number_button=number_retry, text=text,
                                                      text_field="regular", data="retry", answered=True)])
                else:
                    viber.send_messages(vid,
                                        [waybill_form(vid=vid, number_button=n, text_field="hidden", answered=True)])
        else:
            count = WaybillQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
            answered = True if count == 13 else False
            if not action_body.startswith("waybill_") and not action_body.startswith("send_") \
                    and not action_body == "for-drivers":
                res = set_answer_waybill_question(vid, action_body, id_number)
                if str(res).startswith("retry"):
                    number_retry = res.split("_")[1]
                    text = res.split("_")[2]
                    viber.send_messages(vid,
                                        [waybill_form(vid=vid, number_button=number_retry, text=text,
                                                      text_field="regular", data="retry", answered=True)])
                else:
                    viber.send_messages(vid, [
                        waybill_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])

    elif tracking_data.startswith("create-car-form"):
        id_number = tracking_data.split('_')[1]
        n = id_number if id_number != "" else None
        count = CarQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
        answered = True if count == 4 else False
        if not action_body.startswith("car_") and not action_body.startswith("c") and not action_body == "menu":
            set_value_car(vid, action_body, id_number)
        viber.send_messages(vid,
                            [create_car_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])

    elif tracking_data == "from" and not action_body.startswith("/back"):
        from_loc = action_body + "#" + coordinates_from_address(action_body)
        ordering.from_location = from_loc
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место отправления:\n" + action_body), to_address()])
    elif tracking_data == "to" and not action_body.startswith("/back"):
        to_loc = action_body + "#" + coordinates_from_address(action_body)
        ordering.to_location = to_loc
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место прибытия:\n" + action_body), comment()])
    # if tracking_data == 'enter-radius-distance':
    elif tracking_data == 'enter-radius-distance':
        radius_distance = action_body
        viber.send_messages(vid, [driver_location_kb(radius_distance)])
    # if tracking_data == 'support_letter':
    elif tracking_data == 'support_letter':
        if action_body not in ("menu", "info"):
            sender = str(name) + " " + str(subscriber.phone)
            send_email("Письмо в техподдержку от " + sender, action_body)
            viber.send_messages(vid, [TextMessage(text="Ваше сообщение отправлено в техподдержку", min_api_version=6),
                                      info()])
    # elif tracking_data == "time-zone":
    #     if action_body == 'waybill':
    #         return viber.send_messages(vid, [download_waybill_or_edit_kb()])
    #     if validate_time_format(action_body):
    #         set_tz(action_body, subscriber)
    #         tz = int(subscriber.time_zone)
    #         sign = '+' if tz >= 0 else ''
    #         try:
    #             text = "Ваше время соответствует времени " + time_zones[tz] + ". Ваш часовой пояс - UTC" + sign + \
    #                    str(subscriber.time_zone) + "."
    #             viber.send_messages(vid, [TextMessage(text=text, min_api_version=6)])
    #             viber.send_messages(vid, messages=[choice_service(vid)])
    #         except KeyError:
    #             text = "Вы, вероятно, ошиблись при вводе времени! Пожалуйста, напишите время в формате Часы-Минуты, " \
    #                    "например: 12-45"
    #             viber.send_messages(vid, [set_time_zone(text)])
    #     else:
    #         viber.send_messages(vid, [set_time_zone("Ваш ввод не соответствует формату времени, пожалуйста, напишите "
    #                                                 "время в формате Часы-Минуты, например: 12-45")])

    # elif tracking_data == "edit-time-zone":
    #     if action_body == 'waybill':
    #         return viber.send_messages(vid, [download_waybill_or_edit_kb()])
    #     if validate_time_format(action_body):
    #         set_tz(action_body, subscriber)
    #         tz = int(subscriber.time_zone)
    #         sign = '+' if tz >= 0 else ''
    #         try:
    #             text = "Ваше время соответствует времени " + time_zones[tz] + ". Ваш часовой пояс - UTC" + sign +\
    #                    str(subscriber.time_zone) + "."
    #             viber.send_messages(vid, [download_waybill_or_edit_kb(text)])
    #         except KeyError:
    #             text = "Вы, вероятно, ошиблись при вводе времени! Пожалуйста, напишите время в формате Часы-Минуты, " \
    #                    "например: 12-45"
    #             viber.send_messages(vid, messages=[edit_time_zone(text)])
    #     else:
    #         text = "Ваш ввод не соответствует формату времени, пожалуйста, напишите время в формате Часы-Минуты, " \
    #                "например: 12-45"
    #         viber.send_messages(vid, messages=[edit_time_zone(text)])
    if action_body == "start":
        viber.send_messages(vid, [choice_service(viber_request.sender.id)])
    #
    # elif action_body == "edit-time-zone":
    #     tz = int(subscriber.time_zone)
    #     sign = '+' if tz >= 0 else ''
    #     try:
    #         text = "Для корректной работы сервиса необходимо знать время вашего региона.\n\n" \
    #                "Ранее на основании установленного вами времени, ваш часовой пояс был определён как UTC" + sign + \
    #                str(tz) + ", что соответствует времени " + time_zones[tz] + ".\nЕсли хотите его изменить - введите ваше" \
    #                                            " текущее время в формате: ЧЧ-ММ"
    #
    #     except KeyError:
    #         tz = int(subscriber.time_zone)
    #         text = "Для корректной работы сервиса необходимо знать время вашего региона.\n\n" \
    #                "Ранее на основании установленного вами времени, ваш часовой пояс был определён как UTC" + sign +\
    #                str(tz) + ".\nЕсли хотите его изменить - введите ваше" \
    #                                            " текущее время в формате: ЧЧ-ММ"
    #     viber.send_messages(vid, messages=[edit_time_zone(text)])

    elif action_body == "menu":
        viber.send_messages(vid, messages=[choice_service(viber_request.sender.id)])

    elif action_body == "cargo":
        ordering.service = "Грузоперевозки_5"
        ordering.save()
        viber.send_messages(vid, [choice_cargo_tariff()])

    elif action_body == "evacuator":
        ordering.service = "Эвакуатор_4"
        ordering.save()
        viber.send_messages(vid, [choice_evacuator_tariff()])

    elif action_body == "app_job":
        viber.send_messages(vid,
                            [job_application_form(vid=vid, number_button=None, text="Заявка на работу",
                                                  text_field="hidden")])

    elif action_body.startswith("job"):
        number_button = action_body.split('_')[1]
        text = action_body.split('_')[2]
        viber.send_messages(vid,
                            [job_application_form(vid=vid, number_button=number_button, text=text,
                                                  order_data=number_button, text_field="regular")])

    elif action_body == "send_application":
        send_email("Заявка на работу от " + str(Questionnaire.objects.get(applicant=subscriber).name),
                   get_answer_string(vid))
        viber.send_messages(vid, [TextMessage(text="Ваша заявка отправлена\n" + get_answer_string(vid)),
                                  return_to_menu_rich()])

    elif action_body == "send_licensing_application":
        lq = LicensingQuestionnaire.objects.get(applicant=subscriber)
        try:
            files_to_attach = [
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_passport_first_path).split("media\\")[1])),
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_passport_reg_path).split("media\\")[1])),
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_sts_front_side_path).split("media\\")[1])),
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_sts_back_side_path).split("media\\")[1]))
            ]
        except IndexError:
            # send_email(subject="Запрос на лицензирование, " + str(lq.name),
            #            body_text=get_licensing_answer_string(vid))
            t = Thread(target=send_email, args=["Запрос на лицензирование, " + str(lq.name),
                                                get_licensing_answer_string(vid)])
            t.setDaemon(True)
            t.start()
            viber.send_messages(vid, [TextMessage(text="Ваша заявка отправлена\n" + get_licensing_answer_string(vid)),
                                      return_to_menu_rich()])
            return
        # send_email(subject="Запрос на лицензирование, " + str(lq.name),
        #            body_text=get_licensing_answer_string(vid), files_to_attach=files_to_attach)
        t = Thread(target=send_email, args=["Запрос на лицензирование, " + str(lq.name),
                                            get_licensing_answer_string(vid), None, None, None, files_to_attach])
        t.setDaemon(True)
        t.start()
        # t.join()

        # t2 = Thread(target=viber.send_messages,
        #            args=[vid, [TextMessage(text="Ваша заявка отправлена\n" + get_licensing_answer_string(vid)),
        #                        return_to_menu_rich()]])
        #
        # t2.setDaemon(True)
        # t2.start()
        # t2.join()

        viber.send_messages(vid, [TextMessage(text="Ваша заявка отправлена\n" + get_licensing_answer_string(vid)),
                                  return_to_menu_rich()])

    elif action_body == "waybill":
        if not WaybillEntry.objects.filter(applicant=subscriber).exists():
            set_edit_waybill_buttons(vid, False)
            viber.send_messages(vid,
                                [waybill_form(vid=vid, number_button=None, text="Заявка на путевой лист",
                                              text_field="hidden")])
        else:
            url, path_to_pdf, file_name_pdf, user_path = waybill_build(vid)
            viber.send_messages(vid, [download_waybill_or_edit_kb()])
            remove_old_files(user_path)

    elif action_body == "edit-waybill":
        set_edit_waybill_buttons(vid, True)
        viber.send_messages(vid,
                            [waybill_form(vid=vid, number_button=None, text="Заявка на путевой лист",
                                          text_field="hidden")])
    elif action_body == "set-odometer":
        viber.send_messages(vid, [TextMessage(text="Введите показание одометра", min_api_version=6,
                                              tracking_data="save_odometer_value")])

    elif tracking_data == "save_odometer_value":
        url, path_to_pdf, file_name_pdf, user_path = waybill_build(vid, odometer_value=action_body)
        viber.send_messages(vid,
                            [TextMessage(text="Путевой лист легкового автомобиля\n" +
                                              get_waybill_answer_string(vid, action_body))])
        viber.send_messages(vid, [return_waybill_document(url, file_name_pdf)])
        remove_old_files(user_path)

    elif action_body == "send_waybill_application":
        t = Thread(target=waybill_send, args=[vid])
        t.setDaemon(True)
        t.start()

    elif action_body.startswith(server_url):
        save_waybill_to_journal()
        wbe = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid))
        WaybillNote.objects.create(applicant=wbe.applicant,
                                   number=wbe.number,
                                   id_client=wbe.id_client,
                                   surname=wbe.surname,
                                   name=wbe.name,
                                   patronymic=wbe.patronymic,
                                   ser_doc=wbe.ser_doc,
                                   num_doc=wbe.num_doc,
                                   num_lic=wbe.num_lic,
                                   kod_org_doc=wbe.kod_org_doc,
                                   tr_reg_num=wbe.tr_reg_num,
                                   tr_mark=wbe.tr_mark,
                                   tr_model=wbe.tr_model,
                                   odometer_value=wbe.odometer_value,
                                   date=wbe.date,
                                   time=wbe.time,
                                   time_zone=wbe.time_zone)
        viber.send_messages(vid, [back_or_main_menu()])

    elif action_body == "license_form":
        viber.send_messages(vid,
                            [license_form(vid=vid, number_button=None, text="Заявка на лицензию",
                                          text_field="hidden")])
    elif action_body == "apply_for_a_taxi_permit":
        viber.send_messages(vid, [
            TextMessage(text="Выберите регион", min_api_version=6),
            choice_region_kb()])

    elif action_body in [city.region_name for city in ConditionsForRegions.objects.all()]:
        viber.send_messages(vid, [TextMessage(text=str(conditions(action_body)), min_api_version=6),
                                  send_request_or_come_back()])
    elif action_body.startswith("license"):
        number_button = action_body.split('_')[1]
        text = action_body.split('_')[2]
        viber.send_messages(vid,
                            [license_form(vid=vid, number_button=number_button, text=text,
                                          order_data=number_button, text_field="regular")])
    elif action_body.startswith("waybill"):
        number_button = action_body.split("_")[1]
        text = action_body.split("_")[2]
        viber.send_messages(vid,
                            [waybill_form(vid=vid, number_button=number_button, text=text,
                                          order_data=number_button, text_field="regular")])

    elif action_body == "info":
        if not subscriber.phone:
            viber.send_messages(vid, [get_phone_for_letter()])
        else:
            viber.send_messages(vid, [info()])

    elif action_body.startswith("tariff"):
        ordering.tariff = action_body.split('_')[1]
        ordering.save()
        service = services[ordering.service.split('_')[1]]
        viber.send_messages(vid, [from_address(service)])

    elif action_body.startswith("/back_tariff_"):
        service = action_body.split('_')[2]
        if service == "cargo":
            viber.send_messages(vid, [choice_cargo_tariff()])
        elif service == "evacuator":
            viber.send_messages(vid, [choice_evacuator_tariff()])

    elif action_body == "/back_from":
        service = services[ordering.service.split('_')[1]]
        viber.send_messages(vid, [from_address(service)])

    elif action_body == "/back_to":
        viber.send_messages(vid, [to_address()])

    elif action_body == "/back_comment":
        viber.send_messages(vid, [comment()])

    elif action_body == "/comment" or tracking_data == "/comment":
        com = action_body if action_body != "/comment" else ""
        ordering.comment = com
        ordering.save()
        if not Subscriber.objects.get(user=vid).phone:
            viber.send_messages(vid, [get_phone()])
        else:
            set_order(vid)
    elif action_body == "order":
        unit_id = ordering.service.split('_')[1]
        tariff_id = ordering.tariff
        from_location = ordering.from_location.split('#')[0]
        to_location = ordering.to_location.split('#')[0]

        order_id = send_order(unit_id=unit_id, tariff_id=tariff_id, phone=subscriber.phone,
                              addr_from=from_location, addr_to=to_location,
                              comment=ordering.comment).split(b' ')[2].decode()
        ordering.order_id = order_id
        ordering.save()

        viber.send_messages(vid, messages=[TextMessage(text="Ваш заказ отправлен!"),
                                           cancel_order_or_menu_rich()])
    elif action_body == "cancel_order":
        cancel(ordering.order_id)
        viber.send_messages(vid, messages=[TextMessage(text="Ваш заказ отменён!"),
                                           return_to_menu_rich()])
    elif action_body.startswith("driver"):
        order_id = action_body.split("|")[1]
        order = Order.objects.get(order_id=order_id)
        viber.send_messages(vid, [TextMessage(text="Информация о заказе\n" + get_order_string(order.owner.user)),
                                  take_order_or_not_rich(order_id)])
        keyboard = {"Type": "keyboard",
                    "InputFieldState": 'hidden',
                    "Buttons": order_buttons()
                    }

        viber.send_messages(vid, [KeyboardMessage(keyboard=keyboard, min_api_version=6)])
    elif action_body == "for-drivers":
        viber.send_messages(vid, [KeyboardMessage(keyboard=show_all_orders_or_less_remote_locations_kb(),
                                                  min_api_version=6)])
    elif action_body == "get-distance-limited-orders":
        viber.send_messages(vid, [TextMessage(text='Напишите расстояние в км, '
                                                   'в радиусе которого вы хотите видеть заказы',
                                              tracking_data='enter-radius-distance')])

        # viber.send_messages(vid, [KeyboardMessage(keyboard=show_less_remote_locations_kb,
        #                                           min_api_version=6)])

    elif action_body == "get-all-orders":

        keyboard = {"Type": "keyboard",
                    "InputFieldState": 'hidden',
                    "Buttons": order_buttons()
                    }

        viber.send_messages(vid, [to_menu_rich(), KeyboardMessage(keyboard=keyboard, min_api_version=6)])
    elif action_body.startswith("take-order"):
        order_id = action_body.split("|")[1]
        order = Order.objects.get(order_id=order_id)
        order_owner_user = order.owner.user
        order.ord_success = True
        order.save()
        viber.send_messages(vid, [TextMessage(text="Через сколько времени Вы прибудете к месту посадки?",
                                              keyboard=driver_arrival_interval(order_owner_user, order_id),
                                              min_api_version=6)])
    elif action_body.startswith("time-interval"):
        a = action_body.split("|")
        # time_interval = a[1]
        order_owner_user = a[2]
        order_id = a[3]
        viber.send_messages(vid, [
            TextMessage(text="Информация о заказе\n" + get_order_string(order_owner_user) + "\nПринять заказ?")])
        viber.send_messages(vid, [KeyboardMessage(keyboard=accept_the_order_or_cancel_kb(order_id), min_api_version=6)])
    elif action_body.startswith("order-cancellation"):
        order_id = action_body.split("|")[1]
        order = Order.objects.get(order_id=order_id)
        order.ord_success = False
        order.save()
        # viber.send_messages(vid, messages=[choice_service(user=viber_request.sender.id, name='')])
        keyboard = {"Type": "keyboard",
                    "InputFieldState": 'hidden',
                    "Buttons": order_buttons()
                    }

        viber.send_messages(vid, [to_menu_rich(), KeyboardMessage(keyboard=keyboard, min_api_version=6)])

    elif action_body.startswith("accept-order"):
        # Оповестить клиента
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [KeyboardMessage(keyboard=after_take_driver_kb(order_id), min_api_version=6)])
    elif action_body.startswith("call-to-client"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [TextMessage(text="Подтверждение\nПозвонить клиенту?",
                                              keyboard=call_or_cancel_kb(order_id),
                                              min_api_version=6)])
    elif action_body.startswith("in-arrival-call-to-client"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [TextMessage(text="Подтверждение\nПозвонить клиенту?",
                                              keyboard=call_or_cancel_in_arrival_moment_kb(order_id),
                                              min_api_version=6)])
    elif action_body.startswith("arrived-at-place"):
        order_id = action_body.split("|")[1]
        order = Order.objects.get(order_id=order_id)
        landing_place = order.from_location.split("#")[0]
        viber.send_messages(vid, [TextMessage(text="Вы уже на месте посадки - \n" + landing_place + " ?",
                                              keyboard=arrival_or_cancel_kb(order_id),
                                              min_api_version=6)])
    elif action_body.startswith("accept-arrival"):
        # Оповестить клиента
        order_id = action_body.split("|")[1]
        order = Order.objects.get(order_id=order_id)
        order_owner_user = order.owner.user
        viber.send_messages(vid, [TextMessage(text="Информация о заказе\n" + get_order_string(order_owner_user))])
        viber.send_messages(vid, [KeyboardMessage(keyboard=after_accept_arrival_kb(order_id), min_api_version=6)])
    elif action_body.startswith("landing"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [TextMessage(text="Подтверждение\nПоехали?")])
        viber.send_messages(vid, [KeyboardMessage(keyboard=start_trip_or_cancel_kb(order_id), min_api_version=6)])
    elif action_body.startswith("start_trip"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [KeyboardMessage(keyboard=finish_trip_kb(order_id), min_api_version=6)])
    elif action_body.startswith("finish_trip"):
        order_id = action_body.split("|")[1]
        order = Order.objects.get(order_id=order_id)

        viber.send_messages(vid, [TextMessage(text="К оплате " + str(order.order_cost) + " руб.")])
        viber.send_messages(vid, [choice_service(vid)])
    elif action_body == "cars":
        viber.send_messages(vid, [cars()])
    elif action_body.startswith("car"):
        number_button = action_body.split('_')[1]
        text = action_body.split('_')[2]
        viber.send_messages(vid, [create_car_form(vid=vid, number_button=number_button, text=text,
                                                  order_data=number_button, text_field="regular")])
    elif action_body == "my-cars":
        viber.send_messages(vid, [my_cars(vid)])
    elif action_body == "choice-car":
        viber.send_messages(vid, [list_of_cars(vid)])
    elif action_body == "create-car":
        viber.send_messages(vid, [create_car_form(vid=vid, number_button=None, text="Добавить автомобиль",
                                                  text_field="hidden")])
    elif action_body.startswith("add-car"):
        car_number_for_del_auto = action_body.split('_')[1]
        subscriber.cars.add(Car.objects.get(car_number=car_number_for_del_auto))
        # "изменить цвет кнопки на серый"
        viber.send_messages(vid, [list_of_cars(vid)])
    elif action_body == "return-to-car-list":
        viber.send_messages(vid, [list_of_cars(vid)])
    elif action_body.startswith("del-car"):
        car_number_for_del_auto = action_body.split('_')[1]
        car_filter = Car.objects.filter(car_owner=subscriber)
        if car_filter.exists():
            subscriber.cars.remove(car_filter.get(car_number=car_number_for_del_auto))
        viber.send_messages(vid, [my_cars(vid)])
    elif action_body == "balance-info":
        viber.send_messages(vid, [to_menu_rich(), TextMessage(text="Информация о балансе\nНа вашем счету ... руб.\n"),
                                  KeyboardMessage(keyboard=balance_kb(), min_api_version=6)])
    elif action_body.startswith("https://yoomoney.ru/"):
        return False


def waybill_send(vid):
    url, path_to_pdf, file_name_pdf, user_path = waybill_build(vid)
    viber.send_messages(vid,
                        [TextMessage(text="Путевой лист легкового автомобиля\n" + get_waybill_answer_string(vid))])
    viber.send_messages(vid, [return_waybill_document(url, file_name_pdf)])
    remove_old_files(user_path)


def set_tz(data):
    msk_gmt = 3
    offset = timedelta(hours=msk_gmt)
    msk_tz = timezone(offset, name='MSK')
    now_in_msk = datetime.now(tz=msk_tz)
    hours_in_msk = datetime.time(now_in_msk).strftime("%H")
    splitter = re.compile(r'\s*[:,.\-_\s]\s*')

    hours_in_client_tz = re.split(splitter, data)[0]
    # hours_in_client_tz = action_body.split(splitter)[0]
    hours_diff = int(hours_in_client_tz) - int(hours_in_msk)
    time_zone = msk_gmt + hours_diff
    if time_zone > 14:
        d = time_zone - 14
        time_zone = d - 12
    return time_zone


def waybill_build(vid, odometer_value=None):
    wbe = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid))
    journal = get_journal()
    increment = journal.journal_counter + 1
    # offset = timedelta(hours=int(Subscriber.objects.get(user=vid).time_zone))
    offset = timedelta(hours=int(wbe.time_zone))
    tz = timezone(offset, name='TZ')
    now = datetime.now(tz=tz)
    date = datetime.date(now).strftime("%d.%m.%Y")
    time = datetime.time(now).strftime("%H-%M")
    wbe.time = time
    wbe.date = date
    wbe.save()
    if odometer_value is not None:
        odometer_val = odometer_value
        wbe.odometer_value = odometer_value
    else:
        odometer_val = wbe.odometer_value
    user_path, usr_dir_name, path_to_pdf, file_name_pdf, attach_data = \
        render_pdf_template(vid=vid, number=increment, id_client=increment,
                            time=wbe.time, date=wbe.date,
                            surname=wbe.surname, name=wbe.name,
                            patronymic=wbe.patronymic, ser_doc=wbe.ser_doc,
                            num_doc=wbe.num_doc,
                            kod_org_doc=wbe.kod_org_doc, tr_mark=wbe.tr_mark,
                            tr_reg_num=wbe.tr_reg_num,
                            odometer_value=odometer_val)

    wbe.number = increment
    wbe.id_client = increment
    wbe.path_to_pdf_version = Path(path_to_pdf)
    wbe.save()
    # save_waybill_to_journal(vid)
    # url = server_url + MEDIA_URL + usr_dir_name + '/Путевой%20лист.pdf'
    url = server_url + MEDIA_URL + usr_dir_name + '/' + str(file_name_pdf)
    return url, path_to_pdf, file_name_pdf, user_path


def save_waybill_to_journal():
    journal = get_journal()
    # wbe = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid))
    journal.journal_counter += 1
    # journal.entries.add(wbe)
    journal.save()


def set_edit_waybill_buttons(vid, state):
    is_exists_waybill_buttons(vid)
    waybill_questionnaire_buttons = WaybillQuestionnaireButtons.objects.get(user=Subscriber.objects.get(user=vid))
    waybill_questionnaire_buttons.edit = state
    waybill_questionnaire_buttons.save()


def get_journal():
    journal_objects = WaybillJournal.objects
    if not journal_objects.exists():
        journal = journal_objects.create()
    else:
        journal = journal_objects.get()
    return journal


def set_order(vid):
    subscriber = Subscriber.objects.get(user=vid)
    is_exists_order(vid)
    ordering = Order.objects.get(owner=subscriber)
    unit_id = ordering.service.split("_")[1]
    tariff_id = ordering.tariff

    from_location = ordering.from_location.split("#")[1]
    to_location = ordering.to_location.split("#")[1]
    lat_from = from_location.split(" ")[0]
    lon_from = from_location.split(" ")[1]
    lat_to = to_location.split(" ")[0]
    lon_to = to_location.split(" ")[1]
    try:
        dist_map = distance(unit_id, tariff_id, lat_from, lon_from, lat_to, lon_to)
        dist = dist_map["distance"]
        price = dist_map["fix_price"]
        ordering.order_cost = price
        ordering.save()
        order_str = get_order_string(vid) + "\n" + "Расстояние: " + str(dist) + " км\n" + "Стоимость: " + \
                    str(price) + " руб."
        viber.send_messages(vid, messages=[TextMessage(text=order_str), KeyboardMessage(keyboard=order_kb(),
                                                                                        min_api_version=6)])
    except Exception:
        error_str = "Во время построения маршрута произошла ошибка!\n\nПопробуйте ещё раз"
        service = services[ordering.service.split("_")[1]]
        return viber.send_messages(vid, [TextMessage(text=error_str), from_address(service)])


def location_handler(*args):
    vid = args[0]
    lat = args[2]
    lon = args[3]
    track = args[4]
    subscriber = Subscriber.objects.get(user=vid)
    is_exists_order(vid)
    ordering = Order.objects.get(owner=subscriber)
    address = get_address(lat, lon)
    addr_str = address.split("#")[0]
    if track == "from":
        ordering.from_location = address
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место отправления:\n" + addr_str), to_address()])
    elif track == "to":
        ordering.to_location = address
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место прибытия:\n" + addr_str), comment()])
    elif track.startswith("radius_distance"):
        radius_distance = track.split("|")[1]
        keyboard = {"Type": "keyboard",
                    "InputFieldState": "hidden",
                    "Buttons": order_buttons(lat, lon, radius_distance)
                    }
        viber.send_messages(vid, [to_menu_rich(), KeyboardMessage(keyboard=keyboard, min_api_version=6)])


def picture_handler(viber_request):
    tracking_data = viber_request.message.tracking_data
    vid = viber_request.sender.id
    subscriber = Subscriber.objects.get(user=vid)
    name = viber_request.sender.name
    img_u = viber_request.message.thumbnail
    r = requests.get(img_u)
    path_to_media = Path(MEDIA_ROOT)
    if not Path.exists(path_to_media):
        Path.mkdir(path_to_media)
    v = str(vid)
    user_dir_name = str(v).replace("/", "").replace("+", "").replace("=", "")
    user_path = path_to_media.joinpath(user_dir_name)
    if not Path.exists(user_path):
        Path.mkdir(user_path)
    if tracking_data.startswith("license-app-form_"):
        index = str(tracking_data).split("_")[1]
        str_to_photo = names_for_files.get(index) + ".jpg"
        photo_filename = Path(str_to_photo)
        media_file = user_path.joinpath(photo_filename)
        with open(media_file, "wb") as f:
            f.write(r.content)
        set_answer_licensing_question(vid, media_file, index)
        subscriber = Subscriber.objects.get(user=vid)
        count = LicensingQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(
            action_type="none").count()
        answered = True if count == 11 else False
        # answered = True if count == 12 else False
        viber.send_messages(vid, [license_form(vid=vid, number_button=index, text_field="hidden",
                                               answered=answered, data=str(photo_filename))])
    elif tracking_data == "support_letter":
        str_to_photo = "image_for_support.jpg"
        photo_filename = Path(str_to_photo)
        media_file = user_path.joinpath(photo_filename)
        with open(media_file, "wb") as f:
            f.write(r.content)
        sender = str(name) + " " + str(subscriber.phone)
        send_email(subject="Письмо в техподдержку от " + sender, body_text="Письмо с прикреплённым файлом",
                   files_to_attach=[media_file])
        viber.send_messages(vid, [TextMessage(text="Ваше сообщение отправлено в техподдержку", min_api_version=6),
                                  info()])
