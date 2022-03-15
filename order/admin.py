from django.contrib import admin
from order.models import Order, Questionnaire, LicensingQuestionnaire, WaybillEntry, WaybillJournal, WaybillNote, Car


@admin.register(Order)
class ViewOrder(admin.ModelAdmin):
    list_display = (
        'owner',
        'service',
        'tariff',
        'from_location',
        'to_location',
        'comment',
        'order_cost',
        'ord_success'
    )


@admin.register(Questionnaire)
class ViewQuestionnaire(admin.ModelAdmin):
    list_display = (
        'applicant',
        'city',
        'name',
        'phone',
        'car_number',
        'car_model',
        'number_of_seats',
        'car_year_made',
        'car_type',
        'car_color'
    )


@admin.register(LicensingQuestionnaire)
class ViewLicensingQuestionnaire(admin.ModelAdmin):
    list_display = (
        'license_number',
        'applicant',
        'name',
        'surname',
        'phone',
        'car_number',
        'car_model',
        'photo_passport_first_path',
        'photo_passport_reg_path',
        'photo_sts_front_side_path',
        'photo_sts_back_side_path'
    )


@admin.register(WaybillEntry)
class ViewWaybillEntry(admin.ModelAdmin):
    list_display = (
        'tr_reg_num',
        'surname',
        'name',
        'patronymic',
        'tr_mark',
        'ser_doc',
        'num_doc',
        'kod_org_doc'
    )


@admin.register(WaybillNote)
class ViewWaybillNote(admin.ModelAdmin):
    list_display = (
        'number',
        'tr_reg_num',
        'surname',
        'name',
        'patronymic',
        'tr_mark',
        'date',
        'time',
        'time_zone',
        'start_tech_state',
        'odometer_value',
        'arrival_time',
        'finish_tech_state',
        'final_odometer_value',
        'fuel_residue',
        'special_marks',
        'mechanic_signature',
        'driver_signature'
    )


@admin.register(WaybillJournal)
class ViewWaybillJournal(admin.ModelAdmin):
    list_display = (
        'journal_counter',
    )


@admin.register(Car)
class ViewCar(admin.ModelAdmin):
    list_display = (
        'car_owner',
        'car_brand',
        'car_model',
        'car_number'
    )

