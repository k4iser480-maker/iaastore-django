from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<str:order_number>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword/', views.resetPassword, name='resetPassword'),

    # Shipping Addresses
    path('shipping-addresses/', views.shipping_addresses, name='shipping_addresses'),
    path('shipping-addresses/add/', views.add_shipping_address, name='add_shipping_address'),
    path('shipping-addresses/edit/<int:address_id>/', views.edit_shipping_address, name='edit_shipping_address'),
    path('shipping-addresses/delete/<int:address_id>/', views.delete_shipping_address, name='delete_shipping_address'),
    path('shipping-addresses/set-default/<int:address_id>/', views.set_default_shipping_address, name='set_default_shipping_address'),

    # Admin Panel
    path('panel/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('panel/chat/', admin_views.admin_chat_message, name='admin_chat_message'),
    path('panel/orders/', admin_views.admin_orders, name='admin_orders'),
    path('panel/orders/update/<int:order_id>/', admin_views.admin_update_order_status, name='admin_update_order_status'),
    path('panel/orders/delete/<int:order_id>/', admin_views.admin_delete_order, name='admin_delete_order'),
    path('panel/orders/clear/', admin_views.admin_clear_orders, name='admin_clear_orders'),
    
    # Transportistas
    path('panel/transportistas/', admin_views.admin_transportistas, name='admin_transportistas'),
    path('panel/transportistas/create/', admin_views.admin_create_transportista, name='admin_create_transportista'),
    path('panel/products/', admin_views.admin_products, name='admin_products'),
    path('panel/products/export/', admin_views.admin_export_products, name='admin_export_products'),
    path('panel/products/import/', admin_views.admin_import_products, name='admin_import_products'),
    path('panel/products/toggle/<int:product_id>/', admin_views.admin_toggle_product, name='admin_toggle_product'),
    path('panel/products/create/', admin_views.admin_create_product, name='admin_create_product'),
    path('panel/products/edit/<int:product_id>/', admin_views.admin_edit_product, name='admin_edit_product'),
    path('panel/products/delete/<int:product_id>/', admin_views.admin_delete_product, name='admin_delete_product'),
    path('panel/products/clear/', admin_views.admin_clear_products, name='admin_clear_products'),
    path('panel/customers/', admin_views.admin_customers, name='admin_customers'),
    
    # Roles Management
    path('panel/roles/', admin_views.admin_roles, name='admin_roles'),
    path('panel/roles/create/', admin_views.admin_create_role, name='admin_create_role'),
    path('panel/roles/edit/<int:role_id>/', admin_views.admin_edit_role, name='admin_edit_role'),
    path('panel/roles/delete/<int:role_id>/', admin_views.admin_delete_role, name='admin_delete_role'),
    path('panel/roles/clone/<int:role_id>/', admin_views.admin_clone_role, name='admin_clone_role'),

    # Users Management
    path('panel/users/', admin_views.admin_users, name='admin_users'),
    path('panel/users/create/', admin_views.admin_create_user, name='admin_create_user'),
    path('panel/users/edit/<int:user_id>/', admin_views.admin_edit_user, name='admin_edit_user'),
    path('panel/users/delete/<int:user_id>/', admin_views.admin_delete_user, name='admin_delete_user'),

    path('panel/settings/', admin_views.admin_settings, name='admin_settings'),
    path('panel/update-bcv/', admin_views.force_update_bcv, name='force_update_bcv'),
    path('panel/profile/', admin_views.admin_profile, name='admin_profile'),
    path('panel/activity-log/', admin_views.admin_activity_log, name='admin_activity_log'),

    # Backups
    path('panel/backups/', admin_views.admin_backups, name='admin_backups'),
    path('panel/backups/create/', admin_views.admin_create_backup, name='admin_create_backup'),
    path('panel/backups/download/<str:filename>/', admin_views.admin_download_backup, name='admin_download_backup'),
    path('panel/backups/restore/<str:filename>/', admin_views.admin_restore_backup, name='admin_restore_backup'),
    path('panel/backups/delete/<str:filename>/', admin_views.admin_delete_backup, name='admin_delete_backup'),
    path('panel/backups/upload/', admin_views.admin_upload_backup, name='admin_upload_backup'),
    path('panel/backups/schedule/', admin_views.admin_update_backup_schedule, name='admin_update_backup_schedule'),
]
