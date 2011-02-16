<?php
/**
 * PHP client library for accessing the Dokus API (http://dokus.no/).
 * Implements all currently stable resources of the Dokus API, using lazy loading
 * of resources as they are requested.
 * Requires PHP 5.1.3 or newer.
 *
 * @author Frode Danielsen, <frode@z-it.no>
 * @version 1.0
 */
class DokusService {
	const SERVICE_URL = 'https://%s.dokus.no';
	const SERVICE_PORT = 443;

	private static $resources = array(
		'customers',
		'customerGroups',
		'products',
		'draftInvoices',
		'recurringInvoices',
		'sentInvoices'
	);

	private $debug = false;

	// API access details
	private $email;
	private $password;
	private $subdomain;

	// Resource access points. Private due to lazy loading through __get()
	private $customersResource;
	private $customerGroupsResource;
	private $productsResource;
	private $draftInvoicesResource;
	private $sentInvoicesResource;

	/**
	 * Constructs a new Dokus API client for a specific Dokus user account.
	 *
	 * @param string $email     User email address.
	 * @param string $password  User password.
	 * @param string $subdomain User subdomain name.
	 */
	public function __construct ($email, $password, $subdomain) {
		if (function_exists('curl_init') === false) {
			throw new Exception("DokusService requires PHP compiled with the Client URL Library (curl).");
		}

		$this->email = $email;
		$this->password = $password;
		$this->subdomain = $subdomain;
	}

	/**
	 * Toggles debug mode on/off.
	 *
	 * @param bool $debug Debug mode status.
	 */
	public function setDebug ($debug) {
		$this->debug = (bool)$debug;
	}

	/**
	 * Sends a raw Dokus API request to the Dokus resource represented by the URL given.
	 * This should generally not be used directly, all resource instances abstract these requests.
	 *
	 * @param string $url Absolute path to the Dokus resource.
	 * @param string $method HTTP request method.
	 * @param object $params Request parameters.
	 * @return object The response from the Dokus resource.
	 */
	public function request ($url, $method = 'GET', $params = null) {
		$url = sprintf(self::SERVICE_URL, $this->subdomain) . $url;
		$req = curl_init($url);
		$headers = array(
			'Accept: application/json'
		);

		if ($this->debug === true) {
			curl_setopt($req, CURLOPT_VERBOSE, true);
			curl_setopt($req, CURLOPT_STDERR, STDOUT);
		}

		if ($method == 'POST') {
			curl_setopt($req, CURLOPT_POST, true);
			$headers[] = 'Content-Type: application/json';
			if (!empty($params)) {
				curl_setopt($req, CURLOPT_POSTFIELDS, json_encode($params));
			}
		}
		else {
			curl_setopt($req, CURLOPT_HTTPGET, true);
			if (!empty($params)) {
				curl_setopt($req, CURLOPT_URL, $url . '?' . http_build_query($params));
			}
		}

		curl_setopt_array($req, array(
			CURLOPT_PORT => self::SERVICE_PORT,
			CURLOPT_HEADER => true,
			CURLOPT_RETURNTRANSFER => true,
			CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
			CURLOPT_USERPWD =>  "{$this->email}:{$this->password}",
			CURLOPT_HTTPHEADER => $headers
		));

		$response = curl_exec($req);
		list($headers, $body) = explode("\r\n\r\n", $response);

		// Find response status
		preg_match('/^HTTP\/1\.[01] (\d+)/', $headers, $match);
		$status = $match[1];

		// TODO: Wrap in DokusResponse object
		return (object)array(
			'status' => $status,
			'data' => json_decode($body)
		);
	}

	/**
	 * Access point for Dokus API resources which only creates new resource instances as needed (lazy loading).
	 * See the $resources list for currently available resources.
	 */
	public function __get ($var) {
		if (in_array($var, self::$resources)) {
			$var = $var . 'Resource';
			if (!isset($this->$var)) {
				$class = 'Dokus' . ucfirst($var);
				$this->$var = new $class($this);
			}
			return $this->$var;
		}
	}
}

/**
 * Base class for Dokus resources, implementing common convenience methods for fetching and saving data.
 */
class DokusBaseResource {
	private $service;

	protected $path = '';
	protected $respAttrSingle = '';
	protected $respAttrMultiple = '';

	public function __construct ($service) {
		$this->service = $service;
	}

	public function all () {
		$response = $this->service->request($this->path);
		return $response->data !== null ? $response->data->{$this->respAttrMultiple} : null;
	}

	public function find (array $criteria) {
		$response = $this->service->request($this->path, 'GET', $criteria);
		return $response->data !== null ? $response->data->{$this->respAttrMultiple} : null;
	}

	public function get ($id) {
		$response = $this->service->request($this->path . $id . '/');
		return $response->data !== null ? $response->data->{$this->respAttrSingle} : null;
	}

