import os
import sys
import django

# Prepare Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_project1.hais_core.settings')

try:
    django.setup()
except Exception:
    # try alternative settings path if project package name differs
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
    django.setup()

from trust_ethics.trust_ml import trainer


def main():
    print('Building dataset and training confidence model...')
    try:
        stats = trainer.train()
        print('Training completed:')
        print(stats)
    except Exception as e:
        print('Training failed:', str(e))


if __name__ == '__main__':
    main()
