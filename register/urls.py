from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('', views.index, name='index'),
    path('current/', views.current_staff, name='current_staff'),
    path('current/exit/', views.exit_staff, name='exit_staff'),
    path('logs/', views.event_log, name='event_log'),
    path('cards/', views.cards, name='cards'),
    path('cards/register/', views.register_cards, name='register_cards'),
    path('cards/log-in-office/', views.log_cards_in_office, name='log_cards_in_office'),
    path('cards/export/', views.export_cards, name='export_cards'),
    path('cards/import/', views.import_cards, name='import_cards'),
    path('cards/edit/<int:card_id>/', views.edit_card, name='edit_card'),
    path('cards/delete/<int:card_id>/', views.delete_card, name='delete_card'),
    path('api/rfid-scan/', views.rfid_scan, name='rfid_scan'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('api-keys/create/', views.create_api_key, name='create_api_key'),
    path('api-keys/revoke/<int:key_id>/', views.revoke_api_key, name='revoke_api_key'),

    # Fire Marshal management
    path('fire-marshals/', views.fire_marshals, name='fire_marshals'),
    path('fire-marshals/add/', views.add_fire_marshal, name='add_fire_marshal'),
    path('fire-marshals/edit/<int:user_id>/', views.edit_fire_marshal, name='edit_fire_marshal'),
    path('fire-marshals/delete/<int:user_id>/', views.delete_fire_marshal, name='delete_fire_marshal'),
]
