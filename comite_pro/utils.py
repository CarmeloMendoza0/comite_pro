# comite_pro/utils.py

from django.contrib.auth.models import Group

def is_admin(user):
    return user.groups.filter(name='administrador').exists()

def is_accountant(user):
    return user.groups.filter(name='contable').exists()

