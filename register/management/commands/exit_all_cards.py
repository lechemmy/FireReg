from django.core.management.base import BaseCommand
from django.utils import timezone
from register.models import StaffPresence, EntryExitLog

class Command(BaseCommand):
    help = 'Exits all cards/staff that are currently logged in'

    def handle(self, *args, **options):
        current_time = timezone.now()
        present_staff = StaffPresence.objects.filter(is_present=True)
        exit_count = 0

        for presence in present_staff:
            # Create an exit log
            EntryExitLog.objects.create(
                user=presence.user,
                event_type='exit',
                timestamp=current_time
            )

            # Update the presence record
            presence.is_present = False
            presence.last_exit = current_time
            presence.save()

            exit_count += 1

        if exit_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully logged out {exit_count} staff member(s).'))
        else:
            self.stdout.write(self.style.WARNING('No staff members were logged out. They may have already left the building.'))