	public function save ($object) {
		if (is_array($object)) {
			$object = (object)$object;
		}

		$path = $this->path . (isset($object->id) ? $object->id : 'create') . '/';
		$response = $this->service->request($path, 'POST', $object);
		return $response->data !== null ? $response->data->{$this->respAttrSingle} : null;
	}

	public function delete ($objectOrId) {
		if (is_object($objectOrId) && !isset($objectOrId->id)) {
			return false;
		}

		$id = is_object($objectOrId) ? $objectOrId->id : $objectOrId;
		$response = $this->service->request($this->path . $id . '/delete/', 'POST');
		return ($response->status == 204);
	}

	/**
	 * 'list' is a keyword in PHP and can't be used as a method name, so to maintain a 1-to-1 mapping
	 * with the original Dokus Python API we intercept calls to unknown methods and map 'list' to our
	 * internal 'all' method.
	 */
	public function __call ($method, $arguments) {
		if ($method === 'list') {
			return $this->all();
		}
	}
}

/**
 * Dokus Customers Resource.
 * Supports fetching, updating and creating new customers.
 */
class DokusCustomersResource extends DokusBaseResource {
	protected $path = '/customers/';
	protected $respAttrSingle = 'customer';
	protected $respAttrMultiple = 'customers';
}

/**
 * Dokus Customer Groups Resource.
 * Supports fetching, updating and creating new customer groups.
 */
class DokusCustomerGroupsResource extends DokusBaseResource {
	protected $path = '/customers/groups/';
	protected $respAttrSingle = 'group';
	protected $respAttrMultiple = 'groups';
}

/**
 * Dokus Products Resource.
 * Supports fetching, updating and creating new products.
 */
class DokusProductsResource extends DokusBaseResource {
	protected $path = '/products/';
	protected $respAttrSingle = 'product';
	protected $respAttrMultiple = 'products';
}

/**
 * Dokus Invoices Resource.
 * Foundation for all invoice types.
 * Handles sending invoices by email to clients.
 */
class DokusInvoicesResource extends DokusBaseResource {
	protected $path = '/invoices/';
	protected $respAttrSingle = 'invoice';
	protected $respAttrMultiple = 'invoices';

	/**
	 * Sends a draft invoice to the client.
	 *
	 * @param object $invoice The invoice to send.
	 * @param bool $byPost    TRUE for sending the invoice by post.
	 * @param bool $byEmail   TRUE for sending the invoice by email.
	 * @param string $emailCopy1 E-mail address for receiving a copy of the invoice sent.
	 * @param string $emailCopy2 Extra e-mail address for receiving a copy of the invoice sent.
	 */
	public function send ($invoice, $byPost = false, $byEmail = false, $emailCopy1 = '', $emailCopy2 = '') {
		$params = array(
			'send_by_post'       => $byPost,
            'send_by_email'      => $byEmail,
            'send_copy1'         => ($emailCopy1 != ''),
            'send_copy1_address' => $emailCopy1,
            'send_copy2'         => ($emailCopy2 != ''),
            'send_copy2_address' => $emailCopy2,
		);
		// XXX: No response?
		$this->service->request($this->path . $invoice->id . '/send/', 'POST', (object)$params);
	}
}

/**
 * Dokus Draft Invoices Resource.
 * Currently no different from base invoices.
 */
class DokusDraftInvoicesResource extends DokusInvoicesResource {}

/**
 * Dokus Recurring Invoices Resource.
 * Supports fetching, updating and creating new recurring invoices.
 */
class DokusRecurringInvoicesResource extends DokusInvoicesResource {
	protected $path = '/invoices/recurring/';
	protected $respAttrSingle = 'invoice';
	protected $respAttrMultiple = 'recurring_invoices';
}

/**
 * Dokus Sent Invoices Resource.
 * Only supports fetching a list of sent invoices.
 */
class DokusSentInvoicesResource extends DokusInvoicesResource {
	protected $path = '/invoices/sent/';
	protected $respAttrSingle = 'sent_invoice';
	protected $respAttrMultiple = 'sent_invoice';

	public function send ($invoice, $byPost = false, $byEmail = false, $emailCopy1 = '', $emailCopy2 = '') {
		throw new Exception("Cannot re-send a sent invoice.");
	}

	public function save ($invoice) {
		throw new Exception("Cannot modify sent invoices.");
	}

	public function delete ($invoice) {
		throw new Exception("Cannot modify sent invoices.");
	}

	public function createCreditInvoice ($invoice) {
		$response = $this->service->request($this->path . $invoice->id . '/credit/create/', 'POST');
		return $response->status == 200 ? $response->invoice : null;
	}

	public function createReminderInvoice ($invoice) {
		$response = $this->service->request($this->path . $invoice->id . '/reminder/create/', 'POST');
		return $response->status == 200 ? $response->invoice : null;
	}

	public function addPayment ($invoice, $payment) {
		throw new Exception("Not implemented yet.");
	}

	public function removePayment ($invoice, $payment) {
		throw new Exception("Not implemented yet.");
	}
}
