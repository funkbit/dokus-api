<?php

require('DokusService.php');

$dokus = new DokusService("frode@z-it.no", "trineuro83", "testzit");
//$dokus->setDebug(true);
$ivv = $dokus->customers->get(18869);

$customers = $dokus->customers->find(array('email' => 'svein.lindin@vinforedrag.no'));
print_r($customers);

$groups = $dokus->customerGroups->list();
print_r($groups);

/*
$invoice = array(
	'recipient'           => $ivv->id,
	'recipient_type'      => 'customer',
	'recipient_name'      => $ivv->name,
	'recipient_email'     => 'example@example.org',
	'recipient_address1'  => 'Testgata 1',
	'recipient_contact'   => 'Kari Kortholder',
	'recipient_zip_code'  => '0123',
	'recipient_zip_place' => 'OSLO',
	'recipient_country'   => 1,
	'description'         => 'Eksempelfaktura sendt fra Dokus API',
	'sender_ref'          => 'Ref 1',
	'recipient_ref'       => 'Ref 2',
	'send_date'           => date('Y-m-d'),
	'due_days'            => 14,
	'items'               => array(
		array(
			'name' => 'Fakturalinje 1',
			'unit_price' => 100,
			'quantity' => 25,
			'discount' => 0,
			'vat_class' => 1
		),
		array(
			'name' => 'Fakturalinje 2',
			'unit_price' => 100.00,
			'quantity' => 15.5,
			'discount' => 10,
			'vat_class' => 2
		)
	)
);
$invoice = $service->draftInvoices->save((object)$invoice);
$drafts = $dokus->draftInvoices->list();
*/