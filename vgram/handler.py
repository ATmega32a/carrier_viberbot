import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Thread

import requests

from viberbot.api.messages import TextMessage, KeyboardMessage

from botviber.bot_config import viber
from carrier_viberbot.settings import MEDIA_ROOT
from vgram.buttons import license_form
from vgram.models import VgramProfile, Subscriber, VgramProfileButtons

names_for_files = {"4": "passport_first_page", "5": "passport_registration", "6": "sts_front_side",
                   "7": "sts_back_side"}

def is_exists_licensing_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not VgramProfile.objects.filter(applicant=s).exists():
        VgramProfile.objects.create(applicant=s)


def set_answer_licensing_question(vid, data, item):
    is_exists_licensing_questionnaire(vid)
    s = Subscriber.objects.get(user=vid)
    vgram_profile = VgramProfile.objects.get(applicant=s)
    if item == "0":
        vgram_profile.name = data
        vgram_profile.save()
    elif item == "1":
        vgram_profile.phone = data
        vgram_profile.save()
    elif item == "2":
        vgram_profile.car_number = data
        vgram_profile.save()
    elif item == "3":
        vgram_profile.car_model = data
        vgram_profile.save()
    elif item == "4":
        vgram_profile.photo_passport_first_path = str(data)
        vgram_profile.save()
    elif item == "5":
        vgram_profile.photo_passport_reg_path = str(data)
        vgram_profile.save()
    elif item == "6":
        vgram_profile.photo_sts_front_side_path = str(data)
        vgram_profile.save()
    elif item == "7":
        vgram_profile.photo_sts_back_side_path = str(data)
        vgram_profile.save()
    elif item == "8":
        vgram_profile.license_number = str(data)
        vgram_profile.save()


def message_handler(viber_request):
    vid = viber_request.sender.id
    name = viber_request.sender.name
    action_body = str(viber_request.message.text)
    tracking_data = str(viber_request.message.tracking_data)
    subscriber = Subscriber.objects.get(user=vid)


    if tracking_data.startswith("license-app-form"):
        id_number = tracking_data.split('_')[1]
        n = id_number if id_number != "" else None
        count = VgramProfileButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
        answered = True if count == 10 else False
        if not action_body.startswith("license_") and not action_body.startswith("send_") and not action_body == "menu":
            set_answer_licensing_question(vid, action_body, id_number)
        viber.send_messages(vid, [license_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])

    elif action_body == "send_licensing_application":
        pass
        # lq = VgramProfile.objects.get(applicant=subscriber)

    elif action_body == "license_form":
        viber.send_messages(vid,
                            [license_form(vid=vid, number_button=None, text="Заявка на лицензию",
                                          text_field="hidden")])

    elif action_body.startswith("license"):
        number_button = action_body.split('_')[1]
        text = action_body.split('_')[2]
        viber.send_messages(vid,
                            [license_form(vid=vid, number_button=number_button, text=text,
                                          order_data=number_button, text_field="regular")])


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
        count = VgramProfileButtons.objects.get(user=subscriber).buttons.filter(
            action_type="none").count()
        answered = True if count == 10 else False
        viber.send_messages(vid, [license_form(vid=vid, number_button=index, text_field="hidden",
                                               answered=answered, data=str(photo_filename))])
    elif tracking_data == "support_letter":
        str_to_photo = "image_for_support.jpg"
        photo_filename = Path(str_to_photo)
        media_file = user_path.joinpath(photo_filename)
        with open(media_file, "wb") as f:
            f.write(r.content)
        sender = str(name) + " " + str(subscriber.phone)

