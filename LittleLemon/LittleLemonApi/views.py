from django.shortcuts import get_object_or_404
from rest_framework import generics
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticatedUser
from django.contrib.auth.models import User,Group
from rest_framework import viewsets, status

# Create your views here.
def MenuItemsView(request):
    pass

def SingleItemView(request):
    pass

def manager(request):
    pass

def singlemanager(request):
    pass

def deliverycrew(request):
    pass

def singledeliverycrew(request):
    pass

def cartview(request):
    pass

def orderview(request):
    pass

def singleorderview(request):
    pass