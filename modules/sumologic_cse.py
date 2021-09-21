import json
import requests
import time
import warnings
from logzero import logger
import logzero
from functools import wraps
try:
    import cookielib
except ImportError:
    import http.cookiejar as cookielib


# API RATE Limit constants
MAX_TRIES = 10
NUMBER_OF_CALLS = 1000
# per
PERIOD = 60  # in seconds


def backoff(func):
    @wraps(func)
    def limited(*args, **kwargs):
        delay = PERIOD / NUMBER_OF_CALLS *2
        tries = 0
        while tries < MAX_TRIES:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if e.response.status_code == 429:  # rate limited
                    lastException = e
                    tries += 1
                    logger.debug("Rate limited, sleeping for {0}s".format(delay))
                else:
                    raise
            logger.debug(f"delay: {delay} attempts: {tries}")
            time.sleep(delay)
            delay = delay * 2
        logger.debug("Rate limited function still failed after {0} retries.".format(MAX_TRIES))
        raise lastException
    return limited


class SumoLogicCSE(object):
    def __init__(self, api_key, endpoint, log_level='info', log_file=None, caBundle=None, cookieFile='cookies.txt', use_session=True):
        self.session = requests.Session()
        self.log_level = log_level
        self.set_log_level(self.log_level)
        if log_file:
            logzero.logfile(str(log_file))
        self.endpoint = endpoint
        self.use_session = use_session
        self.headers = {'content-type': 'application/json', 'X-API-Key': api_key}
        self.session.headers = self.headers
        if caBundle is not None:
            self.session.verify = caBundle
        cj = cookielib.FileCookieJar(cookieFile)
        self.session.cookies = cj
        if endpoint[-1:] == "/":
            self.endpoint = self.endpoint[:-1]
            warnings.warn(
                "Endpoint should not end with a slash character, it has been removed from your endpoint string.")

    def set_log_level(self, log_level):
        if log_level == 'info':
            self.log_level = log_level
            logzero.loglevel(level=20)
            return True
        elif log_level == 'debug':
            self.log_level = log_level
            logzero.loglevel(level=10)
            logger.debug("[SumologicCSE SDK] Setting logging level to 'debug'")
            return True
        else:
            raise Exception("Bad Logging Level")
            logger.info("[SumologicCSE SDK] Attempt to set undefined logging level.")
            return False

    def get_log_level(self):
        return self.log_level


    def get_versioned_endpoint(self, version):
        return self.endpoint+'/%s' % version

    @backoff
    def delete(self, method, params=None, headers=None, data=None):
        logger.debug("DELETE: " + self.endpoint + method)
        logger.debug("Headers:")
        logger.debug(headers)
        logger.debug("Params:")
        logger.debug(params)
        logger.debug("Body:")
        logger.debug(data)
        if self.use_session:
            r = self.session.delete(self.endpoint + method, params=params, headers=headers, data=data)
        else:
            r = requests.delete(self.endpoint + method, params=params, headers=headers, data=data, auth=self.auth)
        logger.debug("Response:")
        logger.debug(r)
        logger.debug("Response Body:")
        logger.debug(r.text)
        if r.status_code != 200:
            r.reason = r.text
        r.raise_for_status()
        return r

    @backoff
    def get(self, method, params=None, headers=None):
        logger.debug("GET: " + self.endpoint + method)
        logger.debug("Headers:")
        logger.debug(headers)
        logger.debug("Params:")
        logger.debug(params)
        if self.use_session:
            r = self.session.get(self.endpoint + method, params=params, headers=headers)
        else:
            r = requests.get(self.endpoint + method, params=params, headers=headers, auth=self.auth)

        logger.debug("Response:")
        logger.debug(r)
        logger.debug("Response Body:")
        logger.debug(r.text)
        if r.status_code != 200:
            r.reason = r.text
        r.raise_for_status()
        return r

    @backoff
    def post(self, method, data, headers=None, params=None):
        logger.debug("POST: " + self.endpoint + method)
        logger.debug("Headers:")
        logger.debug(headers)
        logger.debug("Params:")
        logger.debug(params)
        logger.debug("Body:")
        logger.debug(data)
        if self.use_session:
            r = self.session.post(self.endpoint + method, data=json.dumps(data), headers=headers, params=params)
        else:
            r = requests.post(self.endpoint + method, data=json.dumps(data), headers={**self.headers, **headers}, params=params, auth=self.auth)
        logger.debug("Response:")
        logger.debug(r)
        logger.debug("Response Body:")
        logger.debug(r.text)
        if r.status_code != 200:
            r.reason = r.text
        r.raise_for_status()
        return r

    @backoff
    def put(self, method, data, headers=None, params=None):
        logger.debug("PUT: " + self.endpoint + method)
        logger.debug("Headers:")
        logger.debug(headers)
        logger.debug("Params:")
        logger.debug(params)
        logger.debug("Body:")
        logger.debug(data)
        if self.use_session:
            r = self.session.put(self.endpoint + method, data=json.dumps(data), headers=headers, params=params)
        else:
            r = requests.put(self.endpoint + method, data=json.dumps(data), headers=headers, params=params, auth=self.auth)
        logger.debug("Response:")
        logger.debug(r)
        logger.debug("Response Body:")
        logger.debug(r.text)
        if r.status_code != 200:
            r.reason = r.text
        r.raise_for_status()
        return r

    def post_file(self, method, params, headers=None):
        """
        Handle file uploads via a separate post request to avoid having to clear
        the content-type header in the session.

        Requests (or urllib3) does not set a boundary in the header if the content-type
        is already set to multipart/form-data.  Urllib will create a boundary but it
        won't be specified in the content-type header, producing invalid POST request.

        Multi-threaded applications using self.session may experience issues if we
        try to clear the content-type from the session.  Thus we don't re-use the
        session for the upload, rather we create a new one off session.
        """

        post_params = {'merge': params['merge']}
        file_data = open(params['full_file_path'], 'rb').read()
        files = {'file': (params['file_name'], file_data)}
        r = requests.post(self.endpoint + method, files=files, params=post_params,
                auth=(self.session.auth[0], self.session.auth[1]), headers=headers)
        if 400 <= r.status_code < 600:
            r.reason = r.text
        r.raise_for_status()
        return r

    def get_threat_intel_indicators(self):
        r = self.get('/threat-intel-indicators')
        return r.json()

    def get_threat_intel_indicator(self, item_id):
        r = self.get('/threat-intel-indicators/' + str(item_id))
        return r.json()

    def update_threat_intel_indicator(self, item_id, item):
        r = self.put('/threat-intel-indicators/' + str(item_id), item)
        return r.json()

    def get_threat_intel_sources(self):
        r = self.get('/threat-intel-sources')
        return r.json()

    def get_threat_intel_source(self, item_id):
        r = self.get('/threat-intel-sources' + str(item_id))
        return r.json()

    def create_threat_intel_source(self, item):
        r = self.post('/threat-intel-sources', item)
        return r.json()

    def add_threat_indicators_to_source(self, source_id, threat_indicators):
        r = self.post('/threat-intel-sources/' + str(source_id) + '/items', threat_indicators)
        return r.json()
