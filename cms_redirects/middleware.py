from cms_redirects.models import CMSRedirect
from django import http
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


def get_redirect(old_path):
    try:
        r = CMSRedirect.objects.get(site__id__exact=settings.SITE_ID,
                                    old_path=old_path)
    except CMSRedirect.DoesNotExist:
        r = None
    return r


def remove_slash(path):
    return path[:path.rfind('/')]+path[path.rfind('/')+1:]


def remove_query(path):
    return path.split('?', 1)[0]


class RedirectFallbackMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, http.Http404):

            # First try the whole path.
            path = request.get_full_path()
            r = get_redirect(path)

            # Isolate the query string
            if path.count('?'):
                qs = path.split('?')[1]
            else:
                qs = None

            # It could be that we need to try without a trailing slash.
            if r is None and settings.APPEND_SLASH:
                r = get_redirect(remove_slash(path))

            # It could be that the redirect is defined without a query string.
            if r is None and path.count('?'):
                r = get_redirect(remove_query(path))

            # It could be that we need to try without query string and without a trailing slash.
            if r is None and path.count('?') and settings.APPEND_SLASH:
                r = get_redirect(remove_slash(remove_query(path)))


            if r is not None:
                if r.page:
                    new_url = r.page.get_absolute_url()
                    if qs:
                        new_url = new_url + '?' + qs
                    if r.response_code == '302':
                        return http.HttpResponseRedirect(new_url)
                    else:
                        return http.HttpResponsePermanentRedirect(new_url)
                if r.new_path == '':
                    return http.HttpResponseGone()
                if r.response_code == '302':
                    new_url = r.new_path
                    # Only append the querystring if the new path doesn't have it's own
                    if qs and not r.new_path.count('?'):
                        new_url = new_url + '?' + qs
                    return http.HttpResponseRedirect(new_url)
                else:
                    new_url = r.new_path
                    # Only append the querystring if the new path doesn't have it's own
                    if qs and not r.new_path.count('?'):
                        new_url = new_url + '?' + qs
                    return http.HttpResponsePermanentRedirect(new_url)


