# Automatic Card Exit at 23:00

This directory contains a Django management command that can be used to automatically exit all cards/staff that are currently logged in. This is useful for ensuring that all cards are properly logged out at the end of the day.

## Command: `exit_all_cards`

The `exit_all_cards` command finds all staff members who are currently marked as present in the system and logs them out. It creates an exit log entry for each staff member and updates their presence status.

### Usage

To run the command manually:

```bash
python manage.py exit_all_cards
```

## Scheduling with Cron

To automatically run this command at 23:00 (11:00 PM) every day, you can set up a cron job. Here's how to do it:

1. Open your crontab file:

```bash
crontab -e
```

2. Add the following line to schedule the command to run at 23:00 daily:

```
0 23 * * * cd /path/to/your/project && /path/to/your/python /path/to/your/project/manage.py exit_all_cards
```

Replace `/path/to/your/project` with the actual path to your Django project, and `/path/to/your/python` with the path to your Python executable.

For example, if your project is at `/home/user/FireReg` and you're using a virtual environment at `/home/user/venv/bin/python`, the cron job would look like:

```
0 23 * * * cd /home/user/FireReg && /home/user/venv/bin/python /home/user/FireReg/manage.py exit_all_cards
```

3. Save and exit the editor.

The cron job will now run the `exit_all_cards` command at 23:00 every day, automatically logging out all staff members who are still marked as present in the system.

## Logging

The command outputs information about how many staff members were logged out. If you want to capture this output, you can redirect it to a log file in your cron job:

```
0 23 * * * cd /path/to/your/project && /path/to/your/python /path/to/your/project/manage.py exit_all_cards >> /path/to/logfile.log 2>&1
```

This will append both standard output and error messages to the specified log file.