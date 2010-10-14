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

from datetime import timedelta
from pydokus import *

# Replace email, password and subdomain with your proper credentials
service = DokusService(email='bruker@dokus.no', password='passord', subdomain='mittfirma')

# List names and e-mail address for all customers
for customer in service.customers.list():
    print "Customer name: %s, email: %s" % (customer.name, customer.email)
    
# List all products
for product in service.products.list():
    print "Product name: %s, price: %s" % (product.name, product.price)

# Creates a new customer
new_customer = DokusObject(
    name='Ny kunde AS',
    email='kontakt@nykunde.no',
    org_number='',
    country=1,
)

new_customer = service.customers.save(new_customer)
print "Created customer with ID %d" % new_customer.id

# Create an invoice draft
invoice = DokusObject(
    recipient=customer.id,
    recipient_type='customer',
    recipient_name=customer.name,
    recipient_email='example@example.org',
    recipient_address1='Testgata 1',
    recipient_contact='Kari Kortholder',
    recipient_zip_code='0123',
    recipient_zip_place='OSLO',
    recipient_country=1,
    description='Eksempelfaktura sendt fra Dokus API',
    sender_ref='Ref 1',
    recipient_ref='Ref 2',
    send_date=date.today(),
    due_days=14,
    items=[
        {
            'name': 'Fakturalinje 1',
            'unit_price': 100,
            'quantity': 25,
            'discount': 0,
            'vat_class': 1
        },
        {
            'name': 'Fakturalinje 2',
            'unit_price': Decimal('100.00'),
            'quantity': Decimal('15.5'),
            'discount': 10,
            'vat_class': 2
        }
    ]
)

invoice = service.draft_invoices.save(invoice)
print "Created draft invoice with ID %d" % invoice.id

# Send the invoice (set send_enabled to True to send invoice)
send_enabled = False
if send_enabled:
    service.draft_invoices.send(invoice, send_by_email=True, send_by_post=False, email_copy1='kopi@mittfirma.no')
    print "The invoice has been sent to %s!" % invoice.recipient_email

# Lists the invoice numbers of all sent invoices
for sent_invoice in service.sent_invoices.list():
    print "Invoice no. %d, sent %s" % (sent_invoice.invoice_number, sent_invoice.sent_date)
