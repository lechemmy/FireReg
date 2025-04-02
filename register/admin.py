from django.contrib import admin
from .models import RFIDTag, EntryExitLog, StaffPresence, Card, APIKey

@admin.register(RFIDTag)
class RFIDTagAdmin(admin.ModelAdmin):
    list_display = ('tag_id', 'user', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('tag_id', 'user__username', 'user__first_name', 'user__last_name')

@admin.register(EntryExitLog)
class EntryExitLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'timestamp'

@admin.register(StaffPresence)
class StaffPresenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_present', 'last_entry', 'last_exit')
    list_filter = ('is_present',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'card_number', 'created_at')
    search_fields = ('name', 'card_number')

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'key', 'is_active', 'created_at', 'last_used')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username', 'key')
    readonly_fields = ('key', 'created_at', 'last_used')
