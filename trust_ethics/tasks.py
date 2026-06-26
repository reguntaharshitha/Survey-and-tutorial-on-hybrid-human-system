from celery import shared_task
import logging
from .trust_ml import trainer
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def retrain_confidence_model(self, update_all=False):
    """Celery task: retrain the confidence model and optionally update trust metrics for users.

    This task is intended to be scheduled periodically (e.g., daily).
    """
    logger.info('Starting retrain_confidence_model task')
    try:
        stats = trainer.train()
        logger.info(f'Training stats: {stats}')
    except Exception as e:
        logger.exception('Retraining failed')
        return {'error': str(e)}

    if update_all:
        User = get_user_model()
        users = User.objects.all()
        results = []
        for u in users:
            try:
                res = trainer.update_trust_metrics_for_user(u.id)
                results.append({'user': u.id, 'res': res})
            except Exception as e:
                logger.exception(f'Failed to update trust metrics for user {u.id}')
                results.append({'user': u.id, 'error': str(e)})
        logger.info('Completed updating trust metrics for all users')
        return {'stats': stats, 'updates': results}

    return {'stats': stats}
