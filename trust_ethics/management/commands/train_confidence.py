from django.core.management.base import BaseCommand
from trust_ethics.trust_ml import trainer
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Train the confidence model and optionally update trust metrics.'

    def add_arguments(self, parser):
        parser.add_argument('--update-user', type=int, help='User id to update trust metrics for')
        parser.add_argument('--update-all', action='store_true', help='Update trust metrics for all users after training')
        parser.add_argument('--no-train', action='store_true', help='Skip training, only update trust metrics using existing model')
        parser.add_argument('--list-models', action='store_true', help='List saved model versions')
        parser.add_argument('--rollback', type=str, help='Rollback to a specific saved model filename')

    def handle(self, *args, **options):
        if options.get('list_models'):
            self.stdout.write('Saved model versions:')
            for fn in trainer.list_saved_models():
                self.stdout.write(f' - {fn}')
            return

        if options.get('rollback'):
            fname = options.get('rollback')
            try:
                path = trainer.rollback_to(fname)
                self.stdout.write(self.style.SUCCESS(f'Rolled back to {path}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Rollback failed: {e}'))
            return

        if not options.get('no_train'):
            self.stdout.write('Starting training of confidence model...')
            try:
                stats = trainer.train()
                self.stdout.write(self.style.SUCCESS(f"Training finished: {stats}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Training failed: {e}"))
                return
        else:
            self.stdout.write('Skipping training (--no-train) and using existing model if present.')

        if options.get('update_user'):
            user_id = options.get('update_user')
            self.stdout.write(f'Updating trust metrics for user {user_id}...')
            try:
                res = trainer.update_trust_metrics_for_user(user_id)
                self.stdout.write(self.style.SUCCESS(f'Updated: {res}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to update user {user_id}: {e}'))
                return

        if options.get('update_all'):
            self.stdout.write('Updating trust metrics for all users...')
            User = get_user_model()
            users = User.objects.all()
            total = users.count()
            self.stdout.write(f'Found {total} users')
            for idx, user in enumerate(users, 1):
                try:
                    res = trainer.update_trust_metrics_for_user(user.id)
                    self.stdout.write(self.style.SUCCESS(f'[{idx}/{total}] {user.id}: {res}'))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'[{idx}/{total}] {user.id} failed: {e}'))
                    # continue to next user
            self.stdout.write(self.style.SUCCESS('Finished updating all users.'))

        if not options.get('update_user') and not options.get('update_all'):
            self.stdout.write('No update requested. Done.')
