from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import (
    Ingredient,
    Recipe
)
from recipe.serializers import IngredientSerializer
from django.urls import reverse
from decimal import Decimal

INGREDIENT_URL = reverse('recipe:ingredient-list')

def get_detail_url(id):

    return reverse('recipe:ingredient-detail', args=[id])

def create_user(email="test@example.com", password="testpassword"):

    return get_user_model().objects.create_user(email=email, password=password)

def create_ingredient(**kwargs):

    return Ingredient.objects.create(**kwargs)


class PublicIngredientApiTestCase(TestCase):

    def setUp(self):

        self.client = APIClient()

    def test_auth_required(self):

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTestCase(TestCase):

    def setUp(self):

        self.user = create_user()

        self.client = APIClient()

        self.client.force_authenticate(self.user)

    def test_retrive_ingredient(self):

        create_ingredient(user=self.user, name="Chilli Powder")
        create_ingredient(user=self.user, name="water")

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient = Ingredient.objects.all().order_by('-name')

        serializer = IngredientSerializer(ingredient, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):

        other_user = create_user(email="other@exampl.com", password="password@other")

        create_ingredient(user=other_user, name="Chilli Powder")
        create_ingredient(user=self.user, name="water")

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient = Ingredient.objects.filter(user=self.user).order_by('-name')

        serializer = IngredientSerializer(ingredient, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_update_ingredient(self):

        ingredient = create_ingredient(user=self.user, name="Rose Water")

        payload = {'name': 'Banana'}

        url = get_detail_url(ingredient.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):

        ingredient = create_ingredient(user=self.user, name="Rose Water")

        url = get_detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredient_assigned_to_recipe(self):

        in1 = Ingredient.objects.create(user=self.user, name="Butter")

        in2 = Ingredient.objects.create(user=self.user, name="Bread")

        recipe = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {"assigned_only": 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):

        in1 = Ingredient.objects.create(user=self.user, name="Butter")
        Ingredient.objects.create(user=self.user, name="Batter")

        recipe1 = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe1.ingredients.add(in1)

        recipe2 = Recipe.objects.create(
            title="Butter Masala",
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe2.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 1)