from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """
    Rate limit for the login endpoint.

    Limit:
        5 login attempts per minute per IP address.

    This protects the authentication endpoint from
    basic brute-force attempts without affecting
    authenticated API requests.
    """

    scope = "login"

    def get_cache_key(self, request, view):
        """
        Use the client IP address as the throttle identity.
        """

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.META.get("REMOTE_ADDR")

        if not client_ip:
            client_ip = "unknown"

        return self.cache_format % {
            "scope": self.scope,
            "ident": client_ip,
        }
