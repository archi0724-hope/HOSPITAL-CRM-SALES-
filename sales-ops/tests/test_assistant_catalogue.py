"""Catalogue setup, public search links and branding; isolated data only."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

from crm_test_environment import app
from quotesaarthi.runtime import QuoteSaarthiService
from assistant_catalogue import FIELDS


class AssistantCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.service=QuoteSaarthiService(self.root/'products.csv',self.root/'assistant')
        self.db=patch.object(app,'DB_PATH',self.root/'crm.db');self.db.start();self.addCleanup(self.db.stop)
        app.init_db();self.client=app.app.test_client()
        self.provider=patch('quotesaarthi.runtime.get_service',return_value=self.service);self.provider.start();self.addCleanup(self.provider.stop)
        self.csv=(','.join(FIELDS)+'\nIV Set,Vendor A,10,100,Injection,Test maker,Luer lock,Not provided\n').encode()

    def upload(self,content=None,replace=False):
        return self.client.post('/api/assistant/catalogue',data={'file':(io.BytesIO(content if content is not None else self.csv),'catalogue.csv'),'replace':str(replace).lower()})

    def chat(self,text,**kwargs):
        return self.client.post('/api/quotesaarthi/chat',json={'message':text,**kwargs})

    def test_upload_then_actual_search_and_quote(self):
        self.assertFalse(self.client.get('/api/assistant/catalogue').json['available'])
        response=self.upload();self.assertEqual(response.status_code,200);self.assertEqual(response.json['products'],1)
        listing=self.chat('IV Set vendor listing').json
        self.assertIn('Vendor A',listing['reply']);self.assertIn('INR 10.00',listing['reply'])
        self.assertNotIn('QuoteSaarthi',listing['reply'])
        quote=self.chat('Quote IV Set 2 units with 0% discount and GST 18%').json
        self.assertEqual(len(quote['exports']),2);self.assertIn('INR 23.60',quote['reply'])
        self.assertNotIn('QuoteSaarthi',quote['reply']);self.assertEqual(quote['assistant'],'AI Assistance')

    def test_invalid_upload_preserves_existing_and_replacement_is_explicit(self):
        self.upload();before=self.service.catalog.read_bytes()
        self.assertEqual(self.upload().status_code,409)
        invalid=self.csv.replace(b',10,100,',b',-10,100,')
        self.assertEqual(self.upload(invalid,replace=True).status_code,400)
        self.assertEqual(before,self.service.catalog.read_bytes())
        self.assertEqual(self.upload(b'product_name,price\nTest,1\n',replace=True).status_code,400)

    def test_updated_catalogue_is_used_without_restart(self):
        self.upload();first=self.chat('IV Set vendor listing').json
        self.upload(self.csv.replace(b',10,100,',b',15,100,'),replace=True)
        second=self.chat('IV Set vendor listing').json
        self.assertIn('INR 15.00',second['reply'])
        # Existing sessions retain their original catalogue snapshot.
        old=self.chat('IV Set vendor listing',session_id=first['session_id']).json
        self.assertIn('INR 10.00',old['reply'])

    def test_no_catalogue_and_google_search_do_not_call_external_apis(self):
        query='hospital beds Jaipur & Delhi'
        with patch('app.requests.post') as post:
            missing=self.chat('IV Set vendor listing').json
            search=self.chat(query,mode='web').json
            hello=self.chat('hello').json
        post.assert_not_called()
        self.assertTrue(missing['ok']);self.assertIn('Upload catalogue',missing['reply'])
        self.assertIn('AI Assistance',hello['reply'])
        url=urlsplit(search['search_actions'][0]['url'])
        self.assertEqual(url.netloc,'www.google.com');self.assertEqual(parse_qs(url.query)['q'],[query])

    def test_cross_origin_upload_is_rejected(self):
        response=self.client.post('/api/assistant/catalogue',data={'file':(io.BytesIO(self.csv),'catalogue.csv')},headers={'Origin':'https://example.test'})
        self.assertEqual(response.status_code,403);self.assertFalse(self.service.catalog.exists())


if __name__=='__main__':unittest.main()
