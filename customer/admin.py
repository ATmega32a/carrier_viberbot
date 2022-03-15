from django.contrib import admin
from customer.models import Subscriber
from customer.models import Driver

admin.site.register(Driver)


@admin.register(Subscriber)
class ViewSubscriber(admin.ModelAdmin):
    list_display = (
        'name',
        'date_sub',
        'image_img',
        'region',
        'phone',
        'source',
        'in_use',
        'is_driver',
        'is_enable'
    )
    search_fields = ['phone']




