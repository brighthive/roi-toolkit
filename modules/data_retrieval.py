import requests
from requests_oauthlib import OAuth2Session
from urllib.parse import urljoin
from datetime import datetime
import os
import json

# API Docs
# https://app.swaggerhub.com/apis-docs/amandajcrawford/colorado-matf/1.0.0

class Credentials:
	client_id = os.getenv('AUTH_CLIENT_KEY')
	client_secret = os.getenv('AUTH_CLIENT_SECRET')
	auth_url = "https://brighthive-test.auth0.com/oauth/token"
	api_base_url = "https://data-resources.reference-data-trust.brighthive.net"
	audience = "http://localhost:8000"
	token_filepath = "tokenfile.json"

def get_token():
	current_time = datetime.now().timestamp()

	if Credentials.client_id is None or Credentials.client_secret is None:
		raise Exception("client id or client secret not specified")

	try: 
		with open(Credentials.token_filepath, "r") as tokenfile:
			data = json.load(tokenfile)
			current_token = data['current_token']
			last_token_retrieval = data['last_token_retrieval']

			if current_time - last_token_retrieval < 86400:
				print(last_token_retrieval)
				return current_token
			else:
				raise Exception("No valid token! Retrieving new token...")
	except:
		headers = {'content-type': 'application/json'}
		data = {'client_id': Credentials.client_id, 'client_secret': Credentials.client_secret,
				'audience': Credentials.audience, 'grant_type': 'client_credentials'}
		r = requests.post(Credentials.auth_url, headers=headers, data=json.dumps(data))
		token = r.json()['access_token']

		# set  variables
		with open(Credentials.token_filepath, "w") as tokenfile:
			data = {"current_token":token, "last_token_retrieval":current_time}
			json.dump(data, tokenfile)

		return token

def make_request(endpoint, token, base_url=Credentials.api_base_url, data = {}):
	headers = {"Authorization": "Bearer {}".format(token)}
	full_url = urljoin(base_url, endpoint)
	r = requests.get(full_url, headers=headers, data=json.dumps(data))
	content = r.content
	parsed_content = json.loads(content)
	return content

def get_programs():
	return None

if __name__ == "__main__":
	token = get_token()
	programs = make_request('programs', token)
	program_prerequisites = make_request('program_prerequisites', token)
	print(token)
	print(programs)
