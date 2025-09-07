# ipo_app/management/commands/applyipo.py
from django.core.management.base import BaseCommand
from ipo_app.tasks import apply_ipo_for_all

class Command(BaseCommand):
    help = "Apply IPO for accounts from .env"

    def handle(self, *args, **kwargs):
        apply_ipo_for_all()
