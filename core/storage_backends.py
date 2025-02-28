from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
import requests
from urllib.parse import urljoin


class MediaStorage(S3Boto3Storage):
    """
    Storage backend for Cloudflare R2 with Worker integration
    """

    location = "media"
    file_overwrite = False

    # R2-specific configuration
    custom_domain = settings.R2_CUSTOM_DOMAIN
    access_key = settings.R2_ACCESS_KEY_ID
    secret_key = settings.R2_SECRET_ACCESS_KEY
    bucket_name = settings.R2_STORAGE_BUCKET_NAME
    endpoint_url = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    region_name = "auto"  # R2 doesn't use regions in the same way as AWS
    addressing_style = "virtual"
    signature_version = "s3v4"

    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Override the default URL method to use the Worker URL when appropriate
        """
        if hasattr(settings, "USE_WORKER_URL") and settings.USE_WORKER_URL:
            # Generate URL through the Worker
            worker_url = settings.WORKER_URL
            worker_auth_key = settings.WORKER_AUTH_KEY

            # Build the complete URL to the file
            path = self._normalize_name(self._clean_name(name))
            file_url = urljoin(worker_url, path)

            return file_url
        else:
            # Use the default S3/R2 URL generation
            return super().url(name, parameters, expire, http_method)

    def worker_request(self, method, name, **kwargs):
        """
        Helper method to make requests to the Worker with authentication
        """
        worker_url = settings.WORKER_URL
        worker_auth_key = settings.WORKER_AUTH_KEY

        # Build the complete URL to the file
        path = self._normalize_name(self._clean_name(name))
        url = urljoin(worker_url, path)

        # Add the custom auth header
        headers = kwargs.get("headers", {})
        headers["X-Custom-Auth-Key"] = worker_auth_key
        kwargs["headers"] = headers

        # Make the request
        return requests.request(method, url, **kwargs)
