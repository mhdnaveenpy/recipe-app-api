from django.test import SimpleTestCase
from app import calc


class CalcTestCase(SimpleTestCase):
    """Test the calc function."""

    def test_add(self):
        """Test adding numbers together."""

        res = calc.add(5, 5)

        self.assertEqual(res, 10)

    def test_subtract(self):
        """Test subtracting numbers together."""

        res = calc.subtract(15, 10)

        self.assertEqual(res, 5)
