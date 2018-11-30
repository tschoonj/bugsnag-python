import bugsnag
from bugsnag.wsgi import request_path

has_flask = False
try:
    from flask import got_request_exception, request, request_started, session
    has_flask = True
except ImportError:
    pass


def handle_exceptions(app):
    got_request_exception.connect(__log_exception, app)
    request_started.connect(__track_session, app)


class RequestMiddleware(object):
    def __init__(self, next_call):
        self.next_call = next_call

    def __call__(self, notification):
        if has_flask:
            if notification.context is None:
                path = request_path(request.environ)
                notification.context = "%s %s" % (request.method, path)

            if "id" not in notification.user:
                notification.set_user(id=request.remote_addr)
            notification.add_tab("session", dict(session))
            notification.add_tab("environment", dict(request.environ))
            notification.add_tab("request", {
                "url": request.base_url,
                "headers": dict(request.headers),
                "params": dict(request.form),
                "data": request.get_json() or dict(body=request.data)
            })
        self.next_call(notification)


# pylint: disable-msg=W0613
def __log_exception(sender, exception, **extra):
    bugsnag.auto_notify(exception, severity_reason={
        "type": "unhandledExceptionMiddleware",
        "attributes": {
            "framework": "Flask"
        }
    })


def __track_session(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()
