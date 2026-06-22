from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

#===================================================2024-06-01: Added dashboard view and template rendering


@login_required(login_url='auth:auth_view')
def dashboard(request):
    context = {
        'page_title': 'Your Dashboard - PU-Marketplace',
        'page_description': 'Manage your account, view activity, and access key features.',
    }
    return render(request, 'dash/dashboard.html', context)


@login_required(login_url='auth:auth_view')
def dashboard_services(request):
    context = {
        'page_title': 'Services - PU-Marketplace',
    }
    return render(request, 'dash/dashboard-services.html', context)


@login_required(login_url='auth:auth_view')
def dashboard_products(request):
    context = {
        'page_title': 'Products - PU-Marketplace',
    }
    return render(request, 'dash/dashboard-products.html', context)
    