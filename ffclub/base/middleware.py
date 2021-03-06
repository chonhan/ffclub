import re
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
import commonware.log


log = commonware.log.getLogger('ffclub')
old_ie_patterns = re.compile(".*MSIE [6-8]\.")


class BrowserDetectionMiddleware(object):
    def process_request(self, request):
        if old_ie_patterns.match(request.META['HTTP_USER_AGENT']):
            redirect_path = reverse('not.supported')
            if request.path != redirect_path and not request.path.startswith('/campaign/'):
                return HttpResponsePermanentRedirect(redirect_path)


class LoggingMiddleware(object):
    def process_request(self, request):
        log.info(request.path, extra={'request': request,})

    def process_exception(self, request, exception):
        log.exception(exception, exc_info=True, extra={'request': request,})


class UserFullnameMiddleware(object):
    def process_request(self, request):
        if request.user:
            try:
                profile = request.user.get_profile()
                request.user.fullname = profile.fullname
            except ObjectDoesNotExist:
                pass
            except AttributeError:
                pass
