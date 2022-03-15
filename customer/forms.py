from django import forms


class UserForm(forms.Form):
    search = forms.CharField(max_length=13, label="Поиск клиентов по номеру телефона",
                             help_text="Введите номер телефона",
                             required=False, error_messages={'required': 'Вы не ввели номер телефона'}, )
