# encoding=utf-8
"""
Copyright (c) 2010, Funkbit AS.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the Dokus service nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY FUNKBIT AS ''AS IS''
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL FUNKBIT AS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import base64
import httplib
import json
import re
import string 
import urllib

from datetime import date, datetime
from decimal import Decimal

class DokusObject(object):
    """
    Base object for resources used with pyDokus.
    """
    
    def __init__(self, **kwargs):
        
        for key, value in kwargs.items():
            setattr(self, key, value)

class DokusJSONEncoder(json.JSONEncoder):
    """
    Supports serializing datetimes/dates/decimals as JSON.
    """

    def default(self, obj):

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, DokusObject):
            return obj.__dict__
        elif isinstance(obj, Decimal):
            return unicode(obj)
        else:
            return json.JSONEncoder.default(self, obj)
                
def DokusJSONDecoder(d):
    """
    Parses dates/datetimes/decimals in decoded JSON.
    """
    
    pattern_date = re.compile('\d{4}-\d{2}-\d{2}$')
    pattern_datetime = re.compile('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
    pattern_decimal = re.compile('\d+\.\d+$')
    
    obj = DokusObject()
    for a, b in d.items():
        
        # Parse datetimes and decimals
        if pattern_datetime.match(unicode(b)):
            b = datetime.strptime(b, '%Y-%m-%d %H:%M:%S')
        elif pattern_date.match(unicode(b)):
            b = datetime.strptime(b, '%Y-%m-%d').date()
        elif pattern_decimal.match(unicode(b)):
            b = Decimal(b)
            
        if isinstance(b, (list, tuple)):
            setattr(obj, a, [obj(x) if isinstance(x, dict) else x for x in b])
        else:
            setattr(obj, a, obj(b) if isinstance(b, dict) else b)

    return obj

class DokusService(object):
    """
    pyDokus client library for accessing Dokus API (http://dokus.no).
    """
    
    # URL and port for the service
    DEBUG = False
    SERVICE_URL = '%(subdomain)s.dokus.no'
    SERVICE_PORT = 443

    def __init__(self, email, password, subdomain):
        """
        Initializes the client with the specified credentials.
        """
        
        self.email = email
        self.password = password
        self.subdomain = subdomain

        self.add_resource('customers', DokusService.CustomerHandler)
        self.add_resource('products', DokusService.ProductHandler)
        self.add_resource('draft_invoices', DokusService.DraftInvoiceHandler)
        self.add_resource('sent_invoices', DokusService.SentInvoiceHandler)
        self.add_resource('vouchers', DokusService.VoucherHandler)
        
    def add_resource(self, name, handler):
        """
        Initializes the handler with this service instance.
        """

        setattr(self, name, handler(self))
            
    ############
    # REQUESTS #
    ############
    
    def _request(self, url, method='GET', params={}):
        """
        Performs an HTTP request, with the specified parameters and method.
        """

        # Prepare connection and construct authorization header
        connection = httplib.HTTPSConnection(self.SERVICE_URL % { 'subdomain': self.subdomain }, self.SERVICE_PORT)
        auth = 'Basic ' + string.strip(base64.encodestring(self.email + ':' + self.password)) 

        if method == 'GET':

            params = self.url_serialize(params)
            connection.request(method, url + '?' + params, None, {
                'Accept': 'application/json',
                'Authorization': auth,
            })
            
        else:
            
            params = self.json_serialize(params)
            connection.request(method, url, params, {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': auth,
            })
            
        # Fetch and reserialize response
        response = connection.getresponse()
        data = response.read()
        if self.DEBUG:
            print response.status
            print data
        
        try:
            obj = json.loads(data, object_hook=DokusJSONDecoder, encoding='utf-8')
        except:
            obj = None
        
        return response.status, obj

    def _list(self, url, criteria=None, retattr=None):
        """
        Gets the resources at the specified URL, optionally filtered by criteria.
        """
        
        status, data = self._request(url, params=criteria)
        if retattr:
            return getattr(data, retattr) if status == 200 else None
        else:
            return data if status == 200 else None
    
    def _get(self, url, id, retattr=None):
        """
        Gets the specific resource at the specified URL and ID.
        """
        
        status, data = self._request('%(url)s%(id)d/' % { 'url': url, 'id': id })
        if retattr:
             return getattr(data, retattr) if status == 200 else None
        else:
            return data if status == 200 else None
            
    def _save(self, url, obj, retattr=None, extra_params={}):
        """
        Creates/updates the specified resource at the URL.
        Creation/update is done based on if the ID of the resource is set.
        """

        # Create or update object?
        params = extra_params
        if hasattr(obj, 'id'):
            params['id'] = obj.id
            url = url + '%(id)d/' % params
        else:
            url = url + 'create/' % params
        
        status, data = self._request(url, method='POST', params=obj)
        if retattr:
             return getattr(data, retattr) if status == 200 else None
        else:
            return data if status == 200 else None

    def _delete(self, url, obj, extra_params={}):
        """
        Deletes the specified resource at the URL and ID.
        """
        
        if not hasattr(obj, 'id'):
            return None
            
        # Delete object
        params = extra_params
        params['id'] = obj.id
        url = url % params
        status, data = self._request(url, method='POST')

        return (status == 204)
       
    ###############
    # SERIALIZERS #
    ###############

    def url_serialize(self, obj):
        """
        Returns the specified dictionary as a URL encoded string, suitable for HTTP GET.
        """
        
        if not obj:
            return ''
        
        params = []
        for key, value in obj.items():
            params.append((key, value))

        return urllib.urlencode(params)

    def json_serialize(self, obj):
        """
        Returns the specified object encoded as JSON, suitable for HTTP POST.
        """

        if not obj:
            return '{}'
        
        if hasattr(obj, '__dict__'):
            obj = obj.__dict__
        
        return json.dumps(obj, cls=DokusJSONEncoder)
            
    #####################
    # RESOURCE HANDLERS #
    #####################

    class BaseHandler(object):
        """
        Base class for implementing handlers, providing resource operations.
        Handlers override URLs and attributes to provide access to specific resources, and
        can add specific methods on resources as needed.
        """

        url = ''
        retattr_single = ''
        retattr_multi = ''
        
        def __init__(self, service):
            self.service = service
        def list(self):
            return self.service._list(self.url, criteria=None, retattr=self.retattr_multi)
        def find(self, **kwargs):
            return self.service._list(self.url, criteria=kwargs, retattr=self.retattr_multi)
        def get(self, id):
            return self.service._get(self.url, id, retattr=self.retattr_single)
        def save(self, obj):
            return self.service._save(self.url, obj, retattr=self.retattr_single)
        def delete(self, obj): 
            return self.service._delete(self.url + unicode(obj.id) + '/delete/', obj)

    class CustomerHandler(BaseHandler):
        
        url = '/customers/'
        retattr_single = 'customer'
        retattr_multi = 'customers'
    
    class CustomerGroupHandler(BaseHandler):
        
        url = '/customers/groups/'
        retattr_single = 'group'
        retattr_multi = 'groups'
    
    class ProductHandler(BaseHandler):

        url = '/products/'
        retattr_single = 'product'
        retattr_multi = 'products'

    class DraftInvoiceHandler(BaseHandler):
        
        url = '/invoices/'
        retattr_single = 'invoice'
        retattr_multi = 'invoices'
        
        def send(self, obj, send_by_post=False, send_by_email=False, email_copy1='', email_copy2=''):
            
            self.service._request(self.url + unicode(obj.id) + '/send/', method='POST', params={
                'send_by_post': send_by_post,
                'send_by_email': send_by_email,
                'send_copy1': (email_copy1 != ''),
                'send_copy1_address': email_copy1,
                'send_copy2': (email_copy2 != ''),
                'send_copy2_address': email_copy2,
            })
    
    class RecurringInvoiceHandler(BaseHandler):

        url = '/invoices/recurring/'
        retattr_single = 'invoice'
        retattr_multi = 'recurring_invoices'
        
        def send(self, obj, send_by_post=False, send_by_email=False, email_copy1='', email_copy2=''):
            
            self.service._request(self.url + ('%d/send/' % obj.id), method='POST', params={
                'send_by_post': send_by_post,
                'send_by_email': send_by_email,
                'send_copy1': (email_copy1 != ''),
                'send_copy1_address': email_copy1,
                'send_copy2': (email_copy2 != ''),
                'send_copy2_address': email_copy2,
            })
        
    class SentInvoiceHandler(BaseHandler):

        url = '/invoices/sent/'
        retattr_single = 'sent_invoice'
        retattr_multi = 'sent_invoices'

        def save(self, obj):
            
            raise Exception('Cannot modify sent invoices.')

        def delete(self, obj):
            
            raise Exception('Cannot modify sent invoices.')

        def create_credit_invoice(self, invoice):
            
            status, data = self.service._request(self.url + ('%d/credit/create/' % invoice.id), method='POST')
            return data.invoice if status == 200 else None
            
        def create_reminder_invoice(self, invoice):
            
            status, data = self.service._request(self.url + ('%d/reminder/create/' % invoice.id), method='POST')
            return data.invoice if status == 200 else None
            
        def add_payment(self, invoice, payment):
            
            status, data = self.service._request(self.url + ('%d/payments/create/' % invoice.id), method='POST', params=payment)
            return data.payment if status == 200 else None
            
        def remove_payment(self, invoice, payment):
            
            status, data = self.service._request(self.url + ('%d/payments/%d/delete/' % (invoice.id, payment.id)), method='POST')
            return (status == 204)
