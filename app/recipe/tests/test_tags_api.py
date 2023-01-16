from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse

from recipe import serializers
from core.models import (
    Tag,
    Recipe,
)

from decimal import Decimal

TAGS_URL = reverse('recipe:tag-list')

def get_detail_url(id):

    return reverse('recipe:tag-detail', args=[id])

def create_user(email="test@example.com", password="testpassword"):

    return get_user_model().objects.create_user(email=email, password=password)

def create_tag(**kwargs):

    return Tag.objects.create(**kwargs)

class PublicTagApiTestCase(TestCase):

    def setUp(self):

        self.client = APIClient()

    def test_auth_required(self):

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagApiTestCase(TestCase):

    def setUp(self):

        self.user = create_user()

        self.client = APIClient()

        self.client.force_authenticate(self.user)

    def test_retrive_tags(self):

        create_tag(user=self.user, name="Tag1")
        create_tag(user=self.user, name="Tag2")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = serializers.TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):

        other_user = create_user(email="other@example.com", password="password@other")

        create_tag(user=other_user, name="Tag1")

        tag = create_tag(user=self.user, name="Tag2")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(user=self.user).order_by('-name')

        serializer = serializers.TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_update_tag(self):

        tag = create_tag(user=self.user, name="Tag1")

        payload = {'name': 'Tag Changed'}

        url = get_detail_url(tag.id)

        res = self.client.patch(url, payload)

        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):

        tag = create_tag(user=self.user, name="Tag1")

        url = get_detail_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tag_assigned_to_recipe(self):

        tag1 = Tag.objects.create(user=self.user, name="Butter")

        tag2 = Tag.objects.create(user=self.user, name="Bread")

        recipe = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = serializers.TagSerializer(tag1)
        s2 = serializers.TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):

        tag1 = Tag.objects.create(user=self.user, name="Butter")
        Tag.objects.create(user=self.user, name="Bun")

        recipe1 = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe1.tags.add(tag1)

        recipe2 = Recipe.objects.create(
            title="Apple Crumble1",
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )

        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 1)




