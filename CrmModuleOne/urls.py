from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('calculator/', views.calculator, name='calculator'),
    path("acknowledge-post/", views.acknowledge_post, name="acknowledge_post"),
     path('post/<int:post_id>/', views.post_detail, name='post_detail'),  # Nowy widok szczegółów posta
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('leady/', views.leads_view, name='leady'),
    path('oferty/', views.oferss_view, name='oferty'),
    path('klienci/', views.clients_view, name='klienci'),
    path('klienci/dodaj/', views.add_client, name='add_client'),  # Dodanie klienta
    path('klienci/edytuj/<int:client_id>/', views.edit_client, name='edit_client'),
    path('klienci/klient/<int:client_id>/', views.client_card, name='client_card'),
    path('klienci/dane-leada/<int:lead_id>/', views.get_lead_data, name='get_lead_data'),
    path('klienci/kalkulator/', views.lead_form, name='lead_form'),
    path('kalkulator/produkty/<int:category_id>/', views.get_products_by_category, name='get_products_by_category'),
    path('kalkulator/produkt/<int:product_id>/', views.get_product_details, name='get_product_details'),
    path("product/<int:product_id>/manage-prices/", views.manage_product_prices, name="manage_product_prices"),
    path("configuration/<int:config_id>/delete/", views.delete_product_configuration, name="delete_product_configuration"),
    path('product/<int:product_id>/get-price/', views.get_price, name='get_price'),
    path("calculate-subsidy/", views.calculate_subsidy, name="calculate_subsidy"),
    path('generate-offer/', views.generate_offer_pdf, name='generate_offer_pdf'),
    path('zadanie/<int:task_id>/zrealizowane/', views.complete_task, name='complete_task'),
     path("spotkanie/<int:meeting_id>/odbyte/", views.mark_meeting_occurred, name="mark_meeting_occurred"),
     path("upload-template/", views.upload_template, name="upload_template"),
      path("delete-template/<int:template_id>/", views.delete_template, name="delete_template"),
      path('get_event_to_calendar/', views.get_event_to_calendar, name='get_event_to_calendars'),
      path('mark_task_completed/<int:task_id>/', views.mark_task_completed, name='mark_task_completed'),
      path("update_meeting_status/", views.update_meeting_status, name="update_meeting_status"),\
      path("get_recent_notifications/", views.get_recent_notifications, name="get_recent_notifications"),
      path('mark_notification_as_read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
      path('notifications/', views.notifications_list, name='notifications_list'),
      path("save-final-offer/", views.save_final_offer, name="save_final_offer"),
      path("zapisz-klienta/", views.client_registration, name="client_registration"),
    path('leadsfb/', views.leadsfb, name='leadsfb'),
    path('grafiks/', views.grafiks, name='grafiks'),
    path('import-leadsfb/', views.import_leadsfb, name='import_leadsfb'),
    path('save-prelead/', views.save_prelead, name='save_prelead'),
    path('add-parcel/', views.add_parcel, name='add_parcel'),
    path('api/parcels/', views.list_parcels, name='list_parcels'),
path('api/parcels/delete/', views.delete_parcel, name='delete_parcel'),
    path("geocode-parcels/", views.geocode_parcels_view, name="geocode_parcels"),
     path('api/parcelss/', views.parcel_points, name='parcel_points'),
    path('api/prelead/<int:lead_id>/', views.get_prelead_detail, name='api_prelead_detail'),
    path('lead/form/<int:lead_id>/', views.prelead_form, name='prelead_form'),
]


