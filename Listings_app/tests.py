from django.test import SimpleTestCase

from Listings_app.views import split_listing_images


class ListingImageParsingTests(SimpleTestCase):
    def test_split_listing_images_handles_multiple_urls(self):
        urls = split_listing_images(
            'https://cdn.example.com/a.jpg, https://cdn.example.com/b.jpg,https://cdn.example.com/c.jpg'
        )

        self.assertEqual(urls, [
            'https://cdn.example.com/a.jpg',
            'https://cdn.example.com/b.jpg',
            'https://cdn.example.com/c.jpg',
        ])

    def test_split_listing_images_handles_empty_values(self):
        self.assertEqual(split_listing_images(''), [])
