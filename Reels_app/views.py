from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required(login_url='auth:auth_view')
def reels(request):
    """
    Reels/Video Feed Page
    GET /reels/reels/
    
    Displays:
    - Short video reels
    - Video recommendations
    - Like and share options
    """
    context = {
        'page_title': 'Reels - PU-Marketplace',
        'page_description': 'Discover trending items and stories on campus.',
    }
    return render(request, 'reels/reels.html', context)
