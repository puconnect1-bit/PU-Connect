from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.



@login_required(login_url='auth:auth_view')
def search(request):
    """
    Search Results Page
    GET /search/

    Displays:
    - Search results
    - Filter options
    - Sort options
    """
    context = {
        'page_title': 'Search Results - PU-Marketplace',
        'page_description': 'Find what you are looking for.',
    }
    return render(request, 'search/search.html', context)
