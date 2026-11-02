"""Small synthetic report fixture; actual private-workbook verification is separate."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import report_knowledge as report


class ReportKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'report.json'
        self.data={'sourceFile':'synthetic.xlsx','period':{'from':'2026-04-01','to':'2026-11-02'},
            'employees':[{'code':'TEST','name':'Test Employee'}],'leads':[],
            'meetings':[{'sourceId':'7','name':'Synthetic Hospital','employeeCode':'TEST','employeeName':'Test Employee','meetingStatus':'Visited',
             'followups':[{'date':'2026-10-20','status':'Completed'},{'date':'2026-03-10','status':'Pending'}],
             'quotations':[{'status':'Accepted','totalAmount':123.45}],'updates':[],'documents':[]}]}
        self.path.write_text(json.dumps(self.data),encoding='utf-8')
        self.source=patch.object(report,'SOURCE',self.path);self.source.start();self.addCleanup(self.source.stop)

    def test_numeric_answers_and_snapshot_attribution(self):
        facts=report.facts(report.load())
        self.assertEqual(facts['followups_all'],2);self.assertEqual(facts['followups_in_period'],1)
        self.assertEqual(facts['overdue_as_of_report'],1);self.assertEqual(facts['quotation_value'],'123.45')
        answer=report.reply('How many quotations?')
        self.assertIn('123.45',answer);self.assertIn('synthetic.xlsx',answer);self.assertIn('snapshot',answer)

    def test_lookup_employee_and_no_invented_data(self):
        self.assertIn('Synthetic Hospital',report.reply('Find meeting id 7'))
        self.assertIn('Meetings: 1',report.reply('Employee TEST'))
        self.assertIn('does not contain verified',report.reply('What GST tax rate?'))
        self.assertIn('read-only',report.reply('Delete meeting 7'))

    def test_reads_updated_file_and_missing_source(self):
        self.data['meetings']=[];self.path.write_text(json.dumps(self.data),encoding='utf-8')
        self.assertEqual(report.facts(report.load())['meetings'],0)
        self.source.stop();self.source=patch.object(report,'SOURCE',Path(self.temp.name)/'missing.json');self.source.start()
        self.assertFalse(report.status()['available'])
        with self.assertRaises(ValueError):report.reply('Report summary')


if __name__=='__main__':unittest.main()
