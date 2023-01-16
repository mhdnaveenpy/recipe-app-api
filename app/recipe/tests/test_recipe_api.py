from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from decimal import Decimal
import tempfile
import os
from PIL import Image

from core.models import (
    Recipe,
    Tag,
    Ingredient
)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPE_URL = reverse('recipe:recipe-list')

def get_details_url(recipe_id):

    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """Create and return an image upload URL"""

    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **kwargs):

    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 5,
        "price": Decimal("5.05"),
        "description": "Test recipe description.",
        "link": "http://example.com/recipe.pdf"
    }

    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe

def create_user(**kwargs):

    return get_user_model().objects.create_user(**kwargs)

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API request """

    def setUp(self):

        self.client = APIClient()

    def test_authentication_required(self):
        """Test auth is required to call the recipie API"""

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipieAPITests(TestCase):
    """Test authenticated API request"""

    def setUp(self):

        self.user = create_user(email='test@example.com',password='password@testuser')

        self.client = APIClient()

        self.client.force_authenticate(self.user)

    def test_retrive_recipe(self):
        """Test retriving the list recipes."""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrive_recipe_limited_to_user(self):

        limited_user = create_user(email = 'other@example.com', password = 'other@password')

        create_recipe(user=limited_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrive_detail_recipe(self):

        recipe = create_recipe(user=self.user)

        res = self.client.get(get_details_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_successful(self):
        """Test create a recipe successful"""

        payload = {
            "title": "Sample recipe title through post",
            "time_minutes": 5,
            "price": Decimal("5.05"),
            "description": "Test recipe description.",
            "link": "http://example.com/recipe.pdf"
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):

        original_link = 'http://example.com/recipe.pdf'

        recipe = create_recipe(
            user=self.user,
            title="Original Title",
            link=original_link
        )

        payload = {'title': 'Original Title New'}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

        self.assertEqual(recipe.link, original_link)

        self.assertEqual(recipe.title, payload['title'])

    def test_full_update(self):

        original_link = 'http://example.com/recipe.pdf'

        recipe = create_recipe(
            user=self.user,
            title="Original Title",
            description="Description of the original recipe",
            price=Decimal(5),
            time_minutes=60,
            link=original_link
        )

        payload = {
            'title': 'Original Title New',
            'description': 'Description of the original recipe new',
            'price': Decimal(12),
            'time_minutes': 30,
            'link': original_link
        }

        url = get_details_url(recipe.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):

        other_user = create_user(email = 'other@example.com', password = 'other@password')

        recipe = create_recipe(
            user=self.user,
            title="Original Title",
            description="Description of the original recipe",
            price=Decimal(5),
            time_minutes=60
        )

        payload = {'user': other_user}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):

        recipe = create_recipe(
            user=self.user,
            title="Original Title",
            description="Description of the original recipe",
            price=Decimal(5),
            time_minutes=60
        )

        url = get_details_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):

        other_user = create_user(email = 'other@example.com', password = 'other@password')

        recipe = create_recipe(
            user=other_user,
            title="Original Title",
            description="Description of the original recipe",
            price=Decimal(5),
            time_minutes=60
        )

        url = get_details_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):

        original_link = 'http://example.com/recipe.pdf'

        payload = {
            'title': 'Original Title New',
            'description': 'Description of the original recipe new',
            'price': Decimal(12),
            'time_minutes': 30,
            'link': original_link,
            'tags': [{'name': 'Indian'}, {'name': 'Dinner'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        recipes = recipes[0]

        self.assertEqual(recipes.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipes.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):

        original_link = 'http://example.com/recipe.pdf'

        ex_tag = Tag.objects.create(name='Turkey', user=self.user)

        payload = {
            'title': 'Original Title New',
            'description': 'Description of the original recipe new',
            'price': Decimal(12),
            'time_minutes': 30,
            'link': original_link,
            'tags': [{'name': 'Turkey'}, {'name': 'Dinner'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        recipes = recipes[0]

        self.assertEqual(recipes.tags.count(), 2)

        self.assertIn(ex_tag, recipes.tags.all())

        for tag in payload['tags']:
            exists = recipes.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_update(self):

        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name='Lunch')

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')

        recipe = create_recipe(user=self.user)

        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')

        payload = {'tags': [{'name': 'Lunch'}]}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(tag_lunch, recipe.tags.all())

        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tag(self):

        tag = Tag.objects.create(user=self.user, name='Dessert')

        recipe = create_recipe(user=self.user)

        recipe.tags.add(tag)

        payload = {'tags': []}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):

        original_link = 'http://example.com/recipe.pdf'

        payload = {
            'title': 'Original Title New',
            'description': 'Description of the original recipe new',
            'price': Decimal(12),
            'time_minutes': 30,
            'link': original_link,
            'ingredients': [{'name': 'mango'}, {'name': 'rose'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        recipes = recipes[0]

        self.assertEqual(recipes.ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            exists = recipes.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):

        original_link = 'http://example.com/recipe.pdf'

        ex_ingredient = Ingredient.objects.create(user=self.user, name="mango")

        payload = {
            'title': 'Original Title New',
            'description': 'Description of the original recipe new',
            'price': Decimal(12),
            'time_minutes': 30,
            'link': original_link,
            'ingredients': [{'name': 'mango'}, {'name': 'rose'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        recipes = recipes[0]

        self.assertEqual(recipes.ingredients.count(), 2)

        self.assertIn(ex_ingredient, recipes.ingredients.all())

        for ingredient in payload["ingredients"]:
            exists = recipes.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()

            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):

        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'mango'}]}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(user=self.user, name='mango')

        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_ingredient_on_update(self):

        ingredient_1 = Ingredient.objects.create(user=self.user, name='mango')

        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(ingredient_1)

        payload = {'ingredients': [{'name': 'banana'}]}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(user=self.user, name='banana')

        self.assertIn(new_ingredient, recipe.ingredients.all())

        self.assertNotIn(ingredient_1, recipe.ingredients.all())

    def test_clear_ingredients(self):

        ingredient_1 = Ingredient.objects.create(user=self.user, name='mango')

        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(ingredient_1)

        payload = {'ingredients': []}

        url = get_details_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering by tags"""

        r1 = create_recipe(user=self.user, title="Butter Chicken")

        r2 = create_recipe(user=self.user, title="Chicken Sanwitch")

        tag1 = Tag.objects.create(user=self.user, name="Indian")

        tag2 = Tag.objects.create(user=self.user, name="Breakfast")

        r1.tags.add(tag1)

        r2.tags.add(tag2)

        r3 = create_recipe(user=self.user, title="Fish and Chips")

        filter = {'tags': f'{tag1.id},{tag2.id}'}

        res = self.client.get(RECIPE_URL, filter)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(s1.data, res.data)

        self.assertIn(s2.data, res.data)

        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredient(self):
        """Test filtering by tags"""

        r1 = create_recipe(user=self.user, title="Butter Chicken")

        r2 = create_recipe(user=self.user, title="Chicken Sanwitch")

        in1 = Ingredient.objects.create(user=self.user, name="Butter")

        in2 = Ingredient.objects.create(user=self.user, name="Bread")

        r1.ingredients.add(in1)

        r2.ingredients.add(in2)

        r3 = create_recipe(user=self.user, title="Fish and Chips")

        filter = {'ingredients': f'{in1.id},{in2.id}'}

        res = self.client.get(RECIPE_URL, filter)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(s1.data, res.data)

        self.assertIn(s2.data, res.data)

        self.assertNotIn(s3.data, res.data)

class ImageUploadTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password@example',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)

        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""

        url = image_upload_url(self.recipe.id)

        payload = {'image': 'invalid_image'}

        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)



