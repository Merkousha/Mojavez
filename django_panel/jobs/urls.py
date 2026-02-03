"""
URLs for jobs app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CrawlJobViewSet, CrawlRecordViewSet, index_view, events_view

router = DefaultRouter()
router.register(r'jobs', CrawlJobViewSet, basename='job')
router.register(r'records', CrawlRecordViewSet, basename='record')

urlpatterns = [
    path('', index_view, name='index'),
    path('api/jobs/events/', events_view, name='events'),
    path('api/', include(router.urls)),
]
