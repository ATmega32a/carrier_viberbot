from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import render
from order.models import LicensingQuestionnaire
from .models import Subscriber


# from django.views.generic import TemplateView, ListView
#
# class HomePageView(TemplateView):
#     template_name = 'html-templates/home.html'
#
#
# class SearchResultsView(ListView):
#     model = Subscriber
#     template_name = 'html-templates/search_results.html'
#
#     @staticmethod
#     def sort_by_name(s):
#         return s.name
#
#     def get_queryset(self, *req):
#
#         query = self.request.GET.get('q')
#         phones = str(query).split(" ")
#         subscribers = []
#
#         for subscriber in Subscriber.objects.all():
#             if subscriber.phone in phones:
#                 subscribers.append(subscriber)
#             else:
#                 for phone in phones:
#                     if str(subscriber.phone).find(phone):
#                         subscribers.append(subscriber)
#         self.setup(self.request)
#         subscribers.sort(key=self.sort_by_name)
#         return render(request=self.request, template_name=self.template_name,
#                       context={"subscribers": subscribers})


def sort_by_name(s):
    return s.name


def drivers_info(subscribers: []):
    counter = 0
    names_drivers = []
    surnames_drivers = []
    car_models = []
    car_numbers = []
    lic_numbers = []
    for s in subscribers:
        lq = LicensingQuestionnaire.objects.filter(applicant=s)
        if lq.exists():
            counter += 1
            lq_obj = lq.get()
            names_drivers.append(lq_obj.name)
            surnames_drivers.append(lq_obj.surname)
            car_models.append(lq_obj.car_brand + " " + lq_obj.car_model)
            car_numbers.append(lq_obj.car_number)
            lic_numbers.append(lq_obj.license_number)
    return names_drivers, surnames_drivers, car_models, car_numbers, lic_numbers, counter


def search_result(request):
    req_get = request.GET
    query = req_get.get('q')
    search_by = req_get['search_by']
    subscribers = Subscriber.objects.all()
    set_subscribers = set()
    searched_phones = set()
    set_ws_duplicate = set()
    found_subscribers = []
    text = ''
    names = str(query).split(",")
    searched_phones_subscribers_str = ''
    list_of_filters = []

    if query != '':
        for name in names:
            if name == '':
                continue
            name = name.strip()
            try:
                if search_by == 'by_name':
                    list_of_filters = filter_by_name(LicensingQuestionnaire, name)
                elif search_by == 'by_surname':
                    list_of_filters = filter_by_surname(LicensingQuestionnaire, name)
                elif search_by == 'by_phone':
                    list_of_filters.append(LicensingQuestionnaire.objects.filter(phone__contains=name))
                elif search_by == 'by_lic_number':
                    list_of_filters.append(LicensingQuestionnaire.objects.filter(license_number__contains=name))
                elif search_by == 'by_car':
                    list_of_filters = filter_by_car(LicensingQuestionnaire, name)
                for lq_filter in list_of_filters:
                    if lq_filter.exists():
                        found_subscribers = set_found_subscribers(searched_phones, set_subscribers, set_ws_duplicate,
                                                                  lq_filter.get().applicant)
                        response(request, search_by, subscribers, searched_phones_subscribers_str,
                                 drivers_info(found_subscribers))

            except MultipleObjectsReturned:
                lq_find_list = []
                for lq_find in LicensingQuestionnaire.objects.all():
                    if search_by == 'by_name':
                        lq_find_list.append((lq_find.name, lq_find.applicant))
                    elif search_by == 'by_surname':
                        lq_find_list.append((lq_find.surname, lq_find.applicant))
                    elif search_by == 'by_phone':
                        lq_find_list.append((lq_find.phone, lq_find.applicant))
                    elif search_by == 'by_lic_number':
                        lq_find_list.append((lq_find.license_number, lq_find.applicant))
                    elif search_by == 'by_car':
                        lq_find_list.append((lq_find.car_brand, lq_find.applicant))
                        lq_find_list.append((lq_find.car_model, lq_find.applicant))
                        lq_find_list.append((lq_find.car_number, lq_find.applicant))
                    for lq_find_field in lq_find_list:
                        if lq_find_field[0].strip().lower().__contains__(name.strip().lower()):
                            s = lq_find_field[1]
                            set_ws_duplicate.add(s)
                            searched_phones.add(s.phone)
                            found_subscribers = [*set_ws_duplicate]
                            searched_phones.add(s.phone)

        found_subscribers.sort(key=sort_by_name)
        for searched_name in searched_phones:
            searched_phones_subscribers_str += searched_name + " "
        if len(found_subscribers) == 0:
            searched_phones_subscribers_str = ''
            text = "По вашему запросу ничего не найдено"
    else:
        searched_phones_subscribers_str = ''
        text = "Вы не ввели поисковый запрос!"
    return response(request, search_by, found_subscribers, searched_phones_subscribers_str,
                    drivers_info(found_subscribers), text)


def filter_by_name(model, name):
    list_of_filters = []
    if model.objects.filter(name__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(name__contains=name.lower()))
    elif model.objects.filter(name__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(name__contains=name.upper()))
    elif model.objects.filter(name__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(name__contains=name.capitalize()))
    return list_of_filters


def filter_by_surname(model, name):
    list_of_filters = []
    if model.objects.filter(surname__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(surname__contains=name.lower()))
    elif model.objects.filter(surname__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(surname__contains=name.upper()))
    elif model.objects.filter(surname__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(surname__contains=name.capitalize()))
    return list_of_filters


def filter_by_car(model, name):
    list_of_filters = []
    if model.objects.filter(car_brand__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(car_brand__contains=name.lower()))
    elif model.objects.filter(car_brand__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(car_brand__contains=name.upper()))
    elif model.objects.filter(car_brand__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(car_brand__contains=name.capitalize()))

    elif model.objects.filter(car_model__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(car_model__contains=name.lower()))
    elif model.objects.filter(car_model__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(car_model__contains=name.upper()))
    elif model.objects.filter(car_model__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(car_model__contains=name.capitalize()))

    elif model.objects.filter(car_number__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(car_number__contains=name.lower()))
    elif model.objects.filter(car_number__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(car_number__contains=name.upper()))
    elif model.objects.filter(car_number__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(car_number__contains=name.capitalize()))
    return list_of_filters


def set_found_subscribers(searched_phones, set_subscribers, set_ws_duplicate, subscriber):
    set_subscribers.add(subscriber)
    set_ws_duplicate.add(subscriber)
    searched_phones.add(subscriber.phone)
    found_subscribers = [*set_ws_duplicate]
    return found_subscribers


def response(request, search_by, subscribers, searched_phones_subscribers_str, info_car_licensing, text=''):
    number_of_subscribers = info_car_licensing[5]
    counter = []
    for i in range(int(number_of_subscribers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')
    subscribers_info = zip(subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                           info_car_licensing[3], info_car_licensing[4])
    return render(request, "html-templates/get-user-list.html",
                  {"subscribers": subscribers_info,
                   "searched_phones": searched_phones_subscribers_str,
                   "counter": counter,
                   "number_of_subscribers": number_of_subscribers,
                   "checked": search_by,
                   "text": text
                   })
