from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from viberbot.api.messages.data_types.contact import Contact
from viberbot.api.messages.data_types.location import Location
from viberbot.api.viber_requests import ViberMessageRequest, ViberSubscribedRequest, ViberUnsubscribedRequest, \
    ViberConversationStartedRequest
from viberbot.api.messages import LocationMessage, PictureMessage
from viberbot.api.messages import ContactMessage

from botviber.bot_config import viber
from botviber.buttons.buttons import choice_service, info, share_phone
from botviber.handler import location_handler, message_handler, set_order, picture_handler
from customer import forms
from customer.models import Subscriber
from customer.views import drivers_info
from order.models import Order, WaybillNote


def return_user(viber_request):
    viber.send_messages(viber_request.user.id, choice_service(viber_request.user.id))


def sort_by_name(s):
    return s.name


def get_users(request):
    subscribers = Subscriber.objects.all()
    number_of_subscribers = Subscriber.objects.count()
    counter = []
    for i in range(int(number_of_subscribers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')
    return render(request, "html-templates/get-user-list.html",
                  {
                      "subscribers": subscribers,
                      "number_of_subscribers": number_of_subscribers,
                      "counter": counter,
                      "checked": "by_name"
                  })


def get_drivers(request):
    drivers = Subscriber.objects.filter(is_driver=True)
    number_of_drivers = drivers.count()
    counter = []
    for i in range(int(number_of_drivers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')

    return render(request, "html-templates/get-driver-list.html",
                  {
                      "subscribers": drivers,
                      "number_of_subscribers": number_of_drivers,
                      "counter": counter,
                  })


def get_orders(request):
    orders = Order.objects.all()
    return render(request, "get-order-list.html",
                  {"orders": orders})


def get_notes(request):
    notes = WaybillNote.objects.all()
    return render(request, "get-waybill-notes-list.html",
                  {"notes": notes})


def set_driver(request, subscriber_id, searched_phones='', search_by='by_name'):

    def _sort_by_name(sub):
        return sub.name

    try:
        subscriber = Subscriber.objects.get(phone=str(subscriber_id))
        role = subscriber.is_driver
        if role:
            subscriber.is_driver = False
        else:
            subscriber.is_driver = True
        subscriber.save()
        current_subscribers = []
        phones = str(searched_phones).strip().split(" ")
        if searched_phones != '':
            for phone in phones:
                current_subscribers.append(Subscriber.objects.get(phone=phone))
        else:
            for subscriber in Subscriber.objects.all():
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=_sort_by_name)
        info_car_licensing = drivers_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4])
        number_of_subscribers = info_car_licensing[5]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def enable_client(request, subscriber_id, searched_phones='', search_by='by_name'):
    try:
        subscriber = Subscriber.objects.get(phone=str(subscriber_id))
        state = subscriber.is_enable
        if state:
            subscriber.is_enable = False
        else:
            subscriber.is_enable = True
        subscriber.save()

        current_subscribers = []
        phones = str(searched_phones).strip().split(" ")
        if searched_phones != '':
            for phone in phones:
                current_subscribers.append(Subscriber.objects.get(phone=phone))
        else:
            for subscriber in Subscriber.objects.all():
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = drivers_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4])
        number_of_subscribers = info_car_licensing[5]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def make_all_drivers(request, searched_phones='', search_by='by_name'):
    try:
        current_subscribers = []
        phones = str(searched_phones).strip().split(" ")
        if searched_phones != '':
            for phone in phones:
                subscriber = Subscriber.objects.get(phone=phone)
                subscriber.is_driver = True
                subscriber.save()
                current_subscribers.append(subscriber)
        else:
            for subscriber in Subscriber.objects.all():
                subscriber.is_driver = True
                subscriber.save()
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = drivers_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4])
        number_of_subscribers = info_car_licensing[5]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def make_all_clients(request, searched_phones='', search_by='by_name'):
    try:
        current_subscribers = []
        phones = str(searched_phones).strip().split(" ")
        if searched_phones != '':
            for phone in phones:
                subscriber = Subscriber.objects.get(phone=phone)
                subscriber.is_driver = False
                subscriber.save()
                current_subscribers.append(subscriber)
        else:
            for subscriber in Subscriber.objects.all():
                subscriber.is_driver = False
                subscriber.save()
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = drivers_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4])
        number_of_subscribers = info_car_licensing[5]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def enable_all_selected(request, searched_phones='', search_by='by_name'):
    try:
        current_subscribers = []
        phones = str(searched_phones).strip().split(" ")
        if searched_phones != '':
            for phone in phones:
                subscriber = Subscriber.objects.get(phone=phone)
                subscriber.is_enable = True
                subscriber.save()
                current_subscribers.append(subscriber)
        else:
            for subscriber in Subscriber.objects.all():
                subscriber.is_driver = False
                subscriber.save()
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = drivers_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4])
        number_of_subscribers = info_car_licensing[5]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def disable_all_selected(request, searched_phones='', search_by='by_name'):
    try:
        current_subscribers = []
        phones = str(searched_phones).strip().split(" ")
        if searched_phones != '':
            for phone in phones:
                subscriber = Subscriber.objects.get(phone=phone)
                subscriber.is_enable = False
                subscriber.save()
                current_subscribers.append(subscriber)
        else:
            for subscriber in Subscriber.objects.all():
                subscriber.is_driver = False
                subscriber.save()
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = drivers_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4])
        number_of_subscribers = info_car_licensing[5]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def viber_events(request):
    if request.method == "POST":
        if not viber.verify_signature(request.body, request.headers.get('X-Viber-Content-Signature')):
            return HttpResponse(status=403)
        viber_request = viber.parse_request(request.body)
        if isinstance(viber_request, ViberMessageRequest):
            message = viber_request.message
            if isinstance(message, LocationMessage):
                location = message.location
                if isinstance(location, Location):
                    vid = viber_request.sender.id
                    name = viber_request.sender.name
                    lat = location.latitude
                    lon = location.longitude
                    tracking_data = viber_request.message.tracking_data
                    location_handler(vid, name, lat, lon, tracking_data)
            elif isinstance(message, ContactMessage):
                contact = message.contact
                if isinstance(contact, Contact):
                    vid = viber_request.sender.id
                    num = contact.phone_number
                    sub = Subscriber.objects.get(user=vid)
                    sub.phone = '+' + num
                    sub.save()
                    if viber_request.message.tracking_data == "share-phone-number":

                        viber.send_messages(vid, messages=[choice_service(vid)])
                    elif viber_request.message.tracking_data == "phone-number-for-support-letter":
                        viber.send_messages(vid, [info()])
                    else:
                        set_order(vid)
            elif isinstance(message, PictureMessage):
                picture_handler(viber_request)
            else:
                message_handler(viber_request)
        elif isinstance(viber_request, ViberConversationStartedRequest):
            uid = viber_request.user.id
            name = viber_request.user.name
            if not viber_request.subscribed:
                Subscriber.save_user(viber_request.user, 'internet')
                viber.send_messages(uid, messages=[share_phone(name)])

        elif isinstance(viber_request, ViberSubscribedRequest):
            usr = Subscriber.objects.get(user=viber_request.user.id)
            usr.in_use = True
            usr.save()
            return_user(viber_request)

        elif isinstance(viber_request, ViberUnsubscribedRequest):
            usr = Subscriber.objects.get(user=viber_request.user_id)
            usr.in_use = False
            usr.save()
        return HttpResponse(status=200)
