"""TEST FOR MODELS"""
from unittest.mock import patch
from decimal import Decimal

from core import models
from django.test import TestCase
from django.contrib.auth import get_user_model

def create_user(email="user @example.com", password="testpassword"):

    return get_user_model().objects.create_user(email=email, password=password)

class ModelTests(TestCase):

    def setUp(self):

        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass'
        )

        dummy_recipe = {
            "user": user,
            "title": "Sample recipe title",
            "time_minutes": 5,
            "price": Decimal("5.05"),
            "description": "Test recipe description."
        }

        self.recipe = models.Recipe.objects.create(**dummy_recipe)

    def test_create_user_with_email_successful(self):

        email = 'mhdnaveen@example.com'
        password = 'Welcome!234'

        user = get_user_model().objects.create_user(
            email=email,
            password=password
            )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for a new user"""

        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com']
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'Welcome!234')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """Test that create a user without an email raises an error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', '123')

    def test_create_superuser(self):

        user = get_user_model().objects.create_superuser(
            'superuser@example.com', 'welcome!234'
        )

        self.assertEqual(user.is_superuser, True)
        self.assertEqual(user.is_staff, True)

    def test_delete_user(self):

        email = 'mhdnaveen@example.com'
        password = 'Welcome!234'

        user = get_user_model().objects.create_user(
                email=email,
                password=password
            )

        del_user = get_user_model().objects.delete_user(user.id)

        self.assertEqual(del_user, True)

    def test_create_recipe(self):
        """Test creating a recipe is successful"""

        self.assertEqual(str(self.recipe), self.recipe.title)

    def test_delete_recipe(self):
        """Test deleting a recipe is successful"""

        res = models.Recipe.objects.filter(id=self.recipe.id).delete()

        self.assertEqual(res[0], 1)

    def test_create_tags(self):

        user = create_user()

        tag = models.Tag.objects.create(user=user, name="test_tag")

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):

        user = create_user()

        ingredient = models.Ingredient.objects.create(
            user=user,
            name="test_ingredient"
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')