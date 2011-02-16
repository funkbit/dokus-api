<?php
require('DokusService.php');

// Replace email, password and subdomain with your proper credentials
$dokus = new DokusService("bruker@dokus.no", "passord", "mittfirma");

// List names and e-mail address for all customers
foreach ($dokus->customers->list() as $customer) {
	printf("Customer name: %s, email: %s\n", $customer->name, $customer->email);
}

// List all products
foreach ($dokus->products->list() as $product) {
	printf("Product name: %s, price: %s\n", $product->name, $product->price);
}

// Creates a new customer
$newCustomer = array(
	'name' => 'Ny kunde',
	'email' => 'kontakt@nykunde.no',
	'org_number' => '',
	'country' => 1
);
$newCustomer = $dokus->customers->save($newCustomer);
printf("Created customer with ID %d\n", $newCustomer->id);

// Create an invoice draft
$invoice = array(
	'recipient' => $newCustomer->id,
	'recipient_type' => 'customer',
	'recipient_name' => $newCustomer->name,
	'recipient_email' => 'example@example.org',
	'recipient_address1' => 'Testgata 1',
	'recipient_contact' => 'Kari Kortholder',
	'recipient_zip_code' => '0123',
	'recipient_zip_place' => 'OSLO',
	'recipient_country' => 1,
	'description' => 'Eksempelfaktura sendt fra Dokus API',
	'sender_ref' => 'Ref 1',
	'recipient_ref' => 'Ref 2',
	'send_date' => date('Y-m-d'),
	'due_days' => 14,
	'items' => array(
		array(
			'name' => 'Fakturalinje 1',
			'unit_price' => 100,
			'quantity' => 25,
			'discount' => 0,
			'vat_class' => DokusService::VAT_REGULAR
		),
		array(
			'name' => 'Fakturalinje 2',
			'unit_price' => '100.00',
			'quantity' => '15.5',
			'discount' => 10,
			'vat_class' => DokusService::VAT_LOW
		)
	)
);
$invoice = $dokus->draftInvoices->save($invoice);
printf("Created draft invoice with ID %d\n", $invoice->id);

// Send the invoice (set $send_enabled to true to send invoice)
$send_enabled = false;
if ($send_enabled) {
	$dokus->draftInvoices->send($invoice, false, true, 'kopi@mittfirma.no');
	printf("The invoice has been sent to %s!", $invoice->recipient_email);
}

// Lists the invoice numbers of all sent invoices
foreach ($dokus->sentInvoices->list() as $sentInvoice) {
	printf("Invoice no. %d, sent %s", $sentInvoice->invoice_number, $sentInvoice->sent_date);
}
