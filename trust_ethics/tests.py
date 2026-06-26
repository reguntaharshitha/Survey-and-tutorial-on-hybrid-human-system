from django.test import TestCase
from django.utils import timezone
from trust_ethics.trust_ml import ConfidenceTrainer
from feedback.models import Feedback
from user_interaction.models import InteractionSession, UserInput, AIResponse
from users.models import CustomUser


class ConfidenceTrainerTests(TestCase):
	def setUp(self):
		# Ensure trainer starts with a clean state
		self.trainer = ConfidenceTrainer()

	def test_build_dataset_empty(self):
		# No feedback in DB -> build_dataset should return None
		df = self.trainer.build_dataset()
		self.assertIsNone(df)

	def test_train_with_mock_data(self):
		# Create a user and linked AIResponse + Feedback entries to allow training
		user = CustomUser.objects.create(username='tester', email='tester@example.com')
		session = InteractionSession.objects.create(user=user, session_id='s1')
		# create several UserInput/AIResponse/Feedback rows (AIResponse is OneToOne with UserInput)
		for i in range(10):
			ui = UserInput.objects.create(session=session, input_type='text', input_data=f'hello {i}')
			ar = AIResponse.objects.create(user_input=ui, response_data=f'resp {i}', reasoning='reason', confidence_score=0.6, timestamp=timezone.now())
			fb = Feedback.objects.create(user=user, ai_response=ar, feedback_type='agreement', rating=5, comment='ok', timestamp=timezone.now())

		# Now build dataset should return a DataFrame
		df = self.trainer.build_dataset()
		self.assertIsNotNone(df)
		self.assertGreater(len(df), 0)

		# Training should run without raising
		stats = self.trainer.train(test_size=0.2)
		self.assertIn('train_r2', stats)
		self.assertIn('test_r2', stats)

		# model file should exist after training
		import os
		self.assertTrue(os.path.exists(self.trainer.model_path))